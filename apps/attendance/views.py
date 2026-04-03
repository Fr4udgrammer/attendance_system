from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q

from .models import Attendance, AttendanceRule
from apps.accounts.services.face_profile_service import (
    FaceRecognitionDependencyError,
    get_user_known_encodings,
    verify_face_frames,
)
from .serializers import (
    AttendanceSerializer,
    AttendanceRuleSerializer,
    CheckInSerializer,
    CheckOutSerializer,
    DashboardStatsSerializer
)


class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet for Attendance CRUD operations."""

    queryset = Attendance.objects.select_related(
        'employee', 'employee__user', 'employee__department'
    ).all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['employee', 'date', 'status']
    search_fields = ['employee__employee_id', 'employee__user__first_name']
    ordering_fields = ['date', 'check_in', 'created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Attendance.objects.select_related(
                'employee', 'employee__user', 'employee__department'
            ).all()
        elif user.is_manager:
            return Attendance.objects.filter(
                employee__department=user.department
            ).select_related(
                'employee', 'employee__user', 'employee__department'
            )
        return Attendance.objects.filter(
            employee=user.employee
        ).select_related(
            'employee', 'employee__user', 'employee__department'
        )


class CheckInView(APIView):
    """Handle employee check-in."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, 'employee'):
            return Response(
                {'error': 'No employee profile found for this user'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CheckInSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        attendance = serializer.save()

        return Response(
            AttendanceSerializer(attendance).data,
            status=status.HTTP_201_CREATED
        )


class CheckOutView(APIView):
    """Handle employee check-out."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, 'employee'):
            return Response(
                {'error': 'No employee profile found for this user'},
                status=status.HTTP_400_BAD_REQUEST
            )

        today = timezone.now().date()

        try:
            attendance = Attendance.objects.get(
                employee=request.user.employee,
                date=today
            )
        except Attendance.DoesNotExist:
            return Response(
                {'error': 'Not checked in today'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attendance.check_out:
            return Response(
                {'error': 'Already checked out today'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CheckOutSerializer(
            instance=attendance,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        attendance = serializer.save()

        return Response(AttendanceSerializer(attendance).data)


class VerifyFaceView(APIView):
    """Verify face image and perform check-in."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not hasattr(user, 'employee'):
            return Response({'success': False, 'error': 'No employee profile found'})

        frame_images = request.data.get('face_frames')
        if not isinstance(frame_images, list):
            frame_images = []

        single_frame = request.data.get('face_image')
        if isinstance(single_frame, str) and single_frame:
            frame_images.insert(0, single_frame)

        frame_images = [frame for frame in frame_images if isinstance(frame, str) and frame]
        if not frame_images:
            return Response({'success': False, 'error': 'No image data provided'})

        notes = request.data.get('notes', '')

        try:
            known_encodings = get_user_known_encodings(user)
            verification_result = verify_face_frames(
                frame_images,
                known_encodings,
                tolerance=0.55,
            )
            
            print(f"DEBUG: Checking in user {user.username}. Verification result: {verification_result}")

            if not verification_result.get('success'):
                return Response({'success': False, 'error': verification_result.get('error', 'Face verification failed')})

            # Auto-backfill encodings for users enrolled before profile fields were added.
            if not user.face_encodings and known_encodings:
                user.face_encodings = known_encodings
                if user.face_registered_at is None:
                    user.face_registered_at = timezone.now()
                user.save(update_fields=['face_encodings', 'face_registered_at'])
        except FaceRecognitionDependencyError as e:
            print(f"DEBUG: FaceRecognitionDependencyError: {e}")
            return Response({'success': False, 'error': str(e)})
        except Exception as e:
            print(f"DEBUG: Exception during verification: {e}")
            return Response({'success': False, 'error': f'Recognition error: {str(e)}'})

        # Process check-in for the verified user
        today = timezone.now().date()
        try:
            best_distance = verification_result.get('best_distance', 'N/A')
            liveness_verified = verification_result.get('liveness_verified', False)
            liveness_status = "Verified" if liveness_verified else "Skipped"
            system_note = f"[Liveness: {liveness_status} | Match Distance: {best_distance}]"
            
            combined_notes = f"{notes}\n{system_note}".strip() if notes else system_note

            # Check if already checked in
            attendance, created = Attendance.objects.get_or_create(
                employee=user.employee,
                date=today,
                defaults={
                    'check_in': timezone.now(),
                    'status': 'present',
                    'notes': combined_notes
                }
            )

            if not created:
                if not attendance.check_out:
                    # Handle check-out if already checked in
                    attendance.check_out = timezone.now()
                    existing_notes = attendance.notes or ''
                    out_note = f"OUT: {notes}" if notes else "OUT: (No User Note)"
                    attendance.notes = f"{existing_notes}\n{out_note}\n{system_note}".strip()
                    attendance.save()
                    return Response({
                        'success': True,
                        'message': f'Face verified! Check-out successful for {user.get_full_name()}'
                    })
                return Response({'success': False, 'error': 'Already checked out for today'})

            return Response({
                'success': True,
                'message': f'Face verified! Check-in successful for {user.get_full_name()}'
            })

        except Exception as e:
            return Response({'success': False, 'error': str(e)})


class TodayAttendanceView(APIView):
    """Get today's attendance status for current user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'employee'):
            return Response({'status': 'no_profile'})

        today = timezone.now().date()

        try:
            attendance = Attendance.objects.get(
                employee=request.user.employee,
                date=today
            )
            return Response({
                'status': 'checked_in',
                'checked_in': attendance.check_in,
                'checked_out': attendance.check_out,
                'attendance_status': attendance.status
            })
        except Attendance.DoesNotExist:
            return Response({'status': 'not_checked_in'})


class AttendanceStatsView(APIView):
    """Get attendance statistics."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        base_queryset = Attendance.objects.filter(date=today)
        if user.is_manager and not user.is_admin:
            base_queryset = base_queryset.filter(employee__department=user.department)

        present = base_queryset.filter(status__in=['present', 'late']).count()
        late = base_queryset.filter(status='late').count()
        absent = base_queryset.filter(status='absent').count()

        total = Attendance.objects.filter(
            employee__status='active'
        )
        if user.is_manager and not user.is_admin:
            total = total.filter(department=user.department)
        total = total.count()

        return Response({
            'today': {
                'present': present,
                'late': late,
                'absent': absent,
                'total': total,
                'attendance_rate': round(present / total * 100, 1) if total > 0 else 0
            }
        })


class AttendanceRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for AttendanceRule CRUD operations."""

    queryset = AttendanceRule.objects.all()
    serializer_class = AttendanceRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_admin:
            return AttendanceRule.objects.all()
        return AttendanceRule.objects.filter(is_active=True)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current active rule."""
        rule = AttendanceRule.objects.filter(is_active=True).first()
        if rule:
            return Response(AttendanceRuleSerializer(rule).data)
        return Response({'error': 'No active rule found'}, status=404)

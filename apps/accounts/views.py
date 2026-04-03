from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from axes.decorators import axes_dispatch
from django.utils.decorators import method_decorator

from .serializers import UserSerializer, UserCreateSerializer

User = get_user_model()


@method_decorator(axes_dispatch, name='dispatch')
class LoginView(APIView):
    """User login view."""

    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'error': 'Username and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return Response({
                'message': 'Login successful',
                'user': UserSerializer(user).data
            })
        else:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    """User logout view."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful'})


class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile view."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserRegistrationView(generics.CreateAPIView):
    """User registration view."""

    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics."""
    from apps.attendance.models import Attendance
    from apps.employees.models import Employee
    from django.utils import timezone

    today = timezone.now().date()

    total_employees = Employee.objects.filter(status='active').count()
    today_attendance = Attendance.objects.filter(date=today)
    present_today = today_attendance.filter(status__in=['present', 'late']).count()
    absent_today = total_employees - present_today
    late_today = today_attendance.filter(status='late').count()

    attendance_rate = (present_today / total_employees * 100) if total_employees > 0 else 0
    on_time_rate = (today_attendance.filter(status='present').count() / present_today * 100) if present_today > 0 else 0

    return Response({
        'total_employees': total_employees,
        'present_today': present_today,
        'absent_today': absent_today,
        'late_today': late_today,
        'attendance_rate': round(attendance_rate, 1),
        'on_time_rate': round(on_time_rate, 1)
    })


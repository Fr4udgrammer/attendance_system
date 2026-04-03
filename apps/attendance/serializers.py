from rest_framework import serializers
from django.utils import timezone
from django.conf import settings
from .models import Attendance, AttendanceRule, CorrectionRequest, AttendanceAuditLog
from apps.employees.models import Employee, Schedule, Shift
from apps.employees.serializers import EmployeeListSerializer


class AttendanceRuleSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceRule model."""

    class Meta:
        model = AttendanceRule
        fields = ['id', 'name', 'check_in_start', 'check_in_end',
                  'check_out_start', 'check_out_end', 'late_threshold', 'is_active',
                  'effective_from', 'effective_to']


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance model."""

    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    employee_id_code = serializers.CharField(source='employee.employee_id', read_only=True)
    department = serializers.CharField(source='employee.department.name', read_only=True)
    duration = serializers.ReadOnlyField()

    class Meta:
        model = Attendance
        fields = ['id', 'employee', 'employee_name', 'employee_id_code',
                  'department', 'date', 'check_in', 'check_out',
                  'status', 'notes', 'duration', 'created_at']
        read_only_fields = ['id', 'created_at']


class CorrectionRequestSerializer(serializers.ModelSerializer):
    """Serializer for CorrectionRequest model."""

    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    date = serializers.DateField(source='attendance.date', read_only=True)

    class Meta:
        model = CorrectionRequest
        fields = ['id', 'attendance', 'employee', 'employee_name', 'date',
                  'requested_check_in', 'requested_check_out', 'reason',
                  'status', 'reviewed_by', 'reviewed_by_name', 'review_notes',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'employee', 'status', 'reviewed_by', 'created_at', 'updated_at']

    def validate(self, attrs):
        request = self.context.get('request')
        if request and hasattr(request.user, 'employee'):
            attrs['employee'] = request.user.employee
        return attrs


from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class CheckInSerializer(serializers.Serializer):
    """Serializer for check-in."""

    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        employee = self.context['request'].user.employee
        today = timezone.now().date()

        if Attendance.objects.filter(employee=employee, date=today).exists():
            raise serializers.ValidationError("Already checked in today.")

        return attrs

    def create(self, validated_data):
        employee = self.context['request'].user.employee
        today = timezone.now().date()
        now = timezone.now()

        # Try to find a schedule for today
        schedule = Schedule.objects.filter(employee=employee, date=today).first()
        status = 'present'
        penalty_minutes = 0

        if schedule:
            shift = schedule.shift
            from datetime import datetime, combine
            shift_start_dt = combine(today, shift.start_time)
            # Make shift_start_dt timezone aware if settings.USE_TZ is True
            if settings.USE_TZ:
                from django.utils.timezone import make_aware, get_current_timezone
                shift_start_dt = make_aware(shift_start_dt, get_current_timezone())

            late_margin = shift_start_dt + timezone.timedelta(minutes=shift.grace_period)
            
            if now > late_margin:
                status = 'late'
                penalty_minutes = int((now - shift_start_dt).total_seconds() / 60)
        else:
            # Fallback to old AttendanceRule logic if no schedule exists
            rule = AttendanceRule.objects.filter(is_active=True).first()
            if rule and now.time() > rule.check_in_end:
                status = 'late'

        attendance = Attendance.objects.create(
            employee=employee,
            schedule=schedule,
            date=today,
            check_in=now,
            status=status,
            penalty_minutes=penalty_minutes,
            notes=validated_data.get('notes', '')
        )

        # Send WebSocket update
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'attendance_updates',
            {
                'type': 'attendance_update',
                'message': {
                    'action': 'check-in',
                    'employee': employee.full_name,
                    'department': employee.department.name,
                    'status': status,
                    'shift': schedule.shift.name if schedule else "No Schedule",
                    'time': now.strftime('%H:%M:%S')
                }
            }
        )
        return attendance


class CheckOutSerializer(serializers.Serializer):
    """Serializer for check-out."""

    notes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        employee = self.context['request'].user.employee
        today = timezone.now().date()

        try:
            attendance = Attendance.objects.get(employee=employee, date=today)
        except Attendance.DoesNotExist:
            raise serializers.ValidationError("Not checked in today.")

        if attendance.check_out:
            raise serializers.ValidationError("Already checked out today.")

        return attrs

    def update(self, instance, validated_data):
        now = timezone.now()
        instance.check_out = now
        instance.notes = validated_data.get('notes', instance.notes)
        
        # Calculate overtime if schedule exists
        if instance.schedule:
            shift = instance.schedule.shift
            from datetime import combine
            shift_end_dt = combine(instance.date, shift.end_time)
            if settings.USE_TZ:
                from django.utils.timezone import make_aware, get_current_timezone
                shift_end_dt = make_aware(shift_end_dt, get_current_timezone())
            
            # Simple daily overtime: checkout after shift end
            if now > shift_end_dt:
                ot_delta = now - shift_end_dt
                instance.overtime_hours = round(ot_delta.total_seconds() / 3600, 2)
            else:
                instance.overtime_hours = 0
        
        instance.save()
        return instance


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics."""

    total_employees = serializers.IntegerField()
    present_today = serializers.IntegerField()
    absent_today = serializers.IntegerField()
    late_today = serializers.IntegerField()
    attendance_rate = serializers.FloatField()
    on_time_rate = serializers.FloatField()

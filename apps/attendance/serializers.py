from rest_framework import serializers
from django.utils import timezone
from django.conf import settings
from .models import Attendance, AttendanceRule
from apps.employees.serializers import EmployeeListSerializer


class AttendanceRuleSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceRule model."""

    class Meta:
        model = AttendanceRule
        fields = ['id', 'name', 'check_in_start', 'check_in_end',
                  'check_out_start', 'check_out_end', 'late_threshold', 'is_active']


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

        rule = AttendanceRule.objects.filter(is_active=True).first()
        status = 'present'

        if rule and now.time() > rule.check_in_end:
            status = 'late'

        attendance = Attendance.objects.create(
            employee=employee,
            date=today,
            check_in=now,
            status=status,
            notes=validated_data.get('notes', '')
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
        instance.check_out = timezone.now()
        instance.notes = validated_data.get('notes', instance.notes)
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

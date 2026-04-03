from rest_framework import serializers
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta


class ReportFilterSerializer(serializers.Serializer):
    """Serializer for filtering reports."""

    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    from_date = serializers.DateField(required=False, help_text="Alias for start_date")
    to_date = serializers.DateField(required=False, help_text="Alias for end_date")
    employee_id = serializers.IntegerField(required=False)
    department_id = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(
        choices=['present', 'late', 'absent', 'half_day'],
        required=False
    )

    def to_internal_value(self, data):
        # Handle 'from' and 'to' as query params
        if 'from' in data:
            data = data.copy()
            data['from_date'] = data.pop('from')
        if 'to' in data:
            data = data.copy()
            data['to_date'] = data.pop('to')
        return super().to_internal_value(data)


class AttendanceReportSerializer(serializers.Serializer):
    """Serializer for attendance report data."""

    total_records = serializers.IntegerField()
    present_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    half_day_count = serializers.IntegerField()
    average_duration = serializers.FloatField()
    attendance_rate = serializers.FloatField()


class MonthlySummarySerializer(serializers.Serializer):
    """Serializer for monthly summary."""

    month = serializers.CharField()
    year = serializers.IntegerField()
    total_days = serializers.IntegerField()
    total_present = serializers.IntegerField()
    total_late = serializers.IntegerField()
    total_absent = serializers.IntegerField()
    average_attendance_rate = serializers.FloatField()

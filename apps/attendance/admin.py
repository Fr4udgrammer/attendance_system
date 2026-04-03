from django.contrib import admin
from .models import Attendance, AttendanceRule


@admin.register(AttendanceRule)
class AttendanceRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'check_in_start', 'check_in_end', 'check_out_start', 'check_out_end', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'check_in', 'check_out', 'status', 'duration']
    search_fields = ['employee__employee_id', 'employee__user__first_name']
    list_filter = ['status', 'date']
    date_hierarchy = 'date'
    ordering = ['-date', '-check_in']

    def duration(self, obj):
        hours = obj.duration
        return f"{hours}h" if hours else "-"
    duration.short_description = 'Duration'

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Department, Employee, SchoolYear, Semester, ClassSchedule,
    LeaveRequest, LeaveBalance, SubstituteLog
)


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'status', 'created_at']
    list_filter = ['status', 'leave_type', 'start_date']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'reason']
    ordering = ['-created_at']
    actions = ['approve_by_head', 'approve_by_hr']

    def approve_by_head(self, request, queryset):
        queryset.update(status='head_approved', head_approver=request.user)
    approve_by_head.short_description = "Approve selected (Head)"

    def approve_by_hr(self, request, queryset):
        queryset.update(status='approved', hr_approver=request.user)
    approve_by_hr.short_description = "Approve selected (HR)"


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'sick_leave', 'vacation_leave', 'forced_leave', 'updated_at']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']
    ordering = ['-updated_at']


@admin.register(SubstituteLog)
class SubstituteLogAdmin(admin.ModelAdmin):
    list_display = ['substitute_teacher', 'original_teacher', 'date', 'class_schedule', 'is_compensated']
    list_filter = ['date', 'is_compensated']
    search_fields = ['substitute_teacher__user__first_name', 'original_teacher__user__first_name']
    ordering = ['-date']


@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_active']
    search_fields = ['name']
    list_filter = ['is_active']
    ordering = ['-start_date']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'head', 'employee_count', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['created_at']
    ordering = ['name']

    def employee_count(self, obj):
        return obj.employees.count()
    employee_count.short_description = 'Employees'


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['name', 'school_year', 'start_date', 'end_date', 'is_active']
    search_fields = ['name', 'school_year__name']
    list_filter = ['is_active', 'school_year']
    ordering = ['-start_date']


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ['subject_code', 'subject_description', 'teacher', 'day_of_week_label', 'time_slot', 'room', 'semester']
    search_fields = ['subject_code', 'subject_description', 'teacher__user__first_name', 'teacher__user__last_name']
    list_filter = ['day_of_week', 'semester', 'semester__school_year']
    ordering = ['semester', 'day_of_week', 'start_time']

    def day_of_week_label(self, obj):
        return obj.get_day_of_week_display()
    day_of_week_label.short_description = 'Day'

    def time_slot(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_slot.short_description = 'Time'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'department', 'position', 'status', 'hire_date']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'position']
    list_filter = ['status', 'department', 'hire_date']
    ordering = ['-created_at']

    def full_name(self, obj):
        return obj.user.get_full_name()
    full_name.short_description = 'Name'

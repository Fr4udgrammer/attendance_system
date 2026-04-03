from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Department, Employee


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'head', 'employee_count', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['created_at']
    ordering = ['name']

    def employee_count(self, obj):
        return obj.employees.count()
    employee_count.short_description = 'Employees'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'department', 'position', 'status', 'hire_date']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'position']
    list_filter = ['status', 'department', 'hire_date']
    ordering = ['-created_at']

    def full_name(self, obj):
        return obj.user.get_full_name()
    full_name.short_description = 'Name'

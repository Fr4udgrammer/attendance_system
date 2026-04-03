from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.db import transaction

from apps.employees.models import Department, Employee
from apps.attendance.models import Attendance, AttendanceRule
from django.utils import timezone
from datetime import timedelta, datetime
import csv
import io
import json
from django.http import HttpResponse

from .services.face_profile_service import (
    FaceRecognitionDependencyError,
    analyze_registration_samples,
    save_avatar_from_data_url,
    validate_single_sample,
)


@method_decorator(login_required, name='dispatch')
class EmployeeListView(View):
    """List all employees."""

    template_name = 'employees/list.html'

    def get(self, request):
        user = request.user

        if user.is_admin:
            employees = Employee.objects.select_related('user', 'department').all()
            departments = Department.objects.all()
        elif user.is_manager:
            employees = Employee.objects.filter(
                department=user.department
            ).select_related('user', 'department')
            departments = Department.objects.filter(id=user.department.id)
        else:
            return redirect('dashboard')

        status_filter = request.GET.get('status', '')
        dept_filter = request.GET.get('department', '')
        search = request.GET.get('search', '')

        if status_filter:
            employees = employees.filter(status=status_filter)
        if dept_filter:
            employees = employees.filter(department_id=dept_filter)
        if search:
            employees = employees.filter(
                user__first_name__icontains=search
            ) | employees.filter(
                user__last_name__icontains=search
            ) | employees.filter(
                employee_id__icontains=search
            )

        context = {
            'employees': employees,
            'departments': departments,
            'status_filter': status_filter,
            'dept_filter': dept_filter,
            'search': search,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class EmployeeAddView(View):
    """Add new employee."""

    template_name = 'employees/add.html'

    def get(self, request):
        if not request.user.is_manager:
            return redirect('dashboard')

        departments = Department.objects.all()
        return render(request, self.template_name, {'departments': departments})

    def post(self, request):
        if not request.user.is_manager:
            return redirect('dashboard')

        from django.contrib.auth import get_user_model
        User = get_user_model()

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        employee_id = request.POST.get('employee_id')
        department_id = request.POST.get('department')
        position = request.POST.get('position')
        hire_date = request.POST.get('hire_date')
        role = request.POST.get('role', 'employee')
        face_image_data = request.POST.get('face_image')
        face_samples_raw = request.POST.get('face_samples', '[]')

        try:
            parsed_samples = json.loads(face_samples_raw) if face_samples_raw else []
            if not isinstance(parsed_samples, list):
                parsed_samples = []
        except json.JSONDecodeError:
            parsed_samples = []

        if face_image_data:
            parsed_samples.insert(0, face_image_data)

        # Preserve order and remove duplicate frames.
        face_samples = []
        seen_samples = set()
        for sample in parsed_samples:
            if isinstance(sample, str) and sample and sample not in seen_samples:
                face_samples.append(sample)
                seen_samples.add(sample)

        try:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists')
                return redirect('employee-add')
            profile_result = analyze_registration_samples(face_samples, min_valid_samples=3)
            if not profile_result.get('success'):
                messages.error(request, profile_result.get('error', 'Face profile registration failed'))
                return redirect('employee-add')

            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    department_id=department_id if department_id else None
                )

                save_avatar_from_data_url(user, profile_result['primary_image'], user.username)
                user.face_encodings = profile_result['encodings']
                user.face_profile = profile_result['analysis']
                user.face_registered_at = timezone.now()
                user.save()

                employee = Employee.objects.create(
                    user=user,
                    employee_id=employee_id,
                    department_id=department_id,
                    position=position,
                    hire_date=hire_date
                )

            valid_samples = profile_result.get('analysis', {}).get('valid_samples', 0)
            messages.success(
                request,
                f'Employee {employee.user.get_full_name()} created with analyzed face profile ({valid_samples} samples).'
            )
        except FaceRecognitionDependencyError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error creating employee: {str(e)}')

        return redirect('employee-list')


@method_decorator(login_required, name='dispatch')
class EmployeeEditView(View):
    """Edit employee."""

    template_name = 'employees/edit.html'

    def get(self, request, pk):
        if not request.user.is_manager:
            return redirect('dashboard')

        employee = get_object_or_404(Employee, pk=pk)
        departments = Department.objects.all()

        context = {
            'employee': employee,
            'departments': departments,
        }
        return render(request, self.template_name, context)

    def post(self, request, pk):
        if not request.user.is_manager:
            return redirect('dashboard')

        employee = get_object_or_404(Employee, pk=pk)

        employee.employee_id = request.POST.get('employee_id')
        employee.department_id = request.POST.get('department')
        employee.position = request.POST.get('position')
        employee.hire_date = request.POST.get('hire_date')
        employee.status = request.POST.get('status')
        employee.save()

        user = employee.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.role = request.POST.get('role')
        user.save()

        messages.success(request, 'Employee updated successfully')
        return redirect('employee-list')


@method_decorator(login_required, name='dispatch')
class EmployeeDeleteView(View):
    """Delete employee."""

    def post(self, request, pk):
        if not request.user.is_admin:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        employee = get_object_or_404(Employee, pk=pk)
        name = employee.user.get_full_name()
        employee.user.delete()
        employee.delete()

        messages.success(request, f'Employee {name} deleted successfully')
        return redirect('employee-list')


@method_decorator(login_required, name='dispatch')
class DepartmentListView(View):
    """List all departments."""

    template_name = 'departments/list.html'

    def get(self, request):
        if not request.user.is_manager:
            return redirect('dashboard')

        departments = Department.objects.all().prefetch_related('employees')
        return render(request, self.template_name, {'departments': departments})


@method_decorator(login_required, name='dispatch')
class DepartmentAddView(View):
    """Add new department."""

    template_name = 'departments/add.html'

    def get(self, request):
        if not request.user.is_admin:
            return redirect('dashboard')

        departments = Department.objects.filter(head__isnull=True)
        return render(request, self.template_name, {'departments': departments})

    def post(self, request):
        if not request.user.is_admin:
            return redirect('dashboard')

        name = request.POST.get('name')
        code = request.POST.get('code')
        description = request.POST.get('description', '')
        head_id = request.POST.get('head')

        try:
            dept = Department.objects.create(
                name=name,
                code=code.upper(),
                description=description,
                head_id=head_id if head_id else None
            )
            messages.success(request, f'Department {name} created successfully')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

        return redirect('department-list')


@method_decorator(login_required, name='dispatch')
class AttendanceListView(View):
    """List attendance records."""

    template_name = 'attendance/list.html'

    def get(self, request):
        user = request.user
        today = timezone.now().date()

        date_from = request.GET.get('from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.GET.get('to', today.strftime('%Y-%m-%d'))
        status_filter = request.GET.get('status', '')
        employee_filter = request.GET.get('employee', '')

        if user.is_admin:
            records = Attendance.objects.select_related(
                'employee', 'employee__user', 'employee__department'
            ).all()
        elif user.is_manager:
            records = Attendance.objects.filter(
                employee__department=user.department
            ).select_related(
                'employee', 'employee__user', 'employee__department'
            )
        else:
            records = Attendance.objects.filter(
                employee=user.employee
            ).select_related(
                'employee', 'employee__user', 'employee__department'
            )

        if date_from:
            records = records.filter(date__gte=date_from)
        if date_to:
            records = records.filter(date__lte=date_to)
        if status_filter:
            records = records.filter(status=status_filter)
        if employee_filter:
            records = records.filter(employee_id=employee_filter)

        records = records.order_by('-date', '-check_in')

        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(records, 20)  # Show 20 records per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'records': page_obj,
            'date_from': date_from,
            'date_to': date_to,
            'status_filter': status_filter,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class AttendanceCheckInView(View):
    """Face-based check-in page."""

    template_name = 'attendance/checkin.html'

    def get(self, request):
        return render(request, self.template_name)


@method_decorator(login_required, name='dispatch')
class ReportsView(View):
    """Attendance reports."""

    template_name = 'reports/list.html'

    def get(self, request):
        user = request.user
        today = timezone.now().date()

        date_from = request.GET.get('from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.GET.get('to', today.strftime('%Y-%m-%d'))

        if user.is_admin:
            records = Attendance.objects.all()
        elif user.is_manager:
            records = Attendance.objects.filter(employee__department=user.department)
        else:
            records = Attendance.objects.filter(employee=user.employee)

        if date_from:
            records = records.filter(date__gte=date_from)
        if date_to:
            records = records.filter(date__lte=date_to)

        total = records.count()
        present = records.filter(status='present').count()
        late = records.filter(status='late').count()
        absent = records.filter(status='absent').count()
        half_day = records.filter(status='half_day').count()

        rate = round((present + late) / total * 100, 1) if total > 0 else 0

        context = {
            'date_from': date_from,
            'date_to': date_to,
            'total': total,
            'present': present,
            'late': late,
            'absent': absent,
            'half_day': half_day,
            'rate': rate,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class SettingsView(View):
    """System settings."""

    template_name = 'settings.html'

    def get(self, request):
        if not request.user.is_admin:
            return redirect('dashboard')

        rules = AttendanceRule.objects.all()
        context = {
            'rules': rules,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        if not request.user.is_admin:
            return redirect('dashboard')

        action = request.POST.get('action')

        if action == 'update_rule':
            rule_id = request.POST.get('rule_id')
            rule = get_object_or_404(AttendanceRule, pk=rule_id)
            rule.name = request.POST.get('name')
            rule.check_in_start = request.POST.get('check_in_start')
            rule.check_in_end = request.POST.get('check_in_end')
            rule.check_out_start = request.POST.get('check_out_start')
            rule.check_out_end = request.POST.get('check_out_end')
            rule.late_threshold = request.POST.get('late_threshold')
            rule.save()
            messages.success(request, 'Attendance rule updated')

        elif action == 'add_rule':
            AttendanceRule.objects.create(
                name=request.POST.get('name'),
                check_in_start=request.POST.get('check_in_start'),
                check_in_end=request.POST.get('check_in_end'),
                check_out_start=request.POST.get('check_out_start'),
                check_out_end=request.POST.get('check_out_end'),
                late_threshold=request.POST.get('late_threshold') or 15,
                is_active=True
            )
            messages.success(request, 'Attendance rule created')

        return redirect('settings')


@method_decorator(login_required, name='dispatch')
class ValidateFaceSampleView(View):
    """Validate a single face sample during registration."""
    
    def post(self, request):
        if not request.user.is_manager:
            return JsonResponse({'valid': False, 'guidance': 'Permission denied.'}, status=403)
            
        try:
            data = json.loads(request.body)
            face_image = data.get('face_image')
            
            if not face_image:
                return JsonResponse({'valid': False, 'guidance': 'No image data provided.'})
                
            result = validate_single_sample(face_image)
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({'valid': False, 'guidance': f'Server error: {str(e)}'}, status=500)


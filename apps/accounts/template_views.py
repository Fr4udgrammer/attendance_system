from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.contrib.auth import authenticate

from apps.attendance.models import Attendance, AttendanceRule
from apps.employees.models import Employee, Department
from django.utils import timezone
from datetime import timedelta


@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    """Main dashboard view."""

    template_name = 'dashboard.html'

    def get(self, request):
        user = request.user
        today = timezone.now().date()

        total_employees = Employee.objects.filter(status='active').count()
        today_attendance = Attendance.objects.filter(date=today)
        present_today = today_attendance.filter(status__in=['present', 'late']).count()
        late_today = today_attendance.filter(status='late').count()
        absent_today = total_employees - present_today

        attendance_rate = (present_today / total_employees * 100) if total_employees > 0 else 0

        recent_records = Attendance.objects.select_related(
            'employee', 'employee__user', 'employee__department'
        ).order_by('-date', '-check_in')[:10]

        departments = Department.objects.all()

        context = {
            'total_employees': total_employees,
            'present_today': present_today,
            'late_today': late_today,
            'absent_today': absent_today,
            'attendance_rate': round(attendance_rate, 1),
            'recent_records': recent_records,
            'departments': departments,
            'user': user,
        }
        return render(request, self.template_name, context)


class LoginPageView(View):
    """Login page view."""

    template_name = 'login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, self.template_name)


class LogoutPageView(View):
    """Logout page view."""

    def get(self, request):
        logout(request)
        return redirect('login-page')

    def post(self, request):
        logout(request)
        return redirect('login-page')

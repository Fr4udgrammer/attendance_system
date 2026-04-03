from django.urls import path
from .template_views import DashboardView, LoginPageView, LogoutPageView
from .feature_views import (
    EmployeeListView, EmployeeAddView, EmployeeEditView, EmployeeDeleteView,
    DepartmentListView, DepartmentAddView,
    AttendanceListView, AttendanceCheckInView, ReportsView, SettingsView,
    ValidateFaceSampleView
)

urlpatterns = [
    path('', LoginPageView.as_view(), name='login-page'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('accounts/logout/', LogoutPageView.as_view(), name='logout-page'),

    # Employee URLs
    path('employees/', EmployeeListView.as_view(), name='employee-list'),
    path('employees/add/', EmployeeAddView.as_view(), name='employee-add'),
    path('employees/<int:pk>/edit/', EmployeeEditView.as_view(), name='employee-edit'),
    path('employees/<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee-delete'),
    
    # Validation URLs
    path('api/accounts/validate-face-sample/', ValidateFaceSampleView.as_view(), name='validate-face-sample'),

    # Department URLs
    path('departments/', DepartmentListView.as_view(), name='department-list'),
    path('departments/add/', DepartmentAddView.as_view(), name='department-add'),

    # Attendance URLs
    path('attendance/', AttendanceListView.as_view(), name='attendance-list'),
    path('attendance/check-in-camera/', AttendanceCheckInView.as_view(), name='attendance-check-in-camera'),

    # Reports URLs
    path('reports/', ReportsView.as_view(), name='reports'),

    # Settings
    path('settings/', SettingsView.as_view(), name='settings'),
]

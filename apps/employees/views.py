from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Department, Employee
from .serializers import (
    DepartmentSerializer,
    EmployeeListSerializer,
    EmployeeDetailSerializer,
    EmployeeCreateUpdateSerializer
)


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Department CRUD operations."""

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code', 'created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Department.objects.all()
        if user.is_manager and user.department:
            return Department.objects.filter(id=user.department.id)
        return Department.objects.none()


class EmployeeViewSet(viewsets.ModelViewSet):
    """ViewSet for Employee CRUD operations."""

    queryset = Employee.objects.select_related('user', 'department').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'status']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'position']
    ordering_fields = ['employee_id', 'hire_date', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EmployeeCreateUpdateSerializer
        return EmployeeDetailSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Employee.objects.select_related('user', 'department').all()
        elif user.is_manager:
            return Employee.objects.filter(
                department=user.department
            ).select_related('user', 'department')
        return Employee.objects.filter(user=user).select_related('user', 'department')

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get employee statistics."""
        queryset = self.get_queryset()
        return Response({
            'total': queryset.count(),
            'active': queryset.filter(status='active').count(),
            'inactive': queryset.filter(status='inactive').count(),
            'on_leave': queryset.filter(status='on_leave').count(),
        })

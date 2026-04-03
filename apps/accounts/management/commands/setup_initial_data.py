from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.employees.models import Department, Employee
from apps.attendance.models import AttendanceRule
from datetime import time

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up initial data for the attendance system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')

        # Create admin user if not exists
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='System',
                last_name='Admin',
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user: admin / admin123'))
        else:
            self.stdout.write('Admin user already exists')

        # Create departments
        departments_data = [
            {'name': 'Engineering', 'code': 'ENG'},
            {'name': 'Human Resources', 'code': 'HR'},
            {'name': 'Marketing', 'code': 'MKT'},
            {'name': 'Finance', 'code': 'FIN'},
            {'name': 'Operations', 'code': 'OPS'},
        ]

        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults={'name': dept_data['name']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created department: {dept.name}'))

        # Create attendance rule
        if not AttendanceRule.objects.filter(is_active=True).exists():
            rule = AttendanceRule.objects.create(
                name='Default Rule',
                check_in_start=time(8, 0),
                check_in_end=time(9, 30),
                check_out_start=time(17, 0),
                check_out_end=time(18, 30),
                late_threshold=15,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('Created default attendance rule'))
        else:
            self.stdout.write('Attendance rule already exists')

        self.stdout.write(self.style.SUCCESS('Initial setup complete!'))

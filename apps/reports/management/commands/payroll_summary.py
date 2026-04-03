from django.core.management.base import BaseCommand
from apps.attendance.models import Attendance
from apps.employees.models import Employee, Schedule
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generate a summary of payroll data for a given period'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30, help='Number of days to look back')

    def handle(self, *args, **options):
        days = options['days']
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        self.stdout.write(f"Generating payroll summary from {start_date} to {end_date}")
        
        employees = Employee.objects.all()
        
        for emp in employees:
            records = Attendance.objects.filter(
                employee=emp, 
                date__range=[start_date, end_date]
            ).aggregate(
                total_ot=Sum('overtime_hours'),
                total_penalties=Sum('penalty_minutes'),
                days_present=Count('id')
            )
            
            # Simple logic: Regular hours = 8 * days_present (placeholder)
            # In a real system, we'd sum (check_out - check_in) minus OT
            
            total_ot = records['total_ot'] or 0
            total_penalties = records['total_penalties'] or 0
            days_present = records['days_present'] or 0
            
            self.stdout.write(
                f"Employee: {emp.employee_id} | Name: {emp.full_name} | "
                f"Present: {days_present} days | OT: {total_ot}h | Penalty: {total_penalties}min"
            )

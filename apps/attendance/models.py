from django.db import models
from django.conf import settings
from django.utils import timezone


class AttendanceRule(models.Model):
    """Attendance rules for check-in/check-out times."""

    name = models.CharField(max_length=100)
    check_in_start = models.TimeField()
    check_in_end = models.TimeField()
    check_out_start = models.TimeField()
    check_out_end = models.TimeField()
    late_threshold = models.IntegerField(default=15)  # minutes
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_rules'
        verbose_name_plural = 'attendance rules'

    def __str__(self):
        return self.name


class Attendance(models.Model):
    """Attendance record for employees."""

    STATUS_CHOICES = [
        ('present', 'Present'),
        ('late', 'Late'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
    ]

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_records'
        constraints = [
            models.UniqueConstraint(fields=['employee', 'date'], name='unique_attendance_employee_date')
        ]
        ordering = ['-date', '-check_in']

    def __str__(self):
        return f"{self.employee} - {self.date}"

    @property
    def duration(self):
        """Calculate work duration in hours."""
        if self.check_in and self.check_out:
            delta = self.check_out - self.check_in
            return round(delta.total_seconds() / 3600, 1)
        return None

    def auto_check_out(self):
        """Automatically set check-out time based on rules."""
        if self.check_in and not self.check_out:
            rule = AttendanceRule.objects.filter(is_active=True).first()
            if rule:
                self.check_out = timezone.now()
                self.save()
        return self.check_out

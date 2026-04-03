from django.db import models
from django.conf import settings
from django.utils import timezone
import json


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
    effective_from = models.DateField(default=timezone.now)
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'attendance_rules'
        verbose_name_plural = 'attendance rules'
        ordering = ['-effective_from']

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
    schedule = models.OneToOneField(
        'employees.Schedule',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance'
    )
    date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    penalty_minutes = models.PositiveIntegerField(default=0)
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


class AttendanceAuditLog(models.Model):
    """Immutable audit trail for attendance changes."""

    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]

    attendance = models.ForeignKey(
        Attendance,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='attendance_audits'
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    changes = models.JSONField()  # Stores before/after values
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'attendance_audit_logs'
        ordering = ['-timestamp']


class CorrectionRequest(models.Model):
    """Employee self-service request to correct an attendance record."""

    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    attendance = models.ForeignKey(
        Attendance,
        on_delete=models.CASCADE,
        related_name='correction_requests'
    )
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='correction_requests'
    )
    requested_check_in = models.DateTimeField(null=True, blank=True)
    requested_check_out = models.DateTimeField(null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_corrections'
    )
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_correction_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"Correction: {self.employee} - {self.attendance.date}"


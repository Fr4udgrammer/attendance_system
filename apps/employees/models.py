from django.db import models
from django.conf import settings


class Department(models.Model):
    """Department model for organizing employees."""

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    head = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='subdepartments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'departments'
        verbose_name_plural = 'departments'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Employee(models.Model):
    """Employee model linked to User."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee'
    )
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='employees'
    )
    position = models.CharField(max_length=100)
    hire_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employees'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"

    @property
    def full_name(self):
        return self.user.get_full_name()


class Shift(models.Model):
    """Shift templates defining standard work hours."""

    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_period = models.PositiveIntegerField(default=15, help_text="Grace period in minutes for late check-in")
    break_duration = models.PositiveIntegerField(default=60, help_text="Unpaid break duration in minutes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shifts'

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"

    @property
    def duration(self):
        """Total duration of the shift in hours (excluding break)."""
        from datetime import datetime, date, combine, timedelta
        dummy_date = date.today()
        start = combine(dummy_date, self.start_time)
        end = combine(dummy_date, self.end_time)
        if end <= start:
            end += timedelta(days=1)
        total_seconds = (end - start).total_seconds()
        return (total_seconds / 3600) - (self.break_duration / 60)


class Schedule(models.Model):
    """Daily schedule assignments for employees."""

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'schedules'
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.date} ({self.shift.name})"


class SchoolYear(models.Model):
    """Academic school year (e.g., 2025-2026)."""
    
    name = models.CharField(max_length=50, unique=True, help_text="e.g., 2025-2026")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'school_years'
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_active:
            SchoolYear.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)


class Semester(models.Model):
    """Academic semester within a school year."""
    
    SEMESTER_CHOICES = [
        ('1st', 'First Semester'),
        ('2nd', 'Second Semester'),
        ('summer', 'Summer/Midyear'),
    ]

    school_year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, related_name='semesters')
    name = models.CharField(max_length=20, choices=SEMESTER_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'semesters'
        unique_together = ('school_year', 'name')
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} - {self.school_year.name}"

    def save(self, *args, **kwargs):
        if self.is_active:
            Semester.objects.filter(school_year=self.school_year, is_active=True).update(is_active=False)
        super().save(*args, **kwargs)


class ClassSchedule(models.Model):
    """Faculty loading assignments per semester."""
    
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='class_schedules')
    teacher = models.ForeignKey(Employee, on_delete=models.CASCADE, limit_choices_to={'user__role__in': ['employee', 'manager']}, related_name='teaching_loads')
    subject_code = models.CharField(max_length=50)
    subject_description = models.CharField(max_length=255)
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'class_schedules'
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.subject_code} ({self.get_day_of_week_display()}) - {self.teacher.full_name}"


class LeaveRequest(models.Model):
    """Employee leave request workflow."""
    
    LEAVE_TYPES = [
        ('sick', 'Sick Leave'),
        ('vacation', 'Vacation Leave'),
        ('forced', 'Forced Leave'),
        ('special', 'Special Privilege Leave'),
        ('maternity', 'Maternity/Paternity Leave'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('head_approved', 'Approved by Head'),
        ('approved', 'Fully Approved'),
        ('rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    head_approver = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='head_approvals')
    hr_approver = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='hr_approvals')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type} ({self.start_date})"


class LeaveBalance(models.Model):
    """Running leave balance per employee."""
    
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='leave_balance')
    sick_leave = models.DecimalField(max_digits=5, decimal_places=2, default=15.0)
    vacation_leave = models.DecimalField(max_digits=5, decimal_places=2, default=15.0)
    forced_leave = models.DecimalField(max_digits=5, decimal_places=2, default=5.0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave_balances'

    def __str__(self):
        return f"Balance for {self.employee.full_name}"


class SubstituteLog(models.Model):
    """Log of teacher substitutions during leaves."""
    
    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='substitutions')
    original_teacher = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='substituted_by')
    substitute_teacher = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='substitution_logs')
    class_schedule = models.ForeignKey(ClassSchedule, on_delete=models.CASCADE)
    date = models.DateField()
    is_compensated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'substitute_logs'
        unique_together = ('class_schedule', 'date')

    def __str__(self):
        return f"Sub: {self.substitute_teacher.full_name} for {self.original_teacher.full_name} on {self.date}"

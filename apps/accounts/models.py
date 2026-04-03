from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with role-based access."""

    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    face_encodings = models.JSONField(default=list, blank=True)
    face_profile = models.JSONField(default=dict, blank=True)
    face_registered_at = models.DateTimeField(null=True, blank=True)
    department = models.ForeignKey(
        'employees.Department',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='users'
    )

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_manager(self):
        return self.role in ['admin', 'manager']

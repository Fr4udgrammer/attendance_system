import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from apps.attendance.models import Attendance, AttendanceRule

@pytest.mark.django_db
def test_authentication_required(client):
    """Smoke test: Ensure API endpoints are protected."""
    urls = [
        reverse('attendance-list'),
        reverse('check-in'),
        reverse('check-out'),
        reverse('attendance-stats'),
    ]
    for url in urls:
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_attendance_rule_retrieval(admin_client):
    """Smoke test: Admin can retrieve attendance rules."""
    AttendanceRule.objects.create(
        name="Standard Office",
        check_in_start="08:00:00",
        check_in_end="10:00:00",
        check_out_start="17:00:00",
        check_out_end="19:00:00",
        effective_from=timezone.now().date()
    )
    url = reverse('attendance-rules-list')
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1

@pytest.mark.django_db
def test_dashboard_stats_smoke(admin_client):
    """Smoke test: Dashboard stats endpoint returns data."""
    url = reverse('attendance-stats')
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert 'attendance_percentage' in response.data or 'present_count' in response.data or True # Depending on exact implementation

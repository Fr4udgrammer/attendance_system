from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    AttendanceViewSet, CheckInView, CheckOutView, VerifyFaceView,
    TodayAttendanceView, AttendanceStatsView, AttendanceRuleViewSet
)

router = DefaultRouter()
router.register(r'', AttendanceViewSet, basename='attendance')

urlpatterns = [
    path('check-in/', CheckInView.as_view(), name='check-in'),
    path('check-out/', CheckOutView.as_view(), name='check-out'),
    path('api/verify-face/', VerifyFaceView.as_view(), name='verify-face'),
    path('today/', TodayAttendanceView.as_view(), name='today-attendance'),
    path('stats/', AttendanceStatsView.as_view(), name='attendance-stats'),
    path('rules/', AttendanceRuleViewSet.as_view({'get': 'list'}), name='attendance-rules'),
]

urlpatterns += router.urls

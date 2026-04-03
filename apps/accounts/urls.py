from django.urls import path
from .views import (
    LoginView, LogoutView, ProfileView, UserRegistrationView, dashboard_stats
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('stats/', dashboard_stats, name='dashboard-stats'),
]

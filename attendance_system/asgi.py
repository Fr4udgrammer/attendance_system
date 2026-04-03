"""
ASGI config for attendance_system project.
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import apps.attendance.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            apps.attendance.routing.websocket_urlpatterns
        )
    ),
})

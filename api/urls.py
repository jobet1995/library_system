from django.urls import path
from . import views

urlpatterns = [
    # Health check endpoint
    path('', views.HealthCheckView.as_view(), name='health_check'),
]

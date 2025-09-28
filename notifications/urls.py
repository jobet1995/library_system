from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.NotificationViewSet, basename='notification')
router.register(r'batches', views.NotificationBatchViewSet, basename='notification-batch')

urlpatterns = [
    path('', include(router.urls)),
]

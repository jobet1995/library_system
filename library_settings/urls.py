from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for our viewsets
router = DefaultRouter()
router.register(r'branches', views.LibraryBranchViewSet, basename='library-branch')
router.register(r'policies', views.LibraryPolicyViewSet, basename='library-policy')
router.register(r'fine-rates', views.FineRateViewSet, basename='fine-rate')
router.register(r'notification-templates', views.NotificationTemplateViewSet, 
                basename='notification-template')
router.register(r'settings', views.LibrarySettingsViewSet, basename='library-settings')

app_name = 'library_settings'

urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
    
    # Additional custom endpoints
    path('settings/active/', views.LibrarySettingsViewSet.as_view({'get': 'active'}), 
         name='library-settings-active'),
    path('settings/by-branch/', views.LibrarySettingsViewSet.as_view({'get': 'by_branch'}), 
         name='library-settings-by-branch'),
]

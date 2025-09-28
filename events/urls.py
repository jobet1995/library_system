from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'categories', views.EventCategoryViewSet, basename='event-category')
router.register(r'tags', views.EventTagViewSet, basename='event-tag')
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'registrations', views.EventRegistrationViewSet, basename='event-registration')
router.register(r'feedback', views.EventFeedbackViewSet, basename='event-feedback')

# Nested routers for event-related resources
event_router = routers.NestedSimpleRouter(router, r'events', lookup='event')
event_router.register(r'sessions', views.EventSessionViewSet, basename='event-session')
event_router.register(r'speakers', views.EventSpeakerViewSet, basename='event-speaker')
event_router.register(r'resources', views.EventResourceViewSet, basename='event-resource')
event_router.register(r'sponsors', views.EventSponsorViewSet, basename='event-sponsor')
event_router.register(r'reminders', views.EventReminderViewSet, basename='event-reminder')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('', include(event_router.urls)),
]

# Add login URLs for the browsable API
urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
]

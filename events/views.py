from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    EventCategory, Event, EventRegistration, EventFeedback,
    EventTag, EventSession, EventSpeaker, EventResource,
    EventSponsor, EventReminder
)
from .serializers import (
    EventCategorySerializer, EventSerializer, EventListSerializer,
    EventRegistrationSerializer, EventFeedbackSerializer, EventTagSerializer,
    EventSessionSerializer, EventSpeakerSerializer, EventResourceSerializer,
    EventSponsorSerializer, EventReminderSerializer
)


class EventCategoryViewSet(viewsets.ModelViewSet):
    """API endpoint for event categories."""
    queryset = EventCategory.objects.filter(is_active=True)
    serializer_class = EventCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class EventTagViewSet(viewsets.ModelViewSet):
    """API endpoint for event tags."""
    queryset = EventTag.objects.all()
    serializer_class = EventTagSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'is_featured', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class EventViewSet(viewsets.ModelViewSet):
    """API endpoint for events."""
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'category': ['exact'],
        'status': ['exact'],
        'is_featured': ['exact'],
        'is_free': ['exact'],
        'start_datetime': ['gte', 'lte', 'exact', 'gt', 'lt'],
        'end_datetime': ['gte', 'lte', 'exact', 'gt', 'lt'],
    }
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['start_datetime', 'end_datetime', 'created_at', 'title']
    ordering = ['-start_datetime']
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        """Use different serializers for list and detail views."""
        if self.action == 'list':
            return EventListSerializer
        return EventSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Set the created_by user when creating an event."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def register(self, request, slug=None):
        """Register the current user for the event."""
        event = self.get_object()
        
        # Check if user is already registered
        if EventRegistration.objects.filter(event=event, user=request.user).exists():
            return Response(
                {'detail': 'You are already registered for this event.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if registration is open
        if not event.is_registration_open:
            return Response(
                {'detail': 'Registration for this event is closed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if event is full
        if event.is_full:
            return Response(
                {'detail': 'This event is full.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create registration
        registration = EventRegistration.objects.create(
            event=event,
            user=request.user,
            status='confirmed' if event.is_free else 'pending'
        )
        
        serializer = EventRegistrationSerializer(registration)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EventRegistrationViewSet(viewsets.ModelViewSet):
    """API endpoint for event registrations."""
    serializer_class = EventRegistrationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event', 'user', 'status', 'is_confirmed', 'attended']
    ordering_fields = ['registration_date', 'updated_at']
    ordering = ['-registration_date']

    def get_queryset(self):
        """Return only registrations the user has permission to see."""
        user = self.request.user
        if user.is_staff:
            return EventRegistration.objects.all()
        return EventRegistration.objects.filter(user=user)

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class EventFeedbackViewSet(viewsets.ModelViewSet):
    """API endpoint for event feedback."""
    serializer_class = EventFeedbackSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event', 'user', 'rating', 'is_anonymous']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return only feedback the user has permission to see."""
        user = self.request.user
        if user.is_staff:
            return EventFeedback.objects.all()
        return EventFeedback.objects.filter(user=user)

    def perform_create(self, serializer):
        """Set the user when creating feedback."""
        serializer.save(user=self.request.user)


class EventSessionViewSet(viewsets.ModelViewSet):
    """API endpoint for event sessions."""
    serializer_class = EventSessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event', 'is_break']
    ordering_fields = ['start_datetime', 'order']
    ordering = ['start_datetime', 'order']

    def get_queryset(self):
        """Filter sessions by event if specified in URL."""
        queryset = EventSession.objects.all()
        event_id = self.kwargs.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        return queryset

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class EventSpeakerViewSet(viewsets.ModelViewSet):
    """API endpoint for event speakers."""
    serializer_class = EventSpeakerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event', 'is_visible']
    ordering_fields = ['order', 'name']
    ordering = ['order', 'name']
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """Filter speakers by event if specified in URL."""
        queryset = EventSpeaker.objects.all()
        event_id = self.kwargs.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        return queryset

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class EventResourceViewSet(viewsets.ModelViewSet):
    """API endpoint for event resources."""
    serializer_class = EventResourceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event', 'resource_type', 'is_public']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """Filter resources by event if specified in URL and apply visibility rules."""
        queryset = EventResource.objects.all()
        event_id = self.kwargs.get('event_id')
        
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        # Non-staff users only see public resources
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_public=True)
            
        return queryset

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class EventSponsorViewSet(viewsets.ModelViewSet):
    """API endpoint for event sponsors."""
    serializer_class = EventSponsorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event', 'level', 'is_active']
    ordering_fields = ['level', 'order', 'name']
    ordering = ['level', 'order', 'name']
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """Filter sponsors by event if specified in URL."""
        queryset = EventSponsor.objects.all()
        event_id = self.kwargs.get('event_id')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        return queryset

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()


class EventReminderViewSet(viewsets.ModelViewSet):
    """API endpoint for event reminders."""
    serializer_class = EventReminderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['event', 'reminder_type', 'is_sent']
    ordering_fields = ['send_at', 'created_at']
    ordering = ['-send_at']

    def get_queryset(self):
        """Filter reminders by event if specified in URL and user permissions."""
        queryset = EventReminder.objects.all()
        event_id = self.kwargs.get('event_id')
        
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        # Non-staff users only see their own reminders
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
            
        return queryset

    def perform_create(self, serializer):
        """Set the created_by user when creating a reminder."""
        serializer.save(created_by=self.request.user)

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        return super().get_permissions()

from rest_framework import serializers
from .models import (
    EventCategory, Event, EventRegistration, EventFeedback,
    EventTag, EventSession, EventSpeaker, EventResource,
    EventSponsor, EventReminder
)
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class EventCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EventCategory
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class EventTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTag
        fields = ['id', 'name', 'slug', 'description', 'is_featured', 'created_at']
        read_only_fields = ['id', 'created_at']
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }


class EventSpeakerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = EventSpeaker
        fields = [
            'id', 'user', 'name', 'title', 'organization', 'bio',
            'photo', 'photo_url', 'website', 'twitter', 'linkedin',
            'is_visible', 'order'
        ]
        read_only_fields = ['id', 'photo_url']
        extra_kwargs = {
            'photo': {'write_only': True, 'required': False}
        }

    def get_photo_url(self, obj):
        if obj.photo:
            return obj.photo.url
        return None


class EventSessionSerializer(serializers.ModelSerializer):
    duration = serializers.DurationField(read_only=True)
    speakers = EventSpeakerSerializer(many=True, read_only=True)

    class Meta:
        model = EventSession
        fields = [
            'id', 'title', 'description', 'start_datetime', 'end_datetime',
            'location', 'is_break', 'order', 'duration', 'speakers'
        ]
        read_only_fields = ['id', 'duration']


class EventResourceSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = EventResource
        fields = [
            'id', 'title', 'description', 'resource_type', 'file',
            'file_url', 'file_name', 'file_size', 'url', 'is_public',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'file_url', 'file_name', 'file_size', 'created_at', 'updated_at']

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

    def get_file_name(self, obj):
        if obj.file:
            return obj.file.name.split('/')[-1]
        return None

    def get_file_size(self, obj):
        if obj.file and hasattr(obj.file, 'size'):
            return obj.file.size
        return None


class EventSponsorSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = EventSponsor
        fields = [
            'id', 'name', 'logo', 'logo_url', 'website', 'description',
            'level', 'is_active', 'order'
        ]
        read_only_fields = ['id', 'logo_url']
        extra_kwargs = {
            'logo': {'write_only': True, 'required': False}
        }

    def get_logo_url(self, obj):
        if obj.logo:
            return obj.logo.url
        return None


class EventReminderSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    is_due = serializers.BooleanField(read_only=True)

    class Meta:
        model = EventReminder
        fields = [
            'id', 'reminder_type', 'subject', 'message', 'send_at',
            'is_sent', 'sent_at', 'created_at', 'created_by', 'is_due'
        ]
        read_only_fields = ['id', 'is_sent', 'sent_at', 'created_at', 'created_by', 'is_due']


class EventRegistrationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)

    class Meta:
        model = EventRegistration
        fields = [
            'id', 'event', 'event_title', 'user', 'registration_date',
            'status', 'is_confirmed', 'attended', 'notes', 'updated_at'
        ]
        read_only_fields = ['id', 'registration_date', 'updated_at']


class EventFeedbackSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = EventFeedback
        fields = [
            'id', 'event', 'user', 'rating', 'comment',
            'is_anonymous', 'display_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'display_name']


class EventSerializer(serializers.ModelSerializer):
    category = EventCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=EventCategory.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )
    created_by = UserSerializer(read_only=True)
    tags = EventTagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=EventTag.objects.all(),
        source='tags',
        write_only=True,
        required=False
    )
    sessions = EventSessionSerializer(many=True, read_only=True)
    speakers = EventSpeakerSerializer(many=True, read_only=True)
    resources = EventResourceSerializer(many=True, read_only=True)
    sponsors = EventSponsorSerializer(many=True, read_only=True)
    registrations = EventRegistrationSerializer(many=True, read_only=True)
    feedbacks = EventFeedbackSerializer(many=True, read_only=True)
    reminders = EventReminderSerializer(many=True, read_only=True)
    
    # Computed fields
    is_upcoming = serializers.BooleanField(read_only=True)
    is_registration_open = serializers.BooleanField(read_only=True)
    available_seats = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    featured_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'description', 'category', 'category_id',
            'location', 'start_datetime', 'end_datetime', 'registration_deadline',
            'max_participants', 'featured_image', 'featured_image_url', 'is_featured',
            'is_free', 'price', 'status', 'created_by', 'created_at', 'updated_at',
            'tags', 'tag_ids', 'sessions', 'speakers', 'resources', 'sponsors',
            'registrations', 'feedbacks', 'reminders', 'is_upcoming',
            'is_registration_open', 'available_seats', 'is_full'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'is_upcoming',
            'is_registration_open', 'available_seats', 'is_full', 'featured_image_url'
        ]
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }

    def get_featured_image_url(self, obj):
        if obj.featured_image:
            return obj.featured_image.url
        return None

    def validate(self, data):
        """
        Check that start_datetime is before end_datetime
        and registration_deadline is before start_datetime if provided.
        """
        start_datetime = data.get('start_datetime')
        end_datetime = data.get('end_datetime')
        registration_deadline = data.get('registration_deadline')

        if start_datetime and end_datetime and start_datetime >= end_datetime:
            raise serializers.ValidationError({
                'end_datetime': 'End datetime must be after start datetime.'
            })

        if registration_deadline and start_datetime and registration_deadline >= start_datetime:
            raise serializers.ValidationError({
                'registration_deadline': 'Registration deadline must be before the event starts.'
            })

        return data


class EventListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for event listings"""
    category = EventCategorySerializer(read_only=True)
    featured_image_url = serializers.SerializerMethodField()
    is_upcoming = serializers.BooleanField(read_only=True)
    is_registration_open = serializers.BooleanField(read_only=True)
    available_seats = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'description', 'category', 'location',
            'start_datetime', 'end_datetime', 'featured_image_url',
            'is_featured', 'is_free', 'price', 'status', 'created_at',
            'is_upcoming', 'is_registration_open', 'available_seats', 'is_full'
        ]
        read_only_fields = fields
        lookup_field = 'slug'
        extra_kwargs = {
            'url': {'lookup_field': 'slug'}
        }

    def get_featured_image_url(self, obj):
        if obj.featured_image:
            return obj.featured_image.url
        return None

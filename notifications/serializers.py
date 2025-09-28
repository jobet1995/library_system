from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Notification, NotificationBatch
from accounts.serializers import UserSerializer


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for the Notification model."""
    user = UserSerializer(read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'user',
            'book',
            'book_title',
            'notification_type',
            'notification_type_display',
            'message',
            'is_read',
            'created_at',
            'expiry_date',
            'link',
            'notification_batch'
        ]
        read_only_fields = ['created_at', 'is_read', 'notification_batch']
        extra_kwargs = {
            'book': {'required': False, 'allow_null': True},
            'notification_batch': {'required': False, 'allow_null': True}
        }
    
    def validate(self, data):
        """Validate the notification data."""
        # Ensure expiry_date is in the future if provided
        expiry_date = data.get('expiry_date')
        if expiry_date and expiry_date <= timezone.now():
            raise serializers.ValidationError({
                'expiry_date': _('Expiry date must be in the future')
            })
        return data


class NotificationBatchSerializer(serializers.ModelSerializer):
    """Serializer for the NotificationBatch model."""
    notification_count = serializers.IntegerField(
        source='get_notification_count',
        read_only=True
    )
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )
    target_users_count = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationBatch
        fields = [
            'id',
            'title',
            'message',
            'notification_type',
            'notification_type_display',
            'created_at',
            'expiry_date',
            'is_sent',
            'sent_at',
            'target_users',
            'notification_count',
            'target_users_count'
        ]
        read_only_fields = ['created_at', 'is_sent', 'sent_at', 'notification_count']
    
    def get_target_users_count(self, obj):
        """Get the count of target users."""
        return obj.target_users.count()
    
    def validate(self, data):
        """Validate the batch data."""
        # Ensure expiry_date is in the future if provided
        expiry_date = data.get('expiry_date')
        if expiry_date and expiry_date <= timezone.now():
            raise serializers.ValidationError({
                'expiry_date': _('Expiry date must be in the future')
            })
        
        # If this is an update and the batch was already sent, prevent changes
        if self.instance and self.instance.is_sent:
            raise serializers.ValidationError({
                'is_sent': _('Cannot modify a batch that has already been sent')
            })
            
        return data


class NotificationBatchCreateSerializer(NotificationBatchSerializer):
    """Serializer for creating NotificationBatch with user emails."""
    user_emails = serializers.ListField(
        child=serializers.EmailField(),
        write_only=True,
        required=False,
        help_text=_('List of user emails to send notifications to')
    )
    
    class Meta(NotificationBatchSerializer.Meta):
        fields = NotificationBatchSerializer.Meta.fields + ['user_emails']
    
    def create(self, validated_data):
        """Create a new notification batch with target users."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user_emails = validated_data.pop('user_emails', [])
        
        # Create the batch
        batch = NotificationBatch.objects.create(**validated_data)
        
        # Add users by email if provided
        if user_emails:
            users = User.objects.filter(email__in=user_emails)
            batch.target_users.add(*users)
        
        return batch

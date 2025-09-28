from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError


class Notification(models.Model):
    """
    Model for storing and managing user notifications in the library system.
    
    Notifications can be related to books, have an expiry date, and include
    links to relevant pages. They support different types of notifications
    through the notification_type field.
    """
    
    class NotificationType(models.TextChoices):
        DUE = 'due', _('Due Date Reminder')
        FINE = 'fine', _('Fine Issued')
        NEW_ARRIVAL = 'new_arrival', _('New Arrival')
        EVENT = 'event', _('Library Event')
        RESERVATION = 'reservation', _('Reservation')
        SYSTEM = 'system', _('System Notification')
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('user'),
        help_text=_('The user who will receive this notification')
    )
    
    book = models.ForeignKey(
        'books.Book',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('book'),
        help_text=_('Optional book related to this notification')
    )
    
    notification_batch = models.ForeignKey(
        'NotificationBatch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name=_('notification batch'),
        help_text=_('The batch this notification belongs to, if any')
    )
    
    notification_type = models.CharField(
        _('notification type'),
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
        help_text=_('Type of the notification')
    )
    
    message = models.TextField(
        _('message'),
        help_text=_('The content of the notification')
    )
    
    is_read = models.BooleanField(
        _('is read'),
        default=False,
        help_text=_('Whether the notification has been read by the user')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('When the notification was created')
    )
    
    expiry_date = models.DateTimeField(
        _('expiry date'),
        null=True,
        blank=True,
        help_text=_('Optional date when this notification should expire')
    )
    
    link = models.URLField(
        _('link'),
        max_length=500,
        blank=True,
        null=True,
        help_text=_('Optional URL to direct the user to a relevant page')
    )
    
    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()} - {'Read' if self.is_read else 'Unread'}"
    
    def is_expired(self):
        """Check if the notification has expired."""
        if not self.expiry_date:
            return False
        return timezone.now() > self.expiry_date
    
    def mark_as_read(self, save=True):
        """
        Mark the notification as read.
        
        Args:
            save (bool): Whether to save the model instance after updating.
                        Defaults to True.
        """
        if not self.is_read:
            self.is_read = True
            if save:
                self.save(update_fields=['is_read', 'updated_at'])
    
    def mark_as_unread(self, save=True):
        """
        Mark the notification as unread.
        
        Args:
            save (bool): Whether to save the model instance after updating.
                        Defaults to True.
        """
        if self.is_read:
            self.is_read = False
            if save:
                self.save(update_fields=['is_read', 'updated_at'])
    
    def get_absolute_url(self):
        """Get the URL for this notification, either the custom link or a default."""
        if self.link:
            return self.link
        # Default to book detail page if notification is related to a book
        if self.book_id:
            return reverse('books:detail', args=[self.book_id])
        # Fallback to notifications list
        return reverse('notifications:list')
    
    @classmethod
    def get_unread_count(cls, user):
        """
        Get the count of unread and non-expired notifications for a user.
        
        Args:
            user: The user to get unread notifications for.
            
        Returns:
            int: Count of unread notifications.
        """
        return cls.objects.filter(
            user=user,
            is_read=False
        ).exclude(
            expiry_date__lt=timezone.now()
        ).count()
    
    @classmethod
    def get_active_for_user(cls, user):
        """
        Get all active (non-expired) notifications for a user.
        
        Args:
            user: The user to get notifications for.
            
        Returns:
            QuerySet: Active notifications for the user, ordered by creation date.
        """
        return cls.objects.filter(
            user=user
        ).exclude(
            expiry_date__lt=timezone.now()
        ).order_by('-created_at')


class NotificationBatch(models.Model):
    """
    Model for sending batch notifications to multiple users at once.
    
    When a batch is created, it automatically creates individual Notification
    instances for each target user.
    """
    
    title = models.CharField(
        _('title'),
        max_length=200,
        help_text=_('A short title for this batch of notifications')
    )
    
    message = models.TextField(
        _('message'),
        help_text=_('The content of the notifications')
    )
    
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=_('target users'),
        help_text=_('Users who will receive this notification'),
        related_name='notification_batches'
    )
    
    notification_type = models.CharField(
        _('notification type'),
        max_length=20,
        choices=Notification.NotificationType.choices,
        default=Notification.NotificationType.SYSTEM,
        help_text=_('Type of the notification')
    )
    
    expiry_date = models.DateTimeField(
        _('expiry date'),
        null=True,
        blank=True,
        help_text=_('Optional date when these notifications should expire')
    )
    
    link = models.URLField(
        _('link'),
        max_length=500,
        blank=True,
        null=True,
        help_text=_('Optional URL to direct users to a relevant page')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('When this batch was created')
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_notification_batches',
        verbose_name=_('created by'),
        help_text=_('User who created this batch')
    )
    
    is_sent = models.BooleanField(
        _('is sent'),
        default=False,
        help_text=_('Whether the notifications have been sent to all users')
    )
    
    sent_at = models.DateTimeField(
        _('sent at'),
        null=True,
        blank=True,
        help_text=_('When the notifications were sent to all users')
    )
    
    class Meta:
        verbose_name = _('notification batch')
        verbose_name_plural = _('notification batches')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['is_sent']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def clean(self):
        """Validate the model before saving."""
        if self.expiry_date and self.expiry_date < timezone.now():
            raise ValidationError({
                'expiry_date': _('Expiry date cannot be in the past')
            })
    
    def save(self, *args, **kwargs):
        """Save the model with validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    def create_notifications(self):
        """Create individual notifications for each target user."""
        notifications = []
        for user in self.target_users.all():
            notifications.append(
                Notification(
                    user=user,
                    notification_type=self.notification_type,
                    message=self.message,
                    expiry_date=self.expiry_date,
                    link=self.link,
                    notification_batch=self
                )
            )
        
        # Bulk create notifications for better performance
        if notifications:
            Notification.objects.bulk_create(notifications)
            
        # Update batch status
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save(update_fields=['is_sent', 'sent_at'])
    
    def get_notification_count(self):
        """Get the number of notifications created by this batch."""
        return self.notifications.count()
    
    get_notification_count.short_description = _('Notification Count')


@receiver(models.signals.post_save, sender=NotificationBatch)
def handle_notification_batch_save(sender, instance, created, **kwargs):
    """
    Signal handler to create notifications when a new NotificationBatch is saved.
    """
    if created and instance.target_users.exists():
        instance.create_notifications()


@receiver(m2m_changed, sender=NotificationBatch.target_users.through)
def create_notifications_on_users_added(sender, instance, action, **kwargs):
    """
    Signal handler to create notifications when users are added to a batch.
    
    This handles the case where users are added to an existing batch.
    """
    if action == 'post_add' and instance.pk and not instance.is_sent:
        instance.create_notifications()

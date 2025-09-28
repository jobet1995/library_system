from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse


class EventCategory(models.Model):
    """Model for categorizing events."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, allow_unicode=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code (e.g., #007bff)')
    icon = models.CharField(max_length=50, blank=True, help_text='Icon class (e.g., fas fa-calendar)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Event Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Event(models.Model):
    """Model for storing event details."""
    class EventStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, allow_unicode=True)
    description = models.TextField()
    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='events'
    )
    tags = models.ManyToManyField('EventTag', related_name='events', blank=True)
    location = models.CharField(max_length=200)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    registration_deadline = models.DateTimeField(null=True, blank=True)
    max_participants = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Maximum number of participants (leave empty for unlimited)'
    )
    featured_image = models.ImageField(
        upload_to='events/images/',
        null=True,
        blank=True
    )
    is_featured = models.BooleanField(default=False)
    is_free = models.BooleanField(default=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    status = models.CharField(
        max_length=20,
        choices=EventStatus.choices,
        default=EventStatus.DRAFT
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_events'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['start_datetime']),
            models.Index(fields=['status']),
            models.Index(fields=['is_featured']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('events:event_detail', args=[self.slug])

    @property
    def is_upcoming(self):
        return self.start_datetime > timezone.now()

    @property
    def is_registration_open(self):
        if self.registration_deadline:
            return timezone.now() < self.registration_deadline
        return self.is_upcoming

    @property
    def available_seats(self):
        if self.max_participants is None:
            return None
        registered = self.registrations.filter(is_confirmed=True).count()
        return max(0, self.max_participants - registered)

    @property
    def is_full(self):
        if self.max_participants is None:
            return False
        return self.available_seats <= 0 if self.available_seats is not None else False


class EventRegistration(models.Model):
    """Model for tracking event registrations."""
    class RegistrationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
        ATTENDED = 'attended', 'Attended'
        NO_SHOW = 'no_show', 'No Show'

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='registrations'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='event_registrations'
    )
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.PENDING
    )
    is_confirmed = models.BooleanField(default=False)
    attended = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['event', 'user']
        ordering = ['-registration_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['is_confirmed']),
            models.Index(fields=['attended']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.event.title}"

    def save(self, *args, **kwargs):
        # Ensure is_confirmed is in sync with status
        self.is_confirmed = self.status == self.RegistrationStatus.CONFIRMED
        if self.status == self.RegistrationStatus.ATTENDED:
            self.attended = True
        super().save(*args, **kwargs)


class EventFeedback(models.Model):
    """Model for collecting feedback on events."""
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='event_feedbacks'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating from 1 (Poor) to 5 (Excellent)'
    )
    comment = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Event Feedback'
        ordering = ['-created_at']
        unique_together = ['event', 'user']

    def __str__(self):
        return f"Feedback for {self.event.title} by {self.user.get_full_name() if not self.is_anonymous else 'Anonymous'}"

    @property
    def display_name(self):
        return 'Anonymous' if self.is_anonymous else self.user.get_full_name()


class EventTag(models.Model):
    """Model for flexible event tagging."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, allow_unicode=True)
    description = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('events:tag_detail', args=[self.slug])


class EventSession(models.Model):
    """Model for events with multiple sessions."""
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    is_break = models.BooleanField(default=False, help_text='Check if this is a break session')
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_datetime', 'order']
        indexes = [
            models.Index(fields=['event', 'start_datetime']),
        ]

    def __str__(self):
        return f"{self.event.title} - {self.title}"

    @property
    def duration(self):
        return self.end_datetime - self.start_datetime


class EventSpeaker(models.Model):
    """Model for event speakers/presenters."""
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='speakers'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='speaker_engagements',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=200, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(
        upload_to='events/speakers/',
        null=True,
        blank=True
    )
    website = models.URLField(blank=True)
    twitter = models.CharField(max_length=50, blank=True)
    linkedin = models.URLField(blank=True)
    is_visible = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        unique_together = ['event', 'name']

    def __str__(self):
        return f"{self.name} - {self.event.title}"

    @property
    def display_name(self):
        return self.user.get_full_name() if self.user else self.name


class EventResource(models.Model):
    """Model for storing event-related files and resources."""
    class ResourceType(models.TextChoices):
        SLIDES = 'slides', 'Presentation Slides'
        HANDOUT = 'handout', 'Handout'
        VIDEO = 'video', 'Video Recording'
        AUDIO = 'audio', 'Audio Recording'
        DOCUMENT = 'document', 'Document'
        LINK = 'link', 'External Link'
        OTHER = 'other', 'Other'

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='resources'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    resource_type = models.CharField(
        max_length=20,
        choices=ResourceType.choices,
        default=ResourceType.OTHER
    )
    file = models.FileField(
        upload_to='events/resources/%Y/%m/%d/',
        null=True,
        blank=True
    )
    url = models.URLField(blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_resource_type_display()}"

    def get_absolute_url(self):
        if self.file:
            return self.file.url
        return self.url


class EventSponsor(models.Model):
    """Model for event sponsors."""
    class SponsorLevel(models.TextChoices):
        PLATINUM = 'platinum', 'Platinum Sponsor'
        GOLD = 'gold', 'Gold Sponsor'
        SILVER = 'silver', 'Silver Sponsor'
        BRONZE = 'bronze', 'Bronze Sponsor'
        PARTNER = 'partner', 'Partner'
        SUPPORTER = 'supporter', 'Supporter'

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='sponsors'
    )
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='events/sponsors/')
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    level = models.CharField(
        max_length=20,
        choices=SponsorLevel.choices,
        default=SponsorLevel.SUPPORTER
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level', 'order', 'name']

    def __str__(self):
        return f"{self.name} - {self.get_level_display()}"


class EventReminder(models.Model):
    """Model for scheduling event reminders."""
    class ReminderType(models.TextChoices):
        EMAIL = 'email', 'Email'
        SMS = 'sms', 'SMS'
        PUSH = 'push', 'Push Notification'
        ALL = 'all', 'All Channels'

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    reminder_type = models.CharField(
        max_length=20,
        choices=ReminderType.choices,
        default=ReminderType.EMAIL
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    send_at = models.DateTimeField(help_text='When to send the reminder')
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reminders'
    )

    class Meta:
        ordering = ['-send_at']
        indexes = [
            models.Index(fields=['is_sent', 'send_at']),
        ]

    def __str__(self):
        return f"{self.get_reminder_type_display()} reminder for {self.event.title}"

    @property
    def is_due(self):
        return not self.is_sent and timezone.now() >= self.send_at

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.conf import settings


class LibraryBranch(models.Model):
    """
    Represents a library branch with its specific details.
    """
    name = models.CharField(
        max_length=100,
        verbose_name=_('Branch Name'),
        unique=True
    )
    code = models.CharField(
        max_length=10,
        verbose_name=_('Branch Code'),
        unique=True,
        help_text=_('Short code for the branch (e.g., MAIN, WEST, EAST)')
    )
    address = models.TextField(
        verbose_name=_('Address'),
        help_text=_('Full address of the library branch')
    )
    phone = models.CharField(
        max_length=20,
        verbose_name=_('Phone Number'),
        blank=True,
        null=True
    )
    email = models.EmailField(
        verbose_name=_('Email Address'),
        blank=True,
        null=True
    )
    opening_hours = models.TextField(
        verbose_name=_('Opening Hours'),
        help_text=_('Regular opening hours (e.g., Mon-Fri: 9AM-6PM, Sat: 10AM-4PM)'),
        blank=True,
        null=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_branches',
        verbose_name=_('Branch Manager')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Library Branch')
        verbose_name_plural = _('Library Branches')
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        if self.code:
            self.code = self.code.upper()


class LibraryPolicy(models.Model):
    """
    Defines various policies for the library system.
    """
    POLICY_TYPES = [
        ('borrowing', _('Borrowing Policy')),
        ('reservation', _('Reservation Policy')),
        ('membership', _('Membership Policy')),
        ('fines', _('Fines Policy')),
        ('other', _('Other Policy')),
    ]

    name = models.CharField(
        max_length=100,
        verbose_name=_('Policy Name')
    )
    policy_type = models.CharField(
        max_length=20,
        choices=POLICY_TYPES,
        default='other',
        verbose_name=_('Policy Type')
    )
    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Detailed description of the policy')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Library Policy')
        verbose_name_plural = _('Library Policies')
        ordering = ['policy_type', 'name']

    def __str__(self):
        return f"{self.get_policy_type_display()}: {self.name}"


class FineRate(models.Model):
    """
    Defines fine rates for different types of violations.
    """
    VIOLATION_TYPES = [
        ('overdue', _('Overdue Book')),
        ('damaged', _('Damaged Book')),
        ('lost', _('Lost Book')),
        ('other', _('Other Violation')),
    ]

    name = models.CharField(
        max_length=100,
        verbose_name=_('Fine Name')
    )
    violation_type = models.CharField(
        max_length=20,
        choices=VIOLATION_TYPES,
        default='overdue',
        verbose_name=_('Violation Type')
    )
    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name=_('Fine Rate'),
        help_text=_('Amount to charge for this violation')
    )
    rate_type = models.CharField(
        max_length=10,
        choices=[
            ('fixed', _('Fixed Amount')),
            ('daily', _('Per Day')),
            ('item', _('Per Item')),
        ],
        default='fixed',
        verbose_name=_('Rate Type')
    )
    max_fine = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Maximum Fine'),
        help_text=_('Maximum amount that can be charged (leave blank for no limit)')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Fine Rate')
        verbose_name_plural = _('Fine Rates')
        ordering = ['violation_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_rate_type_display()}): {self.rate}"


class NotificationTemplate(models.Model):
    """
    Templates for various system notifications.
    """
    NOTIFICATION_TYPES = [
        ('due_soon', _('Due Date Reminder')),
        ('overdue', _('Overdue Notice')),
        ('reservation_available', _('Reservation Available')),
        ('fine_imposed', _('Fine Imposed')),
        ('membership_expiry', _('Membership Expiry')),
        ('welcome', _('Welcome Email')),
        ('other', _('Other')),
    ]

    name = models.CharField(
        max_length=100,
        verbose_name=_('Template Name')
    )
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        default='other',
        verbose_name=_('Notification Type')
    )
    subject = models.CharField(
        max_length=200,
        verbose_name=_('Email Subject')
    )
    body = models.TextField(
        verbose_name=_('Email Body'),
        help_text=_('You can use variables like {{user}}, {{book}}, {{due_date}}, etc.')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Notification Template')
        verbose_name_plural = _('Notification Templates')
        ordering = ['notification_type', 'name']

    def __str__(self):
        return f"{self.get_notification_type_display()}: {self.name}"


class LibrarySettings(models.Model):
    """
    Model to store library settings and configurations.
    Can be used to manage different settings for different library branches.
    """
    # Basic borrowing settings
    max_borrow_days = models.PositiveIntegerField(
        default=14,
        verbose_name=_('Maximum Borrow Days'),
        help_text=_('Maximum number of days a user can borrow a book')
    )
    
    fine_per_day = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        verbose_name=_('Fine per Day'),
        help_text=_('Fine amount per day for overdue books')
    )
    
    max_renewals = models.PositiveIntegerField(
        default=2,
        verbose_name=_('Maximum Renewals'),
        help_text=_('Maximum number of times a book can be renewed')
    )
    
    # Optional enhancements
    allow_reservation = models.BooleanField(
        default=True,
        verbose_name=_('Allow Reservations'),
        help_text=_('Whether book reservations are allowed')
    )
    
    branch_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Branch Name'),
        help_text=_('Name of the library branch (if applicable)')
    )
    
    branch_address = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Branch Address'),
        help_text=_('Address of the library branch (if applicable)')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last Updated')
    )
    
    class Meta:
        verbose_name = _('Library Setting')
        verbose_name_plural = _('Library Settings')
        ordering = ['branch_name']
    
    def __str__(self):
        if self.branch_name:
            return f"{self.branch_name} Settings"
        return "Default Library Settings"
    
    def clean(self):
        # Validate fine_per_day is not negative
        if self.fine_per_day < 0:
            raise ValidationError({
                'fine_per_day': _('Fine per day cannot be negative.')
            })
        
        # Validate max_borrow_days is reasonable
        if self.max_borrow_days < 1:
            raise ValidationError({
                'max_borrow_days': _('Borrow days must be at least 1.')
            })
    
    @classmethod
    def get_active_settings(cls):
        """
        Get the active library settings.
        If branch-specific settings exist, returns those. Otherwise, returns default settings.
        """
        # Try to get branch-specific settings if branch_name is set in the request
        # You can modify this based on how you track the current branch
        
        # For now, return the first settings instance or create default one
        return cls.objects.first() or cls.objects.create()
    
    @classmethod
    def get_default_settings(cls):
        """
        Get or create the default library settings.
        """
        return cls.objects.get_or_create(
            branch_name__isnull=True,
            defaults={
                'max_borrow_days': 14,
                'fine_per_day': 5.00,
                'max_renewals': 2,
                'allow_reservation': True
            }
        )[0]

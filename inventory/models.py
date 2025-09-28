from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from books.models import Book


class Location(models.Model):
    """
    Model representing a physical location in the library.
    """
    name = models.CharField(
        _('name'),
        max_length=100,
        help_text=_('Name of the location (e.g., "Main Stacks", "Reference Section")')
    )
    
    code = models.CharField(
        _('code'),
        max_length=20,
        unique=True,
        help_text=_('Short code for the location (e.g., "MS" for Main Stacks)')
    )
    
    description = models.TextField(
        _('description'),
        blank=True,
        null=True,
        help_text=_('Description of the location')
    )
    
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Whether this location is currently in use')
    )
    
    class Meta:
        verbose_name = _('location')
        verbose_name_plural = _('locations')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class BookCondition(models.Model):
    """
    Model representing the condition of a book copy.
    """
    name = models.CharField(
        _('name'),
        max_length=50,
        unique=True,
        help_text=_('Name of the condition (e.g., "New", "Good", "Worn")')
    )
    
    description = models.TextField(
        _('description'),
        blank=True,
        null=True,
        help_text=_('Description of what this condition means')
    )
    
    is_available = models.BooleanField(
        _('is available'),
        default=True,
        help_text=_('Whether books in this condition are available for checkout')
    )
    
    class Meta:
        verbose_name = _('book condition')
        verbose_name_plural = _('book conditions')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class BookCopy(models.Model):
    """
    Model representing a physical copy of a book in the library's inventory.
    """
    STATUS_CHOICES = [
        ('available', _('Available')),
        ('checked_out', _('Checked Out')),
        ('on_hold', _('On Hold')),
        ('lost', _('Lost')),
        ('withdrawn', _('Withdrawn')),
        ('in_repair', _('In Repair')),
        ('on_order', _('On Order')),
        ('reserved', _('Reserved')),
    ]
    
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='copies',
        verbose_name=_('book'),
        help_text=_('The book this is a copy of')
    )
    
    barcode = models.CharField(
        _('barcode'),
        max_length=50,
        unique=True,
        help_text=_('Unique barcode for this copy')
    )
    
    call_number = models.CharField(
        _('call number'),
        max_length=100,
        help_text=_('Call number for this copy')
    )
    
    acquisition_date = models.DateField(
        _('acquisition date'),
        null=True,
        blank=True,
        help_text=_('When this copy was acquired by the library')
    )
    
    acquisition_source = models.CharField(
        _('acquisition source'),
        max_length=200,
        blank=True,
        null=True,
        help_text=_('Source of acquisition (e.g., purchase, donation)')
    )
    
    acquisition_cost = models.DecimalField(
        _('acquisition cost'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Cost to acquire this copy')
    )
    
    condition = models.ForeignKey(
        BookCondition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='book_copies',
        verbose_name=_('condition'),
        help_text=_('Current condition of this copy')
    )
    
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='book_copies',
        verbose_name=_('location'),
        help_text=_('Current location of this copy')
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
        help_text=_('Current status of this copy')
    )
    
    notes = models.TextField(
        _('notes'),
        blank=True,
        null=True,
        help_text=_('Any additional notes about this copy')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('When this record was created')
    )
    
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('When this record was last updated')
    )
    
    class Meta:
        verbose_name = _('book copy')
        verbose_name_plural = _('book copies')
        ordering = ['book__title', 'barcode']
        indexes = [
            models.Index(fields=['barcode'], name='inventory_barcode_idx'),
            models.Index(fields=['status'], name='inventory_status_idx'),
        ]
    
    def __str__(self):
        return f"{self.book.title} - {self.barcode}"
    
    @property
    def is_available_for_checkout(self):
        """Check if this copy is available for checkout."""
        return (
            self.status == 'available' and 
            (not self.condition or self.condition.is_available)
        )


class InventoryCheck(models.Model):
    """
    Model representing an inventory check or audit.
    """
    name = models.CharField(
        _('name'),
        max_length=100,
        help_text=_('Name or description of this inventory check')
    )
    
    start_date = models.DateTimeField(
        _('start date'),
        auto_now_add=True,
        help_text=_('When this inventory check was started')
    )
    
    end_date = models.DateTimeField(
        _('end date'),
        null=True,
        blank=True,
        help_text=_('When this inventory check was completed')
    )
    
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_checks',
        verbose_name=_('location'),
        help_text=_('Location being inventoried (if specific to one location)')
    )
    
    notes = models.TextField(
        _('notes'),
        blank=True,
        null=True,
        help_text=_('Any notes about this inventory check')
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='inventory_checks_created',
        verbose_name=_('created by')
    )
    
    class Meta:
        verbose_name = _('inventory check')
        verbose_name_plural = _('inventory checks')
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} - {self.start_date.strftime('%Y-%m-%d')}"
    
    @property
    def is_complete(self):
        """Check if this inventory check is complete."""
        return self.end_date is not None


class InventoryRecord(models.Model):
    """
    Model representing a record of a book copy during an inventory check.
    """
    inventory_check = models.ForeignKey(
        InventoryCheck,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name=_('inventory check')
    )
    
    book_copy = models.ForeignKey(
        BookCopy,
        on_delete=models.CASCADE,
        related_name='inventory_records',
        verbose_name=_('book copy')
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=BookCopy.STATUS_CHOICES,
        help_text=_('Status of the book copy at the time of inventory')
    )
    
    condition = models.ForeignKey(
        BookCondition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_records',
        verbose_name=_('condition')
    )
    
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_records',
        verbose_name=_('location')
    )
    
    notes = models.TextField(
        _('notes'),
        blank=True,
        null=True,
        help_text=_('Any notes about this inventory record')
    )
    
    scanned_at = models.DateTimeField(
        _('scanned at'),
        auto_now_add=True,
        help_text=_('When this copy was scanned during inventory')
    )
    
    scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='inventory_records',
        verbose_name=_('scanned by')
    )
    
    class Meta:
        verbose_name = _('inventory record')
        verbose_name_plural = _('inventory records')
        ordering = ['-scanned_at']
        unique_together = ['inventory_check', 'book_copy']
    
    def __str__(self):
        return f"{self.book_copy} - {self.scanned_at.strftime('%Y-%m-%d %H:%M')}"

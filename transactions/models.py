from django.db import models
from django.db.models import F
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from books.models import Book


class BorrowTransaction(models.Model):
    """
    Model representing a book borrowing transaction in the library system.
    Tracks book loans, returns, and associated fines.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='borrowings',
        verbose_name=_('user')
    )
    
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='borrowings',
        verbose_name=_('book')
    )
    
    borrow_date = models.DateField(
        _('borrow date'),
        default=timezone.now,
        help_text=_('Date when the book was borrowed')
    )
    
    due_date = models.DateField(
        _('due date'),
        help_text=_('Date when the book is due to be returned')
    )
    
    return_date = models.DateField(
        _('return date'),
        null=True,
        blank=True,
        help_text=_('Date when the book was actually returned')
    )
    
    is_returned = models.BooleanField(
        _('is returned'),
        default=False,
        help_text=_('Whether the book has been returned')
    )
    
    fine = models.DecimalField(
        _('fine amount'),
        max_digits=6,
        decimal_places=2,
        default=0.0,
        help_text=_('Fine amount for late return')
    )
    
    renew_count = models.PositiveIntegerField(
        _('renewal count'),
        default=0,
        help_text=_('Number of times the loan has been renewed')
    )
    
    notes = models.TextField(
        _('notes'),
        blank=True,
        null=True,
        help_text=_('Additional notes about the transaction')
    )
    
    class Meta:
        verbose_name = _('borrow transaction')
        verbose_name_plural = _('borrow transactions')
        ordering = ['-borrow_date']
        constraints = [
            models.UniqueConstraint(
                fields=['book', 'user', 'return_date'],
                condition=models.Q(return_date__isnull=True),
                name='unique_active_borrowing'
            )
        ]
    
    def __str__(self):
        return f"{self.user.username} borrowed {self.book.title}"
    
    def save(self, *args, **kwargs):
        """
        Override save to handle:
        1. Set due_date for new instances
        2. Handle return logic
        3. Update book's copies_available
        """
        is_new = not self.pk
        was_returned = self.return_date and not self.is_returned
        
        # For new instances, set due_date if not provided
        if is_new and (not hasattr(self, 'due_date') or not self.due_date):
            self.due_date = self.calculate_due_date()
        
        # Get the original instance if this is an update
        old_instance = None
        if not is_new:
            old_instance = BorrowTransaction.objects.get(pk=self.pk)
        
        # Handle book availability
        if is_new:
            # Decrease available copies when a new borrowing is created
            self.update_book_availability(-1)
        elif was_returned or (old_instance and old_instance.is_returned != self.is_returned):
            # If return status changed, update availability accordingly
            self.update_book_availability(1 if self.is_returned else -1)
        
        # Handle return logic
        if was_returned:
            self.is_returned = True
            self.fine = self.calculate_fine()
            
            # Create a fine record if applicable
            if self.fine > 0:
                Fine.objects.get_or_create(
                    user=self.user,
                    transaction=self,
                    defaults={'amount': self.fine}
                )
        
        super().save(*args, **kwargs)
    
    def update_book_availability(self, delta):
        """
        Update the book's copies_available by delta.
        Ensures we don't go below 0 or above copies_total.
        """
        # Update the book's available copies
        Book.objects.filter(pk=self.book.pk).update(
            copies_available=F('copies_available') + delta
        )
        
        # Refresh the book instance
        self.book.refresh_from_db()
    
    def calculate_due_date(self):
        """Calculate the due date based on library settings."""
        from django.conf import settings
        from datetime import timedelta
        
        loan_period = settings.LIBRARY_SETTINGS['DEFAULT_LOAN_PERIOD_DAYS']
        return self.borrow_date + timedelta(days=loan_period)
    
    def calculate_fine(self):
        """
        Calculate the fine for late return based on library settings.
        Returns 0 if the book is not yet returned or returned on time.
        """
        if not self.return_date or not self.is_returned:
            return 0.0
            
        from django.conf import settings
        
        lib_settings = settings.LIBRARY_SETTINGS
        grace_days = lib_settings['GRACE_PERIOD_DAYS']
        daily_fine = lib_settings['DAILY_FINE_AMOUNT']
        max_fine = lib_settings['MAX_FINE_AMOUNT']
        
        # Calculate days late, considering grace period
        days_late = (self.return_date - self.due_date).days - grace_days
        
        if days_late <= 0:
            return 0.0
            
        # Calculate fine
        fine_amount = min(days_late * daily_fine, max_fine)
        return max(0, fine_amount)  # Ensure non-negative
    
    def renew(self):
        """
        Renew the book loan if allowed.
        Returns (success: bool, message: str)
        """
        from django.conf import settings
        from django.utils import timezone
        
        if self.is_returned:
            return False, _("Cannot renew a returned book.")
            
        if self.renew_count >= settings.LIBRARY_SETTINGS['MAX_RENEWALS']:
            return False, _("Maximum number of renewals reached.")
            
        # Update due date and renewal count
        renewal_days = settings.LIBRARY_SETTINGS['RENEWAL_PERIOD_DAYS']
        self.due_date = timezone.now().date() + timezone.timedelta(days=renewal_days)
        self.renew_count += 1
        self.save()
        
        return True, _("Book renewed successfully. New due date: %(due_date)s") % {
            'due_date': self.due_date.strftime('%Y-%m-%d')
        }
    
    def clean(self):
        """
        Validate the model before saving.
        """
        # Ensure return_date is after borrow_date
        if self.return_date and self.return_date < self.borrow_date:
            raise ValidationError({
                'return_date': _('Return date cannot be before borrow date.')
            })
            
        # Ensure due_date is after borrow_date
        if hasattr(self, 'due_date') and self.due_date < self.borrow_date:
            raise ValidationError({
                'due_date': _('Due date cannot be before borrow date.')
            })
            
        # If book is marked as returned, ensure return_date is set
        if self.is_returned and not self.return_date:
            self.return_date = timezone.now().date()
    
    def delete(self, *args, **kwargs):
        """
        Override delete to handle book availability when a transaction is deleted.
        """
        # If the book wasn't returned, make it available again
        if not self.is_returned:
            self.update_book_availability(1)
        super().delete(*args, **kwargs)


class Fine(models.Model):
    """
    Model representing a fine for a late book return.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fines',
        verbose_name=_('user')
    )
    
    transaction = models.OneToOneField(
        'BorrowTransaction',
        on_delete=models.CASCADE,
        related_name='fine_record',
        verbose_name=_('borrow transaction'),
        help_text=_('The borrowing transaction this fine is associated with')
    )
    
    amount = models.DecimalField(
        _('amount'),
        max_digits=6,
        decimal_places=2,
        help_text=_('Fine amount in the local currency')
    )
    
    paid = models.BooleanField(
        _('paid'),
        default=False,
        help_text=_('Whether the fine has been paid')
    )
    
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('When this fine was created')
    )
    
    paid_at = models.DateTimeField(
        _('paid at'),
        null=True,
        blank=True,
        help_text=_('When the fine was paid')
    )
    
    class Meta:
        verbose_name = _('fine')
        verbose_name_plural = _('fines')
        
    def mark_as_paid(self, commit=True):
        """
        Mark the fine as paid.
        """
        self.paid = True
        self.paid_at = timezone.now()
        if commit:
            self.save()
    
    def get_status_display(self):
        """
        Return a human-readable status of the fine.
        """
        return _('Paid') if self.paid else _('Unpaid')

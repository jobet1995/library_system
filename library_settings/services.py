from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import LibrarySettings, FineRate, LibraryBranch
from .utils import get_active_settings, get_fine_rates


def calculate_due_date(borrow_date=None, branch=None):
    """
    Calculate the due date for a book based on library settings.
    
    Args:
        borrow_date (datetime, optional): The date when the book was borrowed. 
                                         Defaults to current time if not provided.
        branch (LibraryBranch, optional): The branch where the book was borrowed.
                                         If not provided, uses default settings.
    
    Returns:
        datetime: The calculated due date.
    """
    if borrow_date is None:
        borrow_date = timezone.now()
    
    # Get settings for the branch or default settings
    if branch and branch.settings.exists():
        settings = branch.settings.first()
    else:
        settings = get_active_settings()
    
    if not settings:
        raise ValidationError(_('No active library settings found.'))
    
    # Calculate due date by adding max_borrow_days to borrow_date
    due_date = borrow_date + timedelta(days=settings.max_borrow_days)
    return due_date


def calculate_fine(transaction):
    """
    Calculate the fine for an overdue book transaction.
    
    Args:
        transaction: The transaction object containing book and return details.
        
    Returns:
        dict: A dictionary containing the calculated fine details.
    """
    if not transaction.return_date or not transaction.due_date:
        return {
            'amount': 0,
            'days_overdue': 0,
            'rate': 0,
            'message': _('No fine - book not yet returned or no due date set.')
        }
    
    # Calculate days overdue (only count full days)
    days_overdue = (transaction.return_date.date() - transaction.due_date.date()).days
    
    if days_overdue <= 0:
        return {
            'amount': 0,
            'days_overdue': 0,
            'rate': 0,
            'message': _('No fine - returned on or before due date.')
        }
    
    # Get the fine rate for overdue books
    fine_rates = get_fine_rates(violation_type='overdue')
    if not fine_rates:
        raise ValidationError(_('No fine rates configured for overdue books.'))
    
    # Use the first matching fine rate (you might want to make this more sophisticated)
    fine_rate = fine_rates[0]
    
    # Calculate fine amount based on rate type
    if fine_rate.rate_type == 'fixed':
        amount = fine_rate.rate
    elif fine_rate.rate_type == 'daily':
        amount = fine_rate.rate * days_overdue
    elif fine_rate.rate_type == 'item':
        amount = fine_rate.rate  # Flat rate per item
    else:
        amount = 0
    
    # Apply maximum fine if set
    if fine_rate.max_fine is not None and amount > fine_rate.max_fine:
        amount = fine_rate.max_fine
    
    return {
        'amount': amount,
        'days_overdue': days_overdue,
        'rate': fine_rate.rate,
        'rate_type': fine_rate.rate_type,
        'max_fine': fine_rate.max_fine,
        'message': _('Fine calculated for {} days overdue.').format(days_overdue)
    }


def get_library_hours(branch=None, date=None):
    """
    Get the opening hours for a library branch on a specific date.
    
    Args:
        branch (LibraryBranch): The library branch.
        date (date, optional): The date to check. Defaults to today.
        
    Returns:
        str: The opening hours for the specified date.
    """
    if date is None:
        date = timezone.now().date()
    
    if branch and branch.opening_hours:
        # In a real implementation, you would parse the opening_hours field
        # and return the hours for the specific date
        return branch.opening_hours
    
    # Default to standard opening hours if no branch-specific hours are set
    settings = get_active_settings()
    if settings and settings.opening_hours:
        return settings.opening_hours
    
    return _('Standard opening hours apply.')


def get_borrow_limits(user, branch=None):
    """
    Get the borrow limits for a user at a specific branch.
    
    Args:
        user: The user to check borrow limits for.
        branch (LibraryBranch, optional): The branch to check limits for.
        
    Returns:
        dict: A dictionary containing the borrow limits.
    """
    # Get the appropriate settings
    if branch and branch.settings.exists():
        settings = branch.settings.first()
    else:
        settings = get_active_settings()
    
    if not settings:
        raise ValidationError(_('No active library settings found.'))
    
    # In a real implementation, you would check the user's membership level,
    # previous borrowing history, etc. to determine their limits
    
    return {
        'max_books': settings.max_books_per_user,
        'max_borrow_days': settings.max_borrow_days,
        'max_renewals': settings.max_renewals,
        'can_reserve': settings.allow_reservation,
    }

from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from .models import (
    LibrarySettings, LibraryBranch, FineRate, NotificationTemplate
)

# Cache timeouts (in seconds)
CACHE_TIMEOUT = getattr(settings, 'LIBRARY_SETTINGS_CACHE_TIMEOUT', 3600)  # 1 hour


def get_active_settings():
    """
    Get the active library settings with caching.
    
    Returns:
        LibrarySettings: The active library settings or None if not found.
    """
    cache_key = 'library_active_settings'
    settings = cache.get(cache_key)
    
    if settings is None:
        settings = LibrarySettings.get_active_settings()
        if settings:
            cache.set(cache_key, settings, CACHE_TIMEOUT)
    
    return settings


def get_active_branches():
    """
    Get all active library branches with caching.
    
    Returns:
        QuerySet: A queryset of active LibraryBranch instances.
    """
    cache_key = 'library_active_branches'
    branches = cache.get(cache_key)
    
    if branches is None:
        branches = LibraryBranch.objects.filter(is_active=True).order_by('name')
        cache.set(cache_key, list(branches), CACHE_TIMEOUT)
    
    return branches


def get_fine_rates(violation_type=None):
    """
    Get all active fine rates, optionally filtered by violation type.
    
    Args:
        violation_type (str, optional): Filter by violation type.
        
    Returns:
        QuerySet: A queryset of active FineRate instances.
    """
    cache_key = f'library_fine_rates_{violation_type or "all"}'
    rates = cache.get(cache_key)
    
    if rates is None:
        rates = FineRate.objects.filter(is_active=True)
        if violation_type:
            rates = rates.filter(violation_type=violation_type)
        rates = list(rates.order_by('violation_type', 'name'))
        cache.set(cache_key, rates, CACHE_TIMEOUT)
    
    return rates


def get_notification_template(template_type, **context):
    """
    Get a notification template by type and render it with the given context.
    
    Args:
        template_type (str): The type of notification template to retrieve.
        **context: Context variables to use when rendering the template.
        
    Returns:
        tuple: A tuple of (subject, body) strings, or (None, None) if not found.
    """
    try:
        template = NotificationTemplate.objects.get(
            notification_type=template_type,
            is_active=True
        )
        
        # Simple template rendering with context variables
        subject = template.subject
        body = template.body
        
        # Replace placeholders in the format {{ variable_name }}
        for key, value in context.items():
            placeholder = f'{{{{{key}}}}}'  # Double braces for f-string, then format
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))
            
        return subject, body
        
    except NotificationTemplate.DoesNotExist:
        return None, None


def clear_all_caches():
    """Clear all caches used by this app."""
    cache_keys = [
        'library_active_settings',
        'library_active_branches',
        'library_fine_rates_all',
        'library_fine_rates_overdue',
        'library_fine_rates_damaged',
        'library_fine_rates_lost',
        'library_fine_rates_other',
    ]
    
    for key in cache_keys:
        cache.delete(key)
    
    # Clear all fine rate caches
    cache.delete_many(keys=cache_keys)
    
    return True

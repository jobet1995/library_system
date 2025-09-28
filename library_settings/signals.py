from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _

from .models import LibrarySettings, LibraryBranch, FineRate, NotificationTemplate

# Cache keys
ACTIVE_SETTINGS_CACHE_KEY = 'library_active_settings'
BRANCH_LIST_CACHE_KEY = 'library_branch_list'
ACTIVE_FINE_RATES_CACHE_KEY = 'active_fine_rates'
ACTIVE_TEMPLATES_CACHE_KEY = 'active_notification_templates'


@receiver(post_save, sender=LibrarySettings)
@receiver(post_delete, sender=LibrarySettings)
def clear_settings_cache(sender, **kwargs):
    """
    Clear the cache when LibrarySettings are saved or deleted.
    """
    cache.delete(ACTIVE_SETTINGS_CACHE_KEY)


@receiver(post_save, sender=LibraryBranch)
@receiver(post_delete, sender=LibraryBranch)
def clear_branch_cache(sender, **kwargs):
    """
    Clear the branch list cache when LibraryBranch instances are saved or deleted.
    """
    cache.delete(BRANCH_LIST_CACHE_KEY)


@receiver(post_save, sender=FineRate)
@receiver(post_delete, sender=FineRate)
def clear_fine_rates_cache(sender, **kwargs):
    """
    Clear the fine rates cache when FineRate instances are saved or deleted.
    """
    cache.delete(ACTIVE_FINE_RATES_CACHE_KEY)


@receiver(post_save, sender=NotificationTemplate)
@receiver(post_delete, sender=NotificationTemplate)
def clear_templates_cache(sender, **kwargs):
    """
    Clear the notification templates cache when NotificationTemplate instances are saved or deleted.
    """
    cache.delete(ACTIVE_TEMPLATES_CACHE_KEY)


def get_cached_active_settings():
    """
    Get the active library settings from cache or database.
    """
    from django.core.cache import cache
    from .models import LibrarySettings
    
    # Try to get from cache first
    settings = cache.get(ACTIVE_SETTINGS_CACHE_KEY)
    
    if settings is None:
        # If not in cache, get from database
        settings = LibrarySettings.get_active_settings()
        if settings:
            # Cache for 1 hour (3600 seconds)
            cache.set(ACTIVE_SETTINGS_CACHE_KEY, settings, 3600)
    
    return settings

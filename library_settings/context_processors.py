from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .utils import get_active_settings


def library_settings(request):
    """
    Add library settings to the template context.
    """
    context = {
        'LIBRARY_NAME': getattr(settings, 'LIBRARY_NAME', 'Library Management System'),
        'LIBRARY_LOGO_URL': getattr(settings, 'LIBRARY_LOGO_URL', None),
        'CURRENT_YEAR': timezone.now().year,
        'LIBRARY_CONTACT_EMAIL': getattr(settings, 'LIBRARY_CONTACT_EMAIL', None),
        'LIBRARY_CONTACT_PHONE': getattr(settings, 'LIBRARY_CONTACT_PHONE', None),
        'LIBRARY_ADDRESS': getattr(settings, 'LIBRARY_ADDRESS', None),
    }
    
    # Try to get active settings from the database
    try:
        settings_obj = get_active_settings()
        if settings_obj:
            context.update({
                'library_settings': settings_obj,
                'LIBRARY_NAME': settings_obj.branch_name or context['LIBRARY_NAME'],
                'LIBRARY_ADDRESS': settings_obj.branch_address or context['LIBRARY_ADDRESS'],
                'LIBRARY_OPENING_HOURS': getattr(settings_obj, 'opening_hours', None),
                'LIBRARY_MAX_BORROW_DAYS': getattr(settings_obj, 'max_borrow_days', 14),
                'LIBRARY_MAX_RENEWALS': getattr(settings_obj, 'max_renewals', 2),
                'LIBRARY_FINE_PER_DAY': getattr(settings_obj, 'fine_per_day', 0.50),
            })
    except Exception:
        # If there's any error, just use the default settings
        pass
        
    return context


def feature_flags(request):
    """
    Add feature flags to the template context.
    """
    return {
        'FEATURE_BOOK_RESERVATIONS': getattr(settings, 'FEATURE_BOOK_RESERVATIONS', True),
        'FEATURE_ONLINE_PAYMENTS': getattr(settings, 'FEATURE_ONLINE_PAYMENTS', False),
        'FEATURE_EMAIL_NOTIFICATIONS': getattr(settings, 'FEATURE_EMAIL_NOTIFICATIONS', True),
        'FEATURE_SMS_NOTIFICATIONS': getattr(settings, 'FEATURE_SMS_NOTIFICATIONS', False),
        'FEATURE_MULTI_BRANCH': getattr(settings, 'FEATURE_MULTI_BRANCH', True),
        'FEATURE_MEMBER_PORTAL': getattr(settings, 'FEATURE_MEMBER_PORTAL', True),
        'FEATURE_ADVANCED_SEARCH': getattr(settings, 'FEATURE_ADVANCED_SEARCH', True),
        'FEATURE_RATINGS_REVIEWS': getattr(settings, 'FEATURE_RATINGS_REVIEWS', False),
        'FEATURE_RECOMMENDATIONS': getattr(settings, 'FEATURE_RECOMMENDATIONS', False),
    }


def user_permissions(request):
    """
    Add user permissions to the template context.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {}
        
    return {
        'user_can_borrow': request.user.has_perm('books.borrow_book'),
        'user_can_reserve': request.user.has_perm('books.reserve_book'),
        'user_can_renew': request.user.has_perm('books.renew_loan'),
        'user_can_manage_books': request.user.has_perm('books.manage_books'),
        'user_can_manage_members': request.user.has_perm('accounts.manage_members'),
        'user_can_manage_fines': request.user.has_perm('transactions.manage_fines'),
        'user_can_view_reports': request.user.has_perm('reports.view_reports'),
        'user_is_librarian': request.user.groups.filter(name='Librarians').exists(),
        'user_is_admin': request.user.is_superuser,
    }

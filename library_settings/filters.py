import django_filters
from django.utils.translation import gettext_lazy as _

from .models import LibraryBranch, LibraryPolicy, FineRate, NotificationTemplate


class LibraryBranchFilter(django_filters.FilterSet):
    """Filter for LibraryBranch model."""
    name = django_filters.CharFilter(lookup_expr='icontains')
    code = django_filters.CharFilter(lookup_expr='iexact')
    email = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = LibraryBranch
        fields = {
            'is_active': ['exact'],
            'created_at': ['gte', 'lte', 'exact', 'gt', 'lt'],
        }


class LibraryPolicyFilter(django_filters.FilterSet):
    """Filter for LibraryPolicy model."""
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = LibraryPolicy
        fields = {
            'policy_type': ['exact', 'in'],
            'is_active': ['exact'],
            'created_at': ['gte', 'lte', 'exact', 'gt', 'lt'],
        }


class FineRateFilter(django_filters.FilterSet):
    """Filter for FineRate model."""
    name = django_filters.CharFilter(lookup_expr='icontains')
    min_rate = django_filters.NumberFilter(field_name='rate', lookup_expr='gte')
    max_rate = django_filters.NumberFilter(field_name='rate', lookup_expr='lte')
    
    class Meta:
        model = FineRate
        fields = {
            'violation_type': ['exact', 'in'],
            'rate_type': ['exact'],
            'is_active': ['exact'],
            'created_at': ['gte', 'lte', 'exact', 'gt', 'lt'],
        }


class NotificationTemplateFilter(django_filters.FilterSet):
    """Filter for NotificationTemplate model."""
    name = django_filters.CharFilter(lookup_expr='icontains')
    subject = django_filters.CharFilter(lookup_expr='icontains')
    body = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = NotificationTemplate
        fields = {
            'notification_type': ['exact', 'in'],
            'is_active': ['exact'],
            'created_at': ['gte', 'lte', 'exact', 'gt', 'lt'],
        }


class LibrarySettingsFilter(django_filters.FilterSet):
    """Filter for LibrarySettings model."""
    branch_name = django_filters.CharFilter(lookup_expr='icontains')
    branch_address = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = LibraryBranch
        fields = {
            'created_at': ['gte', 'lte', 'exact', 'gt', 'lt'],
        }

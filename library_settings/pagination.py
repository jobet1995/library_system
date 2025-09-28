from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _


class StandardResultsSetPagination(PageNumberPagination):
    """
    A standard page number pagination style with configurable page sizes.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'page_size': self.get_page_size(self.request)
        })


class LargeResultsSetPagination(StandardResultsSetPagination):
    """
    A pagination class for endpoints that may return large result sets.
    """
    page_size = 50
    max_page_size = 500


class SmallResultsSetPagination(StandardResultsSetPagination):
    """
    A pagination class for endpoints that typically return small result sets.
    """
    page_size = 5
    max_page_size = 20


class LibraryBranchPagination(StandardResultsSetPagination):
    """
    Pagination class specifically for LibraryBranch endpoints.
    """
    page_size = 20
    max_page_size = 100


class LibraryPolicyPagination(StandardResultsSetPagination):
    """
    Pagination class specifically for LibraryPolicy endpoints.
    """
    page_size = 15
    max_page_size = 50


class FineRatePagination(StandardResultsSetPagination):
    """
    Pagination class specifically for FineRate endpoints.
    """
    page_size = 20
    max_page_size = 100


class NotificationTemplatePagination(StandardResultsSetPagination):
    """
    Pagination class specifically for NotificationTemplate endpoints.
    """
    page_size = 10
    max_page_size = 50


class LibrarySettingsPagination(StandardResultsSetPagination):
    """
    Pagination class specifically for LibrarySettings endpoints.
    """
    page_size = 10
    max_page_size = 50

from rest_framework import status
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _


class MultipleFieldLookupMixin:
    """
    Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field filtering.
    """
    def get_object(self):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        filter_kwargs = {}
        
        for field in self.lookup_fields:
            if self.kwargs.get(field, None):
                filter_kwargs[field] = self.kwargs[field]
                
        if not filter_kwargs:
            raise AssertionError(
                _('Expected view %s to be called with one of the lookup fields: %s')
                % (self.__class__.__name__, ', '.join(self.lookup_fields))
            )
            
        return queryset.get(**filter_kwargs)


class SoftDeleteModelMixin:
    """
    Instead of deleting a model instance, mark it as inactive.
    """
    def perform_destroy(self, instance):
        if hasattr(instance, 'is_active'):
            instance.is_active = False
            instance.save()
        else:
            instance.delete()


class BulkCreateModelMixin:
    """
    Either create or update model instances in bulk by using the HTTP PUT method.
    """
    def get_serializer(self, *args, **kwargs):
        """If an array is passed, set serializer to many."""
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)


class BulkUpdateModelMixin:
    """
    Update model instances in bulk by using the HTTP PATCH method.
    """
    def bulk_update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, 
            data=request.data, 
            many=isinstance(request.data, list),
            partial=partial
        )
        
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_update(serializer)
        
        return Response(serializer.data)
    
    def perform_bulk_update(self, serializer):
        serializer.save()


class BulkDeleteModelMixin:
    """
    Delete model instances in bulk by using the HTTP DELETE method.
    """
    def get_delete_queryset(self):
        """
        Get the list of items to delete.
        Override this method to customize the queryset.
        """
        return self.get_queryset()
    
    def bulk_destroy(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_delete_queryset())
        
        # Apply any filtering from the view's get_queryset method
        queryset = self.get_queryset().filter(pk__in=request.data.get('ids', []))
        
        self.perform_bulk_destroy(queryset)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def perform_bulk_destroy(self, queryset):
        """
        Perform the actual deletion of the queryset.
        Override this method to customize the deletion behavior.
        """
        queryset.delete()


class CacheResponseMixin:
    """
    Mixin to add caching to views.
    """
    cache_timeout = 60 * 5  # 5 minutes default
    
    def get_cache_key(self, request, *args, **kwargs):
        """
        Generate a cache key based on the request URL and query parameters.
        """
        return f"{request.path}?{request.META.get('QUERY_STRING', '')}"
    
    def get_cache_timeout(self):
        """
        Return the cache timeout for this view.
        Can be overridden to provide dynamic timeouts.
        """
        return self.cache_timeout
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to add caching.
        """
        cache_key = self.get_cache_key(request, *args, **kwargs)
        cached_response = cache.get(cache_key)
        
        if cached_response is not None:
            return cached_response
            
        response = super().dispatch(request, *args, **kwargs)
        
        # Only cache successful GET responses
        if request.method == 'GET' and response.status_code == 200:
            cache_timeout = self.get_cache_timeout()
            cache.set(cache_key, response, cache_timeout)
            
        return response

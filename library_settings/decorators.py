from functools import wraps
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie, vary_on_headers
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework import status


def group_required(*group_names):
    """
    Requires user membership in at least one of the groups passed in.
    """
    def in_groups(u):
        if u.is_authenticated:
            if u.is_superuser or bool(u.groups.filter(name__in=group_names)):
                return True
        return False
    
    return user_passes_test(in_groups)


def permission_required(perm, login_url=None, raise_exception=False):
    """
    Decorator for views that checks whether a user has a particular permission
    enabled, redirecting to the log-in page if necessary.
    If the raise_exception parameter is given the PermissionDenied exception
    is raised.
    """
    def check_perms(user):
        if user.has_perm(perm):
            return True
        
        # In case the 403 handler should be called raise the exception
        if raise_exception:
            raise PermissionDenied
            
        # As the last resort, show the login form
        return False
    
    return user_passes_test(check_perms, login_url=login_url)


def api_login_required(function=None):
    """
    Decorator for API views that checks that the user is logged in,
    returning a 403 response if not.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse(
                    {'detail': _('Authentication credentials were not provided.')}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if function:
        return decorator(function)
    return decorator


def api_permission_required(perm):
    """
    Decorator for API views that checks that the user has a specific permission,
    returning a 403 response if not.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_perm(perm):
                return JsonResponse(
                    {'detail': _('You do not have permission to perform this action.')}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def cache_on_auth(timeout):
    """
    Cache page with the key based on user authentication status.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Different cache key for authenticated vs anonymous users
            if request.user.is_authenticated:
                key_prefix = f'user_{request.user.id}'
            else:
                key_prefix = 'anonymous'
                
            return cache_page(timeout, key_prefix=key_prefix)(view_func)(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def class_view_decorator(function_decorator):
    """
    Convert a function based decorator into a class based decorator usable
    on class based Views.
    """
    def simple_decorator(View):
        View.dispatch = method_decorator(function_decorator)(View.dispatch)
        return View
    return simple_decorator


def require_http_methods(request_method_list):
    """
    Decorator to make a view only accept particular request methods.
    """
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            if request.method not in request_method_list:
                response = JsonResponse(
                    {'error': 'Method not allowed'}, 
                    status=status.HTTP_405_METHOD_NOT_ALLOWED
                )
                response['Allow'] = ', '.join(request_method_list)
                return response
            return func(request, *args, **kwargs)
        return inner
    return decorator


def handle_exceptions(func):
    """
    A decorator that wraps the passed in function and handles exceptions.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Log the exception here if needed
            # logger.exception("An error occurred: %s", str(e))
            return JsonResponse(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return wrapper


def validate_request_data(required_fields=None, optional_fields=None):
    """
    Decorator to validate that the request contains the required fields.
    """
    if required_fields is None:
        required_fields = []
    if optional_fields is None:
        optional_fields = []
    
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.method in ('POST', 'PUT', 'PATCH'):
                data = request.data if hasattr(request, 'data') else request.POST
                
                # Check for missing required fields
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return JsonResponse(
                        {'error': f'Missing required fields: {", ".join(missing_fields)}'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Check for unexpected fields
                all_allowed_fields = set(required_fields + optional_fields)
                unexpected_fields = [field for field in data if field not in all_allowed_fields]
                if unexpected_fields:
                    return JsonResponse(
                        {'error': f'Unexpected fields: {", ".join(unexpected_fields)}'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

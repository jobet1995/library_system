import time
from django.utils import timezone
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import activate, get_language
from django.core.cache import cache
from django.contrib.auth import get_user_model


class TimezoneMiddleware(MiddlewareMixin):
    """
    Middleware to properly handle the current timezone for the user.
    """
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            timezone.activate(request.user.timezone)
        else:
            timezone.deactivate()


class LanguageMiddleware(MiddlewareMixin):
    """
    Middleware to set the language based on user preferences or request.
    """
    def process_request(self, request):
        language = None
        
        # Check if user is authenticated and has a preferred language
        if hasattr(request, 'user') and request.user.is_authenticated:
            language = getattr(request.user, 'language', None)
        
        # Fall back to session language
        if not language:
            language = request.session.get('django_language', None)
        
        # Fall back to Accept-Language header
        if not language:
            language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            if language:
                language = language.split(',')[0].split('-')[0]
        
        # Default to settings.LANGUAGE_CODE if still no language
        if not language:
            language = settings.LANGUAGE_CODE
        
        # Activate the language
        activate(language)
        request.LANGUAGE_CODE = language


class ActiveUserMiddleware(MiddlewareMixin):
    """
    Middleware to track when a user was last seen on the site.
    """
    def process_request(self, request):
        if not request.user.is_authenticated:
            return
            
        # Get the current user's last activity from cache
        cache_key = f'user_last_activity_{request.user.id}'
        last_activity = cache.get(cache_key)
        
        # Only update the database at most once per minute to reduce load
        if not last_activity or (timezone.now() - last_activity).seconds > 60:
            User = get_user_model()
            User.objects.filter(pk=request.user.id).update(
                last_activity=timezone.now()
            )
            
        # Update the cache for the next request
        cache.set(cache_key, timezone.now(), settings.USER_LAST_ACTIVITY_INTERVAL_SECONDS)


class RequestTimeMiddleware(MiddlewareMixin):
    """
    Middleware to log request processing time.
    """
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        # Calculate the request processing time
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Add the header to the response
            response['X-Request-Duration'] = f"{duration:.3f}s"
            
            # Log slow requests
            if duration > 2.0:  # Log requests that take more than 2 seconds
                # In a real app, you'd want to log this to your logging system
                print(f"Slow request: {request.path} took {duration:.3f} seconds")
                
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to responses.
    """
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Add CSP header if configured
        if hasattr(settings, 'CSP_HEADER'):
            response['Content-Security-Policy'] = settings.CSP_HEADER
        
        # Add HSTS header if using HTTPS
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
        return response


class MaintenanceModeMiddleware(MiddlewareMixin):
    """
    Middleware to handle maintenance mode.
    """
    def process_request(self, request):
        # Check if maintenance mode is enabled
        maintenance_mode = getattr(settings, 'MAINTENANCE_MODE', False)
        
        # Allow superusers and staff to bypass maintenance mode
        if maintenance_mode and hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_superuser or request.user.is_staff:
                return None
                
        # Return a 503 Service Unavailable response if in maintenance mode
        if maintenance_mode:
            from django.http import HttpResponse
            return HttpResponse(
                "The site is currently down for maintenance. Please check back soon.",
                status=503,
                content_type='text/plain'
            )
            
        return None

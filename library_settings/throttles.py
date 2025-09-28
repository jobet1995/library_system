from rest_framework.throttling import UserRateThrottle, AnonRateThrottle, ScopedRateThrottle
from django.conf import settings


class BurstRateThrottle(UserRateThrottle):
    """
    Limits the rate of API calls that may be made by a given user in a short time period.
    """
    scope = 'burst'
    
    def __init__(self):
        # Override the rate string from settings or use default
        self.THROTTLE_RATES = getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {})
        self.rate = self.THROTTLE_RATES.get(self.scope, '100/hour')


class SustainedRateThrottle(UserRateThrottle):
    """
    Limits the rate of API calls that may be made by a given user over a longer period.
    """
    scope = 'sustained'
    
    def __init__(self):
        # Override the rate string from settings or use default
        self.THROTTLE_RATES = getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {})
        self.rate = self.THROTTLE_RATES.get(self.scope, '1000/day')


class AnonBurstRateThrottle(AnonRateThrottle):
    """
    Limits the rate of API calls that may be made by anonymous users in a short time period.
    """
    scope = 'anon_burst'
    
    def __init__(self):
        # Override the rate string from settings or use default
        self.THROTTLE_RATES = getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {})
        self.rate = self.THROTTLE_RATES.get(self.scope, '50/hour')


class AnonSustainedRateThrottle(AnonRateThrottle):
    """
    Limits the rate of API calls that may be made by anonymous users over a longer period.
    """
    scope = 'anon_sustained'
    
    def __init__(self):
        # Override the rate string from settings or use default
        self.THROTTLE_RATES = getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {})
        self.rate = self.THROTTLE_RATES.get(self.scope, '500/day')


class LibraryBranchThrottle(ScopedRateThrottle):
    """
    Throttle for library branch related endpoints.
    """
    scope_attr = 'throttle_scope'
    
    def __init__(self):
        # Override the rate string from settings or use default
        self.THROTTLE_RATES = getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {})
        self.scope = getattr(self.__class__, 'scope', None)
        self.rate = self.THROTTLE_RATES.get(self.scope, '100/hour')


class FineRateThrottle(ScopedRateThrottle):
    """
    Throttle for fine rate related endpoints.
    """
    scope_attr = 'throttle_scope'
    
    def __init__(self):
        # Override the rate string from settings or use default
        self.THROTTLE_RATES = getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {})
        self.scope = getattr(self.__class__, 'scope', None)
        self.rate = self.THROTTLE_RATES.get(self.scope, '50/hour')


class SettingsThrottle(ScopedRateThrottle):
    """
    Throttle for library settings related endpoints.
    """
    scope_attr = 'throttle_scope'
    
    def __init__(self):
        # Override the rate string from settings or use default
        self.THROTTLE_RATES = getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {})
        self.scope = getattr(self.__class__, 'scope', None)
        self.rate = self.THROTTLE_RATES.get(self.scope, '30/hour')

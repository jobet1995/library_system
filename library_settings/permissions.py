from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow staff members to edit objects.
    Read-only access is allowed to any authenticated user.
    """
    message = _('You do not have permission to perform this action.')
    
    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to staff users.
        return request.user and request.user.is_staff


class IsSuperUserOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow superusers to edit objects.
    Read-only access is allowed to any authenticated user.
    """
    message = _('Only superusers can perform this action.')
    
    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to superusers.
        return request.user and request.user.is_superuser


class IsStaffOrSelf(permissions.BasePermission):
    """
    Custom permission to only allow staff members or the user themselves
    to view or edit user profiles.
    """
    message = _('You do not have permission to access this resource.')
    
    def has_object_permission(self, request, view, obj):
        # Allow staff to perform any action
        if request.user and request.user.is_staff:
            return True
            
        # Allow users to view/edit their own profile
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        # For other cases, check if the object is the user
        return obj == request.user

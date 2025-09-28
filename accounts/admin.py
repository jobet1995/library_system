from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, UserType


class CustomUserAdmin(UserAdmin):
    """Custom User admin interface."""
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'membership_id')
    readonly_fields = ('date_joined', 'last_login', 'membership_id')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name', 'last_name', 'email', 'profile_picture',
                'date_of_birth', 'gender', 'phone', 'address', 'department'
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions', 'user_type'
            ),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined', 'membership_id')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2', 'email',
                'first_name', 'last_name', 'user_type'
            ),
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Make user_type required in admin
        if 'user_type' in form.base_fields:
            form.base_fields['user_type'].required = True
            
            # Only allow superusers to set admin users
            if not request.user.is_superuser and 'user_type' in form.base_fields:
                form.base_fields['user_type'].choices = [
                    (value, label) for value, label in form.base_fields['user_type'].choices 
                    if value != 'admin'
                ]
                
        return form


admin.site.register(CustomUser, CustomUserAdmin)

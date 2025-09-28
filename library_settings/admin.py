from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    LibraryBranch, LibraryPolicy, FineRate, 
    NotificationTemplate, LibrarySettings
)


@admin.register(LibraryBranch)
class LibraryBranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'phone', 'email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'address')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('address', 'phone', 'email')
        }),
        ('Additional Information', {
            'fields': ('opening_hours', 'manager')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LibraryPolicy)
class LibraryPolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'policy_type', 'is_active', 'created_at')
    list_filter = ('policy_type', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'policy_type', 'is_active')
        }),
        ('Policy Details', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FineRate)
class FineRateAdmin(admin.ModelAdmin):
    list_display = ('name', 'violation_type', 'rate', 'rate_type', 'is_active')
    list_filter = ('violation_type', 'rate_type', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('is_active', 'rate')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'violation_type', 'is_active')
        }),
        ('Rate Details', {
            'fields': ('rate', 'rate_type', 'max_fine')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'notification_type', 'is_active', 'created_at')
    list_filter = ('notification_type', 'is_active')
    search_fields = ('name', 'subject', 'body')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at', 'preview_subject', 'preview_body')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'notification_type', 'is_active')
        }),
        ('Email Content', {
            'fields': ('subject', 'body')
        }),
        ('Preview', {
            'fields': ('preview_subject', 'preview_body'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def preview_subject(self, obj):
        return format_html('<div style="background: #f8f9fa; padding: 10px; border: 1px solid #ddd;">{}</div>', 
                          obj.subject)
    preview_subject.short_description = 'Subject Preview'
    
    def preview_body(self, obj):
        return format_html('<div style="background: #f8f9fa; padding: 10px; border: 1px solid #ddd; white-space: pre-line;">{}</div>', 
                          obj.body)
    preview_body.short_description = 'Body Preview'


@admin.register(LibrarySettings)
class LibrarySettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'max_borrow_days', 'fine_per_day', 'allow_reservation')
    list_filter = ('allow_reservation',)
    search_fields = ('branch_name', 'branch_address')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Branch Information', {
            'fields': ('branch_name', 'branch_address')
        }),
        ('Borrowing Settings', {
            'fields': ('max_borrow_days', 'max_renewals')
        }),
        ('Fine Settings', {
            'fields': ('fine_per_day',)
        }),
        ('Features', {
            'fields': ('allow_reservation',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('branch_name')
    
    def get_readonly_fields(self, request, obj=None):
        # Don't allow changing branch name after creation
        if obj:
            return self.readonly_fields + ('branch_name',)
        return self.readonly_fields
    
    def save_model(self, request, obj, form, change):
        # Add any custom save logic here if needed
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the default settings
        if obj and obj.branch_name is None:
            return False
        return super().has_delete_permission(request, obj)
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        # Remove delete selected action
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import Notification, NotificationBatch


class NotificationInline(admin.TabularInline):
    model = Notification
    extra = 0
    readonly_fields = ('created_at', 'is_read')
    fields = ('user', 'notification_type', 'is_read', 'created_at', 'view_notification')
    
    def view_notification(self, obj):
        if obj.id:
            url = reverse('admin:notifications_notification_change', args=[obj.id])
            return format_html('<a href="{}">{}</a>', url, _('View'))
        return ""
    view_notification.short_description = _('Actions')


@admin.register(NotificationBatch)
class NotificationBatchAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'created_at', 'is_sent', 'sent_at', 'notification_count')
    list_filter = ('notification_type', 'is_sent', 'created_at')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at', 'sent_at', 'notification_count')
    date_hierarchy = 'created_at'
    filter_horizontal = ('target_users',)
    fieldsets = (
        (None, {
            'fields': ('title', 'message', 'notification_type')
        }),
        (_('Scheduling'), {
            'fields': ('expiry_date', 'is_sent', 'sent_at')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'notification_count')
        }),
        (_('Target Users'), {
            'fields': ('target_users',)
        }),
    )
    inlines = [NotificationInline]
    
    def notification_count(self, obj):
        return obj.notifications.count()
    notification_count.short_description = _('Notification Count')
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_sent:
            return self.readonly_fields + ('title', 'message', 'notification_type', 'expiry_date', 'target_users')
        return self.readonly_fields


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'is_read', 'created_at', 'expiry_date')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'user__email', 'message')
    readonly_fields = ('created_at', 'notification_batch')
    date_hierarchy = 'created_at'
    list_select_related = ('user', 'notification_batch')
    fieldsets = (
        (None, {
            'fields': ('user', 'notification_type', 'message', 'is_read')
        }),
        (_('Related Items'), {
            'fields': ('book', 'notification_batch')
        }),
        (_('Timing'), {
            'fields': ('created_at', 'expiry_date')
        }),
        (_('Links'), {
            'fields': ('link',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.notification_batch and obj.notification_batch.is_sent:
            return self.readonly_fields + ('user', 'notification_type', 'message', 'book', 'expiry_date', 'link')
        return self.readonly_fields

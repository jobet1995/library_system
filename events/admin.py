from django.contrib import admin
from django.utils.html import format_html
from .models import (
    EventCategory, Event, EventRegistration, EventFeedback,
    EventTag, EventSession, EventSpeaker, EventResource,
    EventSponsor, EventReminder
)


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


class EventResourceInline(admin.TabularInline):
    model = EventResource
    extra = 0
    fields = ('title', 'resource_type', 'file', 'url', 'is_public')
    readonly_fields = ()


class EventSessionInline(admin.TabularInline):
    model = EventSession
    extra = 0
    fields = ('title', 'start_datetime', 'end_datetime', 'location', 'is_break', 'order')
    readonly_fields = ()


class EventSpeakerInline(admin.StackedInline):
    model = EventSpeaker
    extra = 0
    fields = (('user', 'name'), 'title', 'organization', 'photo', 'is_visible', 'order')
    readonly_fields = ()


class EventSponsorInline(admin.TabularInline):
    model = EventSponsor
    extra = 0
    fields = ('name', 'logo', 'website', 'level', 'is_active', 'order')
    readonly_fields = ()


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_datetime', 'end_datetime', 'status', 'is_featured', 'is_free')
    list_filter = ('status', 'is_featured', 'is_free', 'category')
    search_fields = ('title', 'description', 'location')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    date_hierarchy = 'start_datetime'
    # Removed filter_horizontal for tags as it's not defined in the model
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'category', 'tags')
        }),
        ('Date & Time', {
            'fields': ('start_datetime', 'end_datetime', 'registration_deadline')
        }),
        ('Location & Details', {
            'fields': ('location', 'max_participants', 'featured_image', 'is_featured')
        }),
        ('Pricing', {
            'fields': ('is_free', 'price')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [
        EventSessionInline,
        EventSpeakerInline,
        EventResourceInline,
        EventSponsorInline,
    ]
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set created_by during the first save
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'status', 'is_confirmed', 'attended', 'registration_date')
    list_filter = ('status', 'is_confirmed', 'attended')
    search_fields = ('event__title', 'user__username', 'user__email')
    readonly_fields = ('registration_date', 'updated_at')
    date_hierarchy = 'registration_date'


@admin.register(EventFeedback)
class EventFeedbackAdmin(admin.ModelAdmin):
    list_display = ('event', 'display_name', 'rating', 'is_anonymous', 'created_at')
    list_filter = ('rating', 'is_anonymous')
    search_fields = ('event__title', 'user__username', 'user__email', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    def display_name(self, obj):
        return obj.display_name
    display_name.short_description = 'User'


@admin.register(EventTag)
class EventTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_featured', 'created_at')
    list_filter = ('is_featured',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)


@admin.register(EventSession)
class EventSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'event', 'start_datetime', 'end_datetime', 'is_break', 'order')
    list_filter = ('is_break', 'event')
    search_fields = ('title', 'description', 'event__title')
    readonly_fields = ()
    date_hierarchy = 'start_datetime'


@admin.register(EventSpeaker)
class EventSpeakerAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'title', 'organization', 'is_visible', 'order')
    list_filter = ('is_visible', 'event')
    search_fields = ('name', 'title', 'organization', 'event__title')
    readonly_fields = ('photo_preview',)
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-height: 200px;" />',
                obj.photo.url
            )
        return "No photo"
    photo_preview.short_description = 'Photo Preview'


@admin.register(EventResource)
class EventResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'event', 'resource_type', 'is_public', 'created_at')
    list_filter = ('resource_type', 'is_public', 'event')
    search_fields = ('title', 'description', 'event__title')
    readonly_fields = ('created_at', 'updated_at', 'file_url')
    
    def file_url(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">Download</a>',
                obj.file.url
            )
        return "No file"
    file_url.short_description = 'File'


@admin.register(EventSponsor)
class EventSponsorAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'level', 'is_active', 'order')
    list_filter = ('level', 'is_active', 'event')
    search_fields = ('name', 'description', 'event__title')
    readonly_fields = ('logo_preview',)
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 100px;" />',
                obj.logo.url
            )
        return "No logo"
    logo_preview.short_description = 'Logo Preview'


@admin.register(EventReminder)
class EventReminderAdmin(admin.ModelAdmin):
    list_display = ('event', 'reminder_type', 'subject', 'send_at', 'is_sent', 'sent_at')
    list_filter = ('reminder_type', 'is_sent', 'event')
    search_fields = ('subject', 'message', 'event__title')
    readonly_fields = ('created_at', 'sent_at', 'is_due')
    date_hierarchy = 'send_at'
    
    def is_due(self, obj):
        return obj.is_due
    is_due.boolean = True
    is_due.short_description = 'Is Due?'

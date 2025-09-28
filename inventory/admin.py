from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe

from .models import Location, BookCondition, BookCopy, InventoryCheck, InventoryRecord


class InventoryRecordInline(admin.TabularInline):
    model = InventoryRecord
    extra = 0
    readonly_fields = ('scanned_at', 'scanned_by', 'book_copy_link')
    fields = ('book_copy_link', 'status', 'condition', 'location', 'scanned_at', 'scanned_by', 'notes')
    
    def book_copy_link(self, obj):
        url = reverse('admin:inventory_bookcopy_change', args=[obj.book_copy.id])
        return mark_safe(f'<a href="{url}">{obj.book_copy}</a>')
    book_copy_link.short_description = _('Book Copy')
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'description')
    list_editable = ('is_active',)
    ordering = ('name',)
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'is_active')
        }),
    )


@admin.register(BookCondition)
class BookConditionAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_available', 'description_short')
    list_filter = ('is_available',)
    search_fields = ('name', 'description')
    list_editable = ('is_available',)
    ordering = ('name',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_available')
        }),
    )
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if obj.description and len(obj.description) > 50 else obj.description
    description_short.short_description = _('Description')


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'book_title', 'status', 'condition', 'location', 'is_available_for_checkout')
    list_filter = ('status', 'condition', 'location')
    search_fields = ('barcode', 'call_number', 'book__title', 'book__isbn')
    list_select_related = ('book', 'condition', 'location')
    readonly_fields = ('is_available_for_checkout',)
    
    fieldsets = (
        (_('Book Information'), {
            'fields': ('book', 'barcode', 'call_number')
        }),
        (_('Status & Location'), {
            'fields': ('status', 'condition', 'location')
        }),
        (_('Acquisition Details'), {
            'fields': ('acquisition_date', 'acquisition_source', 'acquisition_cost'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('notes', 'is_available_for_checkout'),
            'classes': ('collapse',)
        }),
    )
    
    def book_title(self, obj):
        return obj.book.title
    book_title.short_description = _('Book Title')
    book_title.admin_order_field = 'book__title'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('book', 'condition', 'location')


@admin.register(InventoryCheck)
class InventoryCheckAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'start_date', 'end_date', 'is_complete', 'created_by', 'item_count')
    list_filter = ('location', 'start_date', 'created_by')
    search_fields = ('name', 'notes')
    readonly_fields = ('created_by', 'start_date', 'end_date', 'item_count')
    list_select_related = ('location', 'created_by')
    inlines = [InventoryRecordInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'location', 'notes')
        }),
        (_('Timing'), {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',)
        }),
    )
    
    def is_complete(self, obj):
        return bool(obj.end_date)
    is_complete.boolean = True
    is_complete.short_description = 'Complete'
    
    def item_count(self, obj):
        return obj.records.count()
    item_count.short_description = _('Items Scanned')
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only on create
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(InventoryRecord)
class InventoryRecordAdmin(admin.ModelAdmin):
    list_display = ('book_copy_link', 'inventory_check', 'status', 'condition', 'location', 'scanned_at', 'scanned_by')
    list_filter = ('status', 'inventory_check', 'condition', 'location', 'scanned_at')
    search_fields = ('book_copy__barcode', 'book_copy__book__title', 'notes')
    readonly_fields = ('scanned_at', 'scanned_by', 'book_copy_link')
    list_select_related = ('book_copy', 'book_copy__book', 'condition', 'location', 'scanned_by', 'inventory_check')
    
    fieldsets = (
        (None, {
            'fields': ('inventory_check', 'book_copy_link')
        }),
        (_('Status & Condition'), {
            'fields': ('status', 'condition', 'location')
        }),
        (_('Scan Information'), {
            'fields': ('scanned_at', 'scanned_by', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    def book_copy_link(self, obj):
        url = reverse('admin:inventory_bookcopy_change', args=[obj.book_copy.id])
        return mark_safe(f'<a href="{url}">{obj.book_copy}</a>')
    book_copy_link.short_description = _('Book Copy')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'inventory_check', 'book_copy', 'book_copy__book', 'condition', 'location', 'scanned_by'
        )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only on create
            obj.scanned_by = request.user
        super().save_model(request, obj, form, change)

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Category, Author, Publisher, Book


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for the Category model."""
    list_display = ('name', 'description_short', 'book_count')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        """Return a shortened version of the description for the list display."""
        if obj.description:
            return f"{obj.description[:50]}..." if len(obj.description) > 50 else obj.description
        return ""
    description_short.short_description = _('Description')
    
    def book_count(self, obj):
        """Return the number of books in this category."""
        return obj.books.count()
    book_count.short_description = _('Books Count')


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Admin interface for the Author model."""
    list_display = ('name', 'book_count', 'created_at')
    search_fields = ('name', 'bio')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'bio')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def book_count(self, obj):
        """Return the number of books by this author."""
        return obj.books.count()
    book_count.short_description = _('Books Count')


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Admin interface for the Publisher model."""
    list_display = ('name', 'website_link', 'email', 'book_count', 'created_at')
    search_fields = ('name', 'email')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'website', 'email')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def website_link(self, obj):
        """Return a clickable link to the publisher's website."""
        if obj.website:
            return format_html('<a href="{}" target="_blank">{}</a>', 
                            obj.website, _('Visit Site'))
        return ""
    website_link.short_description = _('Website')
    
    def book_count(self, obj):
        """Return the number of books published by this publisher."""
        return obj.books.count()
    book_count.short_description = _('Books')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Admin interface for the Book model."""
    list_display = ('title', 'display_authors', 'publisher', 'category', 
                   'publication_year', 'language', 'shelf_location', 
                   'copies_status', 'is_available')
    list_filter = ('category', 'publication_date', 'language', 'created_at')
    search_fields = ('title', 'isbn', 'authors__name', 'publisher__name', 
                    'shelf_location')
    readonly_fields = ('created_at', 'updated_at', 'cover_image_preview')
    filter_horizontal = ('authors',)
    date_hierarchy = 'publication_date'
    
    fieldsets = (
        (None, {
            'fields': ('title', 'isbn', 'publication_date', 'language', 'shelf_location')
        }),
        (_('Cover Image'), {
            'fields': ('cover_image', 'cover_image_preview'),
            'classes': ('collapse', 'wide')
        }),
        (_('Description'), {
            'fields': ('summary',),
            'classes': ('collapse',)
        }),
        (_('Relationships'), {
            'fields': ('authors', 'publisher', 'category')
        }),
        (_('Inventory'), {
            'fields': ('copies_total', 'copies_available')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def display_authors(self, obj):
        """Return a string of authors for the list display."""
        return ", ".join([author.name for author in obj.authors.all()])
    display_authors.short_description = _('Authors')
    
    def publication_year(self, obj):
        """Return the publication year for the list display."""
        return obj.publication_date.year if obj.publication_date else ""
    publication_year.short_description = _('Year')
    publication_year.admin_order_field = 'publication_date'
    
    def copies_status(self, obj):
        """Return a string showing available/total copies."""
        return f"{obj.copies_available} / {obj.copies_total}"
    copies_status.short_description = _('Available / Total')
    
    def is_available(self, obj):
        """Return a boolean indicating if the book is available."""
        return obj.copies_available > 0
    is_available.boolean = True
    is_available.short_description = _('Available')
    
    def cover_image_preview(self, obj):
        """Display a preview of the cover image."""
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                obj.cover_image.url
            )
        return _("No cover image")
    cover_image_preview.short_description = _('Cover Preview')

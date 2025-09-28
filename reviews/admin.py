from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Review, ReviewVote, ReviewReport


class ReviewVoteInline(admin.TabularInline):
    model = ReviewVote
    extra = 0
    readonly_fields = ['user', 'vote_type', 'created_at']
    can_delete = False


class ReviewReportInline(admin.TabularInline):
    model = ReviewReport
    extra = 0
    readonly_fields = ['reporter', 'reason', 'description', 'status', 'created_at']
    can_delete = False


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'book_title', 'user_email', 'rating', 'is_approved', 'created_at', 'updated_at']
    list_filter = ['is_approved', 'rating', 'created_at', 'updated_at']
    search_fields = ['title', 'content', 'book__title', 'user__email']
    list_editable = ['is_approved']
    readonly_fields = ['created_at', 'updated_at', 'user', 'book']
    inlines = [ReviewVoteInline, ReviewReportInline]
    actions = ['approve_reviews', 'unapprove_reviews']
    
    def book_title(self, obj):
        return obj.book.title
    book_title.short_description = _('Book')
    book_title.admin_order_field = 'book__title'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = _('User')
    user_email.admin_order_field = 'user__email'
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} review(s) were successfully approved.")
    approve_reviews.short_description = _("Approve selected reviews")
    
    def unapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} review(s) were successfully unapproved.")
    unapprove_reviews.short_description = _("Unapprove selected reviews")


@admin.register(ReviewVote)
class ReviewVoteAdmin(admin.ModelAdmin):
    list_display = ['id', 'review_preview', 'user_email', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']
    search_fields = ['review__title', 'user__email']
    readonly_fields = ['review', 'user', 'vote_type', 'created_at']
    
    def review_preview(self, obj):
        return f"{obj.review.title[:50]}..." if len(obj.review.title) > 50 else obj.review.title
    review_preview.short_description = _('Review')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = _('User')
    user_email.admin_order_field = 'user__email'


@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'review_preview', 'reporter_email', 'reason', 'status', 'created_at', 'reviewed_at']
    list_filter = ['status', 'reason', 'created_at', 'reviewed_at']
    search_fields = ['review__title', 'reporter__email', 'description']
    readonly_fields = ['review', 'reporter', 'created_at', 'reviewed_at', 'reviewed_by']
    actions = ['mark_as_reviewed', 'mark_as_dismissed']
    
    def review_preview(self, obj):
        return f"{obj.review.title[:50]}..." if len(obj.review.title) > 50 else obj.review.title
    review_preview.short_description = _('Review')
    
    def reporter_email(self, obj):
        return obj.reporter.email
    reporter_email.short_description = _('Reported by')
    reporter_email.admin_order_field = 'reporter__email'
    
    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data and obj.status in ['reviewed', 'dismissed'] and not obj.reviewed_at:
            from django.utils import timezone
            obj.reviewed_at = timezone.now()
            obj.reviewed_by = request.user
        super().save_model(request, obj, form, change)
    
    def mark_as_reviewed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(
            status='reviewed', 
            reviewed_at=timezone.now(),
            reviewed_by=request.user
        )
        self.message_user(request, f"{updated} report(s) were marked as reviewed.")
    mark_as_reviewed.short_description = _("Mark selected reports as reviewed")
    
    def mark_as_dismissed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(
            status='dismissed', 
            reviewed_at=timezone.now(),
            reviewed_by=request.user
        )
        self.message_user(request, f"{updated} report(s) were dismissed.")
    mark_as_dismissed.short_description = _("Dismiss selected reports")

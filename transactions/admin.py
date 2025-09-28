from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import F, Q, Sum, Count, Case, When, Value as V
from django.db.models.functions import Concat
from django.utils import timezone
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import BorrowTransaction, Fine

@admin.register(BorrowTransaction)
class BorrowTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'book_title', 'user_info', 'borrow_date', 'due_date', 
                   'return_date', 'days_overdue', 'fine_amount', 'status', 'renew_count')
    list_filter = ('is_returned', 'borrow_date', 'due_date', 'return_date', 'user__groups')
    search_fields = ('book__title', 'book__isbn', 'user__username', 'user__first_name', 
                    'user__last_name', 'user__email')
    list_select_related = ('book', 'user')
    date_hierarchy = 'borrow_date'
    readonly_fields = ('days_remaining', 'fine_amount')
    fieldsets = (
        (_('Loan Information'), {
            'fields': ('user', 'book', 'borrow_date', 'due_date', 'return_date', 'is_returned')
        }),
        (_('Fines & Renewals'), {
            'fields': ('fine', 'renew_count', 'days_remaining', 'fine_amount')
        }),
        (_('Additional Information'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_returned', 'send_overdue_notices', 'generate_fines']

    def book_title(self, obj):
        return obj.book.title
    book_title.short_description = _('Book')
    book_title.admin_order_field = 'book__title'

    def user_info(self, obj):
        return f"{obj.user.get_full_name() or obj.user.username} ({obj.user.email})"
    user_info.short_description = _('User')
    user_info.admin_order_field = 'user__last_name'

    def days_remaining(self, obj):
        if obj.is_returned:
            return _("Returned")
        today = timezone.now().date()
        remaining = (obj.due_date - today).days
        if remaining > 0:
            return _("%(days)s days left") % {'days': remaining}
        return _("%(days)s days overdue") % {'days': -remaining}
    days_remaining.short_description = _('Status')

    def days_overdue(self, obj):
        if obj.is_returned or obj.due_date > timezone.now().date():
            return 0
        return (timezone.now().date() - obj.due_date).days
    days_overdue.short_description = _('Days Overdue')
    days_overdue.admin_order_field = 'due_date'

    def fine_amount(self, obj):
        if obj.fine > 0:
            return f"${obj.fine:.2f}"
        return "-"
    fine_amount.short_description = _('Fine')
    fine_amount.admin_order_field = 'fine'

    def status(self, obj):
        if obj.is_returned:
            return format_html('<span class="status-returned">{}</span>', _('Returned'))
        if obj.due_date < timezone.now().date():
            return format_html(
                '<span class="status-overdue">{}: {}</span>', 
                _('Overdue'), 
                self.days_remaining(obj)
            )
        return format_html(
            '<span class="status-ok">{}: {}</span>', 
            _('On loan'), 
            self.days_remaining(obj)
        )
    status.short_description = _('Status')
    status.admin_order_field = 'is_returned'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            _fine_amount=Case(
                When(fine__gt=0, then='fine'),
                default=V(0)
            )
        )
        return qs

    @admin.action(description=_('Mark selected books as returned'))
    def mark_returned(self, request, queryset):
        updated = queryset.filter(is_returned=False).update(
            return_date=timezone.now().date(),
            is_returned=True
        )
        self.message_user(
            request,
            _("Successfully marked %(count)d books as returned.") % {'count': updated}
        )

    @admin.action(description=_('Send overdue notices'))
    def send_overdue_notices(self, request, queryset):
        overdue_loans = queryset.filter(
            is_returned=False,
            due_date__lt=timezone.now().date()
        )
        count = overdue_loans.count()
        # In a real app, you would send emails here
        self.message_user(
            request,
            _("Sent overdue notices for %(count)d loans.") % {'count': count}
        )

    @admin.action(description=_('Generate fines for overdue books'))
    def generate_fines(self, request, queryset):
        from django.conf import settings
        from datetime import timedelta

        grace_days = settings.LIBRARY_SETTINGS['GRACE_PERIOD_DAYS']
        daily_fine = settings.LIBRARY_SETTINGS['DAILY_FINE_AMOUNT']
        max_fine = settings.LIBRARY_SETTINGS['MAX_FINE_AMOUNT']

        today = timezone.now().date()
        overdue_loans = queryset.filter(
            is_returned=False,
            due_date__lt=today - timedelta(days=grace_days)
        )

        updated = 0
        for loan in overdue_loans:
            days_late = (today - loan.due_date).days - grace_days
            if days_late > 0:
                fine_amount = min(days_late * daily_fine, max_fine)
                loan.fine = fine_amount
                loan.save()
                updated += 1

        self.message_user(
            request,
            _("Generated fines for %(count)d overdue loans.") % {'count': updated}
        )

    class Media:
        css = {
            'all': ('css/admin.css',)
        }

@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_info', 'transaction_link', 'amount_display', 
                   'paid', 'created_at', 'paid_at', 'days_since_created')
    list_filter = ('paid', 'created_at', 'paid_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 
                    'user__email', 'transaction__book__title')
    list_select_related = ('user', 'transaction', 'transaction__book')
    date_hierarchy = 'created_at'
    readonly_fields = ('days_since_created',)
    actions = ['mark_paid', 'export_fines_csv']
    
    fieldsets = (
        (_('Fine Information'), {
            'fields': ('user', 'transaction', 'amount', 'paid', 'paid_at')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'days_since_created'),
            'classes': ('collapse',)
        }),
    )

    def user_info(self, obj):
        return f"{obj.user.get_full_name() or obj.user.username} ({obj.user.email})"
    user_info.short_description = _('User')
    user_info.admin_order_field = 'user__last_name'

    def transaction_link(self, obj):
        url = reverse('admin:transactions_borrowtransaction_change', args=[obj.transaction.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.transaction))
    transaction_link.short_description = _('Transaction')
    transaction_link.admin_order_field = 'transaction__id'

    def amount_display(self, obj):
        return f"${obj.amount:.2f}"
    amount_display.short_description = _('Amount')
    amount_display.admin_order_field = 'amount'

    def days_since_created(self, obj):
        return (timezone.now().date() - obj.created_at.date()).days
    days_since_created.short_description = _('Days Outstanding')

    @admin.action(description=_('Mark selected fines as paid'))
    def mark_paid(self, request, queryset):
        updated = queryset.filter(paid=False).update(
            paid=True,
            paid_at=timezone.now()
        )
        self.message_user(
            request,
            _("Marked %(count)d fines as paid.") % {'count': updated}
        )
    @admin.action(description=_('Export selected fines to CSV'))
    def export_fines_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        from io import StringIO

        f = StringIO()
        writer = csv.writer(f)
        writer.writerow([
            _('ID'), _('User'), _('Email'), _('Book'), 
            _('Amount'), _('Created'), _('Paid'), _('Paid Date')
        ])

        for fine in queryset.select_related('user', 'transaction__book'):
            writer.writerow([
                fine.id,
                fine.user.get_full_name() or fine.user.username,
                fine.user.email,
                fine.transaction.book.title,
                str(fine.amount),
                fine.created_at.strftime('%Y-%m-%d'),
                _('Yes') if fine.paid else _('No'),
                fine.paid_at.strftime('%Y-%m-%d') if fine.paid_at else ''
            ])

        f.seek(0)
        response = HttpResponse(f, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=fines_export.csv'
        return response

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'transaction', 'transaction__book'
        )
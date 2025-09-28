from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Report, ReportArchive, ReportTemplate, ReportSchedule, ReportRecipient,
    ReportParameter, ReportCategory, ReportFavorite, ReportSubscription,
    ReportExport, ReportComment
)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_report_type_display', 'generated_by', 'generated_at', 'is_active', 'data_preview')
    list_filter = ('report_type', 'is_active', 'generated_at')
    search_fields = ('generated_by__username', 'generated_by__email', 'data')
    readonly_fields = ('generated_at',)
    date_hierarchy = 'generated_at'
    
    def data_preview(self, obj):
        return format_html('<pre>{}</pre>', str(obj.data)[:100] + '...' if len(str(obj.data)) > 100 else str(obj.data))
    data_preview.short_description = 'Data Preview'


@admin.register(ReportArchive)
class ReportArchiveAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'archived_at', 'archived_by', 'data_snapshot_preview')
    list_filter = ('archived_at',)
    search_fields = ('report__report_type', 'archived_by__username')
    readonly_fields = ('archived_at',)
    date_hierarchy = 'archived_at'
    
    def data_snapshot_preview(self, obj):
        return format_html('<pre>{}</pre>', str(obj.data_snapshot)[:100] + '...' if len(str(obj.data_snapshot)) > 100 else str(obj.data_snapshot))
    data_snapshot_preview.short_description = 'Data Snapshot'


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'format', 'is_active', 'created_at', 'updated_at')
    list_filter = ('format', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'frequency', 'is_active', 'last_run', 'next_run', 'created_by')
    list_filter = ('frequency', 'is_active', 'report_type')
    search_fields = ('name', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at', 'last_run')


@admin.register(ReportRecipient)
class ReportRecipientAdmin(admin.ModelAdmin):
    list_display = ('name', 'recipient_type', 'email', 'user', 'is_active', 'created_at')
    list_filter = ('recipient_type', 'is_active')
    search_fields = ('name', 'email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ReportParameter)
class ReportParameterAdmin(admin.ModelAdmin):
    list_display = ('name', 'label', 'param_type', 'is_required', 'default_value')
    list_filter = ('param_type', 'is_required')
    search_fields = ('name', 'label')


@admin.register(ReportCategory)
class ReportCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('parent',)


@admin.register(ReportFavorite)
class ReportFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'report', 'created_at')
    search_fields = ('user__username', 'report__report_type')
    readonly_fields = ('created_at',)
    list_select_related = ('user', 'report')


@admin.register(ReportSubscription)
class ReportSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'report', 'frequency', 'is_active', 'last_notified')
    list_filter = ('frequency', 'is_active')
    search_fields = ('user__username', 'report__report_type')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user', 'report')


@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'export_format', 'exported_by', 'created_at', 'download_count', 'file_link')
    list_filter = ('export_format',)
    search_fields = ('report__report_type', 'exported_by__username')
    readonly_fields = ('created_at', 'download_count')
    date_hierarchy = 'created_at'
    
    def file_link(self, obj):
        if obj.file_path:
            return format_html('<a href="{}" target="_blank">Download</a>', obj.file_path.url)
        return "No file"
    file_link.short_description = 'File'


@admin.register(ReportComment)
class ReportCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'author', 'is_internal', 'created_at', 'is_edited')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('content', 'author__username', 'report__report_type')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('report', 'author', 'parent')
    
    def is_edited(self, obj):
        return obj.updated_at > obj.created_at + timezone.timedelta(seconds=1)
    is_edited.boolean = True
    is_edited.short_description = 'Edited'

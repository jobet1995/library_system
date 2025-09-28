from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import (
    Report, ReportArchive, ReportTemplate, ReportSchedule, ReportRecipient,
    ReportParameter, ReportCategory, ReportFavorite, ReportSubscription,
    ReportExport, ReportComment
)
from accounts.serializers import UserSerializer


class ReportParameterSerializer(serializers.ModelSerializer):
    """Serializer for report parameters."""
    
    class Meta:
        model = ReportParameter
        fields = [
            'id', 'name', 'label', 'param_type', 'default_value',
            'is_required', 'choices'
        ]
        read_only_fields = ['id']

    def get_choices(self, obj):
        """Get choices as a list."""
        if obj.choices:
            return [choice.strip() for choice in obj.choices.split(',')]
        return None


class ReportCategorySerializer(serializers.ModelSerializer):
    """Serializer for report categories."""
    
    class Meta:
        model = ReportCategory
        fields = [
            'id', 'name', 'description', 'parent', 'icon',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ReportTemplateSerializer(serializers.ModelSerializer):
    """Serializer for report templates."""
    
    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'description', 'format', 'template_file',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ReportRecipientSerializer(serializers.ModelSerializer):
    """Serializer for report recipients."""
    
    class Meta:
        model = ReportRecipient
        fields = [
            'id', 'name', 'recipient_type', 'email', 'user',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ReportScheduleSerializer(serializers.ModelSerializer):
    """Serializer for report schedules."""
    
    class Meta:
        model = ReportSchedule
        fields = [
            'id', 'name', 'report_type', 'frequency', 'day_of_week',
            'day_of_month', 'time_of_day', 'is_active', 'last_run',
            'next_run', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['last_run', 'next_run', 'created_at', 'updated_at']


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for reports."""
    
    generated_by = UserSerializer(read_only=True)
    report_type_display = serializers.CharField(
        source='get_report_type_display',
        read_only=True
    )
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'report_type', 'report_type_display', 'data', 'generated_by',
            'generated_at', 'is_active', 'scheduled', 'filters', 'description',
            'modified', 'status'
        ]
        read_only_fields = ['generated_at', 'modified']
    
    def get_status(self, obj):
        """Get the status of the report."""
        return 'active' if obj.is_active else 'archived'


class ReportArchiveSerializer(serializers.ModelSerializer):
    """Serializer for report archives."""
    
    archived_by = UserSerializer(read_only=True)
    report = serializers.PrimaryKeyRelatedField(
        queryset=Report.objects.all()
    )
    
    class Meta:
        model = ReportArchive
        fields = [
            'id', 'report', 'data_snapshot', 'archived_by', 'archived_at'
        ]
        read_only_fields = ['archived_at']


class ReportFavoriteSerializer(serializers.ModelSerializer):
    """Serializer for report favorites."""
    
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    report_details = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportFavorite
        fields = ['id', 'user', 'report', 'notes', 'created_at', 'report_details']
        read_only_fields = ['created_at']
    
    def get_report_details(self, obj):
        """Include basic report information."""
        return {
            'id': obj.report.id,
            'report_type': obj.report.get_report_type_display(),
            'generated_at': obj.report.generated_at
        }


class ReportSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for report subscriptions."""
    
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    report_details = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportSubscription
        fields = [
            'id', 'user', 'report', 'frequency', 'is_active',
            'last_notified', 'created_at', 'updated_at', 'report_details'
        ]
        read_only_fields = ['last_notified', 'created_at', 'updated_at']
    
    def get_report_details(self, obj):
        """Include basic report information."""
        return {
            'id': obj.report.id,
            'report_type': obj.report.get_report_type_display(),
            'last_modified': obj.report.modified
        }


class ReportExportSerializer(serializers.ModelSerializer):
    """Serializer for report exports."""
    
    exported_by = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportExport
        fields = [
            'id', 'report', 'exported_by', 'export_format', 'file_path',
            'file_url', 'file_name', 'file_size', 'file_size_mb',
            'download_count', 'expires_at', 'created_at'
        ]
        read_only_fields = [
            'file_path', 'file_size', 'download_count', 'created_at'
        ]
    
    def get_file_url(self, obj):
        """Get the URL to download the exported file."""
        if obj.file_path:
            return obj.file_path.url
        return None
    
    def get_file_name(self, obj):
        """Get the file name from the file path."""
        if obj.file_path:
            return obj.file_path.name.split('/')[-1]
        return None
    
    def get_file_size_mb(self, obj):
        """Get the file size in MB."""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return None


class ReportCommentSerializer(serializers.ModelSerializer):
    """Serializer for report comments."""
    
    author = UserSerializer(read_only=True)
    is_edited = serializers.BooleanField(read_only=True)
    reply_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportComment
        fields = [
            'id', 'report', 'author', 'parent', 'content', 'is_internal',
            'is_edited', 'reply_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_reply_count(self, obj):
        """Get the number of replies to this comment."""
        return obj.replies.count()


class ReportDetailSerializer(ReportSerializer):
    """Detailed serializer for reports with related data."""
    
    archives = ReportArchiveSerializer(many=True, read_only=True)
    exports = ReportExportSerializer(many=True, read_only=True)
    comments = ReportCommentSerializer(many=True, read_only=True)
    
    class Meta(ReportSerializer.Meta):
        fields = ReportSerializer.Meta.fields + [
            'archives', 'exports', 'comments'
        ]


class ReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reports."""
    
    class Meta:
        model = Report
        fields = [
            'report_type', 'data', 'description', 'filters', 'is_active'
        ]
    
    def create(self, validated_data):
        """Create a new report instance."""
        user = self.context['request'].user
        validated_data['generated_by'] = user
        return super().create(validated_data)

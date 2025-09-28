from rest_framework import serializers
from .models import (
    LibraryBranch, LibraryPolicy, FineRate, 
    NotificationTemplate, LibrarySettings
)
from django.utils.translation import gettext_lazy as _


class LibraryBranchSerializer(serializers.ModelSerializer):
    """
    Serializer for LibraryBranch model.
    """
    class Meta:
        model = LibraryBranch
        fields = [
            'id', 'name', 'code', 'address', 'phone', 'email',
            'opening_hours', 'is_active', 'manager', 'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')
        extra_kwargs = {
            'manager': {'required': False}
        }

    def validate_code(self, value):
        """Convert code to uppercase."""
        return value.upper() if value else value


class LibraryPolicySerializer(serializers.ModelSerializer):
    """
    Serializer for LibraryPolicy model.
    """
    policy_type_display = serializers.CharField(
        source='get_policy_type_display', 
        read_only=True
    )

    class Meta:
        model = LibraryPolicy
        fields = [
            'id', 'name', 'policy_type', 'policy_type_display',
            'description', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')


class FineRateSerializer(serializers.ModelSerializer):
    """
    Serializer for FineRate model.
    """
    violation_type_display = serializers.CharField(
        source='get_violation_type_display', 
        read_only=True
    )
    rate_type_display = serializers.CharField(
        source='get_rate_type_display', 
        read_only=True
    )

    class Meta:
        model = FineRate
        fields = [
            'id', 'name', 'violation_type', 'violation_type_display',
            'rate', 'rate_type', 'rate_type_display', 'max_fine',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')

    def validate(self, data):
        """Validate that max_fine is greater than rate if provided."""
        rate = data.get('rate')
        max_fine = data.get('max_fine')
        
        if max_fine is not None and rate is not None and max_fine < rate:
            raise serializers.ValidationError({
                'max_fine': _('Maximum fine cannot be less than the rate.')
            })
        return data


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationTemplate model.
    """
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', 
        read_only=True
    )

    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'notification_type', 'notification_type_display',
            'subject', 'body', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')


class LibrarySettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for LibrarySettings model.
    """
    branch_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = LibrarySettings
        fields = [
            'id', 'branch_name', 'branch_address', 'branch_details',
            'max_borrow_days', 'fine_per_day', 'max_renewals',
            'allow_reservation', 'created_at', 'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')

    def get_branch_details(self, obj):
        """Get branch details if branch_name matches a LibraryBranch."""
        if not obj.branch_name:
            return None
            
        try:
            branch = LibraryBranch.objects.get(name=obj.branch_name, is_active=True)
            return {
                'id': branch.id,
                'code': branch.code,
                'phone': branch.phone,
                'email': branch.email,
                'opening_hours': branch.opening_hours
            }
        except LibraryBranch.DoesNotExist:
            return None

    def validate(self, data):
        """Validate that max_borrow_days is at least 1."""
        if 'max_borrow_days' in data and data['max_borrow_days'] < 1:
            raise serializers.ValidationError({
                'max_borrow_days': _('Borrow days must be at least 1.')
            })
        
        if 'fine_per_day' in data and data['fine_per_day'] < 0:
            raise serializers.ValidationError({
                'fine_per_day': _('Fine per day cannot be negative.')
            })
            
        return data


class LibrarySettingsLiteSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for LibrarySettings with essential fields only.
    Useful for nested representations.
    """
    class Meta:
        model = LibrarySettings
        fields = [
            'id', 'branch_name', 'max_borrow_days', 
            'fine_per_day', 'max_renewals', 'allow_reservation'
        ]

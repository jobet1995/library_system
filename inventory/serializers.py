from rest_framework import serializers
from .models import (
    Location, BookCondition, BookCopy, InventoryCheck, InventoryRecord
)
from books.serializers import BookDetailSerializer
from django.utils.translation import gettext_lazy as _


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class BookConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookCondition
        fields = '__all__'


class BookCopyListSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_cover = serializers.ImageField(source='book.cover_image', read_only=True)
    condition_name = serializers.CharField(source='condition.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    
    class Meta:
        model = BookCopy
        fields = [
            'id', 'barcode', 'book', 'book_title', 'book_cover',
            'call_number', 'status', 'condition', 'condition_name',
            'location', 'location_name', 'is_available_for_checkout'
        ]
        read_only_fields = ['is_available_for_checkout']


class BookCopyDetailSerializer(BookCopyListSerializer):
    book = BookDetailSerializer(read_only=True)
    condition = BookConditionSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    
    class Meta(BookCopyListSerializer.Meta):
        fields = BookCopyListSerializer.Meta.fields + [
            'acquisition_date', 'acquisition_source', 'acquisition_cost',
            'notes', 'created_at', 'updated_at'
        ]


class BookCopyCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookCopy
        fields = [
            'book', 'barcode', 'call_number', 'acquisition_date',
            'acquisition_source', 'acquisition_cost', 'condition',
            'location', 'status', 'notes'
        ]

    def validate_barcode(self, value):
        if self.instance and self.instance.barcode == value:
            return value
        if BookCopy.objects.filter(barcode=value).exists():
            raise serializers.ValidationError(_('A book copy with this barcode already exists.'))
        return value


class InventoryRecordSerializer(serializers.ModelSerializer):
    book_copy_details = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryRecord
        fields = [
            'id', 'inventory_check', 'book_copy', 'book_copy_details',
            'status', 'condition', 'location', 'notes', 'scanned_at', 'scanned_by'
        ]
        read_only_fields = ['scanned_at', 'scanned_by', 'book_copy_details']
    
    def get_book_copy_details(self, obj):
        return {
            'barcode': obj.book_copy.barcode,
            'call_number': obj.book_copy.call_number,
            'book_title': obj.book_copy.book.title
        }
    
    def create(self, validated_data):
        # Set the scanned_by user
        validated_data['scanned_by'] = self.context['request'].user
        return super().create(validated_data)


class InventoryCheckListSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = InventoryCheck
        fields = [
            'id', 'name', 'start_date', 'end_date', 'location',
            'location_name', 'created_by', 'created_by_username',
            'is_complete', 'item_count', 'notes'
        ]
        read_only_fields = ['created_by', 'is_complete', 'item_count']
    
    def get_item_count(self, obj):
        return obj.records.count()


class InventoryCheckDetailSerializer(InventoryCheckListSerializer):
    records = InventoryRecordSerializer(many=True, read_only=True)
    
    class Meta(InventoryCheckListSerializer.Meta):
        fields = InventoryCheckListSerializer.Meta.fields + ['records']

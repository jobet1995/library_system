from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

from .models import Location, BookCondition, BookCopy, InventoryCheck, InventoryRecord
from .serializers import (
    LocationSerializer, BookConditionSerializer, BookCopyListSerializer,
    BookCopyDetailSerializer, BookCopyCreateUpdateSerializer,
    InventoryCheckListSerializer, InventoryCheckDetailSerializer, InventoryRecordSerializer
)


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow staff to edit, but anyone to read.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class LocationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing library locations.
    """
    queryset = Location.objects.all().order_by('name')
    serializer_class = LocationSerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code']
    ordering = ['name']


class BookConditionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing book conditions.
    """
    queryset = BookCondition.objects.all().order_by('name')
    serializer_class = BookConditionSerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'is_available']
    ordering = ['name']


class BookCopyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing book copies.
    """
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact', 'in'],
        'condition': ['exact', 'in'],
        'location': ['exact', 'in'],
        'book': ['exact'],
        'created_at': ['date__gte', 'date__lte', 'date__gt', 'date__lt', 'date'],
    }
    search_fields = ['barcode', 'call_number', 'book__title', 'book__isbn']
    ordering_fields = ['barcode', 'call_number', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = BookCopy.objects.select_related(
            'book', 'condition', 'location'
        ).order_by('-created_at')
        
        # Filter by book title or author if search query is provided
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(book__title__icontains=search) |
                Q(book__authors__name__icontains=search)
            ).distinct()
            
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return BookCopyListSerializer
        elif self.action == 'retrieve':
            return BookCopyDetailSerializer
        return BookCopyCreateUpdateSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """
        Custom action to change the status of a book copy.
        """
        book_copy = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'status': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if new_status not in dict(BookCopy.STATUS_CHOICES):
            return Response(
                {'status': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        book_copy.status = new_status
        book_copy.save()
        
        serializer = self.get_serializer(book_copy)
        return Response(serializer.data)


class InventoryCheckViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing inventory checks.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['location', 'created_by', 'is_complete']
    search_fields = ['name', 'notes']
    ordering_fields = ['start_date', 'end_date']
    ordering = ['-start_date']

    def get_queryset(self):
        return InventoryCheck.objects.select_related('location', 'created_by')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InventoryCheckDetailSerializer
        return InventoryCheckListSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark an inventory check as complete.
        """
        inventory_check = self.get_object()
        if inventory_check.is_complete:
            return Response(
                {'status': 'Inventory check is already complete'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        inventory_check.end_date = timezone.now()
        inventory_check.save()
        
        serializer = self.get_serializer(inventory_check)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def report(self, request, pk=None):
        """
        Generate a report for the inventory check.
        """
        inventory_check = self.get_object()
        records = inventory_check.records.select_related(
            'book_copy', 'book_copy__book', 'condition', 'location'
        )
        
        # Generate report data
        status_counts = records.values('status').annotate(count=models.Count('id'))
        condition_counts = records.values('condition__name').annotate(count=models.Count('id'))
        
        return Response({
            'inventory_check': InventoryCheckDetailSerializer(inventory_check).data,
            'summary': {
                'total_items': records.count(),
                'status_counts': {item['status']: item['count'] for item in status_counts},
                'condition_counts': {item['condition__name']: item['count'] for item in condition_counts if item['condition__name']},
            },
            'items': InventoryRecordSerializer(records, many=True).data
        })


class InventoryRecordViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing inventory records.
    """
    queryset = InventoryRecord.objects.all()
    serializer_class = InventoryRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['inventory_check', 'book_copy', 'status', 'condition', 'location']
    ordering_fields = ['scanned_at']
    ordering = ['-scanned_at']

    def get_queryset(self):
        return InventoryRecord.objects.select_related(
            'inventory_check', 'book_copy', 'book_copy__book', 'condition', 'location', 'scanned_by'
        )
    
    def perform_create(self, serializer):
        serializer.save(scanned_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        # Check if the record already exists
        inventory_check_id = request.data.get('inventory_check')
        book_copy_id = request.data.get('book_copy')
        
        if inventory_check_id and book_copy_id:
            existing = InventoryRecord.objects.filter(
                inventory_check_id=inventory_check_id,
                book_copy_id=book_copy_id
            ).first()
            
            if existing:
                # Update existing record
                serializer = self.get_serializer(existing, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data)
        
        return super().create(request, *args, **kwargs)

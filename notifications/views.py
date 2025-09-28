from rest_framework import viewsets, status, permissions, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Notification, NotificationBatch
from .serializers import (
    NotificationSerializer,
    NotificationBatchSerializer,
    NotificationBatchCreateSerializer
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of an object to edit it."""
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the notification.
        return obj.user == request.user


class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows notifications to be viewed or edited.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """
        This view should return a list of all notifications
        for the currently authenticated user.
        """
        user = self.request.user
        queryset = Notification.objects.filter(user=user)
        
        # Filter by read/unread status if specified
        is_read = self.request.query_params.get('is_read', None)
        if is_read is not None:
            is_read = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read)
            
        # Filter by notification type if specified
        notification_type = self.request.query_params.get('type', None)
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
            
        # Filter by date range if specified
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
            
        return queryset.order_by('-created_at')
    
    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Mark a notification as read.
        """
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read'])
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all user's notifications as read."""
        updated = request.user.notifications.filter(is_read=False).update(is_read=True)
        return Response({'status': f'marked {updated} notifications as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get the count of unread notifications for the current user."""
        count = request.user.notifications.filter(is_read=False).count()
        return Response({'unread_count': count})


class NotificationBatchViewSet(mixins.CreateModelMixin,
                             mixins.RetrieveModelMixin,
                             mixins.ListModelMixin,
                             mixins.DestroyModelMixin,
                             viewsets.GenericViewSet):
    """
    API endpoint that allows notification batches to be viewed or created.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        This view should return a list of all notification batches
        that the user has permission to view.
        """
        if self.request.user.is_staff:
            return NotificationBatch.objects.all()
        return NotificationBatch.objects.none()
    
    def get_serializer_class(self):
        """
        Use different serializers for different actions.
        """
        if self.action == 'create':
            return NotificationBatchCreateSerializer
        return NotificationBatchSerializer
    
    def perform_create(self, serializer):
        """Set the creator of the notification batch."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send a notification batch."""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff users can send notification batches'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        batch = self.get_object()
        
        if batch.is_sent:
            return Response(
                {'error': 'This batch has already been sent'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        batch.send()
        return Response({'status': 'batch sent successfully'})
    
    @action(detail=True, methods=['get'])
    def notifications(self, request, pk=None):
        """Get all notifications for a specific batch."""
        batch = self.get_object()
        notifications = batch.notifications.all()
        page = self.paginate_queryset(notifications)
        
        if page is not None:
            serializer = NotificationSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
            
        serializer = NotificationSerializer(notifications, many=True, context={'request': request})
        return Response(serializer.data)

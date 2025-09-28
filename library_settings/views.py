from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _

from .permissions import IsStaffOrReadOnly, IsSuperUserOrReadOnly

from .models import (
    LibraryBranch, LibraryPolicy, FineRate, 
    NotificationTemplate, LibrarySettings
)
from .serializers import (
    LibraryBranchSerializer, LibraryPolicySerializer,
    FineRateSerializer, NotificationTemplateSerializer,
    LibrarySettingsSerializer, LibrarySettingsLiteSerializer
)


class LibraryBranchViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing library branches.
    """
    queryset = LibraryBranch.objects.all()
    serializer_class = LibraryBranchSerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'address', 'email']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Optionally filter by active status."""
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class LibraryPolicyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing library policies.
    """
    queryset = LibraryPolicy.objects.all()
    serializer_class = LibraryPolicySerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['policy_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['policy_type', 'name', 'created_at']
    ordering = ['policy_type', 'name']

    def get_queryset(self):
        """Optionally filter by active status."""
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class FineRateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing fine rates.
    """
    queryset = FineRate.objects.all()
    serializer_class = FineRateSerializer
    permission_classes = [IsSuperUserOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['violation_type', 'rate_type', 'is_active']
    search_fields = ['name']
    ordering_fields = ['violation_type', 'rate', 'created_at']
    ordering = ['violation_type', 'name']

    def get_queryset(self):
        """Optionally filter by active status."""
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing notification templates.
    """
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'is_active']
    search_fields = ['name', 'subject', 'body']
    ordering_fields = ['notification_type', 'name', 'created_at']
    ordering = ['notification_type', 'name']

    def get_queryset(self):
        """Optionally filter by active status."""
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class LibrarySettingsViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing library settings.
    """
    queryset = LibrarySettings.objects.all()
    serializer_class = LibrarySettingsSerializer
    permission_classes = [IsSuperUserOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['branch_name', 'branch_address']
    ordering_fields = ['branch_name', 'created_at']
    ordering = ['branch_name']

    # Allow read-only access to all authenticated users for active settings
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def active(self, request):
        """Get the active library settings."""
        settings = LibrarySettings.get_active_settings()
        if not settings:
            return Response(
                {'detail': _('No active library settings found.')},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(settings)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def by_branch(self, request):
        """Get settings by branch name."""
        branch_name = request.query_params.get('branch_name')
        if not branch_name:
            return Response(
                {'detail': _('branch_name parameter is required.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            settings = LibrarySettings.objects.get(branch_name=branch_name)
            serializer = self.get_serializer(settings)
            return Response(serializer.data)
        except LibrarySettings.DoesNotExist:
            return Response(
                {'detail': _('No settings found for the specified branch.')},
                status=status.HTTP_404_NOT_FOUND
            )

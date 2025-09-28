from django.utils import timezone
from django.db.models import Q, Count
from django.http import FileResponse, Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, BasePermission
from rest_framework.parsers import MultiPartParser

from .models import (
    Report, ReportArchive, ReportTemplate, ReportSchedule, ReportRecipient,
    ReportCategory, ReportFavorite, ReportSubscription, ReportExport, ReportComment
)
from .serializers import (
    ReportSerializer, ReportArchiveSerializer, ReportTemplateSerializer,
    ReportScheduleSerializer, ReportRecipientSerializer, ReportParameterSerializer,
    ReportCategorySerializer, ReportFavoriteSerializer, ReportSubscriptionSerializer,
    ReportExportSerializer, ReportCommentSerializer, ReportDetailSerializer,
    ReportCreateSerializer
)


class IsOwnerOrAdmin(BasePermission):
    """Custom permission to only allow owners or admins to edit objects."""
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
            
        # Check if the object has a user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        # Check for specific model types
        if isinstance(obj, (Report, ReportExport, ReportComment)):
            return obj.generated_by == request.user
            
        if isinstance(obj, (ReportFavorite, ReportSubscription)):
            return obj.user == request.user
            
        return False


class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet for managing reports."""
    
    queryset = Report.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['report_type', 'is_active', 'scheduled']
    search_fields = ['description', 'data']
    ordering_fields = ['generated_at', 'modified']
    ordering = ['-generated_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReportCreateSerializer
        elif self.action == 'retrieve':
            return ReportDetailSerializer
        return ReportSerializer
    
    def get_queryset(self):
        """Filter reports to only those the user has access to."""
        user = self.request.user
        queryset = super().get_queryset()
        
        if not user.is_staff:
            queryset = queryset.filter(generated_by=user)
            
        return queryset.prefetch_related('archives', 'exports', 'comments')
    def perform_create(self, serializer):
        """Set the generated_by field to the current user."""
        serializer.save(generated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a report."""
        report = self.get_object()
        report.is_active = False
        report.save()
        return Response({'status': 'report archived'})
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore an archived report."""
        report = self.get_object()
        report.is_active = True
        report.save()
        return Response({'status': 'report restored'})
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download the report data as a file."""
        report = self.get_object()
        format = request.query_params.get('format', 'json')
        
        if format == 'json':
            # Return JSON response
            return Response(report.data)
        else:
            # For other formats, you'd typically generate a file
            return Response(
                {'error': 'Unsupported format'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ReportArchiveViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing report archives."""
    
    serializer_class = ReportArchiveSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['report']
    ordering_fields = ['archived_at']
    ordering = ['-archived_at']
    
    def get_queryset(self):
        """Filter archives to those the user has access to."""
        user = self.request.user
        queryset = ReportArchive.objects.all()
        
        if not user.is_staff:
            queryset = queryset.filter(
                Q(archived_by=user) | Q(report__generated_by=user)
            )
            
        return queryset.select_related('report', 'archived_by')


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing report templates."""
    
    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [MultiPartParser, JSONParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['format', 'is_active']
    search_fields = ['name', 'description']
    
    def perform_create(self, serializer):
        """Set the owner when creating a template."""
        serializer.save(created_by=self.request.user)


class ReportScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing report schedules."""
    
    queryset = ReportSchedule.objects.all()
    serializer_class = ReportScheduleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['report_type', 'frequency', 'is_active']
    ordering_fields = ['next_run', 'last_run']
    ordering = ['-next_run']
    
    def get_queryset(self):
        """Filter schedules to those the user has access to."""
        user = self.request.user
        queryset = super().get_queryset()
        
        if not user.is_staff:
            queryset = queryset.filter(created_by=user)
            
        return queryset
    
    def perform_create(self, serializer):
        """Set the created_by field to the current user."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """Run the scheduled report immediately."""
        schedule = self.get_object()
        # Here you would typically call your report generation logic
        # For now, we'll just update the last_run time
        schedule.last_run = timezone.now()
        schedule.save()
        return Response({'status': 'report scheduled to run'})


class ReportRecipientViewSet(viewsets.ModelViewSet):
    """ViewSet for managing report recipients."""
    
    serializer_class = ReportRecipientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['recipient_type', 'is_active']
    search_fields = ['name', 'email']
    
    def get_queryset(self):
        """Filter recipients to those the user has access to."""
        user = self.request.user
        queryset = ReportRecipient.objects.all()
        
        if not user.is_staff:
            queryset = queryset.filter(
                Q(user=user) | Q(created_by=user)
            )
            
        return queryset
    
    def perform_create(self, serializer):
        """Set the created_by field to the current user."""
        serializer.save(created_by=self.request.user)


class ReportParameterViewSet(viewsets.ModelViewSet):
    """ViewSet for managing report parameters."""
    
    queryset = ReportParameter.objects.all()
    serializer_class = ReportParameterSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'label']


class ReportCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing report categories."""
    
    queryset = ReportCategory.objects.all()
    serializer_class = ReportCategorySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        """Return active categories by default."""
        queryset = super().get_queryset()
        show_inactive = self.request.query_params.get('show_inactive', 'false').lower() == 'true'
        
        if not show_inactive:
            queryset = queryset.filter(is_active=True)
            
        return queryset


class ReportFavoriteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user's favorite reports."""
    
    serializer_class = ReportFavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return only the current user's favorites."""
        return ReportFavorite.objects.filter(
            user=self.request.user
        ).select_related('report')
    
    def perform_create(self, serializer):
        """Set the user to the current user."""
        serializer.save(user=self.request.user)


class ReportSubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user's report subscriptions."""
    
    serializer_class = ReportSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'frequency']
    
    def get_queryset(self):
        """Return only the current user's subscriptions."""
        return ReportSubscription.objects.filter(
            user=self.request.user
        ).select_related('report')
    
    def perform_create(self, serializer):
        """Set the user to the current user."""
        serializer.save(user=self.request.user)


class ReportExportViewSet(viewsets.ModelViewSet):
    """ViewSet for managing report exports."""
    
    serializer_class = ReportExportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['report', 'export_format']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter exports to those the user has access to."""
        user = self.request.user
        queryset = ReportExport.objects.all()
        
        if not user.is_staff:
            queryset = queryset.filter(
                Q(exported_by=user) | Q(report__generated_by=user)
            )
            
        return queryset.select_related('report', 'exported_by')
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download the exported file."""
        export = self.get_object()
        
        if not export.file_path:
            return Response(
                {'error': 'File not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Increment download count
        export.increment_download_count()
        
        try:
            return FileResponse(export.file_path.open('rb'))
        except FileNotFoundError:
            raise Http404("File not found on server")


class ReportCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing comments on reports."""
    
    serializer_class = ReportCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['report', 'author', 'is_internal']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['created_at']
    
    def get_queryset(self):
        """Filter comments to those the user has access to."""
        user = self.request.user
        queryset = ReportComment.objects.all()
        
        if not user.is_staff:
            # Regular users can only see non-internal comments or their own comments
            queryset = queryset.filter(
                Q(is_internal=False) | Q(author=user)
            )
            
        return queryset.select_related('author', 'report')
    
    def perform_create(self, serializer):
        """Set the author to the current user."""
        serializer.save(author=self.request.user)
    
    def perform_update(self, serializer):
        """Update the updated_at timestamp."""
        serializer.save(updated_at=timezone.now())


# Additional utility views
class ReportStatsView(views.APIView):
    """View for getting statistics about reports."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        """Get report statistics."""
        user = request.user
        
        if user.is_staff:
            queryset = Report.objects.all()
        else:
            queryset = Report.objects.filter(generated_by=user)
        
        stats = {
            'total_reports': queryset.count(),
            'active_reports': queryset.filter(is_active=True).count(),
            'scheduled_reports': queryset.filter(scheduled=True).count(),
            'report_types': dict(
                queryset.values('report_type')
                .annotate(count=Count('id'))
                .values_list('report_type', 'count')
            ),
        }
        
        return Response(stats)


class UserReportDashboardView(views.APIView):
    """View for user's report dashboard data."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        """Get dashboard data for the current user."""
        user = request.user
        
        # Recent reports
        recent_reports = Report.objects.filter(
            generated_by=user
        ).order_by('-generated_at')[:5]
        
        # Upcoming scheduled reports
        upcoming_schedules = ReportSchedule.objects.filter(
            created_by=user,
            is_active=True,
            next_run__gt=timezone.now()
        ).order_by('next_run')[:5]
        
        # Recent exports
        recent_exports = ReportExport.objects.filter(
            exported_by=user
        ).order_by('-created_at')[:5]
        
        # Unread comments (on user's reports)
        if user.is_staff:
            unread_comments = ReportComment.objects.filter(
                is_internal=True
            ).exclude(
                author=user
            ).count()
        else:
            unread_comments = 0
        
        return Response({
            'recent_reports': ReportSerializer(recent_reports, many=True).data,
            'upcoming_schedules': ReportScheduleSerializer(upcoming_schedules, many=True).data,
            'recent_exports': ReportExportSerializer(recent_exports, many=True).data,
            'unread_comments': unread_comments,
        })

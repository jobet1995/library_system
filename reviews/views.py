from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Review, ReviewVote, ReviewReport
from .serializers import ReviewSerializer, ReviewVoteSerializer, ReviewReportSerializer
from books.models import Book


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the review or admin.
        return obj.user == request.user or request.user.is_staff


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows reviews to be viewed or edited.
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filterset_fields = ['book', 'user', 'is_approved', 'rating']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'rating']
    ordering = ['-created_at']

    def get_queryset(self):
        # Show only approved reviews to non-staff users
        queryset = Review.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_approved=True)
        return queryset

    def perform_create(self, serializer):
        # Auto-approve reviews from staff
        if self.request.user.is_staff:
            serializer.save(user=self.request.user, is_approved=True)
        else:
            serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        """
        Vote on a review (upvote/downvote).
        """
        review = self.get_object()
        vote_type = request.data.get('vote_type')
        
        if vote_type not in ['up', 'down']:
            return Response(
                {"error": "Invalid vote type. Must be 'up' or 'down'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already voted
        vote, created = ReviewVote.objects.get_or_create(
            review=review,
            user=request.user,
            defaults={'vote_type': vote_type}
        )
        
        if not created:
            if vote.vote_type == vote_type:
                # Remove vote if clicking the same button again
                vote.delete()
                return Response({"status": "vote removed"})
            else:
                # Toggle vote type
                vote.vote_type = vote_type
                vote.save()
        
        serializer = ReviewVoteSerializer(vote, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        """
        Report a review as inappropriate.
        """
        review = self.get_object()
        reason = request.data.get('reason')
        description = request.data.get('description', '')
        
        if not reason:
            return Response(
                {"error": "Reason is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report, created = ReviewReport.objects.get_or_create(
            review=review,
            reporter=request.user,
            defaults={
                'reason': reason,
                'description': description
            }
        )
        
        if not created:
            return Response(
                {"error": "You have already reported this review"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReviewReportSerializer(report, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReviewReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows review reports to be viewed or managed.
    """
    serializer_class = ReviewReportSerializer
    permission_classes = [IsAdminUser]  # Only admins can manage reports
    
    def get_queryset(self):
        queryset = ReviewReport.objects.all()
        status_param = self.request.query_params.get('status')
        
        if status_param:
            queryset = queryset.filter(status=status_param)
            
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Resolve a report (approve action and mark as reviewed).
        """
        report = self.get_object()
        action = request.data.get('action', 'dismiss')  # 'dismiss' or 'remove_review'
        
        if action == 'remove_review':
            report.review.delete()
        
        report.status = 'reviewed'
        report.reviewed_by = request.user
        report.save()
        
        return Response({"status": f"Report resolved with action: {action}"})


class BookReviewsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that returns reviews for a specific book.
    """
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        book_id = self.kwargs['book_id']
        queryset = Review.objects.filter(book_id=book_id, is_approved=True)
        
        # Apply filters if provided
        rating = self.request.query_params.get('rating')
        if rating:
            queryset = queryset.filter(rating=rating)
            
        return queryset.order_by('-created_at')
    
    def list(self, request, book_id=None):
        # Verify book exists
        get_object_or_404(Book, pk=book_id)
        return super().list(request)

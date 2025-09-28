from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Category, Author, Publisher, Book
from .serializers import (
    CategorySerializer, AuthorSerializer, PublisherSerializer,
    BookListSerializer, BookDetailSerializer, BookCreateUpdateSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows categories to be viewed or edited.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class AuthorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows authors to be viewed or edited.
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'bio']
    ordering_fields = ['name', 'book_count', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Optionally filter by book count.
        """
        queryset = super().get_queryset()
        min_books = self.request.query_params.get('min_books')
        if min_books is not None:
            try:
                queryset = queryset.annotate(book_count=Count('books')).filter(book_count__gte=int(min_books))
            except (ValueError, TypeError):
                pass
        return queryset


class PublisherViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows publishers to be viewed or edited.
    """
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'email']
    ordering_fields = ['name', 'book_count', 'created_at']
    ordering = ['name']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Optionally filter by book count.
        """
        queryset = super().get_queryset()
        min_books = self.request.query_params.get('min_books')
        if min_books is not None:
            try:
                queryset = queryset.annotate(book_count=Count('books')).filter(book_count__gte=int(min_books))
            except (ValueError, TypeError):
                pass
        return queryset


class BookViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows books to be viewed or edited.
    """
    queryset = Book.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ['title', 'isbn', 'authors__name', 'publisher__name']
    ordering_fields = ['title', 'publication_date', 'created_at', 'copies_available']
    ordering = ['title']
    filterset_fields = {
        'category': ['exact'],
        'authors': ['exact'],
        'publisher': ['exact'],
        'publication_date': ['exact', 'year', 'year__gt', 'year__lt'],
        'language': ['exact'],
        'copies_available': ['exact', 'gt', 'lt'],
    }

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        """
        if self.action == 'list':
            return BookListSerializer
        elif self.action == 'retrieve':
            return BookDetailSerializer
        return BookCreateUpdateSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {'request': self.request}

    def get_queryset(self):
        """
        Optionally filter by availability.
        """
        queryset = super().get_queryset()
        available_only = self.request.query_params.get('available_only', '').lower() == 'true'
        
        if available_only:
            queryset = queryset.filter(copies_available__gt=0)
            
        # Prefetch related to avoid N+1 queries
        return queryset.select_related('publisher', 'category').prefetch_related('authors')

    @action(detail=True, methods=['post'])
    def check_availability(self, request, pk=None):
        """
        Check if a book is available for borrowing.
        """
        book = self.get_object()
        return Response({
            'is_available': book.copies_available > 0,
            'copies_available': book.copies_available,
            'title': book.title,
            'isbn': book.isbn
        })

    @action(detail=True, methods=['post'])
    def add_copy(self, request, pk=None):
        """
        Add a copy of the book to the library.
        """
        book = self.get_object()
        book.copies_total += 1
        book.copies_available += 1
        book.save()
        return Response({
            'status': 'success',
            'message': _('Added one copy to the library'),
            'copies_total': book.copies_total,
            'copies_available': book.copies_available
        })

    @action(detail=True, methods=['post'])
    def remove_copy(self, request, pk=None):
        """
        Remove a copy of the book from the library.
        """
        book = self.get_object()
        if book.copies_total <= 0:
            return Response(
                {'error': _('No copies to remove')},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        book.copies_total -= 1
        if book.copies_available > 0:
            book.copies_available -= 1
            
        book.save()
        return Response({
            'status': 'success',
            'message': _('Removed one copy from the library'),
            'copies_total': book.copies_total,
            'copies_available': book.copies_available
        })

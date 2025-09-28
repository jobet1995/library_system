from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'reviews', views.ReviewViewSet, basename='review')
router.register(r'reports', views.ReviewReportViewSet, basename='report')

# For getting reviews for a specific book
book_review_router = DefaultRouter()
book_review_router.register(r'reviews', views.BookReviewsViewSet, basename='book-reviews')

urlpatterns = [
    path('', include(router.urls)),
    path('books/<int:book_id>/', include(book_review_router.urls)),
]

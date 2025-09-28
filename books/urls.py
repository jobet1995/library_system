from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'authors', views.AuthorViewSet, basename='author')
router.register(r'publishers', views.PublisherViewSet, basename='publisher')
router.register(r'books', views.BookViewSet, basename='book')

app_name = 'books'

urlpatterns = [
    path('', include(router.urls)),
]

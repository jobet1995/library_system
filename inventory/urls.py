from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'locations', views.LocationViewSet, basename='location')
router.register(r'book-conditions', views.BookConditionViewSet, basename='bookcondition')
router.register(r'book-copies', views.BookCopyViewSet, basename='bookcopy')
router.register(r'inventory-checks', views.InventoryCheckViewSet, basename='inventorycheck')
router.register(r'inventory-records', views.InventoryRecordViewSet, basename='inventoryrecord')

app_name = 'inventory'

urlpatterns = [
    path('', include(router.urls)),
]

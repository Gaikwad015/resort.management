from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InventoryItemViewSet, PurchaseOrderViewSet, SupplierViewSet, WastageViewSet

router = DefaultRouter()
router.register(r'items', InventoryItemViewSet, basename='inventory-item')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'wastages', WastageViewSet, basename='wastage')

urlpatterns = [
    path('', include(router.urls)),
]

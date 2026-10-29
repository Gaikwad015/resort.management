from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VehicleViewSet, DriverViewSet, TransportBookingViewSet,
    LostAndFoundViewSet, AIConciergeView
)

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'transports', TransportBookingViewSet, basename='transport-booking')
router.register(r'lost-and-found', LostAndFoundViewSet, basename='lost-and-found')

urlpatterns = [
    path('ai-chat/', AIConciergeView.as_view(), name='ai-concierge-chat'),
    path('', include(router.urls)),
]

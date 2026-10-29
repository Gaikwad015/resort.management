from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventVenueViewSet, CateringPackageViewSet, EventBookingViewSet

router = DefaultRouter()
router.register(r'venues', EventVenueViewSet, basename='event-venue')
router.register(r'catering-packages', CateringPackageViewSet, basename='catering-package')
router.register(r'bookings', EventBookingViewSet, basename='event-booking')

urlpatterns = [
    path('', include(router.urls)),
]

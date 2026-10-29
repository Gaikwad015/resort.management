from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HousekeepingViewSet, DiningVenueViewSet, TableReservationViewSet,
    SpaServiceViewSet, SpaBookingViewSet
)

router = DefaultRouter()
router.register(r'housekeeping', HousekeepingViewSet, basename='housekeeping')
router.register(r'dining-venues', DiningVenueViewSet, basename='dining-venue')
router.register(r'dining-reservations', TableReservationViewSet, basename='dining-reservation')
router.register(r'spa-services', SpaServiceViewSet, basename='spa-service')
router.register(r'spa-bookings', SpaBookingViewSet, basename='spa-booking')

urlpatterns = [
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoomTypeViewSet, RoomViewSet, AvailabilityCheckView

router = DefaultRouter()
router.register(r'room-types', RoomTypeViewSet, basename='roomtype')
router.register(r'rooms', RoomViewSet, basename='room')

urlpatterns = [
    path('availability/', AvailabilityCheckView.as_view(), name='availability_check'),
    path('', include(router.urls)),
]

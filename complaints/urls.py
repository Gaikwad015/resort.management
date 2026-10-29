from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GuestComplaintViewSet

router = DefaultRouter()
router.register(r'tickets', GuestComplaintViewSet, basename='complaint')

urlpatterns = [
    path('', include(router.urls)),
]

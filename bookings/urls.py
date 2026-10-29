from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, PaymentWebhookView

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('payments/webhook/', PaymentWebhookView.as_view(), name='payment_webhook'),
    path('', include(router.urls)),
]

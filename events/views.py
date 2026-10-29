from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from django.db.models import Q
from decimal import Decimal
from .models import EventVenue, CateringPackage, EventBooking
from .serializers import EventVenueSerializer, CateringPackageSerializer, EventBookingSerializer

class EventVenueViewSet(viewsets.ModelViewSet):
    queryset = EventVenue.objects.filter(is_active=True)
    serializer_class = EventVenueSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


class CateringPackageViewSet(viewsets.ModelViewSet):
    queryset = CateringPackage.objects.filter(is_active=True)
    serializer_class = CateringPackageSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]


class EventBookingViewSet(viewsets.ModelViewSet):
    queryset = EventBooking.objects.select_related('venue', 'catering_package', 'assigned_coordinator').all()
    serializer_class = EventBookingSerializer

    def get_permissions(self):
        if self.action in ['create', 'check_availability']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.full_clean()
        instance.save()

    @action(detail=False, methods=['get'], url_path='check-availability')
    def check_availability(self, request):
        """
        Check if a venue is available for a given time window without overlap.
        Query params: venue_id, start_time, end_time
        """
        venue_id = request.query_params.get('venue_id')
        start_time_str = request.query_params.get('start_time')
        end_time_str = request.query_params.get('end_time')

        if not venue_id or not start_time_str or not end_time_str:
            return Response({'error': 'venue_id, start_time, and end_time parameters required.'}, status=status.HTTP_400_BAD_REQUEST)

        start = parse_datetime(start_time_str)
        end = parse_datetime(end_time_str)
        if not start or not end or end <= start:
            return Response({'error': 'Valid ISO format start_time and end_time (end > start) required.'}, status=status.HTTP_400_BAD_REQUEST)

        conflicts = EventBooking.objects.filter(
            venue_id=venue_id,
            status__in=[EventBooking.Status.CONFIRMED, EventBooking.Status.IN_PROGRESS]
        ).filter(
            Q(start_time__lt=end) & Q(end_time__gt=start)
        )

        return Response({
            'available': not conflicts.exists(),
            'conflict_count': conflicts.count(),
            'message': 'Venue is available for booking.' if not conflicts.exists() else 'Venue is occupied during this time window.'
        })

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm_booking(self, request, pk=None):
        booking = self.get_object()
        advance = Decimal(str(request.data.get('advance_paid', booking.advance_paid)))
        booking.advance_paid = advance
        booking.status = EventBooking.Status.CONFIRMED
        booking.full_clean()
        booking.save()
        return Response({'message': f'Event {booking.booking_reference} confirmed.', 'status': booking.status})

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_booking(self, request, pk=None):
        booking = self.get_object()
        booking.status = EventBooking.Status.CANCELLED
        booking.save()
        return Response({'message': f'Event {booking.booking_reference} cancelled.', 'status': booking.status})

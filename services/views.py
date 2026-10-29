from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import HousekeepingTask, DiningVenue, TableReservation, SpaService, SpaBooking
from .serializers import (
    HousekeepingTaskSerializer, DiningVenueSerializer, TableReservationSerializer,
    SpaServiceSerializer, SpaBookingSerializer
)
from core.security.permissions import IsOwnerOrStaff
from core.security.audit import log_security_event

class HousekeepingViewSet(viewsets.ModelViewSet):
    """
    OWASP A01:2025: Role-based Housekeeping Task & Turnover Engine.
    Only Staff/Housekeeping/Admins can access.
    """
    serializer_class = HousekeepingTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        staff_roles = ['SUPER_ADMIN', 'ADMIN', 'HOTEL_MANAGER', 'HOUSEKEEPING', 'RECEPTIONIST']
        if getattr(user, 'role', None) in staff_roles or user.is_superuser:
            return HousekeepingTask.objects.select_related('room', 'assigned_to').all()
        # Non-staff denied
        return HousekeepingTask.objects.none()

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        task = self.get_object()
        task.complete_task()
        log_security_event(
            event_type='CONFIG_CHANGE',
            severity='INFO',
            request=request,
            details={'action': 'Housekeeping Completed', 'room': task.room.room_number},
            status_code=200
        )
        return Response({
            'message': f'Task completed. Room {task.room.room_number} is now marked AVAILABLE for check-in.',
            'task': HousekeepingTaskSerializer(task).data
        })


class DiningVenueViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public ViewSet to discover 5-Star fine dining restaurants and lounges.
    """
    queryset = DiningVenue.objects.filter(is_active=True)
    serializer_class = DiningVenueSerializer
    permission_classes = [permissions.AllowAny]


class TableReservationViewSet(viewsets.ModelViewSet):
    """
    Fine Dining Table Reservation Engine.
    Guests can reserve tables; Staff can manage all reservations.
    """
    serializer_class = TableReservationSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return TableReservation.objects.none()
        staff_roles = ['SUPER_ADMIN', 'ADMIN', 'HOTEL_MANAGER', 'RESTAURANT_MANAGER', 'RECEPTIONIST']
        if getattr(user, 'role', None) in staff_roles or user.is_superuser:
            return TableReservation.objects.select_related('venue').all()
        return TableReservation.objects.select_related('venue').filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user, status=TableReservation.Status.CONFIRMED)


class SpaServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public ViewSet for Ancient Ayurveda & Holistic Spa treatments.
    """
    queryset = SpaService.objects.filter(is_active=True)
    serializer_class = SpaServiceSerializer
    permission_classes = [permissions.AllowAny]


class SpaBookingViewSet(viewsets.ModelViewSet):
    """
    Luxury Spa Appointment Engine.
    """
    serializer_class = SpaBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        staff_roles = ['SUPER_ADMIN', 'ADMIN', 'HOTEL_MANAGER', 'SPA_MANAGER', 'RECEPTIONIST']
        if getattr(user, 'role', None) in staff_roles or user.is_superuser:
            return SpaBooking.objects.select_related('service', 'user').all()
        return SpaBooking.objects.select_related('service', 'user').filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status=SpaBooking.Status.CONFIRMED)

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
from .models import RoomType, Room, RoomAmenity, RoomInspection, RoomAssignmentLog
from .serializers import RoomTypeSerializer, RoomSerializer
from bookings.models import Booking

class RoomTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public API to explore luxury accommodations, suites, and amenities.
    """
    queryset = RoomType.objects.prefetch_related('amenities', 'images', 'rooms').all()
    serializer_class = RoomTypeSerializer
    permission_classes = [permissions.AllowAny]


class RoomViewSet(viewsets.ModelViewSet):
    """
    Enterprise Room Inventory & Floor-wise Management API.
    """
    queryset = Room.objects.select_related('room_type', 'inspected_by').all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='floor-map')
    def floor_map(self, request):
        """
        Interactive floor-wise visual room map for Hotel Command Center.
        Groups rooms by floor with operational status and inspection status.
        Hides sensitive guest names unless requester is authorized hotel staff.
        """
        is_staff = request.user.is_hotel_staff() if hasattr(request.user, 'is_hotel_staff') else request.user.is_staff
        rooms = Room.objects.select_related('room_type', 'inspected_by').order_by('floor', 'room_number')
        
        floors_dict = {}
        for r in rooms:
            floor_name = r.floor or "Main Level"
            if floor_name not in floors_dict:
                floors_dict[floor_name] = []
            
            # Find active current occupant if occupied
            occupant_info = None
            if r.status == Room.Status.OCCUPIED and is_staff:
                active_booking = Booking.objects.filter(
                    room=r,
                    status=Booking.Status.CHECKED_IN
                ).select_related('user').first()
                if active_booking:
                    occupant_info = {
                        'booking_id': str(active_booking.id)[:8].upper(),
                        'guest_name': active_booking.user.get_full_name() or active_booking.user.email,
                        'check_out': active_booking.check_out_date.strftime('%Y-%m-%d')
                    }

            floors_dict[floor_name].append({
                'id': str(r.id),
                'room_number': r.room_number,
                'room_type': r.room_type.name,
                'price': float(r.room_type.base_price_per_night),
                'status': r.status,
                'status_display': r.get_status_display(),
                'is_inspection_approved': r.is_inspection_approved,
                'last_inspected_at': r.last_inspected_at.strftime('%Y-%m-%d %H:%M') if r.last_inspected_at else None,
                'occupant': occupant_info
            })

        return Response({
            'total_rooms': rooms.count(),
            'floors': floors_dict
        })

    @action(detail=True, methods=['post'], url_path='inspect')
    def inspect_room(self, request, pk=None):
        """
        Room Inspection & Supervisor Approval Workflow.
        Transitions cleaned room into APPROVED and AVAILABLE status.
        """
        room = self.get_object()
        cleanliness = int(request.data.get('cleanliness_score', 5))
        is_approved = request.data.get('is_approved', True)
        notes = request.data.get('notes', 'Supervisor inspection completed.')

        RoomInspection.objects.create(
            room=room,
            inspector=request.user,
            cleanliness_score=cleanliness,
            is_approved=is_approved,
            notes=notes
        )

        if is_approved:
            room.is_inspection_approved = True
            room.last_inspected_at = timezone.now()
            room.inspected_by = request.user
            room.status = Room.Status.AVAILABLE
            room.save()
            return Response({
                'message': f'Room {room.room_number} successfully inspected and marked AVAILABLE.',
                'status': room.status
            })
        else:
            room.is_inspection_approved = False
            room.status = Room.Status.CLEANING
            room.save()
            return Response({
                'message': f'Room {room.room_number} inspection REJECTED. Returned to housekeeping cleaning.',
                'status': room.status
            })

    @action(detail=True, methods=['post'], url_path='change-room')
    @transaction.atomic
    def change_room(self, request, pk=None):
        """
        Room Reassignment / Relocation Workflow.
        Atomically switches an active booking to a new room.
        """
        old_room = self.get_object()
        new_room_id = request.data.get('new_room_id')
        reason = request.data.get('reason', 'Guest relocation request')

        if not new_room_id:
            return Response({'error': 'new_room_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_room = Room.objects.select_for_update().get(id=new_room_id)
        except Room.DoesNotExist:
            return Response({'error': 'Target room does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        if new_room.status != Room.Status.AVAILABLE:
            return Response({'error': f'Target room {new_room.room_number} is currently {new_room.status}.'}, status=status.HTTP_400_BAD_REQUEST)

        # Find active checked-in booking
        active_booking = Booking.objects.filter(room=old_room, status=Booking.Status.CHECKED_IN).first()
        if not active_booking:
            return Response({'error': f'No active checked-in booking found in Room {old_room.room_number}.'}, status=status.HTTP_400_BAD_REQUEST)

        # Execute room switch
        active_booking.room = new_room
        active_booking.save()

        # Update room statuses
        old_room.status = Room.Status.CLEANING
        old_room.save()

        new_room.status = Room.Status.OCCUPIED
        new_room.save()

        RoomAssignmentLog.objects.create(
            booking_id=str(active_booking.id),
            old_room=old_room,
            new_room=new_room,
            reason=reason,
            assigned_by=request.user
        )

        return Response({
            'message': f'Guest successfully relocated from Room {old_room.room_number} to Room {new_room.room_number}.',
            'old_room_status': old_room.status,
            'new_room_status': new_room.status
        })

    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        room = self.get_object()
        new_status = request.data.get('status')
        if new_status not in Room.Status.values:
            return Response({'error': f'Invalid room status. Allowed: {Room.Status.values}'}, status=status.HTTP_400_BAD_REQUEST)
        
        room.status = new_status
        if new_status == Room.Status.CLEANING:
            room.last_cleaned_at = timezone.now()
            room.is_inspection_approved = False
        room.save()
        return Response({'message': f'Room {room.room_number} status updated to {new_status}.', 'room': RoomSerializer(room).data})


class AvailabilityCheckView(APIView):
    """
    Public Real-Time Room Availability Search Engine.
    Filters available rooms matching dates and guest counts, and returns instant price estimates.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        check_in_str = request.query_params.get('check_in')
        check_out_str = request.query_params.get('check_out')
        guests = int(request.query_params.get('guests', 1))

        if not check_in_str or not check_out_str:
            available_rooms = Room.objects.filter(status='AVAILABLE', is_active=True).select_related('room_type')
            return Response({
                'count': available_rooms.count(),
                'rooms': RoomSerializer(available_rooms, many=True).data
            })

        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Dates must be in YYYY-MM-DD format.'}, status=status.HTTP_400_BAD_REQUEST)

        if check_in >= check_out:
            return Response({'error': 'Check-out date must be strictly after check-in date.'}, status=status.HTTP_400_BAD_REQUEST)

        booked_room_ids = Booking.objects.filter(
            status__in=['PENDING', 'CONFIRMED', 'CHECKED_IN']
        ).filter(
            Q(check_in_date__lt=check_out) & Q(check_out_date__gt=check_in)
        ).values_list('room_id', flat=True)

        available_rooms = Room.objects.filter(
            status='AVAILABLE',
            is_active=True
        ).exclude(
            id__in=booked_room_ids
        ).select_related('room_type')

        num_nights = (check_out - check_in).days
        results = []
        for room in available_rooms:
            max_capacity = room.room_type.max_adults + room.room_type.max_children
            if guests <= max_capacity:
                base_total = room.room_type.base_price_per_night * num_nights
                tax_total = (base_total * Decimal('0.18')).quantize(Decimal('0.01'))
                final_total = base_total + tax_total

                results.append({
                    'room_id': str(room.id),
                    'room_number': room.room_number,
                    'room_type': room.room_type.name,
                    'floor': room.floor,
                    'num_nights': num_nights,
                    'base_price_per_night': float(room.room_type.base_price_per_night),
                    'estimated_total': float(final_total),
                    'tax': float(tax_total),
                    'max_guests': max_capacity,
                    'bed_type': room.room_type.bed_type,
                    'size_sqm': room.room_type.room_size_sqm
                })

        return Response({
            'check_in': check_in_str,
            'check_out': check_out_str,
            'num_nights': num_nights,
            'available_count': len(results),
            'rooms': results
        })

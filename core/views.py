from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from core.models import SecurityAuditLog
from rooms.models import RoomType, Room, RoomInspection
from bookings.models import Booking, AdditionalCharge, GuestPreArrival, RefundRecord
from services.models import DiningVenue, SpaService, HousekeepingTask, SpaBooking
from accounts.models import LoyaltyAccount, GuestPreference
from complaints.models import GuestComplaint
from concierge.models import TransportBooking
from analytics.models import DailyOperatingExpense
from events.models import EventBooking

User = get_user_model()

def index(request):
    """
    Ultra-luxury 5-Star Hotel & Resort Landing Page.
    Passes real room types, fine dining venues, and spa treatments.
    """
    room_types = RoomType.objects.prefetch_related('amenities').all()
    dining_venues = DiningVenue.objects.filter(is_active=True)
    spa_services = SpaService.objects.filter(is_active=True)
    available_rooms = Room.objects.filter(status='AVAILABLE', is_active=True).select_related('room_type')

    context = {
        'room_types': room_types,
        'dining_venues': dining_venues,
        'spa_services': spa_services,
        'available_rooms': available_rooms,
    }
    return render(request, 'core/index.html', context)

def admin_dashboard(request):
    """
    Hotel Command Center - Real-time Operational Telemetry, Threat Monitor & Floor Map.
    """
    all_rooms = Room.objects.select_related('room_type', 'inspected_by').order_by('floor', 'room_number')
    total_rooms = all_rooms.count()
    available_rooms = all_rooms.filter(status='AVAILABLE').count()
    occupied_rooms = all_rooms.filter(status='OCCUPIED').count()
    cleaning_rooms = all_rooms.filter(status='CLEANING').count()
    reserved_rooms = all_rooms.filter(status='RESERVED').count()
    maintenance_rooms = all_rooms.filter(status='MAINTENANCE').count()
    pending_inspections = all_rooms.filter(status='CLEANING', is_inspection_approved=False).count()

    occupancy_rate = int((occupied_rooms / total_rooms) * 100) if total_rooms else 0

    # Group rooms floor-wise for Visual Floor Map
    floors = {}
    for r in all_rooms:
        floor_label = r.floor or "Floor 1"
        if floor_label not in floors:
            floors[floor_label] = []
        
        # Determine current occupant
        occupant_info = None
        if r.status == Room.Status.OCCUPIED:
            active_bk = Booking.objects.filter(room=r, status=Booking.Status.CHECKED_IN).select_related('user').first()
            if active_bk:
                occupant_info = {
                    'booking_id': str(active_bk.id)[:8].upper(),
                    'guest_name': active_bk.user.get_full_name() or active_bk.user.email,
                    'check_out': active_bk.check_out_date.strftime('%b %d')
                }

        floors[floor_label].append({
            'id': str(r.id),
            'room_number': r.room_number,
            'room_type': r.room_type.name,
            'price': r.room_type.base_price_per_night,
            'status': r.status,
            'status_display': r.get_status_display(),
            'is_inspection_approved': r.is_inspection_approved,
            'last_inspected_at': r.last_inspected_at,
            'occupant': occupant_info
        })

    # Financial KPIs
    active_bks = Booking.objects.filter(status__in=[Booking.Status.CHECKED_IN, Booking.Status.CHECKED_OUT, Booking.Status.CONFIRMED])
    room_rev = active_bks.aggregate(t=Sum('final_amount'))['t'] or Decimal('0.00')
    folio_rev = AdditionalCharge.objects.aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    event_rev = EventBooking.objects.filter(status__in=[EventBooking.Status.CONFIRMED, EventBooking.Status.COMPLETED]).aggregate(t=Sum('total_amount'))['t'] or Decimal('0.00')
    gross_revenue = room_rev + folio_rev + event_rev
    
    expenses = DailyOperatingExpense.objects.aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
    net_profit = gross_revenue - expenses

    adr = (room_rev / Decimal(str(max(occupied_rooms, 1)))) if occupied_rooms > 0 else (room_rev / Decimal('1'))
    revpar = (room_rev / Decimal(str(max(total_rooms, 1)))) if total_rooms > 0 else Decimal('0.00')

    recent_bookings = Booking.objects.select_related('user', 'room', 'room__room_type').order_by('-created_at')[:6]
    housekeeping_tasks = HousekeepingTask.objects.select_related('room').order_by('-created_at')[:4]
    recent_security_logs = SecurityAuditLog.objects.order_by('-timestamp')[:6]
    recent_complaints = GuestComplaint.objects.select_related('guest', 'assigned_staff').order_by('-created_at')[:5]

    context = {
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'occupied_rooms': occupied_rooms,
        'cleaning_rooms': cleaning_rooms,
        'reserved_rooms': reserved_rooms,
        'maintenance_rooms': maintenance_rooms,
        'pending_inspections': pending_inspections,
        'occupancy_rate': occupancy_rate,
        'floors': floors,
        'adr': round(float(adr), 2),
        'revpar': round(float(revpar), 2),
        'gross_revenue': round(float(gross_revenue), 2),
        'operating_expenses': round(float(expenses), 2),
        'net_profit': round(float(net_profit), 2),
        'recent_bookings': recent_bookings,
        'housekeeping_tasks': housekeeping_tasks,
        'security_logs': recent_security_logs,
        'recent_complaints': recent_complaints,
    }
    return render(request, 'dashboard/index.html', context)

def guest_dashboard(request):
    """
    Guest Portal - Upcoming Stays, Loyalty Status, Digital Check-in & Smart Concierge.
    """
    user = request.user
    if not user.is_authenticated:
        user = User.objects.filter(email='guest@elara.com').first()

    loyalty, _ = LoyaltyAccount.objects.get_or_create(user=user, defaults={'tier': 'PLATINUM', 'points_balance': 12450})
    user_bookings = Booking.objects.filter(user=user).select_related('room', 'room__room_type').order_by('-created_at') if user else []
    active_booking = user_bookings.first() if user_bookings else None
    
    pre_arrival = None
    if active_booking:
        pre_arrival = GuestPreArrival.objects.filter(booking=active_booking).first()

    complaints = GuestComplaint.objects.filter(guest=user).order_by('-created_at')[:3] if user else []
    transports = TransportBooking.objects.filter(guest=user).order_by('-created_at')[:3] if user else []

    context = {
        'guest_user': user,
        'loyalty': loyalty,
        'bookings': user_bookings,
        'active_booking': active_booking,
        'pre_arrival': pre_arrival,
        'complaints': complaints,
        'transports': transports,
    }
    return render(request, 'guest/dashboard.html', context)

class SecurityAlertsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not (request.user.role in ['SUPER_ADMIN', 'ADMIN', 'HOTEL_MANAGER'] or request.user.is_superuser):
            return Response({"error": "Unauthorized access to security logs."}, status=403)

        logs = SecurityAuditLog.objects.all()[:20]
        data = [
            {
                'id': str(log.id),
                'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'event_type': log.get_event_type_display(),
                'severity': log.severity,
                'user': log.user_email or 'Anonymous',
                'ip_address': log.ip_address,
                'path': log.path,
                'status_code': log.status_code,
                'details': log.details,
                'is_verified': log.verify_integrity(),
            }
            for log in logs
        ]
        return Response({'security_alerts': data})

def custom_400_view(request, exception=None):
    if request.path.startswith('/api/'):
        return JsonResponse({
            'status': 'error',
            'code': 'BAD_REQUEST',
            'message': 'The request could not be understood or was missing required parameters.',
            'correlation_id': getattr(request, 'correlation_id', '')
        }, status=400)
    return render(request, 'errors/400.html', {'correlation_id': getattr(request, 'correlation_id', '')}, status=400)

def custom_403_view(request, exception=None):
    if request.path.startswith('/api/'):
        return JsonResponse({
            'status': 'error',
            'code': 'FORBIDDEN',
            'message': 'Access to this luxury resource is strictly restricted.',
            'correlation_id': getattr(request, 'correlation_id', '')
        }, status=403)
    return render(request, 'errors/403.html', {'correlation_id': getattr(request, 'correlation_id', '')}, status=403)

def custom_404_view(request, exception=None):
    if request.path.startswith('/api/'):
        return JsonResponse({
            'status': 'error',
            'code': 'NOT_FOUND',
            'message': 'The requested resource does not exist.',
            'correlation_id': getattr(request, 'correlation_id', '')
        }, status=404)
    return render(request, 'errors/404.html', {'correlation_id': getattr(request, 'correlation_id', '')}, status=404)

def custom_500_view(request):
    if request.path.startswith('/api/'):
        return JsonResponse({
            'status': 'error',
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'An unexpected condition occurred. Our concierge technical team has been notified.',
            'correlation_id': getattr(request, 'correlation_id', '')
        }, status=500)
    return render(request, 'errors/500.html', {'correlation_id': getattr(request, 'correlation_id', '')}, status=500)

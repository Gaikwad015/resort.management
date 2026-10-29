import csv
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import UtilityMeter, EnergyConsumptionRecord, DailyOperatingExpense, RevenueForecastSnapshot
from .serializers import (
    UtilityMeterSerializer, EnergyConsumptionRecordSerializer,
    DailyOperatingExpenseSerializer, RevenueForecastSnapshotSerializer
)
from bookings.models import Booking, AdditionalCharge, RefundRecord
from rooms.models import Room
from services.models import SpaBooking
from events.models import EventBooking

class UtilityMeterViewSet(viewsets.ModelViewSet):
    queryset = UtilityMeter.objects.all()
    serializer_class = UtilityMeterSerializer
    permission_classes = [permissions.IsAuthenticated]


class EnergyConsumptionRecordViewSet(viewsets.ModelViewSet):
    queryset = EnergyConsumptionRecord.objects.select_related('meter', 'recorded_by').all()
    serializer_class = EnergyConsumptionRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)


class DailyOperatingExpenseViewSet(viewsets.ModelViewSet):
    queryset = DailyOperatingExpense.objects.select_related('recorded_by').all()
    serializer_class = DailyOperatingExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)


class RevenueForecastSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RevenueForecastSnapshot.objects.all()
    serializer_class = RevenueForecastSnapshotSerializer
    permission_classes = [permissions.IsAuthenticated]


class AnalyticsOverviewAPIView(APIView):
    """
    Hospitality Key Performance Indicators (KPIs) & Financial Breakdown.
    Calculates ADR, RevPAR, department revenues, expenses, and net operating profit.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        thirty_days_ago = today - timedelta(days=30)

        # 1. Room Revenue & Bookings
        active_bookings = Booking.objects.filter(
            status__in=[Booking.Status.CHECKED_IN, Booking.Status.CHECKED_OUT, Booking.Status.CONFIRMED]
        )
        room_revenue = active_bookings.aggregate(total=Sum('final_amount'))['total'] or Decimal('0.00')

        # Additional Folio / Incidental Charges
        folio_revenue = AdditionalCharge.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Spa Revenue
        spa_bookings = SpaBooking.objects.filter(status='CONFIRMED')
        spa_revenue = Decimal('0.00')
        for sb in spa_bookings.select_related('service'):
            if sb.service:
                spa_revenue += sb.service.price

        # Event & Gala Revenue
        event_revenue = EventBooking.objects.filter(
            status__in=[EventBooking.Status.CONFIRMED, EventBooking.Status.IN_PROGRESS, EventBooking.Status.COMPLETED]
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

        # Total Gross Revenue
        gross_revenue = room_revenue + folio_revenue + spa_revenue + event_revenue

        # 2. Operating Expenses
        expenses = DailyOperatingExpense.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        net_profit = gross_revenue - expenses

        # 3. Room Inventory & Metrics
        total_rooms = Room.objects.count()
        occupied_rooms = Room.objects.filter(status=Room.Status.OCCUPIED).count()
        available_rooms = Room.objects.filter(status=Room.Status.AVAILABLE).count()
        cleaning_rooms = Room.objects.filter(status=Room.Status.CLEANING).count()
        maintenance_rooms = Room.objects.filter(status=Room.Status.MAINTENANCE).count()

        occupancy_rate = (occupied_rooms / total_rooms * 100.0) if total_rooms > 0 else 0.0

        # ADR = Room Revenue / Total Occupied Room Nights (simplified to occupied rooms count if non-zero)
        adr = (room_revenue / Decimal(str(max(occupied_rooms, 1)))) if occupied_rooms > 0 else (room_revenue / Decimal('1'))
        
        # RevPAR = Room Revenue / Total Available Rooms
        revpar = (room_revenue / Decimal(str(max(total_rooms, 1)))) if total_rooms > 0 else Decimal('0.00')

        # 4. Cancellations & Refunds
        refunds_total = RefundRecord.objects.filter(status='APPROVED').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        cancelled_bookings = Booking.objects.filter(status=Booking.Status.CANCELLED).count()

        return Response({
            'kpis': {
                'occupancy_percentage': round(occupancy_rate, 1),
                'adr': round(float(adr), 2),
                'revpar': round(float(revpar), 2),
                'gross_revenue': round(float(gross_revenue), 2),
                'operating_expenses': round(float(expenses), 2),
                'net_profit': round(float(net_profit), 2),
            },
            'revenue_breakdown': {
                'rooms': round(float(room_revenue), 2),
                'dining_and_foliage': round(float(folio_revenue), 2),
                'spa_wellness': round(float(spa_revenue), 2),
                'events_weddings': round(float(event_revenue), 2),
            },
            'room_status_distribution': {
                'total': total_rooms,
                'available': available_rooms,
                'occupied': occupied_rooms,
                'cleaning': cleaning_rooms,
                'maintenance': maintenance_rooms,
            },
            'cancellations': {
                'cancelled_count': cancelled_bookings,
                'total_refunded': round(float(refunds_total), 2)
            }
        })


class RevenueForecastAPIView(APIView):
    """
    Predictive Hospitality Revenue Forecasting (7-day and 30-day projection).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        next_7 = today + timedelta(days=7)
        next_30 = today + timedelta(days=30)
        total_rooms = max(Room.objects.count(), 1)

        # 7-day projection from confirmed bookings
        bookings_7d = Booking.objects.filter(
            status__in=[Booking.Status.CONFIRMED, Booking.Status.CHECKED_IN],
            check_in_date__lte=next_7,
            check_out_date__gte=today
        )
        rev_7d = bookings_7d.aggregate(total=Sum('final_amount'))['total'] or Decimal('0.00')
        events_7d = EventBooking.objects.filter(
            status=EventBooking.Status.CONFIRMED,
            start_time__date__lte=next_7,
            start_time__date__gte=today
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_7d = rev_7d + events_7d
        occ_7d = min(100.0, (bookings_7d.count() / (total_rooms * 7)) * 100.0)
        adr_7d = (rev_7d / Decimal(str(max(bookings_7d.count(), 1))))
        revpar_7d = total_7d / Decimal(str(total_rooms * 7))

        # 30-day projection
        bookings_30d = Booking.objects.filter(
            status__in=[Booking.Status.CONFIRMED, Booking.Status.CHECKED_IN],
            check_in_date__lte=next_30,
            check_out_date__gte=today
        )
        rev_30d = bookings_30d.aggregate(total=Sum('final_amount'))['total'] or Decimal('0.00')
        events_30d = EventBooking.objects.filter(
            status=EventBooking.Status.CONFIRMED,
            start_time__date__lte=next_30,
            start_time__date__gte=today
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_30d = rev_30d + events_30d
        occ_30d = min(100.0, (bookings_30d.count() / (total_rooms * 30)) * 100.0)
        adr_30d = (rev_30d / Decimal(str(max(bookings_30d.count(), 1))))
        revpar_30d = total_30d / Decimal(str(total_rooms * 30))

        return Response({
            'forecast_7_days': {
                'projected_revenue': round(float(total_7d), 2),
                'projected_occupancy_pct': round(occ_7d, 1),
                'projected_adr': round(float(adr_7d), 2),
                'projected_revpar': round(float(revpar_7d), 2)
            },
            'forecast_30_days': {
                'projected_revenue': round(float(total_30d), 2),
                'projected_occupancy_pct': round(occ_30d, 1),
                'projected_adr': round(float(adr_30d), 2),
                'projected_revpar': round(float(revpar_30d), 2)
            }
        })


class AnalyticsExportCSVView(APIView):
    """
    Downloads RFC 4180 compliant CSV Financial & Occupancy Report.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        filename = f"elara_grand_financials_{timezone.now().strftime('%Y%m%d_%H%M')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(['ELARA GRAND HOTEL & RESORT - FINANCIAL & OPERATIONAL AUDIT REPORT'])
        writer.writerow(['Generated At', timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')])
        writer.writerow(['Generated By', request.user.email])
        writer.writerow([])

        # Section 1: Bookings & Revenue
        writer.writerow(['--- CONFIRMED & ACTIVE RESERVATIONS ---'])
        writer.writerow(['Booking ID', 'Guest Name', 'Room', 'Check-In', 'Check-Out', 'Total Amount (INR)', 'Status'])
        bookings = Booking.objects.select_related('user', 'room', 'room__room_type').all().order_by('-created_at')[:100]
        for b in bookings:
            writer.writerow([
                str(b.id)[:8].upper(),
                b.user.get_full_name() or b.user.email,
                b.room.room_number if b.room else 'Unassigned',
                b.check_in_date,
                b.check_out_date,
                b.final_amount,
                b.status
            ])

        writer.writerow([])
        # Section 2: Operating Expenses
        writer.writerow(['--- RECORDED OPERATING EXPENSES ---'])
        writer.writerow(['Expense ID', 'Date', 'Category', 'Description', 'Amount (INR)', 'Invoice Ref'])
        expenses = DailyOperatingExpense.objects.all().order_by('-expense_date')[:100]
        for e in expenses:
            writer.writerow([
                str(e.id)[:8].upper(),
                e.expense_date,
                e.get_category_display(),
                e.description,
                e.amount,
                e.invoice_number
            ])

        return response

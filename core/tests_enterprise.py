from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from decimal import Decimal
from datetime import timedelta, date, time

from accounts.models import LoyaltyAccount, GuestPreference
from rooms.models import RoomType, Room, RoomInspection
from rooms.views import RoomViewSet
from bookings.models import Booking, AdditionalCharge, GuestPreArrival
from bookings.views import BookingViewSet
from inventory.models import InventoryCategory, Supplier, InventoryItem, PurchaseOrder, PurchaseOrderItem
from inventory.views import InventoryItemViewSet, PurchaseOrderViewSet
from workforce.models import Department, StaffProfile, ShiftSchedule, AttendanceRecord, LeaveRequest
from workforce.views import AttendanceRecordViewSet
from events.models import EventVenue, CateringPackage, EventBooking
from events.views import EventBookingViewSet
from complaints.models import GuestComplaint, ComplaintAudit
from complaints.views import GuestComplaintViewSet
from concierge.models import Vehicle, Driver, TransportBooking, LostAndFoundItem, AIConciergeQuery
from concierge.views import AIConciergeView
from analytics.views import AnalyticsOverviewAPIView, AnalyticsExportCSVView

User = get_user_model()

class EnterpriseResortModulesTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        # Users
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@elara.com',
            password='AdminPassword123!',
            first_name='Admin',
            last_name='User',
            role='SUPER_ADMIN'
        )
        self.guest_user = User.objects.create_user(
            username='guest_test',
            email='guest@elara.com',
            password='GuestPassword123!',
            first_name='Arjun',
            last_name='Sharma',
            role='CUSTOMER'
        )
        self.staff_user = User.objects.create_user(
            username='staff_test',
            email='staff@elara.com',
            password='StaffPassword123!',
            first_name='Kavita',
            last_name='Deshmukh',
            role='RECEPTIONIST'
        )

        # Room Type & Room
        self.room_type = RoomType.objects.create(
            name='Presidential Kohinoor Suite',
            slug='presidential-kohinoor',
            description='Majestic ultra-luxury suite',
            base_price_per_night=Decimal('75000.00'),
            max_adults=4,
            max_children=2,
            bed_type='Palatial Emperor Bed',
            room_size_sqm=165
        )
        self.room = Room.objects.create(
            room_number='501',
            floor='Floor 5',
            room_type=self.room_type,
            status=Room.Status.AVAILABLE
        )

        # Department & Staff Profile
        self.dept = Department.objects.create(
            name='Front Desk & Concierge',
            code='FDC',
            manager=self.admin_user
        )
        self.staff_profile = StaffProfile.objects.create(
            user=self.staff_user,
            employee_code='EMP-101',
            department=self.dept,
            designation='Senior Butler',
            hire_date=date(2025, 1, 1)
        )

    # 1. Visual Room & Floor Management Workflow (Section 3.A)
    def test_room_floor_map_and_supervisor_inspection(self):
        # Move room to CLEANING
        self.room.status = Room.Status.CLEANING
        self.room.is_inspection_approved = False
        self.room.save()

        # Floor map API call
        request = self.factory.get('/api/v1/rooms/floor-map/')
        force_authenticate(request, user=self.admin_user)
        view = RoomViewSet.as_view({'get': 'floor_map'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn('floors', response.data)
        self.assertIn('Floor 5', response.data['floors'])

        # Supervisor inspection and approval
        inspect_req = self.factory.post(
            f'/api/v1/rooms/{self.room.id}/inspect/',
            {'is_approved': True, 'cleanliness_score': 5, 'notes': 'Suite ready for royal VIP.'},
            format='json'
        )
        force_authenticate(inspect_req, user=self.admin_user)
        inspect_view = RoomViewSet.as_view({'post': 'inspect_room'})
        inspect_res = inspect_view(inspect_req, pk=self.room.id)
        self.assertEqual(inspect_res.status_code, 200)

        self.room.refresh_from_db()
        self.assertTrue(self.room.is_inspection_approved)
        self.assertEqual(self.room.status, Room.Status.AVAILABLE)
        self.assertEqual(RoomInspection.objects.filter(room=self.room).count(), 1)

    # 2. Digital Pre-Arrival & Express Checkout (Section 3.F)
    def test_digital_pre_arrival_and_express_checkout(self):
        today = timezone.localdate()
        booking = Booking.objects.create(
            user=self.guest_user,
            room=self.room,
            check_in_date=today,
            check_out_date=today + timedelta(days=2),
            num_adults=2,
            room_price_total=Decimal('150000.00'),
            tax_total=Decimal('27000.00'),
            final_amount=Decimal('177000.00'),
            status=Booking.Status.CHECKED_IN
        )

        # Pre-arrival registration
        pre_req = self.factory.post(
            f'/api/v1/bookings/{booking.id}/pre-arrival/',
            {
                'id_document_type': 'PASSPORT',
                'id_document_number': 'N1234567',
                'expected_arrival_time': '14:30:00'
            },
            format='json'
        )
        force_authenticate(pre_req, user=self.guest_user)
        pre_view = BookingViewSet.as_view({'post': 'submit_pre_arrival'})
        pre_res = pre_view(pre_req, pk=booking.id)
        self.assertEqual(pre_res.status_code, 200)
        self.assertTrue(GuestPreArrival.objects.filter(booking=booking).exists())

        # Post incidental charge
        charge_req = self.factory.post(
            f'/api/v1/bookings/{booking.id}/add-charge/',
            {'charge_type': 'DINING', 'amount': '4500.00', 'description': 'In-Suite Champagne Breakfast'},
            format='json'
        )
        force_authenticate(charge_req, user=self.admin_user)
        charge_view = BookingViewSet.as_view({'post': 'add_additional_charge'})
        charge_res = charge_view(charge_req, pk=booking.id)
        self.assertEqual(charge_res.status_code, 200)

        booking.refresh_from_db()
        self.assertEqual(booking.additional_charges_total, Decimal('4500.00'))

        # Request Express Checkout
        checkout_req = self.factory.post(f'/api/v1/bookings/{booking.id}/request-express-checkout/')
        force_authenticate(checkout_req, user=self.guest_user)
        checkout_view = BookingViewSet.as_view({'post': 'request_express_checkout'})
        checkout_res = checkout_view(checkout_req, pk=booking.id)
        self.assertEqual(checkout_res.status_code, 200)

        # Approve Checkout -> Room automatically transitions to CLEANING
        approve_req = self.factory.post(f'/api/v1/bookings/{booking.id}/approve-checkout/')
        force_authenticate(approve_req, user=self.admin_user)
        approve_view = BookingViewSet.as_view({'post': 'approve_checkout'})
        approve_res = approve_view(approve_req, pk=booking.id)
        self.assertEqual(approve_res.status_code, 200)

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CHECKED_OUT)
        self.room.refresh_from_db()
        self.assertEqual(self.room.status, Room.Status.CLEANING)

    # 3. Inventory Stock Control & Negative Stock Prevention (Section 3.D)
    def test_inventory_movement_and_negative_stock_rejection(self):
        cat = InventoryCategory.objects.create(name='Linen & Bath', slug='linen-bath')
        supplier = Supplier.objects.create(company_name='Egyptian Cotton Mills', contact_person='Tariq', email='sales@cotton.eg')
        item = InventoryItem.objects.create(
            name='Egyptian Cotton Bath Towel 700 GSM',
            sku='TOWL-EGY-001',
            category=cat,
            unit=InventoryItem.Unit.PIECE,
            unit_cost=Decimal('1200.00'),
            current_stock=Decimal('10.00'),
            minimum_stock_alert=Decimal('5.00')
        )

        # Stock reduction (USAGE_OUT)
        item.record_stock_movement(
            qty=Decimal('3.00'),
            tx_type='USAGE_OUT',
            user=self.admin_user,
            reference='Housekeeping Floor 5 Replenish'
        )
        item.refresh_from_db()
        self.assertEqual(item.current_stock, Decimal('7.00'))

        # Negative stock protection: attempting to deduct 50 when only 7 exist
        with self.assertRaises(ValidationError):
            item.record_stock_movement(
                qty=Decimal('50.00'),
                tx_type='USAGE_OUT',
                user=self.admin_user,
                reference='Exceeding quantity test'
            )

    # 4. Workforce Shift Overlap Conflict Prevention (Section 3.E)
    def test_workforce_shift_overlap_prevention_and_attendance(self):
        today = timezone.localdate()
        # Schedule initial shift
        ShiftSchedule.objects.create(
            staff=self.staff_profile,
            department=self.dept,
            shift_type=ShiftSchedule.ShiftType.MORNING,
            date=today
        )

        # Attempting to double-schedule same staff member on same date must raise ValidationError
        duplicate_shift = ShiftSchedule(
            staff=self.staff_profile,
            department=self.dept,
            shift_type=ShiftSchedule.ShiftType.NIGHT,
            date=today
        )
        with self.assertRaises(ValidationError):
            duplicate_shift.clean()

        # Digital Clock-In
        clock_req = self.factory.post('/api/v1/workforce/attendance/clock-in/')
        force_authenticate(clock_req, user=self.staff_user)
        clock_view = AttendanceRecordViewSet.as_view({'post': 'clock_in'})
        clock_res = clock_view(clock_req)
        self.assertEqual(clock_res.status_code, 200)
        self.assertTrue(AttendanceRecord.objects.filter(staff=self.staff_profile, date=today).exists())

    # 5. Wedding & Event Venue Overlap Prevention (Section 3.K)
    def test_event_venue_overlap_prevention(self):
        venue = EventVenue.objects.create(
            name='The Kohinoor Grand Ballroom',
            slug='kohinoor-ballroom',
            max_capacity=800,
            area_sqft=12000,
            base_daily_rental=Decimal('350000.00'),
            description='Pillarless luxury ballroom'
        )
        now = timezone.now()
        start1 = now + timedelta(days=10, hours=10)
        end1 = now + timedelta(days=10, hours=22)

        # First confirmed event booking
        event1 = EventBooking.objects.create(
            event_name='Deshmukh Royal Destination Wedding',
            venue=venue,
            client_name='Rajesh Deshmukh',
            client_email='deshmukh@example.com',
            client_phone='+919876543210',
            start_time=start1,
            end_time=end1,
            guest_count=450,
            status=EventBooking.Status.CONFIRMED
        )

        # Second event booking overlapping during the same window
        start2 = now + timedelta(days=10, hours=14)
        end2 = now + timedelta(days=11, hours=2)
        overlapping_event = EventBooking(
            event_name='Global Tech Summit',
            venue=venue,
            client_name='Corporate Planner',
            client_email='events@tech.com',
            client_phone='+919123456789',
            start_time=start2,
            end_time=end2,
            guest_count=200,
            status=EventBooking.Status.CONFIRMED
        )

        with self.assertRaises(ValidationError):
            overlapping_event.clean()

    # 6. Guest Complaint SLA Tracking & Service Recovery (Section 3.G)
    def test_complaint_sla_and_resolution(self):
        req = self.factory.post(
            '/api/v1/complaints/tickets/',
            {
                'category': 'HVAC',
                'priority': 'URGENT',
                'title': 'Suite AC Temperature Issue',
                'description': 'Temperature in bedroom is 25C instead of 20C.'
            },
            format='json'
        )
        force_authenticate(req, user=self.guest_user)
        view = GuestComplaintViewSet.as_view({'post': 'create'})
        response = view(req)
        self.assertEqual(response.status_code, 201)

        complaint = GuestComplaint.objects.get(id=response.data['id'])
        self.assertEqual(complaint.priority, 'URGENT')
        self.assertIsNotNone(complaint.sla_due_time)
        self.assertEqual(ComplaintAudit.objects.filter(complaint=complaint).count(), 1)

        # Resolve complaint
        resolve_req = self.factory.post(
            f'/api/v1/complaints/tickets/{complaint.id}/resolve/',
            {'resolution_notes': 'Thermostat sensor recalibrated, set to 19.5C.', 'compensation_offered': 'Spa voucher'},
            format='json'
        )
        force_authenticate(resolve_req, user=self.admin_user)
        resolve_view = GuestComplaintViewSet.as_view({'post': 'resolve_complaint'})
        resolve_res = resolve_view(resolve_req, pk=complaint.id)
        self.assertEqual(resolve_res.status_code, 200)

        complaint.refresh_from_db()
        self.assertEqual(complaint.status, GuestComplaint.Status.RESOLVED)

    # 7. AI Guest Concierge Grounded Knowledge Retrieval
    def test_ai_concierge_query_engine(self):
        # Query about check-in timings
        req = self.factory.post('/api/v1/concierge/ai-chat/', {'query': 'What is the check-in and check-out time?'}, format='json')
        view = AIConciergeView.as_view()
        res = view(req)
        self.assertEqual(res.status_code, 200)
        self.assertIn('14:00', res.data['response'])
        self.assertEqual(res.data['intent'], 'CHECKIN_CHECKOUT_POLICY')
        self.assertTrue(AIConciergeQuery.objects.exists())

    # 8. Revenue & RevPAR Analytics & CSV Export (Section 3.B)
    def test_analytics_kpi_overview_and_csv_export(self):
        # Analytics KPI API
        req = self.factory.get('/api/v1/analytics/overview/')
        force_authenticate(req, user=self.admin_user)
        view = AnalyticsOverviewAPIView.as_view()
        res = view(req)
        self.assertEqual(res.status_code, 200)
        self.assertIn('kpis', res.data)
        self.assertIn('adr', res.data['kpis'])
        self.assertIn('revpar', res.data['kpis'])
        self.assertIn('gross_revenue', res.data['kpis'])

        # CSV Export API
        csv_req = self.factory.get('/api/v1/analytics/export/csv/')
        force_authenticate(csv_req, user=self.admin_user)
        csv_view = AnalyticsExportCSVView.as_view()
        csv_res = csv_view(csv_req)
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res['Content-Type'], 'text/csv')
        self.assertIn('ELARA GRAND HOTEL & RESORT', csv_res.content.decode('utf-8'))

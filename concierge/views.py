from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Vehicle, Driver, TransportBooking, LostAndFoundItem, AIConciergeQuery
from .serializers import (
    VehicleSerializer, DriverSerializer, TransportBookingSerializer,
    LostAndFoundItemSerializer, AIConciergeQuerySerializer
)
from rooms.models import RoomType
from services.models import DiningVenue, SpaService
from events.models import EventVenue

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]


class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [permissions.IsAuthenticated]


class TransportBookingViewSet(viewsets.ModelViewSet):
    queryset = TransportBooking.objects.select_related('guest', 'booking', 'vehicle', 'driver').all()
    serializer_class = TransportBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'is_hotel_staff') and user.is_hotel_staff():
            return self.queryset
        return self.queryset.filter(guest=user)

    def perform_create(self, serializer):
        serializer.save(guest=self.request.user)

    @action(detail=True, methods=['post'], url_path='assign-fleet')
    def assign_fleet(self, request, pk=None):
        booking = self.get_object()
        vehicle_id = request.data.get('vehicle_id')
        driver_id = request.data.get('driver_id')

        if vehicle_id:
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id)
                booking.vehicle = vehicle
                vehicle.status = Vehicle.Status.ON_TRIP
                vehicle.save()
            except Vehicle.DoesNotExist:
                return Response({'error': 'Vehicle not found.'}, status=status.HTTP_404_NOT_FOUND)

        if driver_id:
            try:
                driver = Driver.objects.get(id=driver_id)
                booking.driver = driver
                driver.status = Driver.Status.ON_TRIP
                driver.save()
            except Driver.DoesNotExist:
                return Response({'error': 'Driver not found.'}, status=status.HTTP_404_NOT_FOUND)

        booking.status = TransportBooking.Status.ASSIGNED
        booking.save()
        return Response({'message': 'Fleet and chauffeur assigned successfully.', 'status': booking.status})

    @action(detail=True, methods=['post'], url_path='complete-trip')
    def complete_trip(self, request, pk=None):
        booking = self.get_object()
        booking.status = TransportBooking.Status.COMPLETED
        booking.save()

        if booking.vehicle:
            booking.vehicle.status = Vehicle.Status.AVAILABLE
            booking.vehicle.save()
        if booking.driver:
            booking.driver.status = Driver.Status.ON_DUTY
            booking.driver.save()

        return Response({'message': 'Transport trip completed successfully.', 'status': booking.status})


class LostAndFoundViewSet(viewsets.ModelViewSet):
    queryset = LostAndFoundItem.objects.select_related('found_by_staff', 'claimed_by_guest', 'handed_over_by').all()
    serializer_class = LostAndFoundItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(found_by_staff=self.request.user)

    @action(detail=True, methods=['post'], url_path='claim')
    def claim_item(self, request, pk=None):
        """
        Secure vault release workflow verifying owner identity.
        """
        item = self.get_object()
        if item.status == LostAndFoundItem.Status.CLAIMED:
            return Response({'error': 'Item has already been claimed.'}, status=status.HTTP_400_BAD_REQUEST)

        verification_notes = request.data.get('verification_notes', '')
        if not verification_notes:
            return Response({'error': 'Identity and item ownership verification proof is required.'}, status=status.HTTP_400_BAD_REQUEST)

        from accounts.models import User
        guest_id = request.data.get('guest_id')
        claimed_guest = None
        if guest_id:
            try:
                claimed_guest = User.objects.get(id=guest_id)
            except User.DoesNotExist:
                return Response({'error': 'Guest account not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            claimed_guest = request.user

        item.status = LostAndFoundItem.Status.CLAIMED
        item.claimed_by_guest = claimed_guest
        item.claim_verification_notes = verification_notes
        item.handed_over_by = request.user
        item.claimed_at = timezone.now()
        item.save()

        return Response({
            'message': f'Item {item.reference_code} ({item.item_name}) successfully claimed and released.',
            'status': item.status
        })


class AIConciergeView(APIView):
    """
    Grounded AI Guest Concierge Engine for Elara Grand Hotel & Resort.
    Answers guest inquiries using verified live property data, menus, schedules, and policies.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        query = request.data.get('query', '').strip()
        if not query:
            return Response({'error': 'Query text is required.'}, status=status.HTTP_400_BAD_REQUEST)

        q_lower = query.lower()
        matched_intent = 'GENERAL_ASSISTANCE'
        response_parts = []
        suggestions = []

        # 1. Dining and Restaurants
        if any(w in q_lower for w in ['dine', 'dining', 'food', 'restaurant', 'eat', 'dinner', 'lunch', 'breakfast', 'menu']):
            matched_intent = 'DINING_INQUIRY'
            venues = DiningVenue.objects.filter(is_active=True)
            if venues.exists():
                venue_descriptions = [
                    f"• **{v.name}** ({v.cuisine_type}): Open {v.opening_time.strftime('%H:%M')} - {v.closing_time.strftime('%H:%M')}. Dress code: {v.dress_code}. {v.description}"
                    for v in venues
                ]
                response_parts.append("Here are our culinary destinations at Elara Grand:\n" + "\n".join(venue_descriptions))
            else:
                response_parts.append("Elara Grand features fine Indian royal cuisine, contemporary international dining, and 24/7 in-suite dining.")
            suggestions.extend(["Reserve a table for tonight", "View In-Suite Dining Menu", "Explore Spa treatments"])

        # 2. Spa and Ayurvedic Wellness
        elif any(w in q_lower for w in ['spa', 'massage', 'wellness', 'ayurved', 'treatment', 'relax', 'sauna', 'therapy']):
            matched_intent = 'SPA_INQUIRY'
            services = SpaService.objects.filter(is_active=True)
            if services.exists():
                service_list = [
                    f"• **{s.name}** ({s.duration_minutes} mins • ₹{s.price}): {s.description}"
                    for s in services[:4]
                ]
                response_parts.append("Our Jiva & Ayurvedic Wellness Haven offers rejuvenating royal treatments:\n" + "\n".join(service_list))
            else:
                response_parts.append("Our Spa offers signature Ayurvedic Abhyanga therapies, Swedish body massages, and steam wellness baths.")
            suggestions.extend(["Book a 60-min Deep Tissue Session", "Inquire about Couple Spa packages", "Check dining options"])

        # 3. Rooms and Accommodations
        elif any(w in q_lower for w in ['room', 'suite', 'stay', 'rates', 'price', 'tariff', 'villa', 'penthouse', 'bed']):
            matched_intent = 'ACCOMMODATION_INQUIRY'
            room_types = RoomType.objects.all()
            if room_types.exists():
                types_list = [
                    f"• **{rt.name}** (from ₹{rt.base_price_per_night}/night • up to {rt.max_occupancy} guests): {rt.description[:120]}..."
                    for rt in room_types[:4]
                ]
                response_parts.append("Elara Grand features bespoke luxury suites crafted for timeless comfort:\n" + "\n".join(types_list))
            else:
                response_parts.append("We offer Deluxe King Suites, Executive Business Suites, and Royal Presidential Penthouses.")
            suggestions.extend(["Book a luxury suite", "Check room availability for my dates", "Arrange airport transfer"])

        # 4. Check-in & Check-out Policies
        elif any(w in q_lower for w in ['checkin', 'check in', 'checkout', 'check out', 'timing', 'time', 'hours', 'arrival', 'departure']):
            matched_intent = 'CHECKIN_CHECKOUT_POLICY'
            response_parts.append(
                "**Standard Timings at Elara Grand Hotel & Resort:**\n"
                "• **Check-in:** 14:00 (2:00 PM) onwards.\n"
                "• **Check-out:** 11:00 (11:00 AM).\n"
                "• **Digital Pre-Arrival:** You can complete identity verification online via your Guest Sanctuary portal before arriving for instantaneous key pickup.\n"
                "• **Express Checkout:** Request paperless checkout with zero front-desk waiting directly from your dashboard."
            )
            suggestions.extend(["Complete Pre-Arrival Verification", "Request Express Checkout", "Book airport cab"])

        # 5. Airport Chauffeur & Portico Transport
        elif any(w in q_lower for w in ['car', 'cab', 'airport', 'transport', 'pickup', 'drop', 'driver', 'chauffeur', 'taxi', 'flight']):
            matched_intent = 'TRANSPORT_INQUIRY'
            response_parts.append(
                "**Luxury Chauffeur & Airport Transport:**\n"
                "Our Portico Fleet features BMW 7-Series, Mercedes-Benz V-Class, and Toyota Vellfire executive coaches.\n"
                "• Pune Airport Chauffeur: ₹3,500\n"
                "• Mumbai International Airport Transfer: ₹14,000\n"
                "• Dedicated Hourly Chauffeur Hire: ₹2,500/hr\n"
                "Our concierge tracks your incoming flight to ensure your chauffeur is waiting the moment you land."
            )
            suggestions.extend(["Book an airport pickup", "Request dedicated chauffeur", "Inquire about city tours"])

        # 6. Weddings & Grand Events
        elif any(w in q_lower for w in ['wedding', 'banquet', 'event', 'hall', 'ballroom', 'reception', 'conference', 'meeting', 'capacity']):
            matched_intent = 'EVENT_INQUIRY'
            venues = EventVenue.objects.filter(is_active=True)
            if venues.exists():
                v_list = [f"• **{v.name}** (Capacity: {v.max_capacity} guests • {v.area_sqft} sq.ft): Daily base rental ₹{v.base_daily_rental}" for v in venues]
                response_parts.append("Elara Grand features majestic celebration ballrooms and lush outdoor amphitheaters:\n" + "\n".join(v_list))
            else:
                response_parts.append("We host royal destination weddings, corporate summits, and cocktail soirees in our pillarless grand ballrooms.")
            suggestions.extend(["Check ballroom availability", "Inquire about catering packages", "Contact Event Specialist"])

        # 7. General Hospitality Assistance
        else:
            response_parts.append(
                "Welcome to Elara Grand Hotel & Resort. I am your AI Luxury Concierge.\n"
                "I can assist you with suite bookings, dining reservations at our award-winning restaurants, Ayurvedic spa appointments, airport limousine transfers, and resort activities.\n"
                "How may I make your stay sublime today?"
            )
            suggestions.extend(["Explore Luxury Suites", "Book a table for dining", "Spa treatments", "Airport transfer"])

        full_reply = "\n\n".join(response_parts)

        # Log query to database
        client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()

        AIConciergeQuery.objects.create(
            user=request.user if request.user.is_authenticated else None,
            ip_address=client_ip,
            query_text=query,
            response_text=full_reply,
            matched_intent=matched_intent
        )

        return Response({
            'query': query,
            'response': full_reply,
            'intent': matched_intent,
            'suggestions': suggestions
        })

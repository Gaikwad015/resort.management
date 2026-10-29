from rest_framework import serializers
from .models import HousekeepingTask, DiningVenue, TableReservation, SpaService, SpaBooking
from core.security.validators import sanitize_user_text

class HousekeepingTaskSerializer(serializers.ModelSerializer):
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    assigned_email = serializers.CharField(source='assigned_to.email', read_only=True, default="Unassigned")

    class Meta:
        model = HousekeepingTask
        fields = ('id', 'room', 'room_number', 'assigned_to', 'assigned_email', 'task_type', 'status', 'priority', 'notes', 'created_at', 'updated_at')

    def validate_notes(self, value):
        return sanitize_user_text(value)

class DiningVenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiningVenue
        fields = '__all__'

class TableReservationSerializer(serializers.ModelSerializer):
    venue_name = serializers.CharField(source='venue.name', read_only=True)

    class Meta:
        model = TableReservation
        fields = ('id', 'venue', 'venue_name', 'user', 'guest_name', 'guest_email', 'guest_phone', 'reservation_date', 'reservation_time', 'guests_count', 'special_requests', 'status', 'created_at')
        read_only_fields = ('id', 'user', 'status', 'created_at')

    def validate_special_requests(self, value):
        return sanitize_user_text(value)

class SpaServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaService
        fields = '__all__'

class SpaBookingSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    price = serializers.DecimalField(source='service.price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = SpaBooking
        fields = ('id', 'service', 'service_name', 'price', 'user', 'booking_date', 'booking_time', 'therapist_preference', 'special_requests', 'status', 'created_at')
        read_only_fields = ('id', 'user', 'status', 'created_at')

    def validate_special_requests(self, value):
        return sanitize_user_text(value)

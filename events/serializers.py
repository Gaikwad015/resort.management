from rest_framework import serializers
from .models import EventVenue, CateringPackage, EventBooking

class EventVenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventVenue
        fields = '__all__'

class CateringPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CateringPackage
        fields = '__all__'

class EventBookingSerializer(serializers.ModelSerializer):
    venue_name = serializers.CharField(source='venue.name', read_only=True)
    catering_name = serializers.CharField(source='catering_package.name', read_only=True)
    coordinator_name = serializers.CharField(source='assigned_coordinator.get_full_name', read_only=True)

    class Meta:
        model = EventBooking
        fields = '__all__'
        read_only_fields = ('booking_reference', 'venue_cost', 'catering_cost', 'total_amount', 'created_at', 'updated_at')

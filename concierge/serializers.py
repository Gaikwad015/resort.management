from rest_framework import serializers
from .models import Vehicle, Driver, TransportBooking, LostAndFoundItem, AIConciergeQuery

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = '__all__'

class TransportBookingSerializer(serializers.ModelSerializer):
    guest_name = serializers.CharField(source='guest.get_full_name', read_only=True)
    vehicle_name = serializers.CharField(source='vehicle.model_name', read_only=True)
    driver_name = serializers.CharField(source='driver.name', read_only=True)

    class Meta:
        model = TransportBooking
        fields = '__all__'
        read_only_fields = ('guest', 'created_at')

class LostAndFoundItemSerializer(serializers.ModelSerializer):
    found_by_name = serializers.CharField(source='found_by_staff.get_full_name', read_only=True)
    claimed_by_name = serializers.CharField(source='claimed_by_guest.get_full_name', read_only=True)
    handed_over_by_name = serializers.CharField(source='handed_over_by.get_full_name', read_only=True)

    class Meta:
        model = LostAndFoundItem
        fields = '__all__'
        read_only_fields = ('reference_code', 'created_at', 'claimed_at')

class AIConciergeQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConciergeQuery
        fields = '__all__'
        read_only_fields = ('timestamp',)

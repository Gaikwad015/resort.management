from rest_framework import serializers
from .models import RoomType, Room, RoomAmenity, RoomImage

class RoomAmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomAmenity
        fields = ('id', 'name', 'icon')

class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = ('id', 'image', 'is_primary', 'alt_text')

class RoomTypeSerializer(serializers.ModelSerializer):
    amenities = RoomAmenitySerializer(many=True, read_only=True)
    images = RoomImageSerializer(many=True, read_only=True)
    available_rooms_count = serializers.SerializerMethodField()

    class Meta:
        model = RoomType
        fields = (
            'id', 'name', 'slug', 'description', 'base_price_per_night',
            'max_adults', 'max_children', 'bed_type', 'room_size_sqm',
            'amenities', 'images', 'available_rooms_count'
        )

    def get_available_rooms_count(self, obj):
        return obj.rooms.filter(status='AVAILABLE', is_active=True).count()

class RoomSerializer(serializers.ModelSerializer):
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    price_per_night = serializers.DecimalField(source='room_type.base_price_per_night', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Room
        fields = ('id', 'room_number', 'room_type', 'room_type_name', 'floor', 'status', 'is_active', 'price_per_night')

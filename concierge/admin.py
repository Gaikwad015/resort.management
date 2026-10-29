from django.contrib import admin
from .models import Vehicle, Driver, TransportBooking, LostAndFoundItem, AIConciergeQuery

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'registration_number', 'passenger_capacity', 'hourly_rate', 'status')
    list_filter = ('status',)

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'license_number', 'status', 'rating')
    list_filter = ('status',)

@admin.register(TransportBooking)
class TransportBookingAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'guest', 'pickup_time', 'pickup_location', 'drop_location', 'vehicle', 'driver', 'fare_amount', 'status')
    list_filter = ('service_type', 'status', 'pickup_time')
    search_fields = ('guest__email', 'pickup_location', 'drop_location', 'flight_number')

@admin.register(LostAndFoundItem)
class LostAndFoundItemAdmin(admin.ModelAdmin):
    list_display = ('reference_code', 'item_name', 'category', 'found_date', 'found_location', 'storage_vault', 'status', 'claimed_by_guest')
    list_filter = ('category', 'status', 'found_date')
    search_fields = ('reference_code', 'item_name', 'found_location', 'description')

@admin.register(AIConciergeQuery)
class AIConciergeQueryAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'query_text', 'matched_intent')
    readonly_fields = [f.name for f in AIConciergeQuery._meta.fields]

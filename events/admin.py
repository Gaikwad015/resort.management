from django.contrib import admin
from .models import EventVenue, CateringPackage, EventBooking

@admin.register(EventVenue)
class EventVenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_capacity', 'area_sqft', 'is_outdoor', 'base_daily_rental', 'is_active')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(CateringPackage)
class CateringPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_per_guest', 'courses_count', 'is_active')

@admin.register(EventBooking)
class EventBookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'event_name', 'event_type', 'venue', 'client_name', 'start_time', 'end_time', 'guest_count', 'total_amount', 'status')
    list_filter = ('status', 'event_type', 'venue', 'start_time')
    search_fields = ('booking_reference', 'event_name', 'client_name', 'client_email')

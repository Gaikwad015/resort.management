from django.contrib import admin
from .models import HousekeepingTask, DiningVenue, TableReservation, SpaService, SpaBooking

@admin.register(HousekeepingTask)
class HousekeepingTaskAdmin(admin.ModelAdmin):
    list_display = ('room', 'task_type', 'priority', 'status', 'assigned_to', 'updated_at')
    list_filter = ('status', 'priority', 'task_type')
    search_fields = ('room__room_number', 'assigned_to__email')
    list_editable = ('status', 'priority')

@admin.register(DiningVenue)
class DiningVenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'cuisine', 'dress_code', 'opening_hours', 'is_active')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(TableReservation)
class TableReservationAdmin(admin.ModelAdmin):
    list_display = ('venue', 'guest_name', 'reservation_date', 'reservation_time', 'guests_count', 'status')
    list_filter = ('status', 'venue', 'reservation_date')
    search_fields = ('guest_name', 'guest_email', 'guest_phone')

@admin.register(SpaService)
class SpaServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'duration_minutes', 'price', 'is_active')
    list_filter = ('category', 'is_active')

@admin.register(SpaBooking)
class SpaBookingAdmin(admin.ModelAdmin):
    list_display = ('service', 'user', 'booking_date', 'booking_time', 'status')
    list_filter = ('status', 'booking_date')

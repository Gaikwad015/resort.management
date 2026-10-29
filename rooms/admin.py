from django.contrib import admin
from .models import RoomType, Room, RoomAmenity, RoomImage, RoomInspection, RoomAssignmentLog

@admin.register(RoomAmenity)
class RoomAmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)

@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price_per_night', 'max_adults', 'bed_type', 'room_size_sqm')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('amenities',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'room_type', 'floor', 'status', 'is_inspection_approved', 'inspected_by', 'is_active')
    list_filter = ('status', 'floor', 'room_type', 'is_inspection_approved', 'is_active')
    search_fields = ('room_number',)
    list_editable = ('status', 'is_active')

@admin.register(RoomImage)
class RoomImageAdmin(admin.ModelAdmin):
    list_display = ('room_type', 'is_primary', 'alt_text')

@admin.register(RoomInspection)
class RoomInspectionAdmin(admin.ModelAdmin):
    list_display = ('room', 'inspector', 'cleanliness_score', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'cleanliness_score')

@admin.register(RoomAssignmentLog)
class RoomAssignmentLogAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'old_room', 'new_room', 'reason', 'assigned_by', 'timestamp')
    readonly_fields = [f.name for f in RoomAssignmentLog._meta.fields]

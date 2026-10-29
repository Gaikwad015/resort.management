from django.db import models
from django.conf import settings
import uuid

class RoomAmenity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome or similar icon class")

    def __str__(self):
        return self.name

class RoomType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    base_price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    max_adults = models.PositiveIntegerField(default=2)
    max_children = models.PositiveIntegerField(default=1)
    bed_type = models.CharField(max_length=100)
    room_size_sqm = models.PositiveIntegerField()
    amenities = models.ManyToManyField(RoomAmenity, blank=True)
    
    def __str__(self):
        return self.name

class Room(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        RESERVED = 'RESERVED', 'Reserved'
        OCCUPIED = 'OCCUPIED', 'Occupied'
        CLEANING = 'CLEANING', 'Cleaning in Progress'
        MAINTENANCE = 'MAINTENANCE', 'Out of Order / Maintenance'
        OUT_OF_SERVICE = 'OUT_OF_SERVICE', 'Out of Service'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_number = models.CharField(max_length=20, unique=True, db_index=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='rooms')
    floor = models.CharField(max_length=20, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True
    )
    is_active = models.BooleanField(default=True)
    
    # Inspection and Supervisor Approval Workflow
    last_cleaned_at = models.DateTimeField(null=True, blank=True)
    last_inspected_at = models.DateTimeField(null=True, blank=True)
    inspected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='inspected_rooms')
    is_inspection_approved = models.BooleanField(default=True)
    maintenance_reason = models.TextField(blank=True)
    
    def approve_inspection(self, supervisor):
        self.is_inspection_approved = True
        self.inspected_by = supervisor
        self.status = self.Status.AVAILABLE
        self.save()

    def __str__(self):
        return f"{self.room_number} - {self.room_type.name} [{self.status}]"

class RoomImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='rooms/')
    is_primary = models.BooleanField(default=False)
    alt_text = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Image for {self.room_type.name}"


class RoomInspection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='inspections')
    inspector = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    cleanliness_score = models.PositiveSmallIntegerField(default=5) # 1 to 5
    linens_pass = models.BooleanField(default=True)
    bathroom_pass = models.BooleanField(default=True)
    minibar_pass = models.BooleanField(default=True)
    electronics_pass = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inspection for Room {self.room.room_number} by {self.inspector.email} ({'APPROVED' if self.is_approved else 'REJECTED'})"


class RoomAssignmentLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_id = models.CharField(max_length=100)
    old_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='relocated_from_logs')
    new_room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='assigned_to_logs')
    reason = models.CharField(max_length=200, default='Guest Request')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.booking_id}: Room {self.old_room.room_number if self.old_room else 'None'} -> {self.new_room.room_number}"

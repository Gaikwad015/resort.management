from django.db import models
from django.conf import settings
from rooms.models import Room
import uuid

# ==================================================
# 1. Housekeeping Module
# ==================================================
class HousekeepingTask(models.Model):
    class TaskType(models.TextChoices):
        DAILY_CLEANING = 'DAILY_CLEANING', 'Daily Cleaning'
        CHECKOUT_CLEANING = 'CHECKOUT_CLEANING', 'Checkout Turnover'
        DEEP_CLEANING = 'DEEP_CLEANING', 'Deep Sanitation'
        INSPECTION = 'INSPECTION', 'Manager Inspection'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        VERIFIED = 'VERIFIED', 'Verified / Inspected'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent / VIP Arrival'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='housekeeping_tasks')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_housekeeping'
    )
    task_type = models.CharField(max_length=30, choices=TaskType.choices, default=TaskType.DAILY_CLEANING)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM, db_index=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def complete_task(self):
        self.status = self.Status.COMPLETED
        self.save()
        # Automatically update Room status to AVAILABLE if room was CLEANING
        if self.room.status == Room.Status.CLEANING:
            self.room.status = Room.Status.AVAILABLE
            self.room.save()

    def __str__(self):
        return f"Room {self.room.room_number} - {self.get_task_type_display()} [{self.status}]"


# ==================================================
# 2. Fine Dining & Restaurant Module
# ==================================================
class DiningVenue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    cuisine = models.CharField(max_length=100)
    description = models.TextField()
    opening_hours = models.CharField(max_length=100)
    dress_code = models.CharField(max_length=50, default='Smart Casual')
    image_url = models.URLField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class TableReservation(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        SEATED = 'SEATED', 'Seated'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(DiningVenue, on_delete=models.CASCADE, related_name='reservations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='table_reservations')
    guest_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=20)
    
    reservation_date = models.DateField(db_index=True)
    reservation_time = models.CharField(max_length=20)
    guests_count = models.PositiveIntegerField(default=2)
    special_requests = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.venue.name} - {self.guest_name} ({self.reservation_date} {self.reservation_time})"


# ==================================================
# 3. Luxury Spa & Wellness Module
# ==================================================
class SpaService(models.Model):
    class Category(models.TextChoices):
        AYURVEDA = 'AYURVEDA', 'Ancient Ayurveda'
        MASSAGE = 'MASSAGE', 'Holistic Massages'
        FACIAL = 'FACIAL', 'Radiance Facials'
        HYDROTHERAPY = 'HYDROTHERAPY', 'Hydrotherapy & Scrub'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.MASSAGE)
    duration_minutes = models.PositiveIntegerField(default=60)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.duration_minutes}m - ₹{self.price})"

class SpaBooking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(SpaService, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='spa_bookings')
    
    booking_date = models.DateField(db_index=True)
    booking_time = models.CharField(max_length=20)
    therapist_preference = models.CharField(max_length=20, default='NO_PREFERENCE')
    special_requests = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service.name} - {self.user.email} [{self.booking_date}]"

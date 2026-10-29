from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from decimal import Decimal
import uuid

class EventVenue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(unique=True)
    max_capacity = models.PositiveIntegerField()
    area_sqft = models.PositiveIntegerField()
    is_outdoor = models.BooleanField(default=False)
    base_daily_rental = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('150000.00'))
    description = models.TextField()
    amenities = models.TextField(blank=True, help_text="e.g. Belgian Chandeliers, Bridal Suite, Pre-function foyer")
    image_url = models.URLField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (Cap: {self.max_capacity} guests • {self.area_sqft} sq.ft)"


class CateringPackage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    price_per_guest = models.DecimalField(max_digits=10, decimal_places=2)
    courses_count = models.PositiveIntegerField(default=5)
    menu_highlights = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (₹{self.price_per_guest}/plate)"


class EventBooking(models.Model):
    class EventType(models.TextChoices):
        WEDDING = 'WEDDING', 'Royal Destination Wedding'
        RECEPTION = 'RECEPTION', 'Grand Wedding Reception'
        CORPORATE = 'CORPORATE', 'Corporate Gala / Summit'
        COCKTAIL = 'COCKTAIL', 'Sangeet & Cocktail Soiree'
        CONFERENCE = 'CONFERENCE', 'International Conference'

    class Status(models.TextChoices):
        INQUIRY = 'INQUIRY', 'Inquiry / Proposal Sent'
        CONFIRMED = 'CONFIRMED', 'Confirmed & Advance Secured'
        IN_PROGRESS = 'IN_PROGRESS', 'Event Live / In Progress'
        COMPLETED = 'COMPLETED', 'Event Concluded & Reconciled'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_reference = models.CharField(max_length=50, unique=True, db_index=True)
    event_name = models.CharField(max_length=200)
    event_type = models.CharField(max_length=30, choices=EventType.choices, default=EventType.WEDDING)
    
    venue = models.ForeignKey(EventVenue, on_delete=models.PROTECT, related_name='event_bookings')
    catering_package = models.ForeignKey(CateringPackage, on_delete=models.SET_NULL, null=True, blank=True)
    
    client_name = models.CharField(max_length=150)
    client_email = models.EmailField()
    client_phone = models.CharField(max_length=25)
    
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField(db_index=True)
    guest_count = models.PositiveIntegerField()
    
    venue_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    catering_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    advance_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INQUIRY, db_index=True)
    assigned_coordinator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='coordinated_events')
    special_requirements = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError("Event end time must be strictly after event start time.")
            
            # Concurrency & Venue Overlap Prevention: check for conflicting confirmed events
            overlapping = EventBooking.objects.filter(
                venue=self.venue,
                status__in=[self.Status.CONFIRMED, self.Status.IN_PROGRESS]
            ).filter(
                Q(start_time__lt=self.end_time) & Q(end_time__gt=self.start_time)
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                raise ValidationError(f"Venue {self.venue.name} is already booked for an overlapping event during these hours.")

    def calculate_costs(self):
        self.venue_cost = self.venue.base_daily_rental
        if self.catering_package and self.guest_count:
            self.catering_cost = self.catering_package.price_per_guest * self.guest_count
        self.total_amount = self.venue_cost + self.catering_cost

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = f"EVT-{uuid.uuid4().hex[:7].upper()}"
        if not self.total_amount or self.total_amount == 0:
            self.calculate_costs()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_reference}: {self.event_name} @ {self.venue.name} [{self.status}]"

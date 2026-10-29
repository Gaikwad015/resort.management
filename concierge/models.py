from django.db import models
from django.conf import settings
from decimal import Decimal
from bookings.models import Booking
import uuid

class Vehicle(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available at Portico'
        ON_TRIP = 'ON_TRIP', 'On Chauffeur Trip'
        MAINTENANCE = 'MAINTENANCE', 'Service & Maintenance'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration_number = models.CharField(max_length=50, unique=True)
    model_name = models.CharField(max_length=100) # e.g. BMW 730Ld, Mercedes-Benz V-Class, Toyota Vellfire
    passenger_capacity = models.PositiveIntegerField(default=4)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('2500.00'))

    def __str__(self):
        return f"{self.model_name} [{self.registration_number}] ({self.status})"


class Driver(models.Model):
    class Status(models.TextChoices):
        ON_DUTY = 'ON_DUTY', 'On Duty & Ready'
        ON_TRIP = 'ON_TRIP', 'Driving Active Trip'
        OFF_DUTY = 'OFF_DUTY', 'Off Duty'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=25)
    license_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ON_DUTY)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=Decimal('4.9'))

    def __str__(self):
        return f"{self.name} ({self.status}) - ★{self.rating}"


class TransportBooking(models.Model):
    class ServiceType(models.TextChoices):
        AIRPORT_PICKUP = 'AIRPORT_PICKUP', 'Airport Luxury Pickup (Pune / Mumbai)'
        AIRPORT_DROP = 'AIRPORT_DROP', 'Airport Luxury Drop-off'
        CITY_TOUR = 'CITY_TOUR', 'Pune Heritage & City Tour'
        HOURLY_CHAUFFEUR = 'HOURLY_CHAUFFEUR', 'Dedicated Chauffeur on Hire'

    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', 'Requested by Guest'
        ASSIGNED = 'ASSIGNED', 'Vehicle & Driver Assigned'
        IN_TRANSIT = 'IN_TRANSIT', 'Trip in Progress'
        COMPLETED = 'COMPLETED', 'Trip Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='transports')
    guest = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transport_requests')
    
    service_type = models.CharField(max_length=30, choices=ServiceType.choices)
    pickup_time = models.DateTimeField()
    pickup_location = models.CharField(max_length=255)
    drop_location = models.CharField(max_length=255)
    flight_number = models.CharField(max_length=50, blank=True)
    passenger_count = models.PositiveIntegerField(default=1)
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    
    fare_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('3500.00'))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    special_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_type} - {self.guest.email} [{self.pickup_time.strftime('%Y-%m-%d %H:%M')}]"


# ==================================================
# Lost and Found Management Module (OWASP & PCI Safe)
# ==================================================
class LostAndFoundItem(models.Model):
    class Category(models.TextChoices):
        ELECTRONICS = 'ELECTRONICS', 'Mobile Phone / Laptop / Watch'
        JEWELRY = 'JEWELRY', 'Fine Jewelry & Precious Ornaments'
        WALLET_DOCS = 'WALLET_DOCS', 'Wallets, Passports & ID Documents'
        CLOTHING = 'CLOTHING', 'Designer Apparel & Accessories'
        LUGGAGE = 'LUGGAGE', 'Luggage & Travel Bags'
        OTHER = 'OTHER', 'Other Valuables'

    class Status(models.TextChoices):
        STORED = 'STORED', 'Stored Securely in Vault'
        CLAIMED = 'CLAIMED', 'Verified & Returned to Owner'
        UNCLAIMED_DISPOSED = 'UNCLAIMED_DISPOSED', 'Unclaimed after 90 Days'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_code = models.CharField(max_length=50, unique=True, db_index=True)
    item_name = models.CharField(max_length=150)
    category = models.CharField(max_length=25, choices=Category.choices)
    description = models.TextField()
    found_date = models.DateField()
    found_location = models.CharField(max_length=150, help_text="e.g. Room 401 bathroom vanity, Poolside Cabana 4")
    
    found_by_staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='found_items')
    storage_vault = models.CharField(max_length=100, default='Central Hotel Safe A - Locker #14')
    
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.STORED)
    
    claimed_by_guest = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='claimed_items')
    claim_verification_notes = models.TextField(blank=True, help_text="Verification proof, serial numbers checked before handover")
    handed_over_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='released_items')
    claimed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.reference_code:
            self.reference_code = f"LNF-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference_code} - {self.item_name} [{self.status}]"


# ==================================================
# AI Concierge Query & Audit
# ==================================================
class AIConciergeQuery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    query_text = models.TextField()
    response_text = models.TextField()
    matched_intent = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AI Query [{self.timestamp.strftime('%H:%M:%S')}]: {self.query_text[:40]}"

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from rooms.models import Room
from decimal import Decimal
import uuid

class Booking(models.Model):
    """
    OWASP A06:2025 - Insecure Design & State Machine Protection
    OWASP A01:2025 - Broken Access Control
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CHECKED_IN = 'CHECKED_IN', 'Checked In'
        CHECKED_OUT = 'CHECKED_OUT', 'Checked Out'
        CANCELLED = 'CANCELLED', 'Cancelled'

    # Valid state transitions matrix (State Machine Defense)
    ALLOWED_TRANSITIONS = {
        Status.PENDING: [Status.CONFIRMED, Status.CANCELLED],
        Status.CONFIRMED: [Status.CHECKED_IN, Status.CANCELLED],
        Status.CHECKED_IN: [Status.CHECKED_OUT],
        Status.CHECKED_OUT: [], # Terminal state
        Status.CANCELLED: [],   # Terminal state
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='bookings')
    
    check_in_date = models.DateField(db_index=True)
    check_out_date = models.DateField(db_index=True)
    
    num_adults = models.PositiveIntegerField(default=1)
    num_children = models.PositiveIntegerField(default=0)
    
    special_requests = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    
    # Pricing (Server-side strictly enforced)
    room_price_total = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total price for the room stay")
    tax_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    additional_charges_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    final_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Express Checkout & Approval
    is_express_checkout_requested = models.BooleanField(default=False)
    checkout_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_checkouts')
    checkout_approved_at = models.DateTimeField(null=True, blank=True)
    
    # Concurrency & Idempotency Key (A06:2025)
    idempotency_key = models.CharField(max_length=100, blank=True, null=True, unique=True, db_index=True)

    # Audit timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def can_transition_to(self, target_status: str) -> bool:
        """Enforces strict state machine transitions to prevent business logic bypasses."""
        if self.status == target_status:
            return True
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, [])
        return target_status in allowed

    def recalculate_total_balance(self):
        charges_sum = self.additional_charges.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        self.additional_charges_total = charges_sum
        self.final_amount = self.room_price_total + self.tax_total + charges_sum
        self.save(update_fields=['additional_charges_total', 'final_amount'])

    def clean(self):
        super().clean()
        if self.check_in_date and self.check_out_date:
            if self.check_out_date <= self.check_in_date:
                raise ValidationError("Check-out date must be strictly after check-in date.")

    def __str__(self):
        return f"{self.id} - {self.user.email} - {self.status}"


class Payment(models.Model):
    """
    OWASP A08:2025 - Data Integrity & Webhook verification
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True, null=True, unique=True, db_index=True)
    payment_method = models.CharField(max_length=50, default='CREDIT_CARD')
    
    # Masked card metadata for PCI compliance (A04:2025)
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.transaction_id} - {self.amount} - {self.status}"


class AdditionalCharge(models.Model):
    class ChargeType(models.TextChoices):
        ROOM_SERVICE_DINING = 'DINING', 'In-Room Fine Dining'
        MINIBAR = 'MINIBAR', 'Minibar Consumption'
        SPA = 'SPA', 'Spa Treatment Charges'
        LAUNDRY = 'LAUNDRY', 'Express Laundry & Dry Cleaning'
        TRANSPORT = 'TRANSPORT', 'Airport / Chauffeur Transfer'
        LATE_CHECKOUT = 'LATE_CHECKOUT', 'Late Checkout Fee'
        DAMAGE = 'DAMAGE', 'Property Damage Recovery'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='additional_charges')
    charge_type = models.CharField(max_length=25, choices=ChargeType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Automatically update parent booking additional charges total
        self.booking.recalculate_total_balance()

    def __str__(self):
        return f"{self.get_charge_type_display()}: ₹{self.amount} for #{str(self.booking.id)[:8]}"


class RefundRecord(models.Model):
    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', 'Refund Requested'
        APPROVED = 'APPROVED', 'Approved by Financial Controller'
        REJECTED = 'REJECTED', 'Refund Denied'
        PROCESSED = 'PROCESSED', 'Processed & Settled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name='refunds')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='requested_refunds')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_refunds')
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED, db_index=True)
    gateway_refund_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Refund ₹{self.amount} for Txn {self.payment.transaction_id} [{self.status}]"


class GuestPreArrival(models.Model):
    class IdType(models.TextChoices):
        PASSPORT = 'PASSPORT', 'Passport'
        AADHAAR = 'AADHAAR', 'Aadhaar Card'
        DRIVING_LICENSE = 'DRIVING_LICENSE', 'Driving License'
        VOTER_ID = 'VOTER_ID', 'Voter Identity Card'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='pre_arrival')
    expected_arrival_time = models.TimeField(default='15:00')
    id_document_type = models.CharField(max_length=25, choices=IdType.choices, default=IdType.PASSPORT)
    id_document_number = models.CharField(max_length=50)
    
    flight_or_train_number = models.CharField(max_length=50, blank=True)
    dietary_preferences = models.CharField(max_length=150, blank=True)
    special_occasion = models.CharField(max_length=100, blank=True)
    
    terms_accepted = models.BooleanField(default=True)
    id_verified = models.BooleanField(default=False)
    verified_by_staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pre-arrival for #{str(self.booking.id)[:8]} (ID Verified: {self.id_verified})"

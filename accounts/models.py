from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid

class Role(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN', _('Super Admin')
    ADMIN = 'ADMIN', _('Admin')
    HOTEL_MANAGER = 'HOTEL_MANAGER', _('Hotel Manager')
    RECEPTIONIST = 'RECEPTIONIST', _('Receptionist')
    HOUSEKEEPING = 'HOUSEKEEPING', _('Housekeeping')
    RESTAURANT_MANAGER = 'RESTAURANT_MANAGER', _('Restaurant Manager')
    SPA_MANAGER = 'SPA_MANAGER', _('Spa Manager')
    ACCOUNTANT = 'ACCOUNTANT', _('Accountant')
    INVENTORY_MANAGER = 'INVENTORY_MANAGER', _('Inventory Manager')
    EVENT_MANAGER = 'EVENT_MANAGER', _('Event Manager')
    CUSTOMER = 'CUSTOMER', _('Customer')

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.CUSTOMER
    )
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    date_of_birth = models.DateField(null=True, blank=True)
    anniversary_date = models.DateField(null=True, blank=True)
    
    # We enforce email as the unique identifier for auth
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def is_hotel_staff(self) -> bool:
        staff_roles = [
            Role.SUPER_ADMIN, Role.ADMIN, Role.HOTEL_MANAGER,
            Role.RECEPTIONIST, Role.HOUSEKEEPING, Role.RESTAURANT_MANAGER,
            Role.SPA_MANAGER, Role.ACCOUNTANT, Role.INVENTORY_MANAGER, Role.EVENT_MANAGER
        ]
        return self.role in staff_roles or self.is_superuser or self.is_staff

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"


# ==================================================
# Guest CRM & Loyalty Program Models
# ==================================================

class LoyaltyAccount(models.Model):
    class Tier(models.TextChoices):
        SILVER = 'SILVER', 'Silver Sanctuary'
        GOLD = 'GOLD', 'Gold Elite'
        PLATINUM = 'PLATINUM', 'Platinum Royal'
        DIAMOND = 'DIAMOND', 'Diamond Presidential'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty_account')
    tier = models.CharField(max_length=20, choices=Tier.choices, default=Tier.SILVER)
    points_balance = models.PositiveIntegerField(default=0)
    lifetime_points = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_tier(self):
        if self.lifetime_points >= 50000:
            self.tier = self.Tier.DIAMOND
        elif self.lifetime_points >= 20000:
            self.tier = self.Tier.PLATINUM
        elif self.lifetime_points >= 5000:
            self.tier = self.Tier.GOLD
        else:
            self.tier = self.Tier.SILVER
        self.save()

    def earn_points(self, points: int, description: str, reference_booking_id: str = ""):
        if points <= 0:
            return
        self.points_balance += points
        self.lifetime_points += points
        self.save()
        self.update_tier()
        LoyaltyTransaction.objects.create(
            loyalty_account=self,
            transaction_type=LoyaltyTransaction.TransactionType.EARNED,
            points=points,
            description=description,
            reference_booking_id=reference_booking_id
        )

    def redeem_points(self, points: int, description: str) -> bool:
        if points <= 0:
            raise ValidationError("Redemption points must be greater than zero.")
        if self.points_balance < points:
            raise ValidationError(f"Insufficient points. Available: {self.points_balance}, Requested: {points}")
        
        self.points_balance -= points
        self.save()
        LoyaltyTransaction.objects.create(
            loyalty_account=self,
            transaction_type=LoyaltyTransaction.TransactionType.REDEEMED,
            points=points,
            description=description
        )
        return True

    def __str__(self):
        return f"{self.user.email} - {self.tier} ({self.points_balance} pts)"


class LoyaltyTransaction(models.Model):
    class TransactionType(models.TextChoices):
        EARNED = 'EARNED', 'Points Earned'
        REDEEMED = 'REDEEMED', 'Points Redeemed'
        ADJUSTMENT = 'ADJUSTMENT', 'Management Adjustment'
        EXPIRED = 'EXPIRED', 'Points Expired'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loyalty_account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    points = models.PositiveIntegerField()
    description = models.CharField(max_length=255)
    reference_booking_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.transaction_type}] {self.points} pts - {self.description}"


class GuestPreference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    bed_preference = models.CharField(max_length=50, default='King Bed')
    floor_preference = models.CharField(max_length=50, default='High Floor')
    dietary_preference = models.CharField(max_length=100, default='No Restrictions', blank=True)
    quiet_room = models.BooleanField(default=True)
    pillow_type = models.CharField(max_length=50, default='Goose Down Feather')
    newspaper_choice = models.CharField(max_length=50, default='The Financial Express / Times of India')
    special_notes = models.TextField(blank=True)
    
    # GDPR & Consent Tracking
    consent_email = models.BooleanField(default=True)
    consent_sms = models.BooleanField(default=True)
    consent_whatsapp = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences: {self.user.email}"


class GuestFeedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    booking_reference = models.CharField(max_length=100, blank=True)
    
    overall_rating = models.PositiveSmallIntegerField(default=5) # 1 to 5
    room_comfort_rating = models.PositiveSmallIntegerField(default=5)
    dining_rating = models.PositiveSmallIntegerField(default=5)
    staff_courtesy_rating = models.PositiveSmallIntegerField(default=5)
    
    comments = models.TextField()
    is_reviewed = models.BooleanField(default=False)
    manager_response = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback ({self.overall_rating}★) - {self.user.email}"

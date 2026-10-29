from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid

# ==================================================
# Energy & Sustainability Monitoring
# ==================================================
class UtilityMeter(models.Model):
    class UtilityType(models.TextChoices):
        ELECTRICITY = 'ELECTRICITY', 'Electricity (kWh)'
        WATER = 'WATER', 'Potable Water (kL / Liters)'
        NATURAL_GAS = 'NATURAL_GAS', 'LPG / Natural Gas (SCM)'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meter_code = models.CharField(max_length=50, unique=True)
    utility_type = models.CharField(max_length=20, choices=UtilityType.choices)
    building_wing = models.CharField(max_length=100, default='Main Luxury Tower')
    floor_or_zone = models.CharField(max_length=100, default='All Floors / Central')
    daily_alert_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('2500.00'))
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.meter_code} ({self.get_utility_type_display()}) - {self.building_wing}"


class EnergyConsumptionRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meter = models.ForeignKey(UtilityMeter, on_delete=models.CASCADE, related_name='readings')
    reading_date = models.DateField(db_index=True)
    units_consumed = models.DecimalField(max_digits=12, decimal_places=2)
    cost_per_unit = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('12.50'))
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    notes = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_cost = (self.units_consumed * self.cost_per_unit).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.meter.meter_code} - {self.reading_date}: {self.units_consumed} units (₹{self.total_cost})"


# ==================================================
# Operating Expenses & Financial Snapshots
# ==================================================
class DailyOperatingExpense(models.Model):
    class Category(models.TextChoices):
        PAYROLL = 'PAYROLL', 'Staff Wages & Payroll'
        FNB_INVENTORY = 'FNB_INVENTORY', 'F&B Raw Materials'
        UTILITIES = 'UTILITIES', 'Electricity & Water'
        MAINTENANCE = 'MAINTENANCE', 'Engineering Repairs'
        MARKETING = 'MARKETING', 'PR & Digital Luxury Ads'
        GUEST_AMENITIES = 'GUEST_AMENITIES', 'Toiletries & Florals'
        ADMIN = 'ADMIN', 'Administrative & Software'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    expense_date = models.DateField(db_index=True)
    category = models.CharField(max_length=30, choices=Category.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    invoice_number = models.CharField(max_length=100, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.expense_date} [{self.category}]: ₹{self.amount}"


class RevenueForecastSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snapshot_date = models.DateField(db_index=True)
    forecast_days = models.PositiveSmallIntegerField(default=7) # 7 or 30 days
    projected_revenue = models.DecimalField(max_digits=14, decimal_places=2)
    projected_occupancy_pct = models.DecimalField(max_digits=5, decimal_places=1)
    projected_adr = models.DecimalField(max_digits=10, decimal_places=2)
    projected_revpar = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Forecast {self.forecast_days}d ({self.snapshot_date}): ₹{self.projected_revenue} @ {self.projected_occupancy_pct}%"

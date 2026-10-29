from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid

class InventoryCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Inventory Categories'

    def __str__(self):
        return self.name


class Supplier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=25)
    address = models.TextField()
    gst_tax_number = models.CharField(max_length=50, blank=True)
    payment_terms = models.CharField(max_length=100, default='Net 30 Days')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company_name} ({self.contact_person})"


class InventoryItem(models.Model):
    class Unit(models.TextChoices):
        PIECE = 'PCS', 'Pieces'
        KG = 'KG', 'Kilograms'
        LITER = 'LTR', 'Liters'
        BOTTLE = 'BTL', 'Bottles'
        BOX = 'BOX', 'Boxes / Cartons'
        PACKET = 'PKT', 'Packets'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(InventoryCategory, on_delete=models.PROTECT, related_name='items')
    name = models.CharField(max_length=150)
    sku = models.CharField(max_length=50, unique=True, db_index=True)
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.PIECE)
    
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    minimum_stock_alert = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('10.00'))
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    preferred_supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    location_bin = models.CharField(max_length=50, default='Central Storehouse A')
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_low_stock(self) -> bool:
        return self.current_stock <= self.minimum_stock_alert

    @property
    def total_valuation(self) -> Decimal:
        return (self.current_stock * self.unit_cost).quantize(Decimal('0.01'))

    def record_stock_movement(self, qty: Decimal, tx_type: str, user, reference: str = "", cost: Decimal = None):
        """
        Guarantees transactional consistency and prevents negative inventory.
        """
        if qty <= Decimal('0.00'):
            raise ValidationError("Transaction quantity must be strictly positive.")

        unit_cost_applied = cost if cost is not None else self.unit_cost

        if tx_type in ['PURCHASE_IN', 'RETURN_IN', 'ADJUSTMENT_ADD']:
            self.current_stock += qty
        elif tx_type in ['USAGE_OUT', 'RESTAURANT_OUT', 'WASTAGE_OUT', 'ADJUSTMENT_SUB']:
            if self.current_stock < qty:
                raise ValidationError(f"Insufficient stock for {self.name}. In stock: {self.current_stock}, Requested: {qty}")
            self.current_stock -= qty
        else:
            raise ValidationError(f"Unknown inventory transaction type: {tx_type}")

        self.save()

        StockTransaction.objects.create(
            item=self,
            transaction_type=tx_type,
            quantity=qty,
            unit_cost=unit_cost_applied,
            total_value=qty * unit_cost_applied,
            reference_number=reference,
            performed_by=user
        )

    def __str__(self):
        return f"{self.name} [{self.sku}] - {self.current_stock} {self.unit}"


class StockTransaction(models.Model):
    class TxType(models.TextChoices):
        PURCHASE_IN = 'PURCHASE_IN', 'Purchase Received'
        USAGE_OUT = 'USAGE_OUT', 'Internal Department Usage'
        RESTAURANT_OUT = 'RESTAURANT_OUT', 'Culinary F&B Usage'
        WASTAGE_OUT = 'WASTAGE_OUT', 'Damaged / Expired Wastage'
        RETURN_IN = 'RETURN_IN', 'Returned to Stock'
        ADJUSTMENT_ADD = 'ADJUSTMENT_ADD', 'Audit Stock Addition'
        ADJUSTMENT_SUB = 'ADJUSTMENT_SUB', 'Audit Stock Subtraction'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='stock_transactions')
    transaction_type = models.CharField(max_length=25, choices=TxType.choices, db_index=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_value = models.DecimalField(max_digits=12, decimal_places=2)
    reference_number = models.CharField(max_length=100, blank=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.transaction_type}: {self.quantity} {self.item.unit} of {self.item.name}"


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft PO'
        SUBMITTED = 'SUBMITTED', 'Submitted for Approval'
        APPROVED = 'APPROVED', 'Approved by Financial Controller'
        RECEIVED = 'RECEIVED', 'Goods Fully Received'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    po_number = models.CharField(max_length=50, unique=True, db_index=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_pos')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_pos')
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    received_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"PO #{self.po_number} - {self.supplier.company_name} [{self.status}]"


class PurchaseOrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT)
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def line_total(self) -> Decimal:
        return (self.quantity_ordered * self.unit_cost).quantize(Decimal('0.01'))


class WastageRecord(models.Model):
    class Reason(models.TextChoices):
        EXPIRED = 'EXPIRED', 'Shelf-Life Expired'
        SPOILED = 'SPOILED', 'Perishable Spoilage'
        DAMAGED = 'DAMAGED', 'Physical Breakage / Damage'
        CONTAMINATED = 'CONTAMINATED', 'Contamination'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='wastages')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=20, choices=Reason.choices)
    cost_loss = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wastage: {self.quantity} {self.item.unit} of {self.item.name} ({self.reason})"

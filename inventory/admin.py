from django.contrib import admin
from .models import InventoryCategory, Supplier, InventoryItem, StockTransaction, PurchaseOrder, PurchaseOrderItem, WastageRecord

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1

@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_person', 'phone', 'email', 'payment_terms', 'is_active')
    search_fields = ('company_name', 'contact_person', 'gst_tax_number')

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'current_stock', 'unit', 'minimum_stock_alert', 'unit_cost', 'total_valuation', 'is_low_stock')
    list_filter = ('category', 'unit', 'is_active')
    search_fields = ('name', 'sku')

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('item', 'transaction_type', 'quantity', 'unit_cost', 'total_value', 'reference_number', 'performed_by', 'timestamp')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('item__name', 'reference_number')
    readonly_fields = [f.name for f in StockTransaction._meta.fields]

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'supplier', 'status', 'total_amount', 'created_by', 'approved_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('po_number', 'supplier__company_name')
    inlines = [PurchaseOrderItemInline]

@admin.register(WastageRecord)
class WastageRecordAdmin(admin.ModelAdmin):
    list_display = ('item', 'quantity', 'reason', 'cost_loss', 'recorded_by', 'created_at')
    list_filter = ('reason', 'created_at')

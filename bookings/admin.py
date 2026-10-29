from django.contrib import admin
from .models import Booking, Payment, AdditionalCharge, RefundRecord, GuestPreArrival

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('transaction_id', 'amount', 'payment_method', 'card_last4', 'status', 'created_at')

class AdditionalChargeInline(admin.TabularInline):
    model = AdditionalCharge
    extra = 0

class PreArrivalInline(admin.StackedInline):
    model = GuestPreArrival
    extra = 0

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'room', 'check_in_date', 'check_out_date', 'status', 'final_amount', 'is_express_checkout_requested', 'created_at')
    list_filter = ('status', 'is_express_checkout_requested', 'check_in_date', 'check_out_date')
    search_fields = ('id', 'user__email', 'room__room_number')
    readonly_fields = ('room_price_total', 'tax_total', 'additional_charges_total', 'final_amount', 'created_at', 'updated_at')
    inlines = [PaymentInline, AdditionalChargeInline, PreArrivalInline]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'booking', 'amount', 'payment_method', 'card_last4', 'status', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('transaction_id', 'booking__id')

@admin.register(AdditionalCharge)
class AdditionalChargeAdmin(admin.ModelAdmin):
    list_display = ('booking', 'charge_type', 'amount', 'description', 'posted_by', 'timestamp')
    list_filter = ('charge_type', 'timestamp')
    search_fields = ('booking__id', 'description')

@admin.register(RefundRecord)
class RefundRecordAdmin(admin.ModelAdmin):
    list_display = ('payment', 'amount', 'status', 'requested_by', 'approved_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('payment__transaction_id', 'reason')

@admin.register(GuestPreArrival)
class GuestPreArrivalAdmin(admin.ModelAdmin):
    list_display = ('booking', 'expected_arrival_time', 'id_document_type', 'id_verified', 'verified_by_staff', 'submitted_at')
    list_filter = ('id_verified', 'id_document_type')

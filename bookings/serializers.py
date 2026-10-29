from rest_framework import serializers
from datetime import date
from .models import Booking, Payment, AdditionalCharge, RefundRecord, GuestPreArrival
from core.security.validators import sanitize_user_text

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ('id', 'booking', 'amount', 'transaction_id', 'payment_method', 'card_last4', 'status', 'created_at')
        read_only_fields = ('transaction_id', 'status', 'created_at')

class AdditionalChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdditionalCharge
        fields = ('id', 'booking', 'charge_type', 'amount', 'description', 'posted_by', 'timestamp')
        read_only_fields = ('id', 'posted_by', 'timestamp')

class RefundRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundRecord
        fields = ('id', 'payment', 'amount', 'reason', 'requested_by', 'approved_by', 'status', 'gateway_refund_id', 'created_at', 'processed_at')
        read_only_fields = ('id', 'requested_by', 'approved_by', 'status', 'gateway_refund_id', 'created_at', 'processed_at')

class GuestPreArrivalSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestPreArrival
        fields = ('id', 'booking', 'expected_arrival_time', 'id_document_type', 'id_document_number', 'flight_or_train_number', 'dietary_preferences', 'special_occasion', 'id_verified', 'submitted_at')
        read_only_fields = ('id', 'booking', 'id_verified', 'submitted_at')

class BookingSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    additional_charges = AdditionalChargeSerializer(many=True, read_only=True)
    pre_arrival = GuestPreArrivalSerializer(read_only=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    room_type_name = serializers.CharField(source='room.room_type.name', read_only=True)
    
    class Meta:
        model = Booking
        fields = (
            'id', 'user', 'room', 'room_number', 'room_type_name', 'check_in_date', 'check_out_date',
            'num_adults', 'num_children', 'special_requests', 'status',
            'room_price_total', 'tax_total', 'additional_charges_total', 'final_amount',
            'is_express_checkout_requested', 'idempotency_key',
            'payments', 'additional_charges', 'pre_arrival', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'user', 'room_price_total', 'tax_total', 'additional_charges_total',
            'final_amount', 'status', 'is_express_checkout_requested', 'created_at', 'updated_at'
        )

    def validate_special_requests(self, value):
        return sanitize_user_text(value)

    def validate(self, data):
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        room = data.get('room')
        num_adults = data.get('num_adults', 1)
        num_children = data.get('num_children', 0)

        if check_in and check_in < date.today():
            raise serializers.ValidationError({"check_in_date": "Check-in date cannot be in the past."})

        if check_in and check_out and check_in >= check_out:
            raise serializers.ValidationError({"check_out_date": "Check-out date must be strictly after check-in date."})

        if room:
            max_capacity = room.room_type.max_adults + room.room_type.max_children
            if (num_adults + num_children) > max_capacity:
                raise serializers.ValidationError({
                    "occupancy": f"This room supports up to {max_capacity} guests ({room.room_type.max_adults} adults, {room.room_type.max_children} children)."
                })

        return data

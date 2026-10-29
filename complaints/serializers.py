from rest_framework import serializers
from .models import GuestComplaint, ComplaintAudit

class ComplaintAuditSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True)

    class Meta:
        model = ComplaintAudit
        fields = '__all__'

class GuestComplaintSerializer(serializers.ModelSerializer):
    guest_name = serializers.CharField(source='guest.get_full_name', read_only=True)
    guest_email = serializers.CharField(source='guest.email', read_only=True)
    assigned_staff_name = serializers.CharField(source='assigned_staff.get_full_name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    audit_trail = ComplaintAuditSerializer(many=True, read_only=True)

    class Meta:
        model = GuestComplaint
        fields = '__all__'
        read_only_fields = ('ticket_number', 'guest', 'created_at', 'updated_at', 'resolved_at', 'sla_due_time')

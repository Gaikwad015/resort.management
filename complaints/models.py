from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from bookings.models import Booking
import uuid

class GuestComplaint(models.Model):
    class Category(models.TextChoices):
        ROOM_CONDITION = 'ROOM_CONDITION', 'Room Condition & Housekeeping'
        NOISE = 'NOISE', 'Noise Disturbance'
        HVAC = 'HVAC', 'AC & Climate Control'
        PLUMBING = 'PLUMBING', 'Plumbing & Hot Water'
        FOOD_BEVERAGE = 'FOOD_BEVERAGE', 'Dining & Food Quality'
        SPA_SERVICE = 'SPA_SERVICE', 'Spa Treatment Experience'
        BILLING = 'BILLING', 'Billing & Payment Discrepancy'
        STAFF_CONDUCT = 'STAFF_CONDUCT', 'Staff Conduct & Service'
        OTHER = 'OTHER', 'Other Concierge Inquiry'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low (24 hr SLA)'
        MEDIUM = 'MEDIUM', 'Medium (4 hr SLA)'
        HIGH = 'HIGH', 'High (1 hr SLA)'
        URGENT = 'URGENT', 'Urgent VIP (15 min SLA)'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open & Unassigned'
        ASSIGNED = 'ASSIGNED', 'Assigned to Duty Staff'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        RESOLVED = 'RESOLVED', 'Resolved by Staff'
        CLOSED = 'CLOSED', 'Guest Verified & Closed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_number = models.CharField(max_length=50, unique=True, db_index=True)
    guest = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints')
    room_number = models.CharField(max_length=20, blank=True)
    
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.ROOM_CONDITION)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    assigned_department = models.CharField(max_length=50, default='Front Desk')
    assigned_staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    
    resolution_notes = models.TextField(blank=True)
    compensation_offered = models.CharField(max_length=200, blank=True, help_text="e.g. Complimentary Dining Voucher, Spa Credit")
    
    sla_due_time = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_overdue(self) -> bool:
        if self.status in [self.Status.RESOLVED, self.Status.CLOSED]:
            return False
        if not self.sla_due_time:
            return False
        return timezone.now() > self.sla_due_time

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = f"TKT-{timezone.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:5].upper()}"
        
        # Calculate SLA target
        if not self.sla_due_time:
            hours = 4
            if self.priority == self.Priority.URGENT:
                hours = 0.5
            elif self.priority == self.Priority.HIGH:
                hours = 1
            elif self.priority == self.Priority.LOW:
                hours = 24
            self.sla_due_time = timezone.now() + timedelta(hours=hours)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_number} - {self.title} [{self.status}]"


class ComplaintAudit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complaint = models.ForeignKey(GuestComplaint, on_delete=models.CASCADE, related_name='audit_trail')
    action = models.CharField(max_length=100)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.complaint.ticket_number}: {self.action} at {self.timestamp.strftime('%H:%M')}"

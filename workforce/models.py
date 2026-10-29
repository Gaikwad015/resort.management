from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid

class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')

    def __str__(self):
        return f"{self.name} [{self.code}]"


class StaffProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff_profile')
    employee_code = models.CharField(max_length=20, unique=True, db_index=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='staff_members')
    designation = models.CharField(max_length=100)
    
    hire_date = models.DateField()
    salary_monthly = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('35000.00'))
    hourly_overtime_rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('250.00'))
    
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=25, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee_code} - {self.user.get_full_name() or self.user.email} ({self.designation})"


class ShiftSchedule(models.Model):
    class ShiftType(models.TextChoices):
        MORNING = 'MORNING', 'Morning (06:00 - 15:00)'
        AFTERNOON = 'AFTERNOON', 'Afternoon (14:00 - 23:00)'
        NIGHT = 'NIGHT', 'Night Graveyard (22:00 - 07:00)'
        GENERAL = 'GENERAL', 'General Executive (09:00 - 18:00)'

    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        COMPLETED = 'COMPLETED', 'Completed'
        SWAPPED = 'SWAPPED', 'Shift Swapped'
        ABSENT = 'ABSENT', 'Absent'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='shifts')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    shift_type = models.CharField(max_length=20, choices=ShiftType.choices)
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['date', 'shift_type']

    def clean(self):
        super().clean()
        # Conflict detection: ensure employee is not double-scheduled on the exact same date
        existing = ShiftSchedule.objects.filter(staff=self.staff, date=self.date)
        if self.pk:
            existing = existing.exclude(pk=self.pk)
        if existing.exists():
            raise ValidationError(f"Staff member {self.staff.employee_code} is already scheduled for a shift on {self.date}.")

    def __str__(self):
        return f"{self.staff.employee_code} - {self.date} [{self.get_shift_type_display()}]"


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present & On Time'
        LATE = 'LATE', 'Tardy / Late Arrival'
        HALF_DAY = 'HALF_DAY', 'Half Day'
        ABSENT = 'ABSENT', 'Unexcused Absence'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(db_index=True)
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    overtime_hours = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('0.0'))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('staff', 'date')

    def __str__(self):
        return f"{self.staff.employee_code} - {self.date} ({self.status})"


class LeaveRequest(models.Model):
    class LeaveType(models.TextChoices):
        CASUAL = 'CASUAL', 'Casual Leave'
        SICK = 'SICK', 'Sick Medical Leave'
        ANNUAL = 'ANNUAL', 'Annual Paid Vacation'
        EMERGENCY = 'EMERGENCY', 'Family Emergency'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending HOD Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LeaveType.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    review_remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("Leave end date cannot be earlier than start date.")

    def __str__(self):
        return f"{self.staff.employee_code} - {self.leave_type} ({self.start_date} to {self.end_date}) [{self.status}]"

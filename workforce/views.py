from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Department, StaffProfile, ShiftSchedule, AttendanceRecord, LeaveRequest
from .serializers import (
    DepartmentSerializer, StaffProfileSerializer, ShiftScheduleSerializer,
    AttendanceRecordSerializer, LeaveRequestSerializer
)

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.select_related('manager').all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]


class StaffProfileViewSet(viewsets.ModelViewSet):
    queryset = StaffProfile.objects.select_related('user', 'department').all()
    serializer_class = StaffProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'is_hotel_staff') and user.is_hotel_staff():
            return self.queryset
        # If regular employee, only view own profile
        return self.queryset.filter(user=user)


class ShiftScheduleViewSet(viewsets.ModelViewSet):
    queryset = ShiftSchedule.objects.select_related('staff', 'staff__user', 'department').all()
    serializer_class = ShiftScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'is_hotel_staff') and user.is_hotel_staff():
            return self.queryset
        return self.queryset.filter(staff__user=user)

    def perform_create(self, serializer):
        # Trigger model clean for overlap check
        instance = serializer.save()
        instance.full_clean()

    @action(detail=True, methods=['post'], url_path='swap')
    def swap_shift(self, request, pk=None):
        """
        Request or execute shift swap with another staff member.
        """
        shift = self.get_object()
        target_staff_id = request.data.get('target_staff_id')
        if not target_staff_id:
            return Response({'error': 'target_staff_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_staff = StaffProfile.objects.get(id=target_staff_id)
            # Check if target staff is already working on that date
            if ShiftSchedule.objects.filter(staff=target_staff, date=shift.date).exclude(pk=shift.pk).exists():
                return Response({'error': f'Target staff {target_staff.employee_code} already has a shift on {shift.date}.'}, status=status.HTTP_400_BAD_REQUEST)
            
            shift.staff = target_staff
            shift.status = ShiftSchedule.Status.SWAPPED
            shift.notes = f"{shift.notes} | Swapped to {target_staff.employee_code} by {request.user.email}"
            shift.save()
            return Response({'message': f'Shift swapped successfully to {target_staff.user.get_full_name() or target_staff.employee_code}.'})
        except StaffProfile.DoesNotExist:
            return Response({'error': 'Target staff profile not found.'}, status=status.HTTP_404_NOT_FOUND)


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.select_related('staff', 'staff__user').all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='clock-in')
    def clock_in(self, request):
        """Staff digital biometric/portal clock-in."""
        staff_profile = getattr(request.user, 'staff_profile', None)
        if not staff_profile:
            return Response({'error': 'Current user does not have an active staff profile.'}, status=status.HTTP_403_FORBIDDEN)
        
        today = timezone.localdate()
        record, created = AttendanceRecord.objects.get_or_create(
            staff=staff_profile,
            date=today,
            defaults={'clock_in': timezone.localtime().time(), 'status': AttendanceRecord.Status.PRESENT}
        )
        if not created and record.clock_in:
            return Response({'message': 'Already clocked in for today.', 'clock_in': str(record.clock_in)})
        
        record.clock_in = timezone.localtime().time()
        record.save()
        return Response({'message': 'Clocked in successfully.', 'date': str(today), 'clock_in': str(record.clock_in)})

    @action(detail=False, methods=['post'], url_path='clock-out')
    def clock_out(self, request):
        """Staff digital clock-out."""
        staff_profile = getattr(request.user, 'staff_profile', None)
        if not staff_profile:
            return Response({'error': 'Current user does not have an active staff profile.'}, status=status.HTTP_403_FORBIDDEN)
        
        today = timezone.localdate()
        try:
            record = AttendanceRecord.objects.get(staff=staff_profile, date=today)
            record.clock_out = timezone.localtime().time()
            record.save()
            return Response({'message': 'Clocked out successfully.', 'date': str(today), 'clock_out': str(record.clock_out)})
        except AttendanceRecord.DoesNotExist:
            return Response({'error': 'No clock-in record found for today.'}, status=status.HTTP_400_BAD_REQUEST)


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.select_related('staff', 'staff__user', 'reviewed_by').all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'is_hotel_staff') and user.is_hotel_staff():
            return self.queryset
        return self.queryset.filter(staff__user=user)

    def perform_create(self, serializer):
        staff = getattr(self.request.user, 'staff_profile', None)
        if not staff:
            raise ValidationError('User must have an active staff profile to submit leave.')
        serializer.save(staff=staff)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_leave(self, request, pk=None):
        leave = self.get_object()
        leave.status = LeaveRequest.Status.APPROVED
        leave.reviewed_by = request.user
        leave.rejection_reason = ''
        leave.save()
        return Response({'message': f'Leave request for {leave.staff.employee_code} APPROVED.', 'status': leave.status})

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_leave(self, request, pk=None):
        leave = self.get_object()
        reason = request.data.get('reason', 'Operational workforce requirements.')
        leave.status = LeaveRequest.Status.REJECTED
        leave.reviewed_by = request.user
        leave.rejection_reason = reason
        leave.save()
        return Response({'message': f'Leave request for {leave.staff.employee_code} REJECTED.', 'status': leave.status})

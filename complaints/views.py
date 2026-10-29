from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import GuestComplaint, ComplaintAudit
from .serializers import GuestComplaintSerializer, ComplaintAuditSerializer

class GuestComplaintViewSet(viewsets.ModelViewSet):
    queryset = GuestComplaint.objects.select_related('guest', 'booking', 'assigned_staff').prefetch_related('audit_trail').all()
    serializer_class = GuestComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'is_hotel_staff') and user.is_hotel_staff():
            return self.queryset
        # Strict BOLA / IDOR isolation: Guests can only access their own complaints
        return self.queryset.filter(guest=user)

    def perform_create(self, serializer):
        complaint = serializer.save(guest=self.request.user)
        ComplaintAudit.objects.create(
            complaint=complaint,
            action="TICKET_CREATED",
            performed_by=self.request.user,
            notes=f"Ticket registered by {self.request.user.email} (Priority: {complaint.priority})"
        )

    @action(detail=True, methods=['post'], url_path='assign')
    def assign_staff(self, request, pk=None):
        """Hotel staff / Manager assigns ticket to specific staff member."""
        complaint = self.get_object()
        staff_id = request.data.get('staff_id')
        dept = request.data.get('department', complaint.assigned_department)
        
        if staff_id:
            from accounts.models import User
            try:
                assigned_user = User.objects.get(id=staff_id)
                complaint.assigned_staff = assigned_user
            except User.DoesNotExist:
                return Response({'error': 'Staff user not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        complaint.assigned_department = dept
        complaint.status = GuestComplaint.Status.ASSIGNED
        complaint.save()

        ComplaintAudit.objects.create(
            complaint=complaint,
            action="ASSIGNED_TO_STAFF",
            performed_by=request.user,
            notes=f"Assigned to {complaint.assigned_staff or 'Unassigned'} ({dept})"
        )
        return Response({'message': f'Ticket {complaint.ticket_number} assigned successfully.', 'status': complaint.status})

    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve_complaint(self, request, pk=None):
        """Staff marks complaint as resolved with service recovery notes & compensation."""
        complaint = self.get_object()
        notes = request.data.get('resolution_notes', 'Service recovery completed to guest satisfaction.')
        compensation = request.data.get('compensation_offered', '')

        complaint.status = GuestComplaint.Status.RESOLVED
        complaint.resolved_at = timezone.now()
        complaint.resolution_notes = notes
        if compensation:
            complaint.compensation_offered = compensation
        complaint.save()

        ComplaintAudit.objects.create(
            complaint=complaint,
            action="RESOLVED",
            performed_by=request.user,
            notes=f"Resolution: {notes} | Compensation: {compensation}"
        )
        return Response({'message': f'Ticket {complaint.ticket_number} marked as RESOLVED.', 'status': complaint.status})

    @action(detail=True, methods=['post'], url_path='close')
    def close_complaint(self, request, pk=None):
        """Guest verifies resolution and formally closes the ticket."""
        complaint = self.get_object()
        complaint.status = GuestComplaint.Status.CLOSED
        complaint.save()

        ComplaintAudit.objects.create(
            complaint=complaint,
            action="GUEST_CLOSED",
            performed_by=request.user,
            notes="Guest confirmed satisfaction and closed ticket."
        )
        return Response({'message': f'Ticket {complaint.ticket_number} successfully closed.', 'status': complaint.status})

    @action(detail=False, methods=['get'], url_path='overdue')
    def overdue_tickets(self, request):
        """Returns all open/in-progress tickets that breached SLA."""
        now = timezone.now()
        qs = self.get_queryset().filter(
            status__in=[GuestComplaint.Status.OPEN, GuestComplaint.Status.ASSIGNED, GuestComplaint.Status.IN_PROGRESS],
            sla_due_time__lt=now
        )
        return Response({
            'count': qs.count(),
            'tickets': GuestComplaintSerializer(qs, many=True).data
        })

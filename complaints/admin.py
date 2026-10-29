from django.contrib import admin
from .models import GuestComplaint, ComplaintAudit

class ComplaintAuditInline(admin.TabularInline):
    model = ComplaintAudit
    extra = 0
    readonly_fields = ('action', 'performed_by', 'timestamp', 'notes')

@admin.register(GuestComplaint)
class GuestComplaintAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'guest', 'category', 'priority', 'status', 'assigned_department', 'assigned_staff', 'is_overdue', 'sla_due_time', 'created_at')
    list_filter = ('priority', 'status', 'category', 'assigned_department')
    search_fields = ('ticket_number', 'guest__email', 'room_number', 'title')
    inlines = [ComplaintAuditInline]

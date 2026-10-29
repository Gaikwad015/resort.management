from django.contrib import admin
from .models import Department, StaffProfile, ShiftSchedule, AttendanceRecord, LeaveRequest

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'manager')

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_code', 'user', 'department', 'designation', 'hire_date', 'salary_monthly', 'is_active')
    list_filter = ('department', 'is_active')
    search_fields = ('employee_code', 'user__email', 'user__first_name', 'user__last_name')

@admin.register(ShiftSchedule)
class ShiftScheduleAdmin(admin.ModelAdmin):
    list_display = ('staff', 'department', 'shift_type', 'date', 'status')
    list_filter = ('shift_type', 'status', 'date', 'department')
    search_fields = ('staff__employee_code', 'staff__user__email')

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('staff', 'date', 'clock_in', 'clock_out', 'overtime_hours', 'status')
    list_filter = ('status', 'date')
    search_fields = ('staff__employee_code',)

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('staff', 'leave_type', 'start_date', 'end_date', 'status', 'reviewed_by', 'created_at')
    list_filter = ('status', 'leave_type')
    search_fields = ('staff__employee_code',)

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet, StaffProfileViewSet, ShiftScheduleViewSet,
    AttendanceRecordViewSet, LeaveRequestViewSet
)

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'staff', StaffProfileViewSet, basename='staff-profile')
router.register(r'shifts', ShiftScheduleViewSet, basename='shift-schedule')
router.register(r'attendance', AttendanceRecordViewSet, basename='attendance')
router.register(r'leaves', LeaveRequestViewSet, basename='leave-request')

urlpatterns = [
    path('', include(router.urls)),
]

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, LoyaltyAccount, LoyaltyTransaction, GuestPreference, GuestFeedback

class LoyaltyTransactionInline(admin.TabularInline):
    model = LoyaltyTransaction
    extra = 0
    readonly_fields = ('transaction_type', 'points', 'description', 'reference_booking_id', 'created_at')

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_verified', 'is_staff')
    list_filter = ('role', 'is_verified', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone', 'profile_picture', 'date_of_birth', 'anniversary_date')}),
        ('Role & Permissions', {'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'tier', 'points_balance', 'lifetime_points', 'updated_at')
    list_filter = ('tier',)
    search_fields = ('user__email',)
    inlines = [LoyaltyTransactionInline]

@admin.register(GuestPreference)
class GuestPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'bed_preference', 'floor_preference', 'dietary_preference', 'consent_email', 'consent_sms')
    search_fields = ('user__email',)

@admin.register(GuestFeedback)
class GuestFeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'booking_reference', 'overall_rating', 'is_reviewed', 'created_at')
    list_filter = ('overall_rating', 'is_reviewed')
    search_fields = ('user__email', 'booking_reference', 'comments')

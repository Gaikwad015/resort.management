from django.contrib import admin
from .models import SecurityAuditLog

@admin.register(SecurityAuditLog)
class SecurityAuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'event_type', 'severity', 'user_email', 'ip_address', 'status_code', 'is_tamper_free')
    list_filter = ('severity', 'event_type', 'status_code')
    search_fields = ('user_email', 'ip_address', 'correlation_id', 'path')
    readonly_fields = [f.name for f in SecurityAuditLog._meta.fields]

    def is_tamper_free(self, obj):
        return obj.verify_integrity()
    is_tamper_free.boolean = True
    is_tamper_free.short_description = "HMAC-SHA256 Valid"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

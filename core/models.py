from django.db import models
from django.conf import settings
import uuid
import hmac
import hashlib
import json

class SecurityAuditLog(models.Model):
    """
    OWASP A09:2025 - Security Logging and Alerting Failures
    OWASP A08:2025 - Software or Data Integrity Failures (Tamper-evident log with HMAC-SHA256 checksum)
    """
    class Severity(models.TextChoices):
        INFO = 'INFO', 'Informational'
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class EventType(models.TextChoices):
        LOGIN_SUCCESS = 'LOGIN_SUCCESS', 'Login Success'
        LOGIN_FAILURE = 'LOGIN_FAILURE', 'Login Failure'
        ACCOUNT_LOCKED = 'ACCOUNT_LOCKED', 'Account Locked (Brute Force)'
        UNAUTHORIZED_ACCESS = 'UNAUTHORIZED_ACCESS', 'Broken Access Control (A01)'
        INJECTION_ATTEMPT = 'INJECTION_ATTEMPT', 'Injection Vector Blocked (A05)'
        STEP_UP_AUTH = 'STEP_UP_AUTH', 'Step-Up Authentication Verified'
        PRICE_TAMPER_ATTEMPT = 'PRICE_TAMPER_ATTEMPT', 'Price/Business Logic Tamper Blocked (A06)'
        WEBHOOK_INTEGRITY_FAIL = 'WEBHOOK_INTEGRITY_FAIL', 'Webhook Signature Mismatch (A08)'
        EXCEPTION_TRIGGERED = 'EXCEPTION_TRIGGERED', 'Exceptional Condition Handled (A10)'
        DATA_EXPORT = 'DATA_EXPORT', 'Sensitive Data Export'
        CONFIG_CHANGE = 'CONFIG_CHANGE', 'Security Configuration Changed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    event_type = models.CharField(max_length=50, choices=EventType.choices, db_index=True)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.INFO, db_index=True)
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='security_logs')
    user_email = models.CharField(max_length=255, blank=True, help_text="Cached email for audit even if user is deleted")
    
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.CharField(max_length=500, blank=True)
    path = models.CharField(max_length=500, blank=True)
    http_method = models.CharField(max_length=10, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    
    correlation_id = models.CharField(max_length=100, blank=True, db_index=True)
    details = models.JSONField(default=dict, blank=True)
    
    # Cryptographic HMAC checksum to guarantee tamper evidence (A08:2025)
    checksum = models.CharField(max_length=64, blank=True, help_text="HMAC-SHA256 signature of log integrity")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Security Audit Log'
        verbose_name_plural = 'Security Audit Logs'

    def calculate_checksum(self) -> str:
        """Calculates HMAC-SHA256 of the critical audit log fields."""
        secret = getattr(settings, 'SECRET_KEY', 'default-audit-secret').encode('utf-8')
        payload = f"{self.id}:{self.event_type}:{self.severity}:{self.user_email}:{self.ip_address}:{self.path}:{self.correlation_id}:{json.dumps(self.details, sort_keys=True)}"
        return hmac.new(secret, payload.encode('utf-8'), hashlib.sha256).hexdigest()

    def verify_integrity(self) -> bool:
        """Verifies if this audit entry has been tampered with in the database."""
        if not self.checksum:
            return False
        return hmac.compare_digest(self.checksum, self.calculate_checksum())

    def save(self, *args, **kwargs):
        if self.user and not self.user_email:
            self.user_email = self.user.email
        if not self.checksum:
            self.checksum = self.calculate_checksum()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.severity}] {self.event_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({self.ip_address})"

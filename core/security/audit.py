import logging
import uuid
from typing import Optional, Dict, Any
from django.http import HttpRequest
from core.security.crypto import sanitize_audit_details

logger = logging.getLogger('security.audit')

def get_client_ip(request: HttpRequest) -> str:
    """Safely extracts client IP taking reverse proxy headers into account."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip

def log_security_event(
    event_type: str,
    severity: str = 'INFO',
    request: Optional[HttpRequest] = None,
    user: Optional[Any] = None,
    details: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
    status_code: Optional[int] = None
) -> None:
    """
    Centralized, fail-safe security event logging.
    Enforces OWASP A09:2025 (Logging & Alerting) and A08:2025 (Integrity).
    """
    from core.models import SecurityAuditLog

    if details is None:
        details = {}
    
    sanitized_details = sanitize_audit_details(details)
    corr_id = correlation_id or getattr(request, 'correlation_id', str(uuid.uuid4()))

    ip_addr = None
    ua = ""
    path = ""
    method = ""

    if request:
        ip_addr = get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', '')[:500]
        path = request.path[:500]
        method = request.method[:10]
        if user is None and hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user

    user_email = ""
    if user and getattr(user, 'is_authenticated', False):
        user_email = getattr(user, 'email', str(user))

    # Fallback stdout logging
    logger.info(f"SECURITY_EVENT: [{severity}] {event_type} | User: {user_email} | IP: {ip_addr} | Corr: {corr_id}")

    try:
        SecurityAuditLog.objects.create(
            event_type=event_type,
            severity=severity,
            user=user if (user and getattr(user, 'is_authenticated', False)) else None,
            user_email=user_email,
            ip_address=ip_addr,
            user_agent=ua,
            path=path,
            http_method=method,
            status_code=status_code,
            correlation_id=corr_id,
            details=sanitized_details
        )
    except Exception as e:
        # Fail-closed / safe logging: Never allow logging failure to bring down application (A10:2025)
        logger.error(f"Failed to persist SecurityAuditLog to DB: {e}", exc_info=True)

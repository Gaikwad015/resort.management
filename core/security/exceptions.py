import logging
import uuid
from datetime import datetime, timezone
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException
from core.security.audit import log_security_event

logger = logging.getLogger('security.exceptions')

def custom_security_exception_handler(exc, context):
    """
    OWASP A10:2025 - Mishandling of Exceptional Conditions.
    
    Guarantees:
    1. Fail-closed: Never returns partial or undefined states.
    2. No information leakage: Internal stack traces, database schema, and server paths
       are never returned to clients.
    3. Traceability: Every exception response contains a correlation_id.
    4. Auditing: Logs exceptions to the SecurityAuditLog (A09:2025).
    """
    request = context.get('request')
    correlation_id = getattr(request, 'correlation_id', f"ERR-{uuid.uuid4().hex[:10].upper()}")
    
    # Call DRF's default exception handler first to get the standard error response
    response = exception_handler(exc, context)
    
    now_iso = datetime.now(timezone.utc).isoformat()

    if response is not None:
        # Standard DRF exception (e.g. Validation, NotAuthenticated, PermissionDenied)
        error_code = getattr(exc, 'default_code', 'API_ERROR').upper()
        custom_data = {
            'status': 'error',
            'code': error_code,
            'message': 'Request processing failed.',
            'details': response.data,
            'correlation_id': correlation_id,
            'timestamp': now_iso,
        }
        
        # If permission denied, log broken access control alert (A01:2025)
        if response.status_code == status.HTTP_403_FORBIDDEN:
            log_security_event(
                event_type='UNAUTHORIZED_ACCESS',
                severity='MEDIUM',
                request=request,
                details={'code': error_code, 'view': str(context.get('view'))},
                correlation_id=correlation_id,
                status_code=403
            )
            
        response.data = custom_data
        return response

    # Unhandled unexpected internal exception (HTTP 500)
    # Log complete traceback securely server-side
    logger.error(f"[CORRELATION_ID: {correlation_id}] Unhandled Exception: {exc}", exc_info=True)
    
    log_security_event(
        event_type='EXCEPTION_TRIGGERED',
        severity='CRITICAL',
        request=request,
        details={
            'exception_type': exc.__class__.__name__,
            'exception_message': str(exc)[:200],
            'view': str(context.get('view'))
        },
        correlation_id=correlation_id,
        status_code=500
    )

    # Return safe, non-revealing response to client (Fail Closed)
    safe_error_payload = {
        'status': 'error',
        'code': 'INTERNAL_SERVER_ERROR',
        'message': 'An unexpected condition occurred while processing your request. Please contact luxury concierge support with the correlation ID.',
        'correlation_id': correlation_id,
        'timestamp': now_iso
    }
    
    return Response(safe_error_payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

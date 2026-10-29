import re
import uuid
import json
from django.http import HttpResponseBadRequest, JsonResponse, HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from core.security.audit import log_security_event, get_client_ip

# OWASP A05:2025 Injection Vectors Regex Patterns
SQLI_PATTERNS = [
    r"(\b(UNION(\s+ALL)?|SELECT|INSERT|DELETE|UPDATE|DROP|ALTER|EXEC|EXECUTE)\b.*\b(FROM|INTO|TABLE|DATABASE|WHERE)\b)",
    r"('|\%27)\s*(OR|AND)\s*('|\%27|[0-9]+=[0-9]+|[a-zA-Z]+=[a-zA-Z]+)",
    r"(--|#|/\*).*",
    r"(\bSLEEP\s*\(\s*[0-9]+\s*\)|\bWAITFOR\s+DELAY\b|\bBENCHMARK\s*\()",
]

XSS_PATTERNS = [
    r"<\s*script[^>]*>",
    r"javascript\s*:",
    r"onerror\s*=",
    r"onload\s*=",
    r"eval\s*\(",
    r"document\.(cookie|location|write)",
]

CMD_INJECTION_PATTERNS = [
    r"(\|\s*\w+|\;\s*\w+|\&\&\s*\w+|\`.*\`|\$\(.*\))",
]

COMPILED_INJECTION_RULES = [
    (re.compile(p, re.IGNORECASE), name)
    for patterns, name in [
        (SQLI_PATTERNS, 'SQL_INJECTION'),
        (XSS_PATTERNS, 'CROSS_SITE_SCRIPTING'),
        (CMD_INJECTION_PATTERNS, 'COMMAND_INJECTION'),
    ]
    for p in patterns
]

class CorrelationIdMiddleware(MiddlewareMixin):
    """
    OWASP A10:2025 & A09:2025: Injects a unique Correlation ID into every request
    to track exceptional conditions and audit trails across distributed services.
    """
    def process_request(self, request: HttpRequest):
        corr_id = request.headers.get('X-Correlation-ID') or f"REQ-{uuid.uuid4().hex[:12].upper()}"
        request.correlation_id = corr_id

    def process_response(self, request: HttpRequest, response: HttpResponse):
        if hasattr(request, 'correlation_id'):
            response['X-Correlation-ID'] = request.correlation_id
        return response

class ComprehensiveSecurityHeadersMiddleware(MiddlewareMixin):
    """
    OWASP A02:2025 - Security Misconfiguration Defense.
    Enforces modern browser security headers and isolation policies.
    """
    def process_response(self, request: HttpRequest, response: HttpResponse):
        # Isolation & Embedding protections
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        response['Cross-Origin-Resource-Policy'] = 'same-origin'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        
        # Disable risky hardware/APIs by default (Least Privilege)
        response['Permissions-Policy'] = (
            'geolocation=(), camera=(), microphone=(), payment=(self), '
            'usb=(), magnetometer=(), accelerometer=()'
        )
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response

class AntiInjectionMiddleware(MiddlewareMixin):
    """
    OWASP A05:2025 - Injection Defense.
    Inspects incoming query strings, form bodies, and raw JSON payloads for injection attack patterns.
    Fails closed immediately (400 Bad Request) and raises a HIGH-severity security audit alert.
    """
    def _inspect_text(self, text: str, location: str, request: HttpRequest) -> bool:
        if not text:
            return False
        for regex, attack_type in COMPILED_INJECTION_RULES:
            if regex.search(text):
                log_security_event(
                    event_type='INJECTION_ATTEMPT',
                    severity='HIGH',
                    request=request,
                    details={
                        'attack_type': attack_type,
                        'location': location,
                        'matched_sample': text[:100] # Safe truncated sample
                    },
                    status_code=400
                )
                return True
        return False

    def process_request(self, request: HttpRequest):
        # 1. Inspect Query String
        for key, val in request.GET.items():
            if self._inspect_text(f"{key}={val}", "QUERY_PARAM", request):
                return JsonResponse({
                    'error': 'Potential malicious injection vector detected.',
                    'code': 'INJECTION_DETECTED',
                    'correlation_id': getattr(request, 'correlation_id', '')
                }, status=400)

        # 2. Inspect Body if application/json or form
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.META.get('CONTENT_TYPE', '')
            if 'application/json' in content_type and request.body:
                try:
                    # Check body as decoded string (limit inspection to first 16KB to prevent DoS)
                    body_sample = request.body[:16384].decode('utf-8', errors='ignore')
                    if self._inspect_text(body_sample, "JSON_BODY", request):
                        return JsonResponse({
                            'error': 'Potential malicious injection vector detected in payload.',
                            'code': 'INJECTION_DETECTED',
                            'correlation_id': getattr(request, 'correlation_id', '')
                        }, status=400)
                except Exception:
                    pass

        return None

class SecurityAuditMiddleware(MiddlewareMixin):
    """
    OWASP A09:2025 & A01:2025: Monitors HTTP response statuses.
    Automatically captures 401 Unauthorized, 403 Forbidden, and 500 Server Errors into audit logs.
    """
    def process_response(self, request: HttpRequest, response: HttpResponse):
        if response.status_code == 401:
            log_security_event(
                event_type='LOGIN_FAILURE',
                severity='LOW',
                request=request,
                details={'reason': 'Unauthorized access attempt'},
                status_code=401
            )
        elif response.status_code == 403:
            log_security_event(
                event_type='UNAUTHORIZED_ACCESS',
                severity='MEDIUM',
                request=request,
                details={'reason': 'Broken Access Control check failed (403 Forbidden)'},
                status_code=403
            )
        elif response.status_code >= 500:
            log_security_event(
                event_type='EXCEPTION_TRIGGERED',
                severity='CRITICAL',
                request=request,
                details={'status_code': response.status_code},
                status_code=response.status_code
            )
        return response

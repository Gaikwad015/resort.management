import hmac
import hashlib
import json
import time
from typing import Optional, Tuple
from django.conf import settings
from django.core import signing

def mask_card_number(card_number: Optional[str]) -> str:
    """Masks credit card numbers showing only last 4 digits (PCI-DSS / A04:2025)."""
    if not card_number:
        return ""
    clean = str(card_number).replace(" ", "").replace("-", "")
    if len(clean) < 4:
        return "****"
    return f"****-****-****-{clean[-4:]}"

def mask_email(email: Optional[str]) -> str:
    """Masks email for logging and non-privileged displays (A04:2025)."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"

def mask_phone(phone: Optional[str]) -> str:
    """Masks phone number."""
    if not phone:
        return ""
    clean = str(phone).strip()
    if len(clean) <= 4:
        return "****"
    return "*" * (len(clean) - 4) + clean[-4:]

def sanitize_audit_details(data: dict) -> dict:
    """
    Strips or masks passwords, tokens, API keys, and card numbers before writing to logs.
    OWASP A09:2025 - Security Logging and Alerting Failures (Prevents log leakage).
    """
    sensitive_keys = {
        'password', 'token', 'access', 'refresh', 'secret', 'authorization',
        'api_key', 'card_number', 'cvv', 'card_cvv', 'cvc'
    }
    sanitized = {}
    for k, v in data.items():
        lower_k = k.lower()
        if any(s in lower_k for s in sensitive_keys):
            sanitized[k] = "[REDACTED_BY_SECURITY_POLICY]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_audit_details(v)
        else:
            sanitized[k] = v
    return sanitized

def verify_webhook_hmac(payload_bytes: bytes, signature_header: str, secret_key: Optional[str] = None) -> bool:
    """
    Verifies incoming webhook payload using HMAC-SHA256 with constant-time comparison.
    OWASP A08:2025 - Software or Data Integrity Failures.
    """
    if not signature_header or not payload_bytes:
        return False
    
    key = (secret_key or getattr(settings, 'PAYMENT_WEBHOOK_SECRET', settings.SECRET_KEY)).encode('utf-8')
    computed_sig = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()
    
    # Clean header prefix if present (e.g., 'sha256=abcdef...')
    provided_sig = signature_header.replace('sha256=', '').strip()
    
    return hmac.compare_digest(computed_sig.lower(), provided_sig.lower())

class StepUpTokenManager:
    """
    Issues and verifies step-up authentication tokens for high-risk operations
    (OWASP A07:2025 / A01:2025).
    """
    SALT = "elara.security.stepup"
    DEFAULT_MAX_AGE_SECONDS = 300 # 5 minutes

    @classmethod
    def generate_token(cls, user_id: str, action: str) -> str:
        data = {
            'user_id': str(user_id),
            'action': action,
            'timestamp': int(time.time())
        }
        return signing.dumps(data, salt=cls.SALT)

    @classmethod
    def verify_token(cls, token: str, expected_user_id: str, expected_action: str, max_age: int = DEFAULT_MAX_AGE_SECONDS) -> Tuple[bool, str]:
        try:
            data = signing.loads(token, salt=cls.SALT, max_age=max_age)
            if str(data.get('user_id')) != str(expected_user_id):
                return False, "Token does not belong to the current authenticated user."
            if data.get('action') != expected_action:
                return False, f"Token was issued for '{data.get('action')}', not '{expected_action}'."
            return True, "Verified"
        except signing.SignatureExpired:
            return False, "Step-up authentication token has expired. Please re-authenticate."
        except signing.BadSignature:
            return False, "Invalid step-up authentication token."
        except Exception:
            return False, "Step-up verification error."

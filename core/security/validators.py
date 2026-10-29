import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.utils.html import escape

class LuxuryPasswordComplexityValidator:
    """
    OWASP A07:2025 - Authentication Failures Defense.
    Enforces high-entropy passwords:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one numerical digit
    - At least one special symbol
    """
    def validate(self, password, user=None):
        if len(password) < 12:
            raise ValidationError(
                _("Luxury security standard requires passwords to be at least 12 characters long."),
                code='password_too_short',
            )
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter (A-Z)."),
                code='password_no_upper',
            )
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter (a-z)."),
                code='password_no_lower',
            )
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                _("Password must contain at least one numerical digit (0-9)."),
                code='password_no_digit',
            )
        if not re.search(r'[!@#$%^&*(),.?":{}|<>\-_=+]', password):
            raise ValidationError(
                _("Password must contain at least one special character (!@#$%^&* etc.)."),
                code='password_no_symbol',
            )

    def get_help_text(self):
        return _(
            "Your password must be at least 12 characters long and include an uppercase letter, "
            "a lowercase letter, a digit, and a special character."
        )

def sanitize_user_text(text: str) -> str:
    """
    OWASP A05:2025 - Injection Defense.
    Sanitizes user input (such as guest special requests, notes) to prevent stored XSS.
    """
    if not text:
        return ""
    # Standard HTML escape
    escaped = escape(text.strip())
    # Strip null bytes
    return escaped.replace('\x00', '')

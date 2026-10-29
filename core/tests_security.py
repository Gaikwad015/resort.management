import json
import hmac
import hashlib
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APIClient
from rooms.models import Room, RoomType
from bookings.models import Booking
from core.models import SecurityAuditLog
from core.security.crypto import mask_card_number, verify_webhook_hmac, StepUpTokenManager
from core.security.validators import LuxuryPasswordComplexityValidator
from core.security.middleware import ComprehensiveSecurityHeadersMiddleware, CorrelationIdMiddleware, AntiInjectionMiddleware

User = get_user_model()

class OWASP2025SecurityTests(TestCase):
    """
    Automated Test Suite for OWASP Top 10: 2025 Compliance
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.api_client = APIClient()
        self.user1 = User.objects.create_user(
            email='guest1@elara.com',
            username='guest1@elara.com',
            password='LuxuryPassword123!@#',
            role='CUSTOMER'
        )
        self.user2 = User.objects.create_user(
            email='guest2@elara.com',
            username='guest2@elara.com',
            password='LuxuryPassword123!@#',
            role='CUSTOMER'
        )
        self.room_type = RoomType.objects.create(
            name='Presidential Suite',
            slug='presidential-suite',
            description='Ultimate luxury suite',
            base_price_per_night=50000.00,
            room_size_sqm=120
        )
        self.room = Room.objects.create(
            room_number='801',
            room_type=self.room_type,
            floor='8th Floor'
        )

    # --- A01:2025 - Broken Access Control ---
    def test_a01_broken_access_control_prevent_idor(self):
        booking = Booking.objects.create(
            user=self.user1,
            room=self.room,
            check_in_date='2026-11-01',
            check_out_date='2026-11-05',
            room_price_total=200000.00,
            final_amount=236000.00
        )
        # Authenticate as Guest 2 via JWT Bearer Token
        token = str(RefreshToken.for_user(self.user2).access_token)
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Guest 2 attempts to retrieve Guest 1's booking via API (IDOR attack)
        response = self.api_client.get(f'/api/v1/bookings/{booking.id}/')
        # Zero Trust: returns 404 (filtered from queryset) or 403 (Forbidden)
        self.assertIn(response.status_code, [403, 404])

    # --- A02:2025 - Security Misconfiguration ---
    def test_a02_security_headers_middleware(self):
        request = self.factory.get('/api/v1/security/alerts/')
        middleware = ComprehensiveSecurityHeadersMiddleware(lambda r: self.api_client.get('/api/v1/security/alerts/'))
        response = middleware(request)
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertIn('Permissions-Policy', response.headers)
        self.assertIn('Cross-Origin-Opener-Policy', response.headers)

    # --- A03:2025 - Software Supply Chain Failures ---
    def test_a03_supply_chain_sbom_generation(self):
        from django.core.management import call_command
        import os
        from django.conf import settings
        call_command('security_audit')
        sbom_file = os.path.join(settings.BASE_DIR, 'security_sbom.json')
        self.assertTrue(os.path.exists(sbom_file))

    # --- A04:2025 - Cryptographic Failures ---
    def test_a04_card_masking(self):
        masked = mask_card_number("4532 8921 7842 9821")
        self.assertEqual(masked, "****-****-****-9821")
        self.assertNotIn("4532", masked)

    # --- A05:2025 - Injection Defense ---
    def test_a05_anti_injection_middleware_blocks_sqli(self):
        request = self.factory.get("/?search=' UNION SELECT * FROM accounts_user--")
        corr_middleware = CorrelationIdMiddleware(lambda r: None)
        corr_middleware.process_request(request)
        
        middleware = AntiInjectionMiddleware(lambda r: None)
        result = middleware.process_request(request)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 400)
        data = json.loads(result.content)
        self.assertEqual(data.get('code'), 'INJECTION_DETECTED')

    def test_a05_anti_injection_middleware_blocks_xss(self):
        request = self.factory.get('/?name=<script>alert(document.cookie)</script>')
        corr_middleware = CorrelationIdMiddleware(lambda r: None)
        corr_middleware.process_request(request)
        
        middleware = AntiInjectionMiddleware(lambda r: None)
        result = middleware.process_request(request)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 400)
        data = json.loads(result.content)
        self.assertEqual(data.get('code'), 'INJECTION_DETECTED')

    # --- A06:2025 - Insecure Design & State Machine ---
    def test_a06_state_machine_prevents_invalid_transition(self):
        booking = Booking.objects.create(
            user=self.user1,
            room=self.room,
            check_in_date='2026-11-01',
            check_out_date='2026-11-05',
            room_price_total=200000.00,
            final_amount=236000.00,
            status=Booking.Status.CANCELLED
        )
        # Cannot transition from CANCELLED to CHECKED_IN
        self.assertFalse(booking.can_transition_to(Booking.Status.CHECKED_IN))

    # --- A07:2025 - Authentication Failures ---
    def test_a07_password_complexity_validator(self):
        validator = LuxuryPasswordComplexityValidator()
        with self.assertRaises(ValidationError):
            validator.validate("weakpass")

        with self.assertRaises(ValidationError):
            validator.validate("NoSpecialCharacter123")

        validator.validate("Luxury123!@#Valid")

    def test_a07_step_up_token_verification(self):
        token = StepUpTokenManager.generate_token(str(self.user1.id), "CANCEL_BOOKING")
        valid, _ = StepUpTokenManager.verify_token(token, str(self.user1.id), "CANCEL_BOOKING")
        self.assertTrue(valid)
        
        # User 2 cannot use User 1's step up token
        invalid, _ = StepUpTokenManager.verify_token(token, str(self.user2.id), "CANCEL_BOOKING")
        self.assertFalse(invalid)

    # --- A08:2025 - Software and Data Integrity Failures ---
    def test_a08_webhook_hmac_signature_verification(self):
        secret = "test-webhook-secret-2026"
        payload = b'{"booking_id": "123", "amount": 50000}'
        valid_signature = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()

        self.assertTrue(verify_webhook_hmac(payload, valid_signature, secret))
        tampered_payload = b'{"booking_id": "123", "amount": 100}'
        self.assertFalse(verify_webhook_hmac(tampered_payload, valid_signature, secret))

    def test_a08_audit_log_cryptographic_checksum(self):
        log = SecurityAuditLog.objects.create(
            event_type='LOGIN_SUCCESS',
            severity='INFO',
            ip_address='127.0.0.1',
            user_email='guest1@elara.com'
        )
        self.assertTrue(log.verify_integrity())
        
        # Simulate tampering
        log.user_email = 'hacker@malicious.com'
        self.assertFalse(log.verify_integrity())

    # --- A10:2025 - Mishandling of Exceptional Conditions ---
    def test_a10_correlation_id_middleware(self):
        request = self.factory.get('/api/v1/auth/login/')
        from django.http import HttpResponse
        response = HttpResponse()
        middleware = CorrelationIdMiddleware(lambda r: response)
        middleware.process_request(request)
        self.assertTrue(hasattr(request, 'correlation_id'))
        self.assertTrue(request.correlation_id.startswith('REQ-'))
        response = middleware.process_response(request, response)
        self.assertEqual(response.headers.get('X-Correlation-ID'), request.correlation_id)

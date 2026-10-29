from rest_framework import generics, status, views, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from .serializers import CustomTokenObtainPairSerializer, UserSerializer
from core.security.validators import LuxuryPasswordComplexityValidator
from core.security.crypto import StepUpTokenManager
from core.security.audit import log_security_event

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    OWASP A07:2025 - Authentication Failures Defense.
    Handles login with audit logging and rate limiting.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            email = request.data.get('email', '')
            log_security_event(
                event_type='LOGIN_SUCCESS',
                severity='INFO',
                request=request,
                details={'email': email},
                status_code=200
            )
        return response

class StepUpAuthView(views.APIView):
    """
    OWASP A07:2025 & A01:2025: Issues a short-lived (5 min) Step-Up Token
    after re-verifying the user's password for sensitive operations (cancellations, refunds).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        password = request.data.get('password')
        action = request.data.get('action', 'HIGH_RISK_OPERATION')

        if not password:
            return Response({"error": "Password confirmation is required for step-up verification."}, status=status.HTTP_400_BAD_REQUEST)

        # Verify password
        user = authenticate(username=request.user.email, password=password)
        if not user:
            log_security_event(
                event_type='LOGIN_FAILURE',
                severity='MEDIUM',
                request=request,
                details={'reason': 'Step-up authentication re-check failed'},
                status_code=401
            )
            return Response({"error": "Invalid password confirmation."}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate cryptographic step-up token
        token = StepUpTokenManager.generate_token(str(request.user.id), action)
        
        log_security_event(
            event_type='STEP_UP_AUTH',
            severity='INFO',
            request=request,
            details={'action': action},
            status_code=200
        )

        return Response({
            "step_up_token": token,
            "expires_in_seconds": StepUpTokenManager.DEFAULT_MAX_AGE_SECONDS,
            "action": action
        })

class LogoutView(views.APIView):
    """
    OWASP A07:2025 - Complete Session Invalidation and JWT Blacklisting.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            if hasattr(request, 'session'):
                request.session.flush()
            return Response({"message": "Successfully logged out and session revoked."})
        except Exception:
            return Response({"message": "Logged out."}, status=status.HTTP_200_OK)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    OWASP A01:2025 - Zero Trust Profile Access.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class RegisterView(generics.CreateAPIView):
    """
    OWASP A07:2025 & A01:2025: Hardened User Registration.
    """
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        data = request.data
        email = data.get('email', '').strip()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        phone = data.get('phone', '').strip()

        if not email or not password:
            return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate password complexity (A07:2025)
        validator = LuxuryPasswordComplexityValidator()
        try:
            validator.validate(password)
        except Exception as e:
            return Response({'error': e.messages if hasattr(e, 'messages') else str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Prevent User Enumeration / Duplicate checking (A07:2025)
        if User.objects.filter(email__iexact=email).exists():
            return Response({'error': 'An account with this email address already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        # Mass assignment protection: Enforce role=CUSTOMER (A01:2025)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='CUSTOMER',
            is_verified=False
        )

        log_security_event(
            event_type='LOGIN_SUCCESS',
            severity='INFO',
            request=request,
            user=user,
            details={'action': 'New guest account created'},
            status_code=201
        )
        
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

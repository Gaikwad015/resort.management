from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import CustomTokenObtainPairView, UserProfileView, RegisterView, StepUpAuthView, LogoutView

urlpatterns = [
    # JWT Authentication Endpoints
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('auth/step-up/', StepUpAuthView.as_view(), name='auth_step_up'),
    
    # User Profile Endpoints
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('users/me/', UserProfileView.as_view(), name='user_profile'),
]

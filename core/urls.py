from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('guest-dashboard/', views.guest_dashboard, name='guest_dashboard'),
    path('api/v1/security/alerts/', views.SecurityAlertsAPIView.as_view(), name='security_alerts'),
]

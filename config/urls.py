from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Security: In production, the admin URL can be customized via environment
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    
    # API endpoints (versioned)
    path('api/v1/', include('accounts.urls')),
    path('api/v1/', include('rooms.urls')),
    path('api/v1/', include('bookings.urls')),
    path('api/v1/', include('services.urls')),
    path('api/v1/inventory/', include('inventory.urls')),
    path('api/v1/workforce/', include('workforce.urls')),
    path('api/v1/complaints/', include('complaints.urls')),
    path('api/v1/events/', include('events.urls')),
    path('api/v1/concierge/', include('concierge.urls')),
    path('api/v1/analytics/', include('analytics.urls')),
]

# OWASP A10:2025 & A02:2025: Custom error handlers preventing stack trace leakage
handler400 = 'core.views.custom_400_view'
handler403 = 'core.views.custom_403_view'
handler404 = 'core.views.custom_404_view'
handler500 = 'core.views.custom_500_view'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

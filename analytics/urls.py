from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UtilityMeterViewSet, EnergyConsumptionRecordViewSet,
    DailyOperatingExpenseViewSet, RevenueForecastSnapshotViewSet,
    AnalyticsOverviewAPIView, RevenueForecastAPIView, AnalyticsExportCSVView
)

router = DefaultRouter()
router.register(r'utility-meters', UtilityMeterViewSet, basename='utility-meter')
router.register(r'energy-readings', EnergyConsumptionRecordViewSet, basename='energy-reading')
router.register(r'expenses', DailyOperatingExpenseViewSet, basename='expense')
router.register(r'forecasts', RevenueForecastSnapshotViewSet, basename='forecast-snapshot')

urlpatterns = [
    path('overview/', AnalyticsOverviewAPIView.as_view(), name='analytics-overview'),
    path('forecast/', RevenueForecastAPIView.as_view(), name='analytics-forecast'),
    path('export/csv/', AnalyticsExportCSVView.as_view(), name='analytics-export-csv'),
    path('', include(router.urls)),
]

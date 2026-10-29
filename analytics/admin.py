from django.contrib import admin
from .models import UtilityMeter, EnergyConsumptionRecord, DailyOperatingExpense, RevenueForecastSnapshot

@admin.register(UtilityMeter)
class UtilityMeterAdmin(admin.ModelAdmin):
    list_display = ('meter_code', 'utility_type', 'building_wing', 'floor_or_zone', 'daily_alert_threshold', 'is_active')
    list_filter = ('utility_type', 'building_wing')

@admin.register(EnergyConsumptionRecord)
class EnergyConsumptionRecordAdmin(admin.ModelAdmin):
    list_display = ('meter', 'reading_date', 'units_consumed', 'cost_per_unit', 'total_cost', 'recorded_by')
    list_filter = ('reading_date', 'meter__utility_type')

@admin.register(DailyOperatingExpense)
class DailyOperatingExpenseAdmin(admin.ModelAdmin):
    list_display = ('expense_date', 'category', 'amount', 'description', 'recorded_by')
    list_filter = ('category', 'expense_date')

@admin.register(RevenueForecastSnapshot)
class RevenueForecastSnapshotAdmin(admin.ModelAdmin):
    list_display = ('snapshot_date', 'forecast_days', 'projected_revenue', 'projected_occupancy_pct', 'projected_adr', 'projected_revpar')
    list_filter = ('snapshot_date', 'forecast_days')

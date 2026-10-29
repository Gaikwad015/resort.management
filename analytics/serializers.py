from rest_framework import serializers
from .models import UtilityMeter, EnergyConsumptionRecord, DailyOperatingExpense, RevenueForecastSnapshot

class UtilityMeterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UtilityMeter
        fields = '__all__'

class EnergyConsumptionRecordSerializer(serializers.ModelSerializer):
    meter_code = serializers.CharField(source='meter.meter_code', read_only=True)
    utility_type = serializers.CharField(source='meter.get_utility_type_display', read_only=True)

    class Meta:
        model = EnergyConsumptionRecord
        fields = '__all__'
        read_only_fields = ('total_cost', 'created_at')

class DailyOperatingExpenseSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)

    class Meta:
        model = DailyOperatingExpense
        fields = '__all__'
        read_only_fields = ('created_at',)

class RevenueForecastSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = RevenueForecastSnapshot
        fields = '__all__'
        read_only_fields = ('created_at',)

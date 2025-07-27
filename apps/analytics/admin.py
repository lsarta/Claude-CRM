from django.contrib import admin
from .models import DashboardMetric, ReportTemplate


@admin.register(DashboardMetric)
class DashboardMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_type', 'value', 'period_start', 'period_end', 'calculated_at']
    list_filter = ['metric_type', 'period_start', 'calculated_at']
    readonly_fields = ['calculated_at']
    
    def has_add_permission(self, request):
        return False  # Metrics are calculated automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Metrics are immutable once calculated


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'created_by', 'is_public', 'created_at']
    list_filter = ['report_type', 'is_public', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
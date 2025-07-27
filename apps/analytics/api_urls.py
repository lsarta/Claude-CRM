from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'metrics', api_views.DashboardMetricViewSet)
router.register(r'reports', api_views.ReportTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard-data/', api_views.DashboardDataAPIView.as_view(), name='dashboard_data'),
    path('rfm-analysis/', api_views.RFMAnalysisAPIView.as_view(), name='rfm_analysis'),
    path('revenue-trends/', api_views.RevenueTrendsAPIView.as_view(), name='revenue_trends'),
]
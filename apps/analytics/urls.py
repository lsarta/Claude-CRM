from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('donors/', views.DonorAnalyticsView.as_view(), name='donor_analytics'),
    path('events/', views.EventAnalyticsView.as_view(), name='event_analytics'),
    path('communications/', views.CommunicationAnalyticsView.as_view(), name='communication_analytics'),
    path('financial/', views.FinancialAnalyticsView.as_view(), name='financial_analytics'),
    
    # RFM Analysis
    path('rfm/', views.RFMAnalysisView.as_view(), name='rfm_analysis'),
    path('rfm/update/', views.update_rfm_scores, name='update_rfm_scores'),
    
    # Custom reports
    path('reports/', views.ReportListView.as_view(), name='report_list'),
    path('reports/create/', views.ReportCreateView.as_view(), name='report_create'),
    path('reports/<uuid:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('reports/<uuid:pk>/run/', views.RunReportView.as_view(), name='run_report'),
    
    # Export
    path('export/dashboard/', views.export_dashboard_data, name='export_dashboard'),
    path('export/report/<uuid:pk>/', views.export_report_data, name='export_report'),
    
    # API endpoints for charts
    path('api/revenue-trends/', views.revenue_trends_api, name='api_revenue_trends'),
    path('api/donor-segments/', views.donor_segments_api, name='api_donor_segments'),
    path('api/event-attendance/', views.event_attendance_api, name='api_event_attendance'),
    path('api/campaign-performance/', views.campaign_performance_api, name='api_campaign_performance'),
]
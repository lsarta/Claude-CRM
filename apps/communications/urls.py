from django.urls import path
from . import views

app_name = 'communications'

urlpatterns = [
    path('', views.CommunicationListView.as_view(), name='list'),
    path('create/', views.CommunicationCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.CommunicationDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.CommunicationUpdateView.as_view(), name='edit'),
    path('<uuid:pk>/delete/', views.CommunicationDeleteView.as_view(), name='delete'),
    
    # Email campaigns
    path('campaigns/', views.EmailCampaignListView.as_view(), name='campaign_list'),
    path('campaigns/create/', views.EmailCampaignCreateView.as_view(), name='campaign_create'),
    path('campaigns/<uuid:pk>/', views.EmailCampaignDetailView.as_view(), name='campaign_detail'),
    path('campaigns/<uuid:pk>/send/', views.send_campaign, name='send_campaign'),
    path('campaigns/<uuid:pk>/preview/', views.CampaignPreviewView.as_view(), name='campaign_preview'),
    
    # Templates
    path('templates/', views.EmailTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.EmailTemplateCreateView.as_view(), name='template_create'),
    path('templates/<uuid:pk>/', views.EmailTemplateDetailView.as_view(), name='template_detail'),
    path('templates/<uuid:pk>/edit/', views.EmailTemplateUpdateView.as_view(), name='template_edit'),
    
    # Automated workflows
    path('workflows/', views.AutomatedWorkflowListView.as_view(), name='workflow_list'),
    path('workflows/create/', views.AutomatedWorkflowCreateView.as_view(), name='workflow_create'),
    path('workflows/<uuid:pk>/', views.AutomatedWorkflowDetailView.as_view(), name='workflow_detail'),
    
    # Contact communications
    path('contact/<uuid:contact_id>/', views.ContactCommunicationView.as_view(), name='contact_communications'),
    path('contact/<uuid:contact_id>/add/', views.AddCommunicationView.as_view(), name='add_communication'),
    
    # Unsubscribe
    path('unsubscribe/<str:token>/', views.UnsubscribeView.as_view(), name='unsubscribe'),
    path('unsubscribe/<str:token>/confirm/', views.ConfirmUnsubscribeView.as_view(), name='confirm_unsubscribe'),
    
    # Email tracking
    path('track/open/<uuid:communication_id>/', views.track_email_open, name='track_open'),
    path('track/click/<uuid:communication_id>/', views.track_email_click, name='track_click'),
    
    # Reports
    path('reports/engagement/', views.EngagementReportView.as_view(), name='engagement_report'),
    path('reports/campaigns/', views.CampaignPerformanceReportView.as_view(), name='campaign_performance'),
]
from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.TransactionListView.as_view(), name='list'),
    path('create/', views.TransactionCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.TransactionDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.TransactionUpdateView.as_view(), name='edit'),
    path('<uuid:pk>/delete/', views.TransactionDeleteView.as_view(), name='delete'),
    
    # Donation processing
    path('donate/', views.DonationFormView.as_view(), name='donate'),
    path('recurring/create/', views.RecurringDonationCreateView.as_view(), name='recurring_create'),
    path('recurring/<uuid:pk>/cancel/', views.cancel_recurring_donation, name='recurring_cancel'),
    
    # Receipts
    path('<uuid:pk>/receipt/', views.TaxReceiptView.as_view(), name='receipt'),
    path('receipts/annual/<int:year>/', views.AnnualReceiptView.as_view(), name='annual_receipt'),
    path('receipts/generate/', views.BulkReceiptGenerationView.as_view(), name='bulk_receipts'),
    
    # Campaigns
    path('campaigns/', views.CampaignListView.as_view(), name='campaign_list'),
    path('campaigns/create/', views.CampaignCreateView.as_view(), name='campaign_create'),
    path('campaigns/<uuid:pk>/', views.CampaignDetailView.as_view(), name='campaign_detail'),
    
    # Pledges
    path('pledges/', views.PledgeListView.as_view(), name='pledge_list'),
    path('pledges/create/', views.PledgeCreateView.as_view(), name='pledge_create'),
    path('pledges/<uuid:pk>/', views.PledgeDetailView.as_view(), name='pledge_detail'),
    path('pledges/<uuid:pk>/payment/', views.PledgePaymentView.as_view(), name='pledge_payment'),
    
    # Reports
    path('reports/giving/', views.GivingReportView.as_view(), name='giving_report'),
    path('reports/retention/', views.DonorRetentionReportView.as_view(), name='retention_report'),
    path('reports/campaign/', views.CampaignReportView.as_view(), name='campaign_report'),
    
    # Export
    path('export/transactions/', views.TransactionExportView.as_view(), name='export_transactions'),
    path('export/donors/', views.DonorExportView.as_view(), name='export_donors'),
]
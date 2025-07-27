from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'transactions', api_views.TransactionViewSet)
router.register(r'campaigns', api_views.CampaignViewSet)
router.register(r'pledges', api_views.PledgeViewSet)
router.register(r'recurring', api_views.RecurringDonationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('donation-stats/', api_views.DonationStatsAPIView.as_view(), name='donation_stats'),
    path('campaign-performance/', api_views.CampaignPerformanceAPIView.as_view(), name='campaign_performance'),
]
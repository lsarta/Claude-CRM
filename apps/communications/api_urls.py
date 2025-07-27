from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'communications', api_views.CommunicationViewSet)
router.register(r'campaigns', api_views.EmailCampaignViewSet)
router.register(r'templates', api_views.EmailTemplateViewSet)
router.register(r'workflows', api_views.AutomatedWorkflowViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('engagement-stats/', api_views.EngagementStatsAPIView.as_view(), name='engagement_stats'),
    path('send-test-email/', api_views.SendTestEmailAPIView.as_view(), name='send_test_email'),
]
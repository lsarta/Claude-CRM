from django.urls import path, include
from rest_framework.routers import DefaultRouter

# API router for REST endpoints
router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('contacts/', include('apps.contacts.api_urls')),
    path('events/', include('apps.events.api_urls')),
    path('transactions/', include('apps.transactions.api_urls')),
    path('communications/', include('apps.communications.api_urls')),
    path('analytics/', include('apps.analytics.api_urls')),
]
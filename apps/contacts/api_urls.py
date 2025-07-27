from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'contacts', api_views.ContactViewSet)
router.register(r'relationships', api_views.ContactRelationshipViewSet)
router.register(r'tags', api_views.ContactTagViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('search/', api_views.ContactSearchAPIView.as_view(), name='contact_search'),
    path('bulk-update/', api_views.ContactBulkUpdateAPIView.as_view(), name='bulk_update'),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'events', api_views.EventViewSet)
router.register(r'venues', api_views.VenueViewSet)
router.register(r'attendance', api_views.EventAttendanceViewSet)
router.register(r'series', api_views.EventSeriesViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('calendar/', api_views.EventCalendarAPIView.as_view(), name='event_calendar'),
    path('upcoming/', api_views.UpcomingEventsAPIView.as_view(), name='upcoming_events'),
]
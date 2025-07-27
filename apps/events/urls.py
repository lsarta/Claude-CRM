from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.EventListView.as_view(), name='list'),
    path('create/', views.EventCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.EventDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.EventUpdateView.as_view(), name='edit'),
    path('<uuid:pk>/delete/', views.EventDeleteView.as_view(), name='delete'),
    
    # Event management
    path('<uuid:pk>/attendance/', views.EventAttendanceView.as_view(), name='attendance'),
    path('<uuid:pk>/check-in/', views.EventCheckInView.as_view(), name='check_in'),
    path('<uuid:pk>/authors/', views.EventAuthorView.as_view(), name='authors'),
    
    # Registration
    path('<uuid:pk>/register/', views.EventRegistrationView.as_view(), name='register'),
    path('registration/<uuid:pk>/cancel/', views.cancel_registration, name='cancel_registration'),
    
    # Series management
    path('series/', views.EventSeriesListView.as_view(), name='series_list'),
    path('series/create/', views.EventSeriesCreateView.as_view(), name='series_create'),
    path('series/<uuid:pk>/', views.EventSeriesDetailView.as_view(), name='series_detail'),
    
    # Venues
    path('venues/', views.VenueListView.as_view(), name='venue_list'),
    path('venues/create/', views.VenueCreateView.as_view(), name='venue_create'),
    path('venues/<uuid:pk>/', views.VenueDetailView.as_view(), name='venue_detail'),
    
    # Reports
    path('reports/attendance/', views.AttendanceReportView.as_view(), name='attendance_report'),
    path('reports/revenue/', views.EventRevenueReportView.as_view(), name='revenue_report'),
]
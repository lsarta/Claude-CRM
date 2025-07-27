from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    path('', views.ContactListView.as_view(), name='list'),
    path('create/', views.ContactCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.ContactDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.ContactUpdateView.as_view(), name='edit'),
    path('<uuid:pk>/delete/', views.ContactDeleteView.as_view(), name='delete'),
    
    # AJAX endpoints
    path('ajax/search/', views.contact_search_ajax, name='ajax_search'),
    path('ajax/quick-create/', views.contact_quick_create_ajax, name='ajax_quick_create'),
    path('<uuid:pk>/ajax/update-rfm/', views.update_rfm_ajax, name='ajax_update_rfm'),
    
    # Bulk operations
    path('bulk/export/', views.ContactExportView.as_view(), name='bulk_export'),
    path('bulk/import/', views.ContactImportView.as_view(), name='bulk_import'),
    path('bulk/tag/', views.ContactBulkTagView.as_view(), name='bulk_tag'),
    
    # Relationships
    path('<uuid:pk>/relationships/', views.ContactRelationshipView.as_view(), name='relationships'),
    
    # Tags
    path('tags/', views.ContactTagListView.as_view(), name='tag_list'),
    path('tags/create/', views.ContactTagCreateView.as_view(), name='tag_create'),
]
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='home'),
    path('dashboard/', include('apps.analytics.urls')),
    path('contacts/', include('apps.contacts.urls')),
    path('events/', include('apps.events.urls')),
    path('transactions/', include('apps.transactions.urls')),
    path('communications/', include('apps.communications.urls')),
    path('users/', include('apps.users.urls')),
    path('api/', include('make_crm.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
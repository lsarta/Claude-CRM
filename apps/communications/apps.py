from django.apps import AppConfig


class CommunicationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.communications'
    verbose_name = 'Communications Management'
    
    def ready(self):
        """Import signal handlers when the app is ready"""
        import apps.communications.signals
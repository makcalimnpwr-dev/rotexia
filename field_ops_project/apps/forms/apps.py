from django.apps import AppConfig

class FormsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # ESKİSİ: name = 'forms'
    # YENİSİ (Doğrusu):
    name = 'apps.forms'
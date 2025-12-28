from django.apps import AppConfig

class FieldOperationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # BURASI DEĞİŞTİ: Başına 'apps.' ekledik
    name = 'apps.field_operations'
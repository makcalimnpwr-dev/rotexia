from django.apps import AppConfig

class CustomersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.customers' # <-- Burası 'customers' idi, başına 'apps.' ekledik.
    verbose_name = "Müşteri Yönetimi"
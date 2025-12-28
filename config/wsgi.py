import os
from django.core.wsgi import get_wsgi_application

# 'config' yerine proje klasörünün adı neyse o yazmalı (genelde config veya proje adı olur)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
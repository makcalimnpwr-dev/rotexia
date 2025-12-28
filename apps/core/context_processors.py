from .models import SiteSetting

def site_settings(request):
    """
    Tüm template'lere 'settings' değişkenini gönderir.
    Böylece base.html içinde {{ settings.primary_color }} diyebiliriz.
    """
    return {'settings': SiteSetting.load()}
from .models import SiteSetting

def site_settings(request):
    """تنظیمات سایت در همه تمپلیت‌ها در دسترس"""
    return {'site': SiteSetting.load()}

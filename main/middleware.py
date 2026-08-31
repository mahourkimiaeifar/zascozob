from django.shortcuts import render
from django.conf import settings


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # اگر حالت تعمیر فعال است و کاربر ادمین نیست
        if hasattr(settings, 'MAINTENANCE_MODE') and settings.MAINTENANCE_MODE:
            if not request.user.is_staff:
                return render(request, 'main/maintenance.html', status=503)
        
        response = self.get_response(request)
        return response
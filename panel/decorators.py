from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def permission_required(permission_code):
    """
    دکوراتور بررسی دسترسی بر اساس نقش
    
    استفاده:
    @permission_required('can_add_article')
    def my_view(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # سوپریوزر همه دسترسی‌ها رو داره
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # بررسی نقش کاربر
            if hasattr(request.user, 'profile') and request.user.profile.has_permission(permission_code):
                return view_func(request, *args, **kwargs)
            
            messages.error(request, '❌ شما دسترسی لازم برای انجام این کار را ندارید.')
            return redirect('panel:dashboard')
        
        return wrapper
    return decorator
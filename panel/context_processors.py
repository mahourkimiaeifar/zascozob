from blog.models import Comment
from main.models import CustomRole

def panel_badges(request):
    """تعداد کامنت‌های در انتظار تایید برای بج سایدبار"""
    if not (request.user.is_authenticated and request.user.is_staff):
        return {}
    return {
        'pending_comments': Comment.objects.filter(approved=False, is_deleted=False).count(),
    }

def user_permissions(request):
    """
    دسترسی‌های کاربر فعلی را به عنوان یک شی به تمپلیت‌ها اضافه می‌کند.
    
    استفاده در تمپلیت:
        {% if user_perms.can_add_article %}...{% endif %}
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {'user_perms': UserPermissions(set())}
    
    # سوپریوزر همه دسترسی‌ها را دارد
    if request.user.is_superuser:
        all_perms = {code for code, _ in CustomRole.ALL_PERMISSIONS}
        return {'user_perms': UserPermissions(all_perms)}
    
    # کاربران عادی فقط دسترسی‌های نقش‌شان را دارند
    if hasattr(request.user, 'profile') and request.user.profile.role:
        perms = set(request.user.profile.role.permissions)
        return {'user_perms': UserPermissions(perms)}
    
    return {'user_perms': UserPermissions(set())}


class UserPermissions:
    """کلاس کمکی برای دسترسی آسان به پرمیشن‌ها در تمپلیت"""
    def __init__(self, perms_set):
        self._perms = perms_set
    
    def __getattr__(self, name):
        # هر ویژگی‌ای که بخواهی، چک می‌شود
        return name in self._perms
    
    def __bool__(self):
        return bool(self._perms)
    
    def has(self, permission_code):
        """متد برای چک صریح: {% if user_perms.has 'can_add_article' %}"""
        return permission_code in self._perms
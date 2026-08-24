from blog.models import Comment

def panel_badges(request):
    """تعداد کامنت‌های در انتظار تایید برای بج سایدبار"""
    if not (request.user.is_authenticated and request.user.is_staff):
        return {}
    return {
        'pending_comments': Comment.objects.filter(approved=False, is_deleted=False).count(),
    }
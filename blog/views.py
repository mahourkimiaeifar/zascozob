from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Count
from .models import Post, Category, Comment, VoteRecord
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def post_list(request):
    posts_qs = Post.objects.filter(published=True, is_deleted=False).select_related('category').order_by('-publish_date')
    categories = Category.objects.all()

    search_query = request.GET.get('q', '').strip()
    current_category = request.GET.get('category', '').strip()

    if search_query:
        posts_qs = posts_qs.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query) | Q(excerpt__icontains=search_query))
    if current_category:
        posts_qs = posts_qs.filter(category__slug=current_category)

    # ═══ صفحه‌بندی: ۶ مقاله در هر صفحه ═══
    paginator = Paginator(posts_qs, 6)
    try:
        posts = paginator.page(request.GET.get('page'))
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    # حفظ فیلترها در لینک‌های صفحه‌بندی
    params = request.GET.copy()
    params.pop('page', None)
    extra_get = params.urlencode()
    if extra_get:
        extra_get += '&'

    return render(request, 'main_pages/post_list.html', {
        'posts': posts,
        'categories': categories,
        'search_query': search_query,
        'current_category': current_category,
        'extra_get': extra_get,
    })
    posts = Post.objects.filter(published=True, is_deleted=False).select_related('category')
    categories = Category.objects.filter(posts__published=True).distinct()
    category_slug = request.GET.get('category')
    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    search_query = request.GET.get('q', '').strip()
    if search_query:
        posts = posts.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))
    return render(request, 'main_pages/post_list.html', {
        'posts': posts,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search_query,
    })


def post_detail(request, slug):
    # ═══ ۱) گرفتن پست ═══
    post = get_object_or_404(Post, slug=slug, published=True, is_deleted=False)

    # ═══ ۲) کامنت‌های ابتدایی و پست‌های مرتبط ═══
    comments = post.comments.filter(approved=True, is_deleted=False)[:5]
    related_posts = Post.objects.filter(
        category=post.category, published=True, is_deleted=False
    ).exclude(id=post.id)[:3] if post.category else []

    # ═══ ) آخرین مقالات ═══
    latest_posts = Post.objects.filter(
        published=True, is_deleted=False
    ).exclude(id=post.id).order_by('-publish_date')[:4]

    # ═══ دسته‌بندی‌های سایدبار (شمارش ضدخطا) ═══
    sidebar_categories = []
    for cat in Category.objects.all():
        num = cat.posts.filter(published=True, is_deleted=False).count()
        if num > 0:
            cat.num_posts = num
            sidebar_categories.append(cat)
    
    # ═══ ۵) شمارنده بازدید ═══
    if not request.session.get(f'viewed_post_{post.id}'):
        post.views += 1
        post.save(update_fields=['views'])
        request.session[f'viewed_post_{post.id}'] = True

    # ═══ ۶) وضعیت رأی‌های کاربر ═══
    user_likes_comments = set()
    user_dislikes_comments = set()
    for c in comments:
        v = get_existing_vote(request, 'comment', c.id)
        if v:
            if v.vote_type == 'like':
                user_likes_comments.add(c.id)
            else:
                user_dislikes_comments.add(c.id)

    post_vote = get_existing_vote(request, 'post', post.id)
    post_user_voted = (post_vote and post_vote.vote_type == 'like')

    # ═══ ۷) ارسال به تمپلیت ═══
    return render(request, 'main_pages/post_detail.html', {
        'post': post,
        'comments': comments,
        'related_posts': related_posts,
        'latest_posts': latest_posts,
        'sidebar_categories': sidebar_categories,   # ← حتماً باشه
        'total_comments': post.comments.filter(approved=True, is_deleted=False).count(),
        'user_likes_comments': user_likes_comments,
        'user_dislikes_comments': user_dislikes_comments,
        'post_user_voted': post_user_voted,
    })
    
    latest_posts = Post.objects.filter(published=True, is_deleted=False).exclude(id=post.id).order_by('-publish_date')[:4]
    sidebar_categories = Category.objects.annotate(num_posts=Count('posts')).filter(num_posts__gt=0)
    post = get_object_or_404(Post, slug=slug, published=True, is_deleted=False)
    comments = post.comments.filter(approved=True, is_deleted=False)[:5]
    related_posts = Post.objects.filter(
        category=post.category, published=True, is_deleted=False
    ).exclude(id=post.id)[:3]

    if not request.session.get(f'viewed_post_{post.id}'):
        post.views += 1
        post.save(update_fields=['views'])
        request.session[f'viewed_post_{post.id}'] = True

    # ═══ وضعیت رأی‌های کاربر ═══
    user_likes_comments = set()
    user_dislikes_comments = set()

    for c in comments:
        v = get_existing_vote(request, 'comment', c.id)
        if v:
            if v.vote_type == 'like':
                user_likes_comments.add(c.id)
            else:
                user_dislikes_comments.add(c.id)

    post_vote = get_existing_vote(request, 'post', post.id)
    post_user_voted = (post_vote and post_vote.vote_type == 'like')

    return render(request, 'main_pages/post_detail.html', {
        'post': post,
        'comments': comments,
        'related_posts': related_posts,
        'total_comments': post.comments.filter(approved=True, is_deleted=False).count(),
        'user_likes_comments': user_likes_comments,
        'user_dislikes_comments': user_dislikes_comments,
        'post_user_voted': post_user_voted,
        'latest_posts': latest_posts,              
        'sidebar_categories': sidebar_categories,   
    })


@require_POST
def load_more_comments(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    offset = int(request.POST.get('offset', 0))
    comments = post.comments.filter(approved=True, is_deleted=False)[offset:offset + 5]
    data = [{
        'name': c.name, 'text': c.text, 'likes': c.likes, 'dislikes': c.dislikes,
        'created': c.created.strftime('%Y/%m/%d - %H:%M'), 'id': c.id,
    } for c in comments]
    return JsonResponse({
        'comments': data,
        'has_more': post.comments.filter(approved=True, is_deleted=False).count() > offset + 5,
    })


@require_POST
def submit_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    name = request.POST.get('name', '').strip()
    text = request.POST.get('text', '').strip()
    if not name or not text:
        return JsonResponse({'success': False, 'error': 'نام و متن اجباری است'})
    if len(text) < 10:
        return JsonResponse({'success': False, 'error': 'متن باید حداقل ۱۰ کاراکتر باشد'})
    Comment.objects.create(post=post, name=name, text=text)
    return JsonResponse({'success': True, 'message': 'کامنت شما پس از تایید ادمین نمایش داده می‌شود'})



@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    existing = get_existing_vote(request, 'post', post_id)

    if existing:
        if existing.vote_type == 'like':
            return JsonResponse({'success': False, 'error': 'شما قبلاً این مقاله را لایک کرده‌اید'}, status=400)
        # تعویض: dislike → like
        post.dislikes = max(0, post.dislikes - 1)
        post.likes += 1
        post.save(update_fields=['likes', 'dislikes'])
        existing.vote_type = 'like'
        existing.save(update_fields=['vote_type'])
        return JsonResponse({'success': True, 'likes': post.likes})

    # رأی اول
    post.likes += 1
    post.save(update_fields=['likes'])
    create_vote_record(request, 'post', post_id, 'like')
    return JsonResponse({'success': True, 'likes': post.likes})

@require_POST
def like_comment(request, comment_id):
    c = get_object_or_404(Comment, id=comment_id)
    existing = get_existing_vote(request, 'comment', comment_id)

    if existing:
        if existing.vote_type == 'like':
            return JsonResponse({'success': False, 'error': 'قبلاً این کامنت را لایک کرده‌اید'}, status=400)
        # تعویض: dislike → like
        c.dislikes = max(0, c.dislikes - 1)
        c.likes += 1
        c.save(update_fields=['likes', 'dislikes'])
        existing.vote_type = 'like'
        existing.save(update_fields=['vote_type'])
        return JsonResponse({'success': True, 'likes': c.likes, 'dislikes': c.dislikes})

    # رأی اول
    c.likes += 1
    c.save(update_fields=['likes'])
    create_vote_record(request, 'comment', comment_id, 'like')
    return JsonResponse({'success': True, 'likes': c.likes, 'dislikes': c.dislikes})



@require_POST
def dislike_comment(request, comment_id):
    c = get_object_or_404(Comment, id=comment_id)
    existing = get_existing_vote(request, 'comment', comment_id)

    if existing:
        if existing.vote_type == 'dislike':
            return JsonResponse({'success': False, 'error': 'قبلاً این کامنت را دیسلایک کرده‌اید'}, status=400)
        # تعویض: like → dislike
        c.likes = max(0, c.likes - 1)
        c.dislikes += 1
        c.save(update_fields=['likes', 'dislikes'])
        existing.vote_type = 'dislike'
        existing.save(update_fields=['vote_type'])
        return JsonResponse({'success': True, 'likes': c.likes, 'dislikes': c.dislikes})

    # رأی اول
    c.dislikes += 1
    c.save(update_fields=['dislikes'])
    create_vote_record(request, 'comment', comment_id, 'dislike')
    return JsonResponse({'success': True, 'likes': c.likes, 'dislikes': c.dislikes})


def get_client_ip(request):
    """گرفتن IP واقعی کاربر (با proxy)"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def get_existing_vote(request, target_type, target_id):
    """
    رکورد رأی قبلی کاربر رو پیدا می‌کنه (مهم نیست like بوده یا dislike)
    برمی‌گردونه VoteRecord یا None
    """
    ip = get_client_ip(request)
    session_key = request.session.session_key

    base_filter = Q(target_type=target_type, target_id=target_id)

    if request.user.is_authenticated:
        return VoteRecord.objects.filter(base_filter, user=request.user).first()

    # غیرلاگین: IP یا session
    ip_or_session = Q(ip_address=ip)
    if session_key:
        ip_or_session |= Q(session_key=session_key)

    return VoteRecord.objects.filter(base_filter).filter(ip_or_session).first()

def create_vote_record(request, target_type, target_id, vote_type):
    """رکورد رأی جدید می‌سازه"""
    ip = get_client_ip(request)
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key or ''

    if request.user.is_authenticated:
        VoteRecord.objects.create(
            user=request.user,
            target_type=target_type,
            target_id=target_id,
            vote_type=vote_type,
        )
    else:
        VoteRecord.objects.create(
            ip_address=ip,
            session_key=session_key,
            target_type=target_type,
            target_id=target_id,
            vote_type=vote_type,
        )
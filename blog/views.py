from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Post, Category, Comment


def post_list(request):
    """صفحه اصلی بلاگ — لیست مقالات"""
    posts = Post.objects.filter(published=True, is_deleted=False).select_related('category')
    categories = Category.objects.filter(posts__published=True).distinct()
    
    # فیلتر بر اساس دسته‌بندی
    category_slug = request.GET.get('category')
    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    
    # جستجو
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
    """صفحه تک مقاله"""
    post = get_object_or_404(Post, slug=slug, published=True, is_deleted=False)
    
    # کامنت‌های تایید شده
    comments = post.comments.filter(approved=True, is_deleted=False)[:5]  # ۵ تا اول
    
    # پست‌های مرتبط (هم دسته‌بندی)
    related_posts = Post.objects.filter(
        category=post.category,
        published=True,
        is_deleted=False
    ).exclude(id=post.id)[:3]
    
    # افزایش views
    if not request.session.get(f'viewed_post_{post.id}'):
        post.views += 1
        post.save(update_fields=['views'])
        request.session[f'viewed_post_{post.id}'] = True
    
    return render(request, 'main_pages/post_detail.html', {
        'post': post,
        'comments': comments,
        'related_posts': related_posts,
        'total_comments': post.comments.filter(approved=True, is_deleted=False).count(),
    })


@require_POST
def load_more_comments(request, post_id):
    """لود کامنت‌های بیشتر"""
    post = get_object_or_404(Post, id=post_id)
    offset = int(request.POST.get('offset', 0))
    limit = 5
    
    comments = post.comments.filter(approved=True, is_deleted=False)[offset:offset + limit]
    
    comments_data = []
    for comment in comments:
        comments_data.append({
            'name': comment.name,
            'text': comment.text,
            'likes': comment.likes,
            'dislikes': comment.dislikes,
            'created': comment.created.strftime('%Y/%m/%d - %H:%M'),
            'id': comment.id,
        })
    
    return JsonResponse({
        'comments': comments_data,
        'has_more': post.comments.filter(approved=True, is_deleted=False).count() > offset + limit,
    })


@require_POST
def submit_comment(request, post_id):
    """ثبت کامنت جدید"""
    post = get_object_or_404(Post, id=post_id)
    name = request.POST.get('name', '').strip()
    text = request.POST.get('text', '').strip()
    
    if not name or not text:
        return JsonResponse({'success': False, 'error': 'نام و متن کامنت اجباری است'})
    
    if len(text) < 10:
        return JsonResponse({'success': False, 'error': 'متن کامنت باید حداقل ۱۰ کاراکتر باشد'})
    
    Comment.objects.create(post=post, name=name, text=text)
    return JsonResponse({'success': True, 'message': 'کامنت شما پس از تایید ادمین نمایش داده خواهد شد'})


@require_POST
def like_post(request, post_id):
    """لایک مقاله"""
    post = get_object_or_404(Post, id=post_id)
    post.likes += 1
    post.save(update_fields=['likes'])
    return JsonResponse({'success': True, 'likes': post.likes})


@require_POST
def like_comment(request, comment_id):
    """لایک کامنت"""
    comment = get_object_or_404(Comment, id=comment_id)
    comment.likes += 1
    comment.save(update_fields=['likes'])
    return JsonResponse({'success': True, 'likes': comment.likes})


@require_POST
def dislike_comment(request, comment_id):
    """دیسلایک کامنت"""
    comment = get_object_or_404(Comment, id=comment_id)
    comment.dislikes += 1
    comment.save(update_fields=['dislikes'])
    return JsonResponse({'success': True, 'dislikes': comment.dislikes})
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Post, Category, Comment


def post_list(request):
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
    post = get_object_or_404(Post, slug=slug, published=True, is_deleted=False)
    comments = post.comments.filter(approved=True, is_deleted=False)[:5]
    related_posts = Post.objects.filter(
        category=post.category, published=True, is_deleted=False
    ).exclude(id=post.id)[:3]
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
    post.likes += 1
    post.save(update_fields=['likes'])
    return JsonResponse({'success': True, 'likes': post.likes})


@require_POST
def like_comment(request, comment_id):
    c = get_object_or_404(Comment, id=comment_id)
    c.likes += 1
    c.save(update_fields=['likes'])
    return JsonResponse({'success': True, 'likes': c.likes})


@require_POST
def dislike_comment(request, comment_id):
    c = get_object_or_404(Comment, id=comment_id)
    c.dislikes += 1
    c.save(update_fields=['dislikes'])
    return JsonResponse({'success': True, 'dislikes': c.dislikes})

@require_POST
def vote_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    ip = request.META.get('REMOTE_ADDR')
        
    vote_type = request.POST.get('vote_type')

    if vote_type not in ['like', 'dislike']:
        return JsonResponse({'error': 'Invalid vote type'}, status=400)

    existing_vote = CommentVote.objects.filter(comment=comment, ip_address=ip).first()
    
    if existing_vote:
        likes = comment.votes.filter(vote_type='like').count()
        dislikes = comment.votes.filter(vote_type='dislike').count()
        return JsonResponse({
            'likes': likes,
            'dislikes': dislikes,
            'message': 'شما قبلاً به این کامنت رای داده‌اید.'
        })

    CommentVote.objects.create(comment=comment, ip_address=ip, vote_type=vote_type)
    
    likes = comment.votes.filter(vote_type='like').count()
    dislikes = comment.votes.filter(vote_type='dislike').count()

    return JsonResponse({
        'likes': likes,
        'dislikes': dislikes,
        'message': 'رای شما با موفقیت ثبت شد.'
    })
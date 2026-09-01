import time
import os
import jdatetime
from datetime import datetime
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.views.decorators.http import require_POST
from main.models import (ContactMessage, ReplyAttachment, SiteSetting, MediaFile, CustomRole, UserProfile, AuditLog)
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from blog.models import Post, Category, Comment
from django.utils.text import slugify
from panel.forms import PostForm
from django.db.models import Q, Count
from portfolio.models import PortfolioItem, PortfolioCategory
from portfolio.forms import PortfolioItemForm
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import InMemoryUploadedFile
from gallery.models import GalleryAlbum, GalleryImage
from gallery.utils import add_watermark_and_compress
from gallery.forms import GalleryAlbumForm, MultipleImageUploadForm
from django.core.cache import cache
from main.utils import register_file_in_library, log_activity
from panel.decorators import permission_required


# ═══ ورود و خروج ═══
def panel_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('panel:dashboard')
    lock = _check_lockout(request)
    if lock['locked']:
        return render(request, 'main_pages/panel/login.html', {'locked': True, 'wait_minutes': lock['wait_minutes']})
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        attempts = request.session.get('login_attempts', 0)
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            request.session['login_attempts'] = 0
            # 📝 لاگ ورود
            log_activity(request, 'ورود موفق به پنل', 'User', user.id, f'کاربر {user.username} وارد شد')
            return redirect('panel:dashboard')
        request.session['login_attempts'] = attempts + 1
        remaining = 5 - (attempts + 1)
        if remaining <= 0:
            request.session['locked_until'] = time.time() + 1800
            # 📝 لاگ تلاش ناموفق مکرر
            log_activity(request, f'تلاش ناموفق مکرر برای ورود (قفل شد)', 'User', None, f'نام کاربری: {username}')
            return render(request, 'main_pages/panel/login.html', {'locked': True, 'wait_minutes': 30})
        messages.error(request, f'نام کاربری یا رمز اشتباه است. {remaining} تلاش باقی‌مانده.')
    return render(request, 'main_pages/panel/login.html')


def panel_logout(request):
    # 📝 لاگ خروج (قبل از logout که user از دست نره)
    if request.user.is_authenticated:
        log_activity(request, 'خروج از پنل', 'User', request.user.id, f'کاربر {request.user.username} خارج شد')
    logout(request)
    return redirect('panel:login')


def _check_lockout(request):
    locked_until = request.session.get('locked_until', 0)
    now = time.time()
    if locked_until > now:
        return {'locked': True, 'wait_minutes': int((locked_until - now) / 60) + 1}
    if locked_until > 0:
        request.session.pop('locked_until', None)
        request.session['login_attempts'] = 0
    return {'locked': False, 'wait_minutes': 0}


# ═══ داشبورد ═══
@login_required
def dashboard(request):
    if not request.user.is_staff:
        return redirect('panel:login')
    return render(request, 'main_pages/panel/dashboard.html', {
        'total_messages': ContactMessage.objects.count(),
        'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
        'answered_messages': ContactMessage.objects.filter(is_read=True).count(),
        'attachments_count': ContactMessage.objects.exclude(attachment='').exclude(attachment=None).count(),
        'recent_messages': ContactMessage.objects.all()[:5],
    })


# ═══ پیام‌های تماس ═══
@login_required
def main_contact(request):
    if not request.user.is_staff:
        return redirect('panel:login')

    messages_list = []
    for msg in ContactMessage.objects.all().order_by('-created_at'):
        created = timezone.localtime(msg.created_at)
        created_jd = jdatetime.datetime.fromgregorian(datetime=created)
        replied_jd = None
        if msg.replied_at:
            replied = timezone.localtime(msg.replied_at)
            replied_jd = jdatetime.datetime.fromgregorian(datetime=replied)
        messages_list.append({
            'id': msg.id, 'name': msg.name, 'email': msg.email, 'phone': msg.phone,
            'message': msg.message, 'attachment': msg.attachment, 'is_read': msg.is_read,
            'reply_subject': msg.reply_subject, 'reply_body': msg.reply_body,
            'reply_attachments': msg.reply_attachments.all(),
            'created_date': created_jd.strftime('%Y/%m/%d'),
            'created_time': created.strftime('%H:%M'),
            'replied_date': replied_jd.strftime('%Y/%m/%d') if replied_jd else None,
            'replied_time': replied.strftime('%H:%M') if replied_jd else None,
        })

    paginator = Paginator(messages_list, 10)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return render(request, 'main_pages/main/contact.html', {
        'messages_list': page_obj.object_list,
        'messages_count': paginator.count,
        'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
        'page_obj': page_obj,
    })


@login_required
@require_POST
@permission_required('can_reply_messages')
def main_contact_reply(request):
    try:
        msg = ContactMessage.objects.get(id=request.POST.get('message_id'))
    except ContactMessage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'پیام یافت نشد'})

    subject = request.POST.get('subject', '').strip()
    body = request.POST.get('body', '').strip()
    files = [f for f in request.FILES.getlist('attachments') if f.size <= 10 * 1024 * 1024]

    if not msg.email or not subject or not body:
        return JsonResponse({'success': False, 'error': 'فیلدهای اجباری خالی است'})

    total_size = sum(f.size for f in files)
    if total_size > 15 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': 'مجموع حجم پیوست‌ها نباید بیشتر از ۱۵ مگابایت باشد'})

    try:
        mail = EmailMultiAlternatives(
            subject=subject, body='این ایمیل HTML است.',
            from_email=settings.DEFAULT_FROM_EMAIL, to=[msg.email])
        mail.attach_alternative(body, "text/html")
        for f in files:
            mail.attach(f.name, f.read(), f.content_type)

        last_error = None
        for attempt in range(3):
            try:
                mail.send()
                last_error = None
                break
            except Exception as e:
                last_error = e
                time.sleep(2)
        if last_error:
            print('=' * 60)
            print('❌ EMAIL ERROR:', type(last_error).__name__, str(last_error))
            print('=' * 60)
            return JsonResponse({'success': False, 'error': str(last_error)})
        msg.is_read = True
        msg.reply_subject = subject
        msg.reply_body = body
        msg.replied_at = timezone.now()
        msg.save()
        for f in files:
            ReplyAttachment.objects.create(message=msg, file=f)
        # 📝 لاگ پاسخ پیام
        log_activity(request, 'پاسخ ایمیل به پیام', 'ContactMessage', msg.id, f'پاسخ به {msg.name} - موضوع: {subject}')
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def mark_read(request, pk):
    if not request.user.is_staff:
        return JsonResponse({'success': False}, status=403)
    ContactMessage.objects.filter(id=pk).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
@require_POST
def delete_message(request, pk):
    if not request.user.is_staff:
        return JsonResponse({'success': False}, status=403)
    try:
        msg = ContactMessage.objects.get(id=pk)
        msg_name = msg.name
        if msg.attachment:
            try: os.remove(msg.attachment.path)
            except Exception: pass
        msg.delete()
        # 📝 لاگ حذف پیام
        log_activity(request, 'حذف پیام تماس', 'ContactMessage', pk, f'پیام از طرف {msg_name}')
        return JsonResponse({'success': True})
    except ContactMessage.DoesNotExist:
        return JsonResponse({'success': False})


# ═══ تنظیمات سایت ═══
@login_required
@permission_required('can_manage_settings')
def site_settings(request):
    from django import forms

    class SettingsForm(forms.ModelForm):
        class Meta:
            model = SiteSetting
            fields = '__all__'
            widgets = {
                'about_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
                'address_factory': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
                'address_rd': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
                'footer_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
                'copyright_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            }

    setting = SiteSetting.load()
    if request.method == 'POST':
        form = SettingsForm(request.POST, request.FILES, instance=setting)
        if form.is_valid():
            form.save()
            # 📝 لاگ تغییر تنظیمات
            log_activity(request, 'تغییر تنظیمات سایت', 'SiteSetting', 1)
            messages.success(request, '✅ تنظیمات سایت با موفقیت ذخیره شد')
            return redirect('panel:site_settings')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = SettingsForm(instance=setting)

    return render(request, 'main_pages/main/site_settings.html', {'form': form, 'setting': setting})


# ═══ مدیریت پست‌های بلاگ ═══
@login_required
def blog_post_list(request):
    if not request.user.is_staff:
        return redirect('panel:login')
    posts = Post.objects.all().select_related('category').order_by('-publish_date')
    paginator = Paginator(posts, 10)
    posts = paginator.get_page(request.GET.get('page'))
    return render(request, 'main_pages/blog/post_list.html', {'posts': posts})


@login_required
@permission_required('can_add_article')
def blog_post_add(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            if not post.publish_date and post.published:
                post.publish_date = timezone.now()
            post.save()
            if post.featured_image:
                register_file_in_library(post.featured_image.name, title=post.title,
                                         uploaded_by=request.user, used_in='blog', auto_create=True)
            # 📝 لاگ ایجاد مقاله
            log_activity(request, 'ایجاد مقاله جدید', 'Post', post.id, post.title)
            messages.success(request, 'مقاله با موفقیت اضافه شد.')
            return redirect('panel:blog_post_list')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = PostForm()

    categories = Category.objects.all()
    categories_data = [{'id': c.id, 'title': c.title, 'parent': c.parent_id} for c in categories]
    return render(request, 'main_pages/blog/post_form.html', {
        'form': form, 'post': None, 'categories': categories, 'categories_data': categories_data,
    })


@login_required
@permission_required('can_edit_article')
def blog_post_edit(request, pk):
    post = get_object_or_404(Post, id=pk)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            # 📝 لاگ ویرایش مقاله
            log_activity(request, 'ویرایش مقاله', 'Post', post.id, post.title)
            return redirect('panel:blog_post_list')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = PostForm(instance=post)

    categories = Category.objects.all()
    categories_data = [{'id': c.id, 'title': c.title, 'parent': c.parent_id} for c in categories]
    return render(request, 'main_pages/blog/post_form.html', {
        'form': form, 'post': post, 'categories': categories, 'categories_data': categories_data,
    })


@login_required
@require_POST
@permission_required('can_delete_article')
def blog_post_delete(request, pk):
    try:
        post = Post.objects.get(id=pk)
        post_title = post.title
        post.delete()
        # 📝 لاگ حذف مقاله
        log_activity(request, 'حذف مقاله', 'Post', pk, post_title)
    except Post.DoesNotExist:
        pass
    return JsonResponse({'success': True})


# ═══ مدیریت دسته‌بندی‌های بلاگ ═══
@login_required
def blog_category_list(request):
    if not request.user.is_staff:
        return redirect('panel:login')
    cats = Category.objects.annotate(posts_count=Count('posts')).order_by('-id')
    paginator = Paginator(cats, 10)
    categories = paginator.get_page(request.GET.get('page'))
    return render(request, 'main_pages/blog/category_list.html', {'categories': categories})


@login_required
@permission_required('can_edit_article')
def blog_category_add(request):
    if request.method == 'POST':
        cat = Category()
        cat.title = request.POST.get('title', '').strip()
        cat.slug = slugify(cat.title, allow_unicode=True)
        parent_id = request.POST.get('parent')
        if parent_id:
            cat.parent = Category.objects.get(id=parent_id)
        cat.save()
        # 📝 لاگ ایجاد دسته‌بندی بلاگ
        log_activity(request, 'ایجاد دسته‌بندی بلاگ', 'Category', cat.id, cat.title)
        return redirect('panel:blog_category_list')
    parents = Category.objects.filter(parent=None)
    return render(request, 'main_pages/blog/category_form.html', {'parents': parents})


@login_required
@permission_required('can_edit_article')
def blog_category_edit(request, pk):
    cat = get_object_or_404(Category, id=pk)
    if request.method == 'POST':
        cat.title = request.POST.get('title', '').strip()
        cat.slug = slugify(cat.title, allow_unicode=True)
        parent_id = request.POST.get('parent')
        cat.parent = Category.objects.get(id=parent_id) if parent_id else None
        cat.save()
        # 📝 لاگ ویرایش دسته‌بندی بلاگ
        log_activity(request, 'ویرایش دسته‌بندی بلاگ', 'Category', cat.id, cat.title)
        return redirect('panel:blog_category_list')
    parents = Category.objects.filter(parent=None).exclude(id=pk)
    return render(request, 'main_pages/blog/category_form.html', {'category': cat, 'parents': parents})


@login_required
@require_POST
@permission_required('can_delete_article')
def blog_category_delete(request, pk):
    try:
        cat = Category.objects.get(id=pk)
        cat_title = cat.title
        cat.delete()
        # 📝 لاگ حذف دسته‌بندی بلاگ
        log_activity(request, 'حذف دسته‌بندی بلاگ', 'Category', pk, cat_title)
    except Category.DoesNotExist:
        pass
    return JsonResponse({'success': True})


# ═══ مدیریت کامنت‌ها ═══
@login_required
def blog_comment_list(request):
    if not request.user.is_staff:
        return redirect('panel:login')
    comments = Comment.objects.select_related('post').order_by('-created')
    paginator = Paginator(comments, 10)
    comments = paginator.get_page(request.GET.get('page'))
    return render(request, 'main_pages/blog/comment_list.html', {'comments': comments})


@login_required
@require_POST
@permission_required('can_approve_comments')
def blog_comment_approve(request, pk):
    try:
        c = Comment.objects.get(id=pk)
        c.approve()
        # 📝 لاگ تایید کامنت
        log_activity(request, 'تایید کامنت', 'Comment', pk, f'کامنت از طرف {getattr(c, "author_name", "کاربر")}')
        return JsonResponse({'success': True})
    except Comment.DoesNotExist:
        return JsonResponse({'success': False})


@login_required
@require_POST
@permission_required('can_delete_comments')
def blog_comment_delete(request, pk):
    try:
        c = Comment.objects.get(id=pk)
        author_name = getattr(c, 'author_name', 'کاربر')
    except Comment.DoesNotExist:
        author_name = 'نامشخص'
    Comment.objects.filter(id=pk).delete()
    # 📝 لاگ حذف کامنت
    log_activity(request, 'حذف کامنت', 'Comment', pk, f'کامنت از طرف {author_name}')
    return JsonResponse({'success': True})


# ═══ مدیریت نمونه‌کارها ═══
@login_required
def portfolio_list(request):
    if not request.user.is_staff:
        return redirect('panel:login')
    items = PortfolioItem.objects.select_related('category').order_by('-created')
    paginator = Paginator(items, 10)
    items = paginator.get_page(request.GET.get('page'))
    return render(request, 'main_pages/portfolio/portfolio_list.html', {'items': items})


@login_required
@permission_required('can_add_portfolio')
def portfolio_add(request):
    categories_qs = PortfolioCategory.objects.filter(is_deleted=False).order_by('order', 'title')
    categories_data = [{'id': c.id, 'title': c.title, 'parent': None} for c in categories_qs]

    if request.method == 'POST':
        form = PortfolioItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            cat_id = request.POST.get('category')
            if cat_id:
                item.category = PortfolioCategory.objects.filter(id=cat_id, is_deleted=False).first()
            item.save()
            if item.featured_image:
                register_file_in_library(item.featured_image.name, title=item.title,
                                         uploaded_by=request.user, used_in='portfolio', auto_create=True)
            # 📝 لاگ ایجاد نمونه‌کار
            log_activity(request, 'ایجاد نمونه‌کار جدید', 'PortfolioItem', item.id, item.title)
            messages.success(request, 'نمونه‌کار با موفقیت اضافه شد.')
            return redirect('panel:portfolio_list')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = PortfolioItemForm()

    return render(request, 'main_pages/portfolio/portfolio_form.html', {
        'form': form, 'categories': categories_qs, 'categories_data': categories_data,
    })


@login_required
@permission_required('can_edit_portfolio')
def portfolio_edit(request, pk):
    item = get_object_or_404(PortfolioItem, id=pk, is_deleted=False)
    categories_qs = PortfolioCategory.objects.filter(is_deleted=False).order_by('order', 'title')
    categories_data = [{'id': c.id, 'title': c.title, 'parent': None} for c in categories_qs]

    if request.method == 'POST':
        form = PortfolioItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            cat_id = request.POST.get('category')
            if cat_id:
                item.category = PortfolioCategory.objects.filter(id=cat_id, is_deleted=False).first()
            else:
                item.category = None
            item.save()
            # 📝 لاگ ویرایش نمونه‌کار
            log_activity(request, 'ویرایش نمونه‌کار', 'PortfolioItem', item.id, item.title)
            messages.success(request, 'تغییرات ذخیره شد.')
            return redirect('panel:portfolio_list')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = PortfolioItemForm(instance=item)

    return render(request, 'main_pages/portfolio/portfolio_form.html', {
        'form': form, 'item': item, 'categories': categories_qs, 'categories_data': categories_data,
    })


@login_required
@permission_required('can_delete_portfolio')
def portfolio_delete(request, pk):
    item = get_object_or_404(PortfolioItem, id=pk)
    item_title = item.title
    item.is_deleted = True
    item.save()
    # 📝 لاگ حذف نمونه‌کار
    log_activity(request, 'حذف نمونه‌کار', 'PortfolioItem', pk, item_title)
    messages.success(request, 'نمونه‌کار حذف شد.')
    return redirect('panel:portfolio_list')


@login_required
def portfolio_category_list(request):
    if not request.user.is_staff:
        return redirect('panel:login')
    categories = PortfolioCategory.objects.annotate(
        items_count=Count('items', filter=Q(items__published=True, items__is_deleted=False))
    ).order_by('order', 'title')
    paginator = Paginator(categories, 10)
    categories = paginator.get_page(request.GET.get('page'))
    return render(request, 'main_pages/portfolio/category_list.html', {'categories': categories})


@login_required
@permission_required('can_add_portfolio')
def portfolio_category_add(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            messages.error(request, 'عنوان الزامی است.')
            return redirect('panel:portfolio_category_add')
        cat = PortfolioCategory(
            title=title,
            description=request.POST.get('description', ''),
            order=int(request.POST.get('order', 0) or 0),
        )
        cat.save()
        # 📝 لاگ ایجاد دسته‌بندی نمونه‌کار
        log_activity(request, 'ایجاد دسته‌بندی نمونه‌کار', 'PortfolioCategory', cat.id, cat.title)
        messages.success(request, 'دسته‌بندی اضافه شد.')
        return redirect('panel:portfolio_category_list')
    return render(request, 'main_pages/portfolio/category_form.html')


@login_required
@permission_required('can_edit_portfolio')
def portfolio_category_edit(request, pk):
    cat = get_object_or_404(PortfolioCategory, id=pk)
    if request.method == 'POST':
        cat.title = request.POST.get('title', '').strip() or cat.title
        cat.description = request.POST.get('description', '')
        cat.order = int(request.POST.get('order', 0) or 0)
        cat.save()
        # 📝 لاگ ویرایش دسته‌بندی نمونه‌کار
        log_activity(request, 'ویرایش دسته‌بندی نمونه‌کار', 'PortfolioCategory', cat.id, cat.title)
        messages.success(request, 'تغییرات ذخیره شد.')
        return redirect('panel:portfolio_category_list')
    return render(request, 'main_pages/portfolio/category_form.html', {'cat': cat})


@login_required
@permission_required('can_delete_portfolio')
def portfolio_category_delete(request, pk):
    cat = get_object_or_404(PortfolioCategory, id=pk)
    cat_title = cat.title
    cat.is_deleted = True
    cat.save()
    # 📝 لاگ حذف دسته‌بندی نمونه‌کار
    log_activity(request, 'حذف دسته‌بندی نمونه‌کار', 'PortfolioCategory', pk, cat_title)
    messages.success(request, 'دسته‌بندی حذف شد.')
    return redirect('panel:portfolio_category_list')


# ═══ مدیریت گالری تصاویر ═══
@login_required
def gallery_album_list(request):
    if not request.user.is_staff:
        return redirect('panel:login')
    albums = GalleryAlbum.objects.filter(is_deleted=False).order_by('-created')
    return render(request, 'main_pages/gallery/album_list.html', {'albums': albums})


@login_required
@permission_required('can_add_gallery')
def gallery_album_add(request):
    if request.method == 'POST':
        form = GalleryAlbumForm(request.POST)
        if form.is_valid():
            album = form.save()
            # 📝 لاگ ایجاد آلبوم
            log_activity(request, 'ایجاد آلبوم گالری جدید', 'GalleryAlbum', album.id, album.title)
            messages.success(request, f'آلبوم "{album.title}" با موفقیت ایجاد شد.')
            return redirect('panel:gallery_album_images', album_id=album.id)
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = GalleryAlbumForm()
    return render(request, 'main_pages/gallery/album_form.html', {'form': form})


@login_required
@permission_required('can_edit_gallery')
def gallery_album_edit(request, pk):
    album = get_object_or_404(GalleryAlbum, id=pk, is_deleted=False)
    if request.method == 'POST':
        form = GalleryAlbumForm(request.POST, instance=album)
        if form.is_valid():
            form.save()
            # 📝 لاگ ویرایش آلبوم
            log_activity(request, 'ویرایش آلبوم گالری', 'GalleryAlbum', album.id, album.title)
            messages.success(request, 'آلبوم با موفقیت ویرایش شد.')
            return redirect('panel:gallery_album_list')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = GalleryAlbumForm(instance=album)
    return render(request, 'main_pages/gallery/album_form.html', {'form': form, 'album': album})


@login_required
@permission_required('can_add_gallery')
def gallery_album_images(request, album_id):
    album = get_object_or_404(GalleryAlbum, id=album_id, is_deleted=False)
    images = album.images.filter(is_deleted=False).order_by('order', 'uploaded_at')

    if request.method == 'POST':
        upload_form = MultipleImageUploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            files = request.FILES.getlist('images')
            count = 0
            for f in files:
                try:
                    processed_image = add_watermark_and_compress(f, watermark_text="ZASCO")
                    max_order = album.images.filter(is_deleted=False).count()
                    img = GalleryImage(album=album, order=max_order + 1)
                    img.image.save(
                        f.name,
                        InMemoryUploadedFile(processed_image, None, f.name, 'image/jpeg',
                                             processed_image.getbuffer().nbytes, None),
                        save=False
                    )
                    img.save()
                    count += 1
                except Exception as e:
                    print(f"Error processing {f.name}: {e}")
                    continue
            # 📝 لاگ آپلود تصاویر در آلبوم
            if count > 0:
                log_activity(request, f'آپلود {count} تصویر در آلبوم', 'GalleryImage', album.id, f'آلبوم: {album.title}')
            messages.success(request, f'{count} تصویر با موفقیت آپلود شد.')
            return redirect('panel:gallery_album_images', album_id=album.id)
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        upload_form = MultipleImageUploadForm()

    return render(request, 'main_pages/gallery/album_images.html', {
        'album': album, 'images': images, 'upload_form': upload_form,
    })


@login_required
@permission_required('can_edit_gallery')
def gallery_image_edit(request, pk):
    image = get_object_or_404(GalleryImage, id=pk, is_deleted=False)
    if request.method == 'POST':
        image.title = request.POST.get('title', '')
        image.description = request.POST.get('description', '')
        image.order = int(request.POST.get('order', 0))
        image.save()
        # 📝 لاگ ویرایش تصویر
        log_activity(request, 'ویرایش تصویر گالری', 'GalleryImage', pk, image.title or 'بدون عنوان')
        messages.success(request, 'تصویر با موفقیت ویرایش شد.')
        return redirect('panel:gallery_album_images', album_id=image.album.id)
    return render(request, 'main_pages/gallery/album_edit.html', {'image': image})


@login_required
@permission_required('can_delete_gallery')
def gallery_image_delete(request, pk):
    image = get_object_or_404(GalleryImage, id=pk, is_deleted=False)
    album_id = image.album.id
    album_title = image.album.title
    image_title = image.title or 'بدون عنوان'
    if request.method == 'POST':
        image.is_deleted = True
        image.save()
        # 📝 لاگ حذف تصویر
        log_activity(request, 'حذف تصویر از گالری', 'GalleryImage', pk, f'{image_title} از آلبوم {album_title}')
        messages.success(request, 'تصویر حذف شد.')
        return redirect('panel:gallery_album_images', album_id=album_id)
    return render(request, 'main_pages/gallery/image_delete.html', {'image': image})


@login_required
@permission_required('can_delete_gallery')
def gallery_album_delete(request, pk):
    album = get_object_or_404(GalleryAlbum, id=pk, is_deleted=False)
    album_title = album.title
    if request.method == 'POST':
        album.is_deleted = True
        album.save()
        # 📝 لاگ حذف آلبوم
        log_activity(request, 'حذف آلبوم گالری', 'GalleryAlbum', pk, album_title)
        messages.success(request, 'آلبوم حذف شد.')
        return redirect('panel:gallery_album_list')
    return render(request, 'main_pages/gallery/album_delete.html', {'album': album})


# ═══ کتابخانه فایل‌ها ═══
@login_required
@permission_required('can_manage_media')
def media_library(request):
    files = MediaFile.objects.filter(is_deleted=False).order_by('-uploaded_at')

    file_type = request.GET.get('type', '')
    if file_type:
        files = files.filter(file_type=file_type)

    search = request.GET.get('q', '')
    if search:
        files = files.filter(title__icontains=search)

    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('files')
        count = 0
        for f in uploaded_files:
            MediaFile.objects.create(title=f.name, file=f, uploaded_by=request.user)
            count += 1
        # 📝 لاگ آپلود فایل در کتابخانه
        if count > 0:
            log_activity(request, f'آپلود {count} فایل در کتابخانه', 'MediaFile', None, f'{count} فایل جدید')
        messages.success(request, f'{count} فایل با موفقیت آپلود شد.')
        return redirect('panel:media_library')

    paginator = Paginator(files, 20)
    files_page = paginator.get_page(request.GET.get('page'))
    return render(request, 'main_pages/panel/media/media_library.html', {
        'files': files_page, 'file_type': file_type, 'search': search,
    })


@login_required
@permission_required('can_manage_media')
def media_file_delete(request, pk):
    file = get_object_or_404(MediaFile, id=pk, is_deleted=False)
    file_title = file.title
    if request.method == 'POST':
        file.is_deleted = True
        file.save()
        # 📝 لاگ حذف فایل از کتابخانه
        log_activity(request, 'حذف فایل از کتابخانه', 'MediaFile', pk, file_title)
        messages.success(request, 'فایل حذف شد.')
        return redirect('panel:media_library')
    return render(request, 'main_pages/panel/media/media_file_delete.html', {'file': file})


# ═══ مدیریت کاربران ═══
@login_required
@permission_required('can_manage_users')
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'main_pages/panel/user/user_list.html', {'users': users})


@login_required
@permission_required('can_manage_users')
def user_add(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on' and request.user.is_superuser
        role_id = request.POST.get('role') or None

        if not username or not password:
            messages.error(request, 'نام کاربری و رمز عبور الزامی است.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'این نام کاربری قبلاً استفاده شده.')
        else:
            user = User.objects.create_user(
                username=username, email=email, password=password,
                is_staff=is_staff, is_superuser=is_superuser
            )
            if role_id:
                UserProfile.objects.create(user=user, role_id=role_id)
            # 📝 لاگ ایجاد کاربر
            role_info = 'بدون نقش'
            if role_id:
                try:
                    role = CustomRole.objects.get(id=role_id)
                    role_info = f'نقش: {role.name}'
                except CustomRole.DoesNotExist:
                    pass
            log_activity(request, 'ایجاد کاربر جدید', 'User', user.id, f'{username} - {role_info}')
            messages.success(request, f'کاربر "{username}" با موفقیت ایجاد شد.')
            return redirect('panel:user_list')

    return render(request, 'main_pages/panel/user/user_form.html', {
        'roles': CustomRole.objects.filter(is_deleted=False),
    })


@login_required
@permission_required('can_manage_users')
def user_edit(request, pk):
    user = get_object_or_404(User, id=pk)

    if request.method == 'POST':
        user.email = request.POST.get('email', '').strip()
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_superuser = request.POST.get('is_superuser') == 'on' and request.user.is_superuser

        new_password = request.POST.get('new_password', '')
        if new_password:
            user.password = make_password(new_password)
        user.save()

        role_id = request.POST.get('role') or None
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role_id = role_id
        profile.save()

        # 📝 لاگ ویرایش کاربر
        log_activity(request, 'ویرایش کاربر', 'User', user.id, user.username)
        messages.success(request, 'کاربر با موفقیت ویرایش شد.')
        return redirect('panel:user_list')

    current_role_id = user.profile.role_id if hasattr(user, 'profile') else None
    return render(request, 'main_pages/panel/user/user_form.html', {
        'user_obj': user,
        'roles': CustomRole.objects.filter(is_deleted=False),
        'current_role_id': current_role_id,
    })


@login_required
@permission_required('can_manage_users')
def user_delete(request, pk):
    user = get_object_or_404(User, id=pk)
    if request.method == 'POST':
        if user == request.user:
            messages.error(request, 'نمی‌توانید خودتان را حذف کنید!')
        else:
            username_to_delete = user.username
            user.delete()
            # 📝 لاگ حذف کاربر
            log_activity(request, 'حذف کاربر', 'User', pk, username_to_delete)
            messages.success(request, 'کاربر حذف شد.')
        return redirect('panel:user_list')
    return render(request, 'main_pages/panel/user/user_delete.html', {'user_obj': user})


# ═══ لاگ فعالیت‌ها ═══
@login_required
@permission_required('can_view_audit_log')
def audit_log(request):
    """لاگ فعالیت‌ها"""
    logs = AuditLog.objects.all().select_related('user').order_by('-created_at')
    
    user_id = request.GET.get('user', '')
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    action_filter = request.GET.get('action', '')
    if action_filter:
        logs = logs.filter(action__icontains=action_filter)
    
    paginator = Paginator(logs, 50)
    logs_page = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'main_pages/panel/audit_log/audit_log.html', {
        'logs': logs_page,
        'user_id': user_id,
        'action_filter': action_filter,
        'users': User.objects.filter(is_staff=True).order_by('username'),
    })


# ═══ مدیریت بک‌آپ ═══
@login_required
@permission_required('can_manage_backup')
def backup_manager(request):
    if not request.user.is_staff:
        return redirect('panel:login')

    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    if request.method == 'POST' and request.POST.get('action') == 'create':
        import zipfile
        from django.core.management import call_command
        from io import StringIO

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.zip')

        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                db_buffer = StringIO()
                call_command('dumpdata', 'blog', 'portfolio', 'gallery', 'main',
                             'auth.user', 'auth.group', '--indent', '2', stdout=db_buffer)
                zipf.writestr('database_dump.json', db_buffer.getvalue())

                db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
                if os.path.exists(db_path):
                    zipf.write(db_path, 'db.sqlite3')

                media_root = settings.MEDIA_ROOT
                if os.path.exists(media_root):
                    for root, dirs, files in os.walk(media_root):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, settings.BASE_DIR)
                            zipf.write(file_path, arcname)

                info_content = f"""Backup Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Articles: {Post.objects.count()}
Total Portfolio Items: {PortfolioItem.objects.count()}
Total Gallery Albums: {GalleryAlbum.objects.count()}
"""
                zipf.writestr('backup_info.txt', info_content)
            # 📝 لاگ ایجاد بک‌آپ
            log_activity(request, 'ایجاد بک‌آپ کامل', 'Backup', None, backup_file)
            messages.success(request, '✅ بک‌آپ کامل با موفقیت ایجاد شد.')
        except Exception as e:
            messages.error(request, f'❌ خطا در ایجاد بک‌آپ: {str(e)}')
        return redirect('panel:backup_manager')

    backups = []
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.endswith('.zip'):
                file_path = os.path.join(backup_dir, file)
                backups.append({
                    'name': file,
                    'size': os.path.getsize(file_path),
                    'created': datetime.fromtimestamp(os.path.getctime(file_path)),
                })
    backups.sort(key=lambda x: x['created'], reverse=True)

    return render(request, 'main_pages/panel/backup/backup_manager.html', {
        'backups': backups,
        'total_articles': Post.objects.count(),
        'total_portfolio': PortfolioItem.objects.count(),
        'total_gallery': GalleryAlbum.objects.count(),
    })


@login_required
@permission_required('can_manage_backup')
def backup_upload(request):
    if not request.user.is_staff:
        return redirect('panel:login')

    if request.method == 'POST':
        backup_file = request.FILES.get('backup_file')
        if not backup_file:
            messages.error(request, '❌ لطفاً یک فایل بک‌آپ انتخاب کنید.')
            return redirect('panel:backup_manager')
        if not backup_file.name.endswith('.zip'):
            messages.error(request, '❌ فقط فایل‌های ZIP قابل بازگردانی هستند.')
            return redirect('panel:backup_manager')
        if backup_file.size > 500 * 1024 * 1024:
            messages.error(request, '❌ حجم فایل بیش از حد مجاز است (حداکثر 500 مگابایت).')
            return redirect('panel:backup_manager')

        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_filename = f'uploaded_{timestamp}_{backup_file.name}'
        saved_path = os.path.join(backup_dir, saved_filename)
        with open(saved_path, 'wb+') as destination:
            for chunk in backup_file.chunks():
                destination.write(chunk)
        # 📝 لاگ آپلود بک‌آپ
        log_activity(request, 'آپلود فایل بک‌آپ', 'Backup', None, saved_filename)
        messages.success(request, f'✅ فایل بک‌آپ با موفقیت آپلود شد.')
        return redirect('panel:backup_manager')
    return redirect('panel:backup_manager')


@login_required
@permission_required('can_manage_backup')
def backup_restore(request, filename):
    if not request.user.is_staff:
        return redirect('panel:login')

    current_user_id = request.user.id
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    backup_file = os.path.join(backup_dir, filename)

    if not os.path.exists(backup_file):
        messages.error(request, 'فایل بک‌آپ یافت نشد.')
        return redirect('panel:backup_manager')

    if request.method == 'POST':
        try:
            import zipfile
            from django.core.management import call_command

            with zipfile.ZipFile(backup_file, 'r') as zipf:
                media_count = 0
                for member in zipf.namelist():
                    if member.startswith('media/') and not member.endswith('/'):
                        zipf.extract(member, settings.BASE_DIR)
                        media_count += 1

                if 'database_dump.json' in zipf.namelist():
                    json_data = zipf.read('database_dump.json')
                    temp_file = os.path.join(backup_dir, 'temp_restore.json')
                    with open(temp_file, 'wb') as f:
                        f.write(json_data)
                    call_command('loaddata', temp_file, verbosity=0)
                    os.remove(temp_file)

            try:
                user = User.objects.get(id=current_user_id)
                login(request, user)
                # 📝 لاگ بازگردانی بک‌آپ
                log_activity(request, 'بازگردانی بک‌آپ', 'Backup', None, filename)
                messages.success(request, f'✅ بک‌آپ با موفقیت بازگردانی شد! ({media_count} فایل مدیا)')
            except User.DoesNotExist:
                logout(request)
                messages.warning(request, '✅ بک‌آپ بازگردانی شد ولی حساب شما در این بک‌آپ نبود. دوباره وارد شوید.')
                return redirect('panel:login')
            return redirect('panel:backup_manager')
        except Exception as e:
            messages.error(request, f'❌ خطا در بازگردانی بک‌آپ: {str(e)}')
            return redirect('panel:backup_manager')

    try:
        import zipfile
        with zipfile.ZipFile(backup_file, 'r') as zipf:
            info_content = zipf.read('backup_info.txt').decode('utf-8') if 'backup_info.txt' in zipf.namelist() else 'اطلاعات بک‌آپ موجود نیست'
    except Exception:
        info_content = 'خطا در خواندن اطلاعات بک‌آپ'

    return render(request, 'main_pages/panel/backup/backup_restore_confirm.html', {
        'filename': filename, 'info_content': info_content,
    })


@login_required
@permission_required('can_manage_backup')
def backup_download(request, filename):
    if not request.user.is_staff:
        return redirect('panel:login')
    file_path = os.path.join(settings.BASE_DIR, 'backups', filename)
    if os.path.exists(file_path):
        # 📝 لاگ دانلود بک‌آپ
        log_activity(request, 'دانلود بک‌آپ', 'Backup', None, filename)
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    messages.error(request, 'فایل یافت نشد.')
    return redirect('panel:backup_manager')


@login_required
@permission_required('can_manage_backup')
def backup_delete(request, filename):
    if not request.user.is_staff:
        return redirect('panel:login')
    file_path = os.path.join(settings.BASE_DIR, 'backups', filename)
    if request.method == 'POST' and os.path.exists(file_path):
        os.remove(file_path)
        # 📝 لاگ حذف بک‌آپ
        log_activity(request, 'حذف بک‌آپ', 'Backup', None, filename)
        messages.success(request, 'بک‌آپ حذف شد.')
    return redirect('panel:backup_manager')


# ═══ مدیریت کش ═══
@login_required
@permission_required('can_manage_cache')
def cache_manager(request):
    """مدیریت کش سایت"""
    cache_stats = {
        'backend': cache.__class__.__name__,
        'backend_module': cache.__class__.__module__,
    }

    # آمار backend
    try:
        if hasattr(cache, '_dir'):
            cache_stats['cache_dir'] = cache._dir
            files = [f for f in os.listdir(cache._dir) if os.path.isfile(os.path.join(cache._dir, f))]
            cache_stats['total_keys'] = len(files)
            cache_stats['total_size'] = sum(os.path.getsize(os.path.join(cache._dir, f)) for f in files)
        elif hasattr(cache, '_table'):
            cache_stats['table'] = cache._table
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {cache._table}")
                cache_stats['total_keys'] = cursor.fetchone()[0]
    except Exception:
        pass

    # ═══ خواندن نتایج آخرین تست از session (رفع باگ redirect) ═══
    last_test = request.session.get('cache_test_results')
    if last_test:
        cache_stats.update(last_test)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'clear_all':
            cache.clear()
            log_activity(request, 'پاک کردن تمام کش سایت', 'Cache', None, f'Backend: {cache.__class__.__name__}')
            messages.success(request, '✅ تمام کش سایت با موفقیت پاک شد.')

        elif action == 'clear_templates':
            try:
                from django.template import engines
                cleared = 0
                for engine in engines.all():
                    if hasattr(engine, 'engine'):
                        for loader in engine.engine.template_loaders:
                            if hasattr(loader, 'reset'):
                                loader.reset()
                                cleared += 1
                log_activity(request, f'پاک کردن کش تمپلیت‌ها ({cleared} loader)', 'Cache')
                messages.success(request, f'✅ کش {cleared} تمپلیت لودر پاک شد.')
            except Exception as e:
                messages.error(request, f'❌ خطا در پاک کردن کش تمپلیت‌ها: {str(e)}')

        elif action == 'clear_page':
            cache.clear()
            log_activity(request, 'پاک کردن کش صفحات', 'Cache')
            messages.success(request, '✅ کش صفحات با موفقیت پاک شد.')

        elif action == 'test_cache':
            # ═══ تست سرعت با داده ۱۰ کیلوبایتی ═══
            test_key = f'cache_speed_test_{int(time.time() * 1000)}'
            test_value = 'x' * 10240

            start = time.perf_counter()
            cache.set(test_key, test_value, 60)
            write_ms = round((time.perf_counter() - start) * 1000, 2)

            start = time.perf_counter()
            cache.get(test_key)
            read_ms = round((time.perf_counter() - start) * 1000, 2)

            cache.delete(test_key)

            # ═══ ارزیابی کیفیت سرعت ═══
            avg = (write_ms + read_ms) / 2
            if avg < 2:
                verdict, verdict_class, verdict_icon, verdict_desc = 'عالی', 'excellent', '🟢', 'کش فوق‌العاده سریعه! سایتت مثل موشک پرواز می‌کنه.'
            elif avg < 10:
                verdict, verdict_class, verdict_icon, verdict_desc = 'خوب', 'good', '🟢', 'سرعت کش کاملاً قابل قبوله و نیازی به تغییر نیست.'
            elif avg < 50:
                verdict, verdict_class, verdict_icon, verdict_desc = 'متوسط', 'medium', '🟡', 'بد نیست ولی با Redis یا Memcached خیلی سریع‌تر می‌شه.'
            else:
                verdict, verdict_class, verdict_icon, verdict_desc = 'کند', 'slow', '🔴', 'کش کنده! حتماً از Redis/Memcached در production استفاده کن.'

            # ═══ ذخیره در session تا بعد از redirect هم نمایش داده بشه ═══
            request.session['cache_test_results'] = {
                'test_write_ms': write_ms,
                'test_read_ms': read_ms,
                'test_avg_ms': round(avg, 2),
                'verdict': verdict,
                'verdict_class': verdict_class,
                'verdict_icon': verdict_icon,
                'verdict_desc': verdict_desc,
                'tested_at': datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
            }
            messages.success(request, f'✅ تست کش انجام شد: {verdict_icon} {verdict}')

        return redirect('panel:cache_manager')

    return render(request, 'main_pages/panel/cache/cache_manager.html', {
        'cache_stats': cache_stats,
    })

# ═══ حالت تعمیر ═══
@login_required
@permission_required('can_manage_settings')
def maintenance_mode(request):
    setting = SiteSetting.load()
    if request.method == 'POST':
        old_mode = setting.maintenance_mode
        setting.maintenance_mode = request.POST.get('maintenance_mode') == 'on'
        setting.maintenance_message = request.POST.get('maintenance_message', '')
        setting.save()
        settings.MAINTENANCE_MODE = setting.maintenance_mode
        # 📝 لاگ تغییر حالت تعمیر
        if old_mode != setting.maintenance_mode:
            status = 'فعال' if setting.maintenance_mode else 'غیرفعال'
            log_activity(request, f'حالت تعمیر {status} شد', 'SiteSetting', 1, status)
        messages.success(request, 'تنظیمات حالت تعمیر ذخیره شد.')
        return redirect('panel:maintenance_mode')
    return render(request, 'main_pages/panel/maintenance/maintenance_mode.html', {'setting': setting})


# ═══ مدیریت نقش‌ها ═══
@login_required
@permission_required('can_manage_roles')
def role_list(request):
    roles = CustomRole.objects.filter(is_deleted=False)
    return render(request, 'main_pages/panel/roles/role_list.html', {'roles': roles})


@login_required
@permission_required('can_manage_roles')
def role_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        permissions = request.POST.getlist('permissions')
        if not name:
            messages.error(request, 'نام نقش الزامی است.')
        elif CustomRole.objects.filter(name=name).exists():
            messages.error(request, 'این نام نقش قبلاً استفاده شده.')
        else:
            role = CustomRole.objects.create(name=name, description=description, permissions=permissions)
            # 📝 لاگ ایجاد نقش
            log_activity(request, 'ایجاد نقش جدید', 'CustomRole', role.id, f'{name} با {len(permissions)} دسترسی')
            messages.success(request, f'نقش "{name}" با موفقیت ایجاد شد.')
            return redirect('panel:role_list')
    return render(request, 'main_pages/panel/roles/role_form.html', {
        'all_permissions': CustomRole.ALL_PERMISSIONS,
    })


@login_required
@permission_required('can_manage_roles')
def role_edit(request, pk):
    role = get_object_or_404(CustomRole, id=pk, is_deleted=False)
    if request.method == 'POST':
        role.name = request.POST.get('name', '').strip()
        role.description = request.POST.get('description', '').strip()
        role.permissions = request.POST.getlist('permissions')
        role.save()
        # 📝 لاگ ویرایش نقش
        log_activity(request, 'ویرایش نقش', 'CustomRole', role.id, f'{role.name} با {len(role.permissions)} دسترسی')
        messages.success(request, 'نقش با موفقیت ویرایش شد.')
        return redirect('panel:role_list')
    return render(request, 'main_pages/panel/roles/role_form.html', {
        'role': role, 'all_permissions': CustomRole.ALL_PERMISSIONS,
    })


@login_required
@permission_required('can_manage_roles')
def role_delete(request, pk):
    role = get_object_or_404(CustomRole, id=pk, is_deleted=False)
    if request.method == 'POST':
        role_name = role.name
        role.is_deleted = True
        role.save()
        # 📝 لاگ حذف نقش
        log_activity(request, 'حذف نقش', 'CustomRole', pk, role_name)
        messages.success(request, 'نقش حذف شد.')
        return redirect('panel:role_list')
    return render(request, 'main_pages/panel/roles/role_delete.html', {'role': role})
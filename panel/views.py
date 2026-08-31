import json
import time
import os
import jdatetime
import shutil
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.views.decorators.http import require_POST
from django.core.mail.backends.smtp import EmailBackend
from main.models import ContactMessage, ReplyAttachment, SiteSetting
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from blog.models import Post, Category, Comment
from django.utils.text import slugify
from panel.forms import PostForm
from django.core.paginator import Paginator
from django.db.models import Q,Count
from portfolio.models import PortfolioItem, PortfolioCategory
from portfolio.forms import PortfolioItemForm
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import InMemoryUploadedFile
from gallery.models import GalleryAlbum, GalleryImage
from gallery.utils import add_watermark_and_compress
from gallery.forms import GalleryAlbumForm, MultipleImageUploadForm
from main.models import AuditLog
from django.core.cache import cache


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
            return redirect('panel:dashboard')
        request.session['login_attempts'] = attempts + 1
        remaining = 5 - (attempts + 1)
        if remaining <= 0:
            request.session['locked_until'] = time.time() + 1800
            return render(request, 'main_pages/panel/login.html', {'locked': True, 'wait_minutes': 30})
        messages.error(request, f'نام کاربری یا رمز اشتباه است. {remaining} تلاش باقی‌مانده.')
    return render(request, 'main_pages/panel/login.html')


def panel_logout(request):
    logout(request)
    return redirect('panel:login')


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
            'id': msg.id,
            'name': msg.name,
            'email': msg.email,
            'phone': msg.phone,
            'message': msg.message,
            'attachment': msg.attachment,
            'is_read': msg.is_read,
            'reply_subject': msg.reply_subject,
            'reply_body': msg.reply_body,
            'reply_attachments': msg.reply_attachments.all(),
            'created_date': created_jd.strftime('%Y/%m/%d'),
            'created_time': created.strftime('%H:%M'),
            'replied_date': replied_jd.strftime('%Y/%m/%d') if replied_jd else None,
            'replied_time': replied.strftime('%H:%M') if replied_jd else None,
        })

    # ═══ Pagination: ۱۰ پیام در هر صفحه ═══
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
def main_contact_reply(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
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

        # ارسال با ۳ بار تلاش (ضد قطعی شبکه)
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
        if msg.attachment:
            try: os.remove(msg.attachment.path)
            except Exception: pass
        msg.delete()
        return JsonResponse({'success': True})
    except ContactMessage.DoesNotExist:
        return JsonResponse({'success': False})


def _check_lockout(request):
    locked_until = request.session.get('locked_until', 0)
    now = time.time()
    if locked_until > now:
        return {'locked': True, 'wait_minutes': int((locked_until - now) / 60) + 1}
    if locked_until > 0:
        request.session.pop('locked_until', None)
        request.session['login_attempts'] = 0
    return {'locked': False, 'wait_minutes': 0}

@login_required
def site_settings(request):
    if not request.user.is_staff:
        return redirect('panel:login')
    setting = SiteSetting.load()
    if request.method == 'POST':
        from django import forms
        
        class SettingsForm(forms.ModelForm):
            class Meta:
                model = SiteSetting
                fields = '__all__'
        
        form = SettingsForm(request.POST, request.FILES, instance=setting)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ تنظیمات سایت با موفقیت ذخیره شد')
            return redirect('panel:site_settings')
    else:
        from django import forms
        class SettingsForm(forms.ModelForm):
            class Meta:
                model = SiteSetting
                fields = '__all__'
                widgets = {
                    'about_text': forms.Textarea(attrs={'rows': 4}),
                    'address_factory': forms.Textarea(attrs={'rows': 2}),
                    'address_rd': forms.Textarea(attrs={'rows': 2}),
                    'footer_description': forms.Textarea(attrs={'rows': 3}),
                    'copyright_text': forms.Textarea(attrs={'rows': 2}),
                }
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
def blog_post_add(request):
    if not request.user.is_staff:
        return redirect('panel:login')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            if not post.publish_date and post.published:
                post.publish_date = timezone.now()
            post.save()
            return redirect('panel:blog_post_list')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = PostForm()
    
    # ✅ اصلاح شده: حذف is_deleted
    categories = Category.objects.all()
    categories_data = [{'id': c.id, 'title': c.title, 'parent': c.parent_id} for c in categories]
    
    return render(request, 'main_pages/blog/post_form.html', {
        'form': form,
        'post': None,
        'categories': categories,
        'categories_data': categories_data,
    })
    
@login_required
def blog_post_edit(request, pk):
    if not request.user.is_staff:
        return redirect('panel:login')
    
    post = get_object_or_404(Post, id=pk)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('panel:blog_post_list')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = PostForm(instance=post)
    
    # ← این دو خط مهم هستند!
    categories = Category.objects.filter(is_deleted=False).order_by('order', 'title')
    categories_data = [{'id': c.id, 'title': c.title, 'parent': c.parent_id} for c in categories]
    
    return render(request, 'main_pages/blog/post_form.html', {
        'form': form,
        'post': post,
        'categories': categories,  # ← برای حلقه for در JS
        'categories_data': categories_data,  # ← برای json_script
    })
    
@login_required
@require_POST
def blog_post_delete(request, pk):
    if not request.user.is_staff:
        return JsonResponse({'success': False}, status=403)
    Post.objects.filter(id=pk).delete()
    return JsonResponse({'success': True})


# ═══ مدیریت دسته‌بندی‌ها ═══
@login_required
def blog_category_list(request):
    if not request.user.is_staff:
        return redirect('panel:login')
    cats = Category.objects.annotate(posts_count=Count('posts')).order_by('-id')
    paginator = Paginator(cats, 10)
    categories = paginator.get_page(request.GET.get('page'))
    return render(request, 'main_pages/blog/category_list.html', {'categories': categories})


@login_required
def blog_category_add(request):
    if not request.user.is_staff:
        return redirect('panel:login')
    if request.method == 'POST':
        cat = Category()
        cat.title = request.POST.get('title', '').strip()
        cat.slug = slugify(cat.title, allow_unicode=True)
        parent_id = request.POST.get('parent')
        if parent_id:
            cat.parent = Category.objects.get(id=parent_id)
        cat.save()
        return redirect('panel:blog_category_list')
    
    parents = Category.objects.filter(parent=None)
    return render(request, 'main_pages/blog/category_form.html', {'parents': parents})


@login_required
def blog_category_edit(request, pk):
    if not request.user.is_staff:
        return redirect('panel:login')
    cat = get_object_or_404(Category, id=pk)
    if request.method == 'POST':
        cat.title = request.POST.get('title', '').strip()
        cat.slug = slugify(cat.title, allow_unicode=True)
        parent_id = request.POST.get('parent')
        cat.parent = Category.objects.get(id=parent_id) if parent_id else None
        cat.save()
        return redirect('panel:blog_category_list')
    
    parents = Category.objects.filter(parent=None).exclude(id=pk)
    return render(request, 'main_pages/blog/category_form.html', {'category': cat, 'parents': parents})


@login_required
@require_POST
def blog_category_delete(request, pk):
    if not request.user.is_staff:
        return JsonResponse({'success': False}, status=403)
    Category.objects.filter(id=pk).delete()
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
def blog_comment_approve(request, pk):
    if not request.user.is_staff:
        return JsonResponse({'success': False}, status=403)
    try:
        c = Comment.objects.get(id=pk)
        c.approve()
        return JsonResponse({'success': True})
    except Comment.DoesNotExist:
        return JsonResponse({'success': False})


@login_required
@require_POST
def blog_comment_delete(request, pk):
    if not request.user.is_staff:
        return JsonResponse({'success': False}, status=403)
    Comment.objects.filter(id=pk).delete()
    return JsonResponse({'success': True})

# ═══ مدیریت نمونه کارها ═══
@login_required
def portfolio_list(request):
    if not request.user.is_staff:
        return redirect('panel:login')
    items = PortfolioItem.objects.select_related('category').order_by('-created')
    paginator = Paginator(items, 10)
    items = paginator.get_page(request.GET.get('page'))
    return render(request, 'main_pages/portfolio/portfolio_list.html', {'items': items})


@login_required
def portfolio_add(request):
    if not request.user.is_staff:
        return redirect('panel:login')

    categories_qs = PortfolioCategory.objects.filter(is_deleted=False).order_by('order', 'title')
    categories_data = [{'id': c.id, 'title': c.title, 'parent': None} for c in categories_qs]
    
    # دیباگ: چاپ در کنسول
    print(f"DEBUG: {len(categories_data)} دسته‌بندی پیدا شد")
    for c in categories_data:
        print(f"  - {c}")

    if request.method == 'POST':
        form = PortfolioItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            cat_id = request.POST.get('category')
            if cat_id:
                item.category = PortfolioCategory.objects.filter(id=cat_id, is_deleted=False).first()
            item.save()
            messages.success(request, 'نمونه‌کار با موفقیت اضافه شد.')
            return redirect('panel:portfolio_list')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = PortfolioItemForm()

    return render(request, 'main_pages/portfolio/portfolio_form.html', {
        'form': form,
        'categories': categories_qs,
        'categories_data': categories_data,  # ← این خط مهمه
    })


@login_required
def portfolio_edit(request, pk):
    if not request.user.is_staff:
        return redirect('panel:login')

    item = get_object_or_404(PortfolioItem, id=pk, is_deleted=False)
    categories_qs = PortfolioCategory.objects.filter(is_deleted=False).order_by('order', 'title')
    categories_data = [{'id': c.id, 'title': c.title, 'parent': None} for c in categories_qs]
    
    # دیباگ: چاپ در کنسول
    print(f"DEBUG EDIT: {len(categories_data)} دسته‌بندی پیدا شد")

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
            messages.success(request, 'تغییرات ذخیره شد.')
            return redirect('panel:portfolio_list')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = PortfolioItemForm(instance=item)

    return render(request, 'main_pages/portfolio/portfolio_form.html', {
        'form': form,
        'item': item,
        'categories': categories_qs,
        'categories_data': categories_data,  # ← این خط مهمه
    })
    
@login_required
def portfolio_delete(request, pk):
    if not request.user.is_staff:
        return redirect('panel:login')
    item = get_object_or_404(PortfolioItem, id=pk)
    item.is_deleted = True
    item.save()
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
def portfolio_category_add(request):
    if not request.user.is_staff:
        return redirect('panel:login')
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
        messages.success(request, 'دسته‌بندی اضافه شد.')
        return redirect('panel:portfolio_category_list')
    return render(request, 'main_pages/portfolio/category_form.html')


@login_required
def portfolio_category_edit(request, pk):
    if not request.user.is_staff:
        return redirect('panel:login')
    cat = get_object_or_404(PortfolioCategory, id=pk)
    if request.method == 'POST':
        cat.title = request.POST.get('title', '').strip() or cat.title
        cat.description = request.POST.get('description', '')
        cat.order = int(request.POST.get('order', 0) or 0)
        cat.save()
        messages.success(request, 'تغییرات ذخیره شد.')
        return redirect('panel:portfolio_category_list')
    return render(request, 'main_pages/portfolio/category_form.html', {'cat': cat})


@login_required
def portfolio_category_delete(request, pk):
    if not request.user.is_staff:
        return redirect('panel:login')
    cat = get_object_or_404(PortfolioCategory, id=pk)
    cat.is_deleted = True
    cat.save()
    messages.success(request, 'دسته‌بندی حذف شد.')
    return redirect('panel:portfolio_category_list')

# ═══ مدیریت گالری تصاویر ═══
@login_required
def gallery_album_list(request):
    """لیست آلبوم‌های گالری"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    albums = GalleryAlbum.objects.filter(is_deleted=False).order_by('-created')
    return render(request, 'main_pages/gallery/album_list.html', {
        'albums': albums,
    })


@login_required
def gallery_album_add(request):
    """ایجاد آلبوم جدید"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    if request.method == 'POST':
        form = GalleryAlbumForm(request.POST)
        if form.is_valid():
            album = form.save()
            messages.success(request, f'آلبوم "{album.title}" با موفقیت ایجاد شد.')
            return redirect('panel:gallery_album_images', album_id=album.id)
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = GalleryAlbumForm()
    
    return render(request, 'main_pages/gallery/album_form.html', {
        'form': form,
    })


@login_required
def gallery_album_edit(request, pk):
    """ویرایش آلبوم"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    album = get_object_or_404(GalleryAlbum, id=pk, is_deleted=False)
    
    if request.method == 'POST':
        form = GalleryAlbumForm(request.POST, instance=album)
        if form.is_valid():
            form.save()
            messages.success(request, 'آلبوم با موفقیت ویرایش شد.')
            return redirect('panel:gallery_album_list')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = GalleryAlbumForm(instance=album)
    
    return render(request, 'main_pages/gallery/album_form.html', {
        'form': form,
        'album': album,
    })


@login_required
def gallery_album_images(request, album_id):
    """مدیریت تصاویر یک آلبوم"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
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
                    
                    img = GalleryImage(
                        album=album,
                        order=max_order + 1,
                    )
                    
                    img.image.save(
                        f.name,
                        InMemoryUploadedFile(
                            processed_image,
                            None,
                            f.name,
                            'image/jpeg',
                            processed_image.getbuffer().nbytes,
                            None
                        ),
                        save=False
                    )
                    img.save()
                    count += 1
                except Exception as e:
                    print(f"Error processing {f.name}: {e}")
                    continue
            
            messages.success(request, f'{count} تصویر با موفقیت آپلود شد.')
            return redirect('panel:gallery_album_images', album_id=album.id)
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        upload_form = MultipleImageUploadForm()
    
    return render(request, 'main_pages/gallery/album_images.html', {
        'album': album,
        'images': images,
        'upload_form': upload_form,
    })


@login_required
def gallery_image_edit(request, pk):
    """ویرایش تصویر"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    image = get_object_or_404(GalleryImage, id=pk, is_deleted=False)
    
    if request.method == 'POST':
        image.title = request.POST.get('title', '')
        image.description = request.POST.get('description', '')
        image.order = int(request.POST.get('order', 0))
        image.save()
        messages.success(request, 'تصویر با موفقیت ویرایش شد.')
        return redirect('panel:gallery_album_images', album_id=image.album.id)
    
    return render(request, 'main_pages/gallery/album_edit.html', {
        'image': image,
    })


@login_required
def gallery_image_delete(request, pk):
    """حذف تصویر"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    image = get_object_or_404(GalleryImage, id=pk, is_deleted=False)
    album_id = image.album.id
    
    if request.method == 'POST':
        image.is_deleted = True
        image.save()
        messages.success(request, 'تصویر حذف شد.')
        return redirect('panel:gallery_album_images', album_id=album_id)
    
    return render(request, 'main_pages/gallery/image_delete.html', {
        'image': image,
    })


@login_required
def gallery_album_delete(request, pk):
    """حذف آلبوم"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    album = get_object_or_404(GalleryAlbum, id=pk, is_deleted=False)
    
    if request.method == 'POST':
        album.is_deleted = True
        album.save()
        messages.success(request, 'آلبوم حذف شد.')
        return redirect('panel:gallery_album_list')
    
    return render(request, 'main_pages/gallery/album_delete.html', {
        'album': album,
    })
    """حذف آلبوم"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    album = get_object_or_404(GalleryAlbum, id=pk, is_deleted=False)
    
    if request.method == 'POST':
        album.is_deleted = True
        album.save()
        messages.success(request, 'آلبوم حذف شد.')
        return redirect('panel:gallery_album_list')
    
    return render(request, 'main_pages/gallery/album_delete.html', {
        'album': album,
    })
    """لیست آلبوم‌های گالری"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    albums = GalleryAlbum.objects.filter(is_deleted=False).order_by('-created')
    
    return render(request, 'main_pages/gallery/album_list.html', {
        'albums': albums,
    })
    
# ═══ مدیریت رسانه ها ═══
@login_required
def media_library(request):
    """کتابخانه فایل‌ها"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    files = MediaFile.objects.filter(is_deleted=False).order_by('-uploaded_at')
    
    # فیلتر بر اساس نوع
    file_type = request.GET.get('type', '')
    if file_type:
        files = files.filter(file_type=file_type)
    
    # جستجو
    search = request.GET.get('q', '')
    if search:
        files = files.filter(title__icontains=search)
    
    # آپلود فایل جدید
    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('files')
        count = 0
        for f in uploaded_files:
            MediaFile.objects.create(
                title=f.name,
                file=f,
                uploaded_by=request.user
            )
            count += 1
        messages.success(request, f'{count} فایل با موفقیت آپلود شد.')
        return redirect('panel:media_library')
    
    paginator = Paginator(files, 20)
    page = request.GET.get('page')
    files_page = paginator.get_page(page)
    
    return render(request, 'panel/media_library.html', {
        'files': files_page,
        'file_type': file_type,
        'search': search,
    })

@login_required
def media_file_delete(request, pk):
    """حذف فایل"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    file = get_object_or_404(MediaFile, id=pk, is_deleted=False)
    
    if request.method == 'POST':
        file.is_deleted = True
        file.save()
        messages.success(request, 'فایل حذف شد.')
        return redirect('panel:media_library')
    
    return render(request, 'panel/media_file_delete.html', {'file': file})

# ═══ مدیریت کاربر ═══
@login_required
def user_list(request):
    """لیست کاربران"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    users = User.objects.all().order_by('-date_joined')
    
    return render(request, 'panel/user_list.html', {'users': users})

@login_required
def user_add(request):
    """افزودن کاربر جدید"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        
        if not username or not password:
            messages.error(request, 'نام کاربری و رمز عبور الزامی است.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'این نام کاربری قبلاً استفاده شده.')
        else:
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=is_staff,
                is_superuser=is_superuser
            )
            messages.success(request, f'کاربر "{username}" با موفقیت ایجاد شد.')
            return redirect('panel:user_list')
    
    return render(request, 'panel/user_form.html')

@login_required
def user_edit(request, pk):
    """ویرایش کاربر"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    user = get_object_or_404(User, id=pk)
    
    if request.method == 'POST':
        user.email = request.POST.get('email', '').strip()
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_superuser = request.POST.get('is_superuser') == 'on'
        
        new_password = request.POST.get('new_password', '')
        if new_password:
            user.password = make_password(new_password)
        
        user.save()
        messages.success(request, 'کاربر با موفقیت ویرایش شد.')
        return redirect('panel:user_list')
    
    return render(request, 'panel/user_form.html', {'user_obj': user})

@login_required
def user_delete(request, pk):
    """حذف کاربر"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    user = get_object_or_404(User, id=pk)
    
    if request.method == 'POST':
        if user == request.user:
            messages.error(request, 'نمی‌توانید خودتان را حذف کنید!')
        else:
            user.delete()
            messages.success(request, 'کاربر حذف شد.')
        return redirect('panel:user_list')
    
    return render(request, 'panel/user_delete.html', {'user_obj': user})

# ═══ فعالیت لاگ ها ═══
@login_required
def audit_log(request):
    """لاگ فعالیت‌ها"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    logs = AuditLog.objects.all().select_related('user').order_by('-created_at')
    
    # فیلتر بر اساس کاربر
    user_id = request.GET.get('user', '')
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    # فیلتر بر اساس عملیات
    action = request.GET.get('action', '')
    if action:
        logs = logs.filter(action__icontains=action)
    
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs_page = paginator.get_page(page)
    
    return render(request, 'panel/audit_log.html', {
        'logs': logs_page,
        'user_id': user_id,
        'action': action,
        'users': User.objects.filter(is_staff=True),
    })
# ═══ مدیریت بکاپ ═══
@login_required
def backup_manager(request):
    """مدیریت بک‌آپ"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    # ایجاد بک‌آپ جدید
    if request.method == 'POST' and request.POST.get('action') == 'create':
        import zipfile
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.zip')
        
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # بک‌آپ دیتابیس
            db_path = os.path.join(settings.BASE_DIR, 'db.sqlite3')
            if os.path.exists(db_path):
                zipf.write(db_path, 'db.sqlite3')
            
            # بک‌آپ فایل‌های مدیا
            media_root = settings.MEDIA_ROOT
            if os.path.exists(media_root):
                for root, dirs, files in os.walk(media_root):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, settings.BASE_DIR)
                        zipf.write(file_path, arcname)
        
        messages.success(request, 'بک‌آپ با موفقیت ایجاد شد.')
        return redirect('panel:backup_manager')
    
    # لیست بک‌آپ‌های موجود
    backups = []
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.endswith('.zip'):
                file_path = os.path.join(backup_dir, file)
                backups.append({
                    'name': file,
                    'size': os.path.getsize(file_path),
                    'created': os.path.getctime(file_path),
                })
    
    backups.sort(key=lambda x: x['created'], reverse=True)
    
    return render(request, 'panel/backup_manager.html', {'backups': backups})

@login_required
def backup_download(request, filename):
    """دانلود بک‌آپ"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    file_path = os.path.join(backup_dir, filename)
    
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    
    messages.error(request, 'فایل یافت نشد.')
    return redirect('panel:backup_manager')

@login_required
def backup_delete(request, filename):
    """حذف بک‌آپ"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    file_path = os.path.join(backup_dir, filename)
    
    if request.method == 'POST' and os.path.exists(file_path):
        os.remove(file_path)
        messages.success(request, 'بک‌آپ حذف شد.')
    
    return redirect('panel:backup_manager')
# ═══ مدیریت کش ها ═══
@login_required
def cache_manager(request):
    """مدیریت کش"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'clear_all':
            cache.clear()
            messages.success(request, 'تمام کش پاک شد.')
        elif action == 'clear_templates':
            # پاک کردن کش تمپلیت‌ها
            from django.template import engines
            for engine in engines.all():
                if hasattr(engine, 'engine'):
                    engine.engine.template_loaders[0].reset()
            messages.success(request, 'کش تمپلیت‌ها پاک شد.')
        
        return redirect('panel:cache_manager')
    
    # آمار کش
    cache_stats = {
        'backend': cache.__class__.__name__,
    }
    
    return render(request, 'panel/cache_manager.html', {'cache_stats': cache_stats})

# ═══ مدیریت حالت تعمیر ═══
@login_required
def maintenance_mode(request):
    """مدیریت حالت تعمیر"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    from main.models import SiteSetting
    setting = SiteSetting.load()
    
    if request.method == 'POST':
        setting.maintenance_mode = request.POST.get('maintenance_mode') == 'on'
        setting.maintenance_message = request.POST.get('maintenance_message', '')
        setting.save()
        
        # بروزرسانی settings.py
        settings.MAINTENANCE_MODE = setting.maintenance_mode
        
        messages.success(request, 'تنظیمات حالت تعمیر ذخیره شد.')
        return redirect('panel:maintenance_mode')
    
    return render(request, 'panel/maintenance_mode.html', {'setting': setting})




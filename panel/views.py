import time
import os
import jdatetime
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.views.decorators.http import require_POST
from django.core.mail.backends.smtp import EmailBackend
from main.models import ContactMessage, ReplyAttachment, SiteSetting
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from blog.models import Post, Category, Comment
from django.utils.text import slugify
from panel.forms import PostForm



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
    posts = Post.objects.all().select_related('category').order_by('-created')
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
        form = PostForm()
    return render(request, 'main_pages/blog/post_form.html', {'form': form})


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
        form = PostForm(instance=post)
    return render(request, 'main_pages/blog/post_form.html', {'form': form, 'post': post})

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
    categories = Category.objects.all().select_related('parent')
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
    comments = Comment.objects.all().select_related('post').order_by('-created')
    pending = Comment.objects.filter(approved=False).count()
    return render(request, 'main_pages/blog/comment_list.html', {'comments': comments, 'pending_count': pending})


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
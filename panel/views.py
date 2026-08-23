import time
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.views.decorators.http import require_POST
from main.models import ContactMessage


def panel_login(request):
    """ورود به پنل با قفل زمانی"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('panel:dashboard')

    lock_info = _check_lockout(request)
    if lock_info['locked']:
        return render(request, 'main_pages/panel/login.html', {
            'locked': True, 'wait_minutes': lock_info['wait_minutes']
        })

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        attempts = request.session.get('login_attempts', 0)
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            request.session['login_attempts'] = 0
            return redirect('panel:dashboard')
        else:
            request.session['login_attempts'] = attempts + 1
            remaining = 5 - (attempts + 1)
            if remaining <= 0:
                request.session['locked_until'] = time.time() + 1800
                return render(request, 'main_pages/panel/login.html', {
                    'locked': True, 'wait_minutes': 30
                })
            messages.error(request, f'نام کاربری یا رمز عبور اشتباه است. {remaining} تلاش باقی‌مانده.')

    return render(request, 'main_pages/panel/login.html')


def panel_logout(request):
    logout(request)
    return redirect('panel:login')


@login_required
def dashboard(request):
    """داشبورد اصلی پنل"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    total = ContactMessage.objects.count()
    unread = ContactMessage.objects.filter(is_read=False).count()
    answered = ContactMessage.objects.filter(is_read=True).count()
    attachments = ContactMessage.objects.exclude(attachment='').exclude(attachment=None).count()
    recent = ContactMessage.objects.all()[:5]
    
    return render(request, 'main_pages/panel/dashboard.html', {
        'total_messages': total,
        'unread_messages': unread,
        'answered_messages': answered,
        'attachments_count': attachments,
        'recent_messages': recent,
    })


@login_required
def main_contact(request):
    """مدیریت پیام‌های تماس"""
    if not request.user.is_staff:
        return redirect('panel:login')
    
    all_messages = ContactMessage.objects.all().order_by('-created_at')
    unread = ContactMessage.objects.filter(is_read=False).count()
    
    return render(request, 'main_pages/main/contact.html', {
        'messages': all_messages,
        'unread_messages': unread,
    })


@login_required
@require_POST
def main_contact_reply(request):
    """پاسخ به پیام با ایمیل"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    msg_id = request.POST.get('message_id')
    subject = request.POST.get('subject', '').strip()
    body = request.POST.get('body', '').strip()

    try:
        msg = ContactMessage.objects.get(id=msg_id)
    except ContactMessage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'پیام یافت نشد'})

    if not msg.email or not subject or not body:
        return JsonResponse({'success': False, 'error': 'فیلدهای اجباری خالی است'})

    try:
        mail = EmailMultiAlternatives(
            subject=subject,
            body='این ایمیل به صورت HTML ارسال شده است.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[msg.email],
        )
        mail.attach_alternative(body, "text/html")
        mail.send()
        msg.is_read = True
        msg.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def mark_read(request, pk):
    """علامت‌گذاری به عنوان خوانده شده"""
    if not request.user.is_staff:
        return JsonResponse({'success': False}, status=403)
    try:
        msg = ContactMessage.objects.get(id=pk)
        msg.is_read = True
        msg.save()
        return JsonResponse({'success': True})
    except ContactMessage.DoesNotExist:
        return JsonResponse({'success': False})


@login_required
@require_POST
def delete_message(request, pk):
    """حذف پیام"""
    if not request.user.is_staff:
        return JsonResponse({'success': False}, status=403)
    try:
        msg = ContactMessage.objects.get(id=pk)
        if msg.attachment:
            try:
                os.remove(msg.attachment.path)
            except:
                pass
        msg.delete()
        return JsonResponse({'success': True})
    except ContactMessage.DoesNotExist:
        return JsonResponse({'success': False})


def _check_lockout(request):
    """بررسی قفل زمانی"""
    locked_until = request.session.get('locked_until', 0)
    now = time.time()
    if locked_until > now:
        return {'locked': True, 'wait_minutes': int((locked_until - now) / 60) + 1}
    if locked_until > 0 and locked_until <= now:
        request.session.pop('locked_until', None)
        request.session['login_attempts'] = 0
    return {'locked': False, 'wait_minutes': 0}
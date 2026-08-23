import time
import os
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.views.decorators.http import require_POST
from main.models import ContactMessage


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
    return render(request, 'main_pages/main/contact.html', {
        'messages_list': ContactMessage.objects.all().order_by('-created_at'),
        'messages_count': ContactMessage.objects.count(),
        'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
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
    if not msg.email or not subject or not body:
        return JsonResponse({'success': False, 'error': 'فیلدهای اجباری خالی است'})
    try:
        mail = EmailMultiAlternatives(subject=subject, body='این ایمیل HTML است.',
                                      from_email=settings.DEFAULT_FROM_EMAIL, to=[msg.email])
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
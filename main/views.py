import re
import os
import traceback
from django.shortcuts import render, redirect
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from .models import ContactMessage
from blog.models import Post
from portfolio.models import PortfolioItem, PortfolioCategory
from main.models import SiteSetting

def home(request):
    # ← این خط حیاتی است: دریافت تنظیمات از دیتابیس
    site = SiteSetting.load() 
    
    latest_posts = Post.objects.filter(published=True)[:3]
    latest_works = PortfolioItem.objects.filter(published=True)[:4]
    
    return render(request, 'main_pages/home.html', {
        'site': site,  # ← این خط حیاتی است: ارسال به تمپلیت
        'latest_posts': latest_posts,
        'latest_works': latest_works,
    })


def about(request):
    return render(request, 'main_pages/about.html')


def contact(request):
    context = {}

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        phone_clean = phone.replace(' ', '').replace('-', '')
        if not re.match(r'^(\+98|0)[0-9]{10,11}$', phone_clean):
            context['phone_error'] = 'شماره تماس معتبر نیست. لطفاً مانند 09123456789 وارد کنید.'
            return render(request, 'main_pages/contact.html', context)
        subject = request.POST.get('subject', 'پیام جدید از وب‌سایت').strip()
        message = request.POST.get('message', '').strip()
        attachment = request.FILES.get('attachment')

        # اعتبارسنجی فایل پیوست
        attachment_content = None
        attachment_mime = 'application/octet-stream'
        if attachment:
            if attachment.size > 5 * 1024 * 1024:
                context['file_error'] = 'حجم فایل نباید بیشتر از ۵ مگابایت باشد.'
                return render(request, 'main_pages/contact.html', context)

            allowed_types = [
                'image/jpeg', 'image/png', 'image/jpg', 'image/gif', 'image/webp',
                'application/pdf', 'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/acad', 'application/dwg', 'application/x-dwg',
            ]
            allowed_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.doc', '.docx', '.dwg']
            ext = os.path.splitext(attachment.name)[1].lower()
            if attachment.content_type not in allowed_types and ext not in allowed_exts:
                context['file_error'] = 'نوع فایل مجاز نیست. لطفاً تصویر، PDF، Word یا DWG ارسال کنید.'
                return render(request, 'main_pages/contact.html', context)

            # محتوا رو قبل از save بخون و نگه دار
            attachment_content = attachment.read()
            attachment_mime = attachment.content_type or 'application/octet-stream'
            attachment.seek(0)

        # ذخیره در دیتابیس
        contact_msg = ContactMessage.objects.create(
            name=name, email=email, phone=phone,
            message=f"{subject}\n\n{message}"
        )
        if attachment:
            contact_msg.attachment = attachment
            contact_msg.save()

        # ارسال ایمیل با قالب مشکی/نارنجی
        try:
            attachment_html = ""
            if attachment_content:
                size_kb = round(len(attachment_content) / 1024)
                attachment_html = f"""<div class='field attachment'><div class='label'>📎 فایل پیوست</div><div class='value'>{attachment.name} ({size_kb} KB)</div></div>"""

            html_content = f"""
            <html dir="rtl">
            <head>
                <style>
                    body {{ font-family: 'Vazirmatn', Tahoma, sans-serif; background: #0b0d10; padding: 24px; margin: 0; }}
                    .container {{ max-width: 620px; margin: 0 auto; background: #141419; border-radius: 16px; overflow: hidden; border: 1px solid rgba(255,107,0,0.3); box-shadow: 0 10px 40px rgba(0,0,0,0.5); }}
                    .header {{ background: linear-gradient(135deg, #ff6b00, #ff8533); color: #ffffff; padding: 28px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 1.4rem; }}
                    .header p {{ margin: 8px 0 0; font-size: 0.85rem; opacity: 0.9; }}
                    .content {{ padding: 28px; }}
                    .field {{ margin-bottom: 16px; padding: 14px 18px; background: #1a1d24; border-radius: 10px; border-right: 4px solid #ff6b00; }}
                    .label {{ font-weight: 700; color: #ff9a4d; margin-bottom: 6px; font-size: 0.82rem; }}
                    .value {{ color: #eef1f6; line-height: 1.8; font-size: 0.95rem; word-break: break-word; }}
                    .attachment {{ border-right-color: #ffaa00; background: #201710; }}
                    .footer {{ background: #0b0d10; color: #9aa3b2; padding: 18px; text-align: center; font-size: 0.78rem; border-top: 1px solid rgba(255,255,255,0.06); }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📧 پیام جدید از وب‌سایت زاسکو ذوب</h1>
                        <p>فرم تماس با ما</p>
                    </div>
                    <div class="content">
                        <div class="field"><div class="label">نام و نام خانوادگی</div><div class="value">{name}</div></div>
                        <div class="field"><div class="label">ایمیل</div><div class="value">{email}</div></div>
                        <div class="field"><div class="label">شماره تماس</div><div class="value" dir="ltr">{phone}</div></div>
                        <div class="field"><div class="label">موضوع</div><div class="value">{subject}</div></div>
                        <div class="field"><div class="label">پیام</div><div class="value">{message}</div></div>
                        {attachment_html}
                    </div>
                    <div class="footer">این پیام از طریق فرم تماس وب‌سایت زاسکو ذوب ارسال شده است.</div>
                </div>
            </body>
            </html>
            """

            msg = EmailMultiAlternatives(
                subject=f'پیام جدید از {name} - {subject}',
                body=f'نام: {name}\nایمیل: {email}\nتلفن: {phone}\n\n{message}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.CONTACT_EMAIL],
                reply_to=[email] if email else []
            )
            msg.attach_alternative(html_content, "text/html")

            # پیوست با محتوای از قبل خونده‌شده (دیگه 0B نمی‌شه!)
            if attachment_content:
                msg.attach(attachment.name, attachment_content, attachment_mime)

            msg.send()
            return redirect('/contact/?success=1')

        except Exception as e:
            error_detail = str(e)
            print("=" * 80)
            print("❌ خطا در ارسال ایمیل:")
            print(f"   نوع خطا: {type(e).__name__}")
            print(f"   پیام: {error_detail}")
            print("=" * 80)
            context['email_error'] = error_detail
            return render(request, 'main_pages/contact.html', context)

    return render(request, 'main_pages/contact.html', context)
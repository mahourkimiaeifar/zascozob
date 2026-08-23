from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone


# ═══ زیرساخت سطل زباله (مشترک برای بقیه اپ‌ها) ═══
class SoftDeleteManager(models.Manager):
    """فقط آیتم‌های زنده"""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    def deleted(self):
        """سطل زباله"""
        return super().get_queryset().filter(is_deleted=True)


class AllObjectsManager(models.Manager):
    """همه‌چیز، حتی سطل زباله"""
    pass


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField('حذف شده', default=False)
    deleted_at = models.DateTimeField('تاریخ حذف', null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


# ═══ تنظیمات سایت — فقط ویرایش، هرگز حذف ═══
class SiteSetting(models.Model):
    # ═══ عمومی ═══
    site_title = models.CharField('عنوان اصلی سایت', max_length=100, default='زاسکو ذوب',
        help_text='در هر صفحه جلوی آن می‌آید؛ مثل «زاسکو ذوب - درباره ما»')
    subtitle = models.CharField('زیرعنوان سایت', max_length=150, default='قطعه ریزان ذوب آرای سپاهان',
        help_text='در هدر یا هیرو نمایش داده می‌شود')
    about_text = models.TextField('متن توضیح کلی شرکت',
        default='کارخانه ریخته‌گری زاسکو ذوب فعال در زمینه‌های ریخته‌گری آلیاژهای آهنی و غیرآهنی...')

    # ═══ اطلاعات شرکت (ستون اول فوتر) ═══
    footer_title_company = models.CharField('سرعنوان: اطلاعات شرکت', max_length=100, default='اطلاعات شرکت')
    phone_mobile = models.CharField('شماره موبایل شرکت', max_length=20, default='+989134302591')
    phone_office = models.CharField('شماره تلفن ثابت شرکت', max_length=20, default='031-42318530')
    email = models.EmailField('ایمیل شرکت', default='zascozob@gmail.com')
    address_factory = models.TextField('آدرس کارخانه',
        default='اصفهان، نجف‌آباد، شهرک صنعتی منتظریه، ابتدای خیابان قادری شمالی، ضلع غربی، پلاک ۲، کد ۱۳۰')
    address_rd = models.TextField('آدرس واحد تحقیقات و فناوری',
        default='اصفهان، نجف‌آباد، دانشگاه آزاد اسلامی، ساختمان علم و فناوری، اتاق ۳۰۲')

    # ═══ دیگر صفحات (ستون دوم فوتر) ═══
    footer_title_pages = models.CharField('سرعنوان: دیگر صفحات', max_length=100, default='دیگر صفحات')
    footer_description = models.TextField('توضیحات زیر عنوان فوتر (بالای کپی‌رایت)', blank=True)
    catalog_link = models.URLField('لینک کاتالوگ', blank=True)
    catalog_qr = models.ImageField('تصویر QR کاتالوگ', upload_to='catalog/', blank=True)

    # ═══ خبرنامه (ستون سوم فوتر) ═══
    footer_title_newsletter = models.CharField('سرعنوان: خبرنامه', max_length=100, default='خبرنامه')
    newsletter_text = models.CharField('متن خبرنامه', max_length=200,
        default='با عضویت در خبرنامه سریع‌تر در جریان اخبار قرار بگیرید')
    newsletter_button_text = models.CharField('متن دکمه خبرنامه', max_length=50, default='مشترک شدن')

    # ═══ شبکه‌های اجتماعی (۶ لینک) ═══
    link_whatsapp = models.URLField('لینک واتساپ', blank=True)
    link_instagram = models.URLField('لینک اینستاگرام', blank=True)
    link_telegram = models.URLField('لینک تلگرام', blank=True)
    link_linkedin = models.URLField('لینک لینکدین', blank=True)
    link_aparat = models.URLField('لینک آپارات', blank=True)
    link_youtube = models.URLField('لینک یوتیوب', blank=True)

    # ═══ کپی‌رایت ═══
    copyright_text = models.TextField('متن کپی‌رایت',
        default='تمامی منابع، تصاویر، حقوق و مطالب موجود در این وبسایت متعلق به قطعه ریزان ذوب آرای سپاهان است و هرگونه کپی‌برداری از آن پیگرد قانونی دارد © ۱۴۰۵')

    class Meta:
        verbose_name = 'تنظیمات سایت'
        verbose_name_plural = 'تنظیمات سایت'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError('⛔ تنظیمات سایت قابل حذف نیست؛ فقط ویرایش کن.')

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def social_links(self):
        """لیست شبکه‌های اجتماعی پر شده"""
        items = [
            ('واتساپ', self.link_whatsapp, 'whatsapp'),
            ('اینستاگرام', self.link_instagram, 'instagram'),
            ('تلگرام', self.link_telegram, 'telegram'),
            ('لینکدین', self.link_linkedin, 'linkedin'),
            ('آپارات', self.link_aparat, 'aparat'),
            ('یوتیوب', self.link_youtube, 'youtube'),
        ]
        return [{'name': n, 'url': u, 'icon': i} for n, u, i in items if u]

    def __str__(self):
        return self.site_title
    
# ═══ مدل پیام‌های تماس با ما ═══
class ContactMessage(models.Model):
    name = models.CharField('نام و نام خانوادگی', max_length=150)
    email = models.EmailField('ایمیل', max_length=254, blank=True, null=True)
    phone = models.CharField('شماره تماس', max_length=20)
    message = models.TextField('متن پیام')
    attachment = models.FileField('فایل پیوست', upload_to='contact_attachments/%Y/%m/', blank=True, null=True)
    reply_subject = models.CharField('موضوع پاسخ', max_length=255, blank=True, null=True)
    reply_body = models.TextField('متن پاسخ', blank=True, null=True)
    replied_at = models.DateTimeField('تاریخ پاسخ', null=True, blank=True)
    created_at = models.DateTimeField('تاریخ ثبت', auto_now_add=True)
    is_read = models.BooleanField('خوانده شده', default=False)

    class Meta:
        verbose_name = 'پیام تماس'
        verbose_name_plural = 'پیام‌های تماس'
        ordering = ['-created_at']

    def __str__(self):
        return f'پیام از {self.name} - {self.created_at.strftime("%Y/%m/%d")}'


# 🔒 قفل حذف حتی از طریق کوئری‌ست
@receiver(pre_delete, sender=SiteSetting)
def protect_site_setting(sender, instance, **kwargs):
    raise PermissionError('⛔ تنظیمات سایت قابل حذف نیست؛ فقط ویرایش کن.')

class ReplyAttachment(models.Model):
    message = models.ForeignKey(ContactMessage, on_delete=models.CASCADE, related_name='reply_attachments', verbose_name='پیام')
    file = models.FileField('فایل پیوست', upload_to='reply_attachments/%Y/%m/')
    uploaded_at = models.DateTimeField('تاریخ بارگذاری', auto_now_add=True)

    class Meta:
        verbose_name = 'پیوست پاسخ'
        verbose_name_plural = 'پیوست‌های پاسخ'

    def __str__(self):
        return self.file.name
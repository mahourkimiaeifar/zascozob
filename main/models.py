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
    site_title = models.CharField('عنوان اصلی سایت', max_length=100, default='زاسکو ذوب',
        help_text='در هر صفحه جلوی آن می‌آید؛ مثل «زاسکو ذوب - درباره ما»')
    phone_mobile = models.CharField('شماره موبایل شرکت', max_length=20)
    phone_office = models.CharField('شماره تلفن ثابت شرکت', max_length=20)
    email = models.EmailField('ایمیل شرکت')
    address_factory = models.TextField('آدرس کارخانه')
    address_rd = models.TextField('آدرس واحد تحقیقات و فناوری')
    link_whatsapp = models.URLField('لینک واتساپ', blank=True)
    link_instagram = models.URLField('لینک اینستاگرام', blank=True)
    footer_title = models.CharField('عنوان فوتر', max_length=150)
    footer_description = models.TextField('توضیحات زیر عنوان فوتر')
    newsletter_text = models.CharField('متن خبرنامه', max_length=200,
        default='با عضویت در خبرنامه سریع‌تر در جریان اخبار قرار بگیرید')
    copyright_text = models.TextField('متن کپی‌رایت')
    catalog_qr = models.ImageField('تصویر QR کاتالوگ', upload_to='catalog/', blank=True)
    catalog_link = models.URLField('لینک کاتالوگ', blank=True)

    class Meta:
        verbose_name = 'تنظیمات سایت'; verbose_name_plural = 'تنظیمات سایت'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError('⛔ تنظیمات سایت قابل حذف نیست؛ فقط ویرایش کن.')

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self): return self.site_title
    
# ═══ مدل پیام‌های تماس با ما ═══
class ContactMessage(models.Model):
    name = models.CharField('نام و نام خانوادگی', max_length=150)
    email = models.EmailField('ایمیل', max_length=254, blank=True, null=True)
    phone = models.CharField('شماره تماس', max_length=20)
    message = models.TextField('متن پیام')
    attachment = models.FileField('فایل پیوست', upload_to='contact_attachments/%Y/%m/', blank=True, null=True)
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
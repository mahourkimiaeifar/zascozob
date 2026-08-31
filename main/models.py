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
    
class MediaFile(SoftDeleteModel):
    """کتابخانه مرکزی فایل‌ها"""
    FILE_TYPE_CHOICES = [
        ('image', 'تصویر'),
        ('document', 'سند'),
        ('video', 'ویدیو'),
        ('audio', 'صدا'),
        ('other', 'سایر'),
    ]
    
    title = models.CharField('عنوان فایل', max_length=200)
    file = models.FileField('فایل', upload_to='media_library/%Y/%m/')
    file_type = models.CharField('نوع فایل', max_length=20, choices=FILE_TYPE_CHOICES, default='other')
    file_size = models.PositiveBigIntegerField('حجم فایل (بایت)', default=0)
    alt_text = models.CharField('متن جایگزین (ALT)', max_length=255, blank=True)
    description = models.TextField('توضیحات', blank=True)
    uploaded_by = models.ForeignKey('auth.User', verbose_name='آپلود کننده', on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField('تاریخ آپلود', auto_now_add=True)
    used_in = models.CharField('استفاده شده در', max_length=100, blank=True, help_text='مثلاً: portfolio, blog, gallery')

    class Meta:
        verbose_name = 'فایل'
        verbose_name_plural = 'کتابخانه فایل‌ها'
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # تشخیص خودکار نوع فایل و حجم
        if self.file and not self.file_size:
            self.file_size = self.file.size
        
        if self.file and self.file_type == 'other':
            ext = self.file.name.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'webp', 'gif', 'svg']:
                self.file_type = 'image'
            elif ext in ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar']:
                self.file_type = 'document'
            elif ext in ['mp4', 'avi', 'mov', 'mkv']:
                self.file_type = 'video'
            elif ext in ['mp3', 'wav', 'ogg']:
                self.file_type = 'audio'
                
        super().save(*args, **kwargs)

    def get_url(self):
        """دریافت URL فایل"""
        return self.file.url if self.file else ''

    def get_thumbnail_url(self):
        """دریافت URL تصویر بندانگشتی (برای تصاویر)"""
        if self.file_type == 'image':
            return self.file.url
        return None
    
class AuditLog(models.Model):
    """لاگ فعالیت‌های کاربران"""
    user = models.ForeignKey(
        'auth.User',
        verbose_name='کاربر',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action = models.CharField('عملیات', max_length=100)
    model_name = models.CharField('مدل', max_length=100, blank=True)
    object_id = models.PositiveIntegerField('شناسه شیء', null=True, blank=True)
    description = models.TextField('توضیحات', blank=True)
    ip_address = models.GenericIPAddressField('آدرس IP', null=True, blank=True)
    created_at = models.DateTimeField('تاریخ', auto_now_add=True)
    
    class Meta:
        verbose_name = 'لاگ فعالیت'
        verbose_name_plural = 'لاگ فعالیت‌ها'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user} - {self.action} - {self.created_at}'
    
class SiteSetting(SoftDeleteModel):
    # ... فیلدهای موجود ...
    
    maintenance_mode = models.BooleanField('حالت تعمیر', default=False)
    maintenance_message = models.TextField(
        'پیام حالت تعمیر',
        default='سایت در حال بروزرسانی است. لطفاً بعداً مراجعه کنید.',
        blank=True
    )
    
    class Meta:
        verbose_name = 'تنظیمات سایت'
        verbose_name_plural = 'تنظیمات سایت'

    def __str__(self):
        return 'تنظیمات اصلی سایت'

    # ═══ این متد را اضافه کنید ═══
    @classmethod
    def load(cls):
        # اگر تنظیماتی وجود داشت آن را برمی‌گرداند، در غیر این صورت یک رکورد جدید می‌سازد
        setting, created = cls.objects.get_or_create(
            id=1,
            defaults={
                # اگر فیلد اجباری (required=True) دارید که مقدار پیش‌فرض ندارد، 
                # نام آن را اینجا با یک مقدار خالی یا پیش‌فرض بنویسید تا خطا ندهد.
                # مثال: 'site_name': 'زاسکو ذوب'
            }
        )
        return setting
    
class CustomRole(SoftDeleteModel):
    """نقش‌های سفارشی برای مدیریت دسترسی‌ها"""
    name = models.CharField('نام نقش', max_length=100, unique=True)
    description = models.TextField('توضیحات', blank=True)
    permissions = models.JSONField('دسترسی‌ها', default=list, blank=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    
    # دسترسی‌های پیش‌فرض
    ALL_PERMISSIONS = [
        ('can_add_article', 'افزودن مقاله'),
        ('can_edit_article', 'ویرایش مقاله'),
        ('can_delete_article', 'حذف مقاله'),
        ('can_publish_article', 'انتشار مقاله'),
        
        ('can_add_portfolio', 'افزودن نمونه‌کار'),
        ('can_edit_portfolio', 'ویرایش نمونه‌کار'),
        ('can_delete_portfolio', 'حذف نمونه‌کار'),
        
        ('can_add_gallery', 'افزودن گالری'),
        ('can_edit_gallery', 'ویرایش گالری'),
        ('can_delete_gallery', 'حذف گالری'),
        
        ('can_approve_comments', 'تایید/رد کامنت‌ها'),
        ('can_delete_comments', 'حذف کامنت‌ها'),
        
        ('can_reply_messages', 'پاسخ به پیام‌ها'),
        ('can_send_email', 'ارسال ایمیل'),
        
        ('can_manage_media', 'مدیریت کتابخانه فایل‌ها'),
        ('can_manage_users', 'مدیریت کاربران'),
        ('can_manage_roles', 'مدیریت نقش‌ها'),
        
        ('can_view_analytics', 'مشاهده آمار و تحلیل‌ها'),
        ('can_manage_settings', 'مدیریت تنظیمات سایت'),
    ]
    
    class Meta:
        verbose_name = 'نقش'
        verbose_name_plural = 'نقش‌ها'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """پروفایل کاربری با نقش سفارشی"""
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(CustomRole, verbose_name='نقش', on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField('شماره تماس', max_length=20, blank=True)
    avatar = models.ImageField('آواتار', upload_to='avatars/', blank=True, null=True)
    
    class Meta:
        verbose_name = 'پروفایل کاربری'
        verbose_name_plural = 'پروفایل‌های کاربری'
    
    def __str__(self):
        return f'پروفایل {self.user.username}'
    
    def has_permission(self, permission_code):
        """بررسی دسترسی کاربر"""
        if self.user.is_superuser:
            return True
        if self.role and permission_code in self.role.permissions:
            return True
        return False
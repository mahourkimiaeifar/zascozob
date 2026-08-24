from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from main.models import SoftDeleteModel


class Category(models.Model):
    title = models.CharField('عنوان دسته‌بندی', max_length=100)
    slug = models.SlugField('اسلاگ', max_length=120, unique=True, allow_unicode=True, blank=True)
    parent = models.ForeignKey('self', verbose_name='دسته مادر', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='children')

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'

    def save(self, *a, **k):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*a, **k)

    def __str__(self):
        return f'{self.parent.title} > {self.title}' if self.parent else self.title


class Post(SoftDeleteModel):
    title = models.CharField('عنوان مقاله', max_length=200)
    slug = models.SlugField('اسلاگ', max_length=220, unique=True, allow_unicode=True, blank=True)
    excerpt = models.TextField('چکیده', blank=True)
    content = models.TextField('متن مقاله')
    featured_image = models.ImageField('تصویر شاخص', upload_to='blog/%Y/%m/')
    category = models.ForeignKey(Category, verbose_name='دسته‌بندی', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='posts')
    read_time = models.PositiveIntegerField('زمان تقریبی خواندن (دقیقه)', default=1)
    views = models.PositiveIntegerField('بازدیدها', default=0)
    likes = models.PositiveIntegerField('لایک‌ها', default=0)
    published = models.BooleanField('منتشر شده', default=False)
    publish_date = models.DateTimeField('تاریخ انتشار', null=True, blank=True)
    updated = models.DateTimeField('تاریخ به‌روزرسانی', auto_now=True)
    created = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)

    class Meta:
        verbose_name = 'مقاله'
        verbose_name_plural = 'مقالات'
        ordering = ['-publish_date', '-created']

    def save(self, *a, **k):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*a, **k)

    def __str__(self):
        return self.title


class Comment(SoftDeleteModel):
    post = models.ForeignKey(Post, verbose_name='مقاله', on_delete=models.CASCADE, related_name='comments')
    name = models.CharField('نام', max_length=100)
    text = models.TextField('متن کامنت')
    likes = models.PositiveIntegerField('لایک', default=0)
    dislikes = models.PositiveIntegerField('دیسلایک', default=0)
    approved = models.BooleanField('تایید شده', default=False)
    created = models.DateTimeField('تاریخ ثبت', auto_now_add=True)
    published_at = models.DateTimeField('تاریخ انتشار', null=True, blank=True)

    class Meta:
        verbose_name = 'کامنت'
        verbose_name_plural = 'کامنت‌ها'
        ordering = ['-created']

    def approve(self):
        self.approved = True
        self.published_at = timezone.now()
        self.save(update_fields=['approved', 'published_at'])

    @property
    def is_public(self):
        return self.approved and not self.is_deleted

    def __str__(self):
        return f'{self.name} — {self.post.title}'
    
class VoteRecord(models.Model):
    """رکورد رأی‌ها برای جلوگیری از رأی تکراری"""
    VOTE_TYPES = [('like', 'لایک'), ('dislike', 'دیسلایک')]
    TARGET_TYPES = [('post', 'مقاله'), ('comment', 'کامنت')]
    
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True,
        related_name='blog_votes', verbose_name='کاربر')
    ip_address = models.GenericIPAddressField('آی‌پی', null=True, blank=True)
    session_key = models.CharField('شناسه سشن', max_length=40, blank=True)
    
    target_type = models.CharField('نوع', max_length=10, choices=TARGET_TYPES)
    target_id = models.PositiveIntegerField('شناسه هدف')
    vote_type = models.CharField('نوع رأی', max_length=10, choices=VOTE_TYPES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'رکورد رأی'
        verbose_name_plural = 'رکوردهای رأی'
        unique_together = [
            ('user', 'target_type', 'target_id'),
            ('ip_address', 'target_type', 'target_id'),
            ('session_key', 'target_type', 'target_id'),
        ]
    
    def __str__(self):
        return f'{self.vote_type} → {self.target_type}#{self.target_id}'
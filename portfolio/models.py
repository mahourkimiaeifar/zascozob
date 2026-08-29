from django.db import models
from django.utils.text import slugify
from main.models import SoftDeleteModel
from ckeditor_uploader.fields import RichTextUploadingField


class PortfolioCategory(SoftDeleteModel):
    title = models.CharField('عنوان دسته', max_length=120)
    slug = models.SlugField('اسلاگ', max_length=160, unique=True, allow_unicode=True)
    description = models.TextField('توضیحات سئو', blank=True)
    order = models.PositiveIntegerField('ترتیب', default=0)

    class Meta:
        verbose_name = 'دسته نمونه‌کار'
        verbose_name_plural = 'دسته‌های نمونه‌کار'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)


class PortfolioItem(SoftDeleteModel):
    title = models.CharField('عنوان قطعه', max_length=200)
    slug = models.SlugField('اسلاگ', max_length=220, unique=True, allow_unicode=True)
    category = models.ForeignKey(
        PortfolioCategory, verbose_name='دسته',
        null=True, blank=True, on_delete=models.SET_NULL, related_name='items'
    )
    summary = models.CharField('خلاصه', max_length=300, blank=True)
    content = RichTextUploadingField('توضیحات کامل', blank=True)
    featured_image = models.ImageField('تصویر شاخص', upload_to='portfolio/%Y/%m/')
    image_alt = models.CharField('متن جایگزین تصویر (سئو)', max_length=200, blank=True)
    material = models.CharField('جنس آلیاژ', max_length=100, blank=True)
    weight = models.CharField('وزن قطعه', max_length=50, blank=True)
    standard = models.CharField('استاندارد', max_length=100, blank=True)
    meta_description = models.CharField('توضیحات متا سئو', max_length=300, blank=True)
    published = models.BooleanField('منتشر شده', default=True)
    views = models.PositiveIntegerField('بازدید', default=0)
    created = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    updated = models.DateTimeField('به‌روزرسانی', auto_now=True)

    class Meta:
        verbose_name = 'نمونه‌کار'
        verbose_name_plural = 'نمونه‌کارها'
        ordering = ['-created']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True)
            slug, n = base, 1
            while PortfolioItem.objects.filter(slug=slug).exists():
                n += 1
                slug = f'{base}-{n}'
            self.slug = slug
        super().save(*args, **kwargs)
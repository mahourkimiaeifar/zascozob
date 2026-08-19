from django.db import models
from django.utils.text import slugify
from main.models import SoftDeleteModel

class Tag(models.Model):
    title = models.CharField('برچسب', max_length=100, unique=True)
    slug = models.SlugField('اسلاگ', max_length=120, unique=True, allow_unicode=True, blank=True)

    class Meta:
        verbose_name = 'برچسب'; verbose_name_plural = 'برچسب‌ها'
    def save(self, *a, **k):
        if not self.slug: self.slug = slugify(self.title, allow_unicode=True)
        super().save(*a, **k)
    @staticmethod
    def bulk_from_string(text):
        tags = []
        for part in text.split('*'):
            t = part.strip()
            if t:
                obj, _ = Tag.objects.get_or_create(title=t)
                tags.append(obj)
        return tags
    def __str__(self): return self.title

class PortfolioItem(SoftDeleteModel):
    title = models.CharField('عنوان نمونه‌کار', max_length=200)
    slug = models.SlugField('اسلاگ', max_length=220, unique=True, allow_unicode=True, blank=True)
    excerpt = models.TextField('چکیده', blank=True)
    description = models.TextField('توضیحات')
    cover = models.ImageField('تصویر شاخص', upload_to='portfolio/%Y/%m/')
    tags = models.ManyToManyField(Tag, verbose_name='برچسب‌ها', blank=True, related_name='items')
    published = models.BooleanField('منتشر شده', default=False)
    created = models.DateTimeField('تاریخ', auto_now_add=True)
    order = models.PositiveIntegerField('ترتیب', default=0)

    class Meta:
        verbose_name = 'نمونه‌کار'; verbose_name_plural = 'نمونه‌کارها'; ordering = ['-created']
    def save(self, *a, **k):
        if not self.slug: self.slug = slugify(self.title, allow_unicode=True)
        super().save(*a, **k)
    def assign_tags_from_string(self, text):
        self.tags.set(Tag.bulk_from_string(text))
    def __str__(self): return self.title
from django.db import models
from main.models import SoftDeleteModel

class GalleryAlbum(SoftDeleteModel):
    title = models.CharField('عنوان آلبوم', max_length=200)
    description = models.TextField('توضیحات', blank=True)
    created = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    published = models.BooleanField('منتشر شده', default=True)

    class Meta:
        verbose_name = 'آلبوم گالری'
        verbose_name_plural = 'آلبوم‌های گالری'
        ordering = ['-created']

    def __str__(self):
        return self.title

    def images_count(self):
        return self.images.count()


class GalleryImage(SoftDeleteModel):
    album = models.ForeignKey(
        GalleryAlbum, 
        verbose_name='آلبوم', 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField('تصویر', upload_to='gallery/%Y/%m/')
    title = models.CharField('عنوان تصویر', max_length=200, blank=True)
    description = models.TextField('توضیحات', blank=True)
    order = models.PositiveIntegerField('ترتیب', default=0)
    uploaded_at = models.DateTimeField('تاریخ آپلود', auto_now_add=True)

    class Meta:
        verbose_name = 'تصویر'
        verbose_name_plural = 'تصاویر'
        ordering = ['order', 'uploaded_at']

    def __str__(self):
        return self.title or f'تصویر {self.id}'
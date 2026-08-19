from django.db import models
from main.models import SoftDeleteModel

class GalleryAlbum(SoftDeleteModel):
    title = models.CharField('عنوان تصاویر', max_length=200)
    description = models.TextField('توضیحات', blank=True)
    created = models.DateTimeField('تاریخ آپلود', auto_now_add=True)
    published = models.BooleanField('منتشر شده', default=True)

    class Meta:
        verbose_name = 'آلبوم گالری'; verbose_name_plural = 'گالری تصاویر'; ordering = ['-created']
    def __str__(self): return self.title

class GalleryImage(SoftDeleteModel):
    album = models.ForeignKey(GalleryAlbum, verbose_name='آلبوم', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField('تصویر', upload_to='gallery/%Y/%m/')
    uploaded_at = models.DateTimeField('تاریخ آپلود', auto_now_add=True)

    class Meta:
        verbose_name = 'تصویر'; verbose_name_plural = 'تصاویر'
    def __str__(self): return self.album.title
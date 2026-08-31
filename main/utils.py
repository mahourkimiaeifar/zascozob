from main.models import MediaFile
from django.core.files.storage import default_storage
import os


def register_file_in_library(file_path, title=None, uploaded_by=None, used_in='', auto_create=True):
    """
    ثبت فایل در کتابخانه Media Library
    
    اگر فایل قبلاً ثبت شده، همان را برمی‌گرداند.
    اگر auto_create=True باشد و فایل ثبت نشده باشد، یک رکورد جدید می‌سازد.
    """
    # بررسی کنید که آیا فایل قبلاً ثبت شده
    existing = MediaFile.objects.filter(file=file_path).first()
    if existing:
        return existing
    
    if not auto_create:
        return None
    
    # ساخت رکورد جدید
    if not title:
        title = os.path.basename(file_path)
    
    media_file = MediaFile.objects.create(
        title=title,
        file=file_path,
        uploaded_by=uploaded_by,
        used_in=used_in,
    )
    
    return media_file


def sync_existing_files_to_library(app_label='', used_in=''):
    """
    همگام‌سازی فایل‌های موجود در دیتابیس با Media Library
    
    این تابع تمام فایل‌های موجود در مدل‌های مختلف را اسکن کرده
    و در Media Library ثبت می‌کند.
    """
    from django.apps import apps
    from django.db import models
    
    count = 0
    
    # دریافت تمام مدل‌ها
    if app_label:
        model_list = apps.get_app_config(app_label).get_models()
    else:
        model_list = apps.get_models()
    
    for model in model_list:
        # پیدا کردن فیلدهای FileField و ImageField
        file_fields = [
            f for f in model._meta.get_fields()
            if isinstance(f, (models.FileField, models.ImageField))
        ]
        
        if not file_fields:
            continue
        
        # اسکن تمام رکوردهای مدل
        for obj in model.objects.all():
            for field in file_fields:
                file_instance = getattr(obj, field.name)
                if file_instance and file_instance.name:
                    title = getattr(obj, 'title', f'{model.__name__} - {obj.id}')
                    register_file_in_library(
                        file_instance.name,
                        title=f"{title} ({field.name})",
                        used_in=used_in or f"{app_label}.{model.__name__}",
                        auto_create=True
                    )
                    count += 1
    
    return count
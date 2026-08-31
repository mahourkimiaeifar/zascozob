from django.db.models.signals import post_save
from django.dispatch import receiver
from main.utils import register_file_in_library
from portfolio.models import PortfolioItem
from blog.models import Post


@receiver(post_save, sender=PortfolioItem)
def auto_register_portfolio_image(sender, instance, created, **kwargs):
    """ثبت خودکار تصویر نمونه‌کار در Media Library"""
    if instance.featured_image:
        register_file_in_library(
            instance.featured_image.name,
            title=instance.title,
            used_in='portfolio',
            auto_create=True
        )


@receiver(post_save, sender=Post)
def auto_register_blog_image(sender, instance, created, **kwargs):
    """ثبت خودکار تصویر مقاله در Media Library"""
    if instance.featured_image:
        register_file_in_library(
            instance.featured_image.name,
            title=instance.title,
            used_in='blog',
            auto_create=True
        )
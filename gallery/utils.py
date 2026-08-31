from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os


def add_watermark_and_compress(image_file, watermark_text="ZASCO"):
    """
    افزودن واترمارک + فشرده‌سازی تصویر
    """
    # باز کردن تصویر
    img = Image.open(image_file)
    
    # تبدیل به RGBA
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # ایجاد لایه شفاف برای واترمارک
    txt_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)
    
    # تنظیم فونت
    try:
        font_size = max(36, img.width // 20)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # محاسبه موقعیت واترمارک (گوشه پایین راست)
    bbox = draw.textbbox((0, 0), watermark_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = img.width - text_width - 20
    y = img.height - text_height - 20
    
    # رسم واترمارک با شفافیت
    draw.text(
        (x, y), 
        watermark_text, 
        font=font, 
        fill=(255, 255, 255, 128)
    )
    
    # ترکیب تصویر اصلی با لایه واترمارک
    watermarked = Image.alpha_composite(img, txt_layer)
    
    # تغییر سایز اگر تصویر خیلی بزرگ باشد (حداکثر 1920x1080)
    max_size = (1920, 1080)
    watermarked.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # تبدیل به RGB
    watermarked = watermarked.convert('RGB')
    
    # ذخیره با کیفیت 85
    buffer = BytesIO()
    watermarked.save(buffer, format='JPEG', quality=85, optimize=True, progressive=True)
    buffer.seek(0)
    
    return buffer
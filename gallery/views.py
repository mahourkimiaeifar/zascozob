import json
from django.shortcuts import render
from .models import GalleryAlbum
from main.models import SiteSetting

def gallery_3d_view(request):
    albums = GalleryAlbum.objects.filter(is_deleted=False, published=True).order_by('-created')
    
    albums_data = []
    for album in albums:
        images = album.images.filter(is_deleted=False).order_by('order', 'uploaded_at')
        albums_data.append({
            'id': album.id,
            'title': album.title,
            'description': album.description or '',
            'cover': images[0].image.url if images else None,
            'images': [
                {
                    'id': img.id,
                    'url': img.image.url,
                    'title': img.title or '',
                    'description': img.description or '',
                    'order': img.order
                } for img in images
            ],
            'images_count': images.count()
        })
    
    # ← اضافه کن: context برای navbar و footer
    return render(request, 'gallery_3d.html', {
        'albums_data': albums_data,
        'albums_json': json.dumps(albums_data, ensure_ascii=False),
        'site': SiteSetting.load(),  # ← برای navbar و footer
    })
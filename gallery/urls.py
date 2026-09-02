from django.urls import path
from . import views

app_name = 'gallery'

urlpatterns = [
    path('3d/', views.gallery_3d_view, name='gallery_3d'),
]
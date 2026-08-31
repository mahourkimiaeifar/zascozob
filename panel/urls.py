from django.urls import path
from . import views

app_name = 'panel'
PANEL_PATH = 'zasco-admin-x9k2p'

urlpatterns = [
    # path('accounts/', include('django.contrib.auth.urls'))
    path('login/', views.panel_login, name='login'),
    path('logout/', views.panel_logout, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('main/contact/', views.main_contact, name='main_contact'),
    path('main/contact/reply/', views.main_contact_reply, name='main_contact_reply'),
    path('api/mark-read/<int:pk>/', views.mark_read, name='mark_read'),
    path('api/delete/<int:pk>/', views.delete_message, name='delete_message'),
    path('main/settings/', views.site_settings, name='site_settings'),
        # ═══ Blog Management ═══
    path('blog/posts/', views.blog_post_list, name='blog_post_list'),
    path('blog/post/add/', views.blog_post_add, name='blog_post_add'),
    path('blog/post/<int:pk>/edit/', views.blog_post_edit, name='blog_post_edit'),
    path('blog/post/<int:pk>/delete/', views.blog_post_delete, name='blog_post_delete'),
    path('blog/categories/', views.blog_category_list, name='blog_category_list'),
    path('blog/category/add/', views.blog_category_add, name='blog_category_add'),
    path('blog/category/<int:pk>/edit/', views.blog_category_edit, name='blog_category_edit'),
    path('blog/category/<int:pk>/delete/', views.blog_category_delete, name='blog_category_delete'),
    path('blog/comments/', views.blog_comment_list, name='blog_comment_list'),
    path('blog/comment/<int:pk>/approve/', views.blog_comment_approve, name='blog_comment_approve'),
    path('blog/comment/<int:pk>/delete/', views.blog_comment_delete, name='blog_comment_delete'),
        # ═══ Portfolio Managment ═══
    path('portfolio/', views.portfolio_list, name='portfolio_list'),
    path('portfolio/add/', views.portfolio_add, name='portfolio_add'),
    path('portfolio/<int:pk>/edit/', views.portfolio_edit, name='portfolio_edit'),
    path('portfolio/<int:pk>/delete/', views.portfolio_delete, name='portfolio_delete'),
    path('portfolio-categories/', views.portfolio_category_list, name='portfolio_category_list'),
    path('portfolio-categories/add/', views.portfolio_category_add, name='portfolio_category_add'),
    path('portfolio-categories/<int:pk>/edit/', views.portfolio_category_edit, name='portfolio_category_edit'),
    path('portfolio-categories/<int:pk>/delete/', views.portfolio_category_delete, name='portfolio_category_delete'),
        # ═══ gallery Managment ═══
    path('gallery/', views.gallery_album_list, name='gallery_album_list'),
    path('gallery/add/', views.gallery_album_add, name='gallery_album_add'),
    path('gallery/<int:pk>/edit/', views.gallery_album_edit, name='gallery_album_edit'),
    path('gallery/<int:pk>/delete/', views.gallery_album_delete, name='gallery_album_delete'),
    path('gallery/<int:album_id>/images/', views.gallery_album_images, name='gallery_album_images'),
    path('gallery/image/<int:pk>/edit/', views.gallery_image_edit, name='gallery_image_edit'),
    path('gallery/image/<int:pk>/delete/', views.gallery_image_delete, name='gallery_image_delete'),    
]
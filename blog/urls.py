from django.urls import path, re_path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.post_list, name='post_list'),
    re_path(r'^(?P<slug>[\w\u0600-\u06FF\-]+)/$', views.post_detail, name='post_detail'),
    path('api/comments/<int:post_id>/load/', views.load_more_comments, name='load_comments'),
    path('api/comments/<int:post_id>/submit/', views.submit_comment, name='submit_comment'),
    path('api/posts/<int:post_id>/like/', views.like_post, name='like_post'),
    path('api/comments/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    path('api/comments/<int:comment_id>/dislike/', views.dislike_comment, name='dislike_comment'),
]
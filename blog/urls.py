from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path(r'(?P<slug>[-a-zA-Z0-9_]+)/', views.post_detail, name='post_detail'),
    path('api/comments/<int:post_id>/load/', views.load_more_comments, name='load_comments'),
    path('api/comments/<int:post_id>/submit/', views.submit_comment, name='submit_comment'),
    path('api/posts/<int:post_id>/like/', views.like_post, name='like_post'),
    path('api/comments/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    path('api/comments/<int:comment_id>/dislike/', views.dislike_comment, name='dislike_comment'),
]
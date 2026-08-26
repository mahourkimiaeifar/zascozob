from django.urls import path, re_path
from . import views

app_name = 'portfolio' 

urlpatterns = [
    path('', views.portfolio_list, name='portfolio_list'),
    re_path(r'^(?P<slug>[\w\u0600-\u06FF-]+)/$', views.portfolio_detail, name='portfolio_detail'),
]
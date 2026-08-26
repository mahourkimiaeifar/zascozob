from django.urls import path, re_path

app_name = 'portfolio'

urlpatterns = [
    path('portfolio/', views.portfolio_list, name='portfolio_list'),
    re_path(r'^portfolio/(?P<slug>[\w\u0600-\u06FF-]+)/$', views.portfolio_detail, name='portfolio_detail'),
]
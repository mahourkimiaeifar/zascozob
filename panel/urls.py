from django.urls import path
from . import views

app_name = 'panel'
PANEL_PATH = 'zasco-admin-x9k2p'

urlpatterns = [
    path('login/', views.panel_login, name='login'),
    path('logout/', views.panel_logout, name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('main/contact/', views.main_contact, name='main_contact'),
    path('main/contact/reply/', views.main_contact_reply, name='main_contact_reply'),
    path('api/mark-read/<int:pk>/', views.mark_read, name='mark_read'),
    path('api/delete/<int:pk>/', views.delete_message, name='delete_message'),
    path('main/settings/', views.site_settings, name='site_settings'),
]
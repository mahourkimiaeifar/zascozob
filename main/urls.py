from django.urls import path, include
from django.views.generic import RedirectView
from . import views
from panel.urls import PANEL_PATH

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('blog/', include('blog.urls')),
    path('portfolio/', include('portfolio.urls')),
    path('admin/', RedirectView.as_view(url=f'/{PANEL_PATH}/login/', permanent=False)),
    path(f'{PANEL_PATH}/', include('panel.urls')),
]
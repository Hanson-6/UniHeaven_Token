# project-level urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    # All API endpoints will be available under '/api/'.
    path('api/', include('core.urls')),
    path('', RedirectView.as_view(url='/api/', permanent=False), name='api-root'),
]

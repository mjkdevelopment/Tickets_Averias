"""
URL Configuration para Tickets_Averias
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from apps.usuarios import api_fcm


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.usuarios.urls')),
    path('tickets/', include('apps.tickets.urls')),
    path('locales/', include('apps.locales.urls')),
    path('reportes/', include('apps.reportes.urls')),
    path("api/register-device/", api_fcm.registrar_dispositivo, name="api_register_device"),


    # URLs de autenticación
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

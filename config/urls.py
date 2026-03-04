"""
URL Configuration para Tickets_Averias
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from django.shortcuts import render
from apps.usuarios import api_fcm
from config.app_version import APP_VERSION
import os


def api_app_version(request):
    """Devuelve la versión actual de la app y la URL de descarga."""
    base = settings.BASE_URL.rstrip("/") if hasattr(settings, 'BASE_URL') else request.build_absolute_uri('/').rstrip('/')
    download_url = f"{base}/media/app/mjk_tickets.apk"
    return JsonResponse({
        "version": APP_VERSION,
        "download_url": download_url,
    })


def descargar_app_view(request):
    """Página de descarga de la APK."""
    base = settings.BASE_URL.rstrip("/") if hasattr(settings, 'BASE_URL') else request.build_absolute_uri('/').rstrip('/')
    apk_path = os.path.join(settings.MEDIA_ROOT, 'app', 'mjk_tickets.apk')
    apk_available = os.path.exists(apk_path)
    download_url = f"{base}/media/app/mjk_tickets.apk"
    return render(request, "descargar_app.html", {
        "version": APP_VERSION,
        "apk_available": apk_available,
        "download_url": download_url,
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.usuarios.urls')),
    path('tickets/', include('apps.tickets.urls')),
    path('locales/', include('apps.locales.urls')),
    path('reportes/', include('apps.reportes.urls')),
    path("api/register-device/", api_fcm.registrar_dispositivo, name="api_register_device"),
    path("api/device/enroll/", api_fcm.inscribir_dispositivo, name="api_device_enroll"),
    path("api/device/status/", api_fcm.estado_dispositivo, name="api_device_status"),

    # App versioning & distribution
    path("api/app/version/", api_app_version, name="api_app_version"),
    path("descargar-app/", descargar_app_view, name="descargar_app"),

    # URLs de autenticación
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


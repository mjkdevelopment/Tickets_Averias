"""
Configuración de Django para el proyecto Tickets_Averias
"""

from pathlib import Path
from decouple import config
from django.urls import reverse_lazy
from django.templatetags.static import static
from django.utils import timezone
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-cambiar-esto-en-produccion')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'unfold',  # Django Unfold debe ir antes de django.contrib.admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps de terceros
    'crispy_forms',
    'crispy_bootstrap4',
    'widget_tweaks',
    'django_filters',

    # Apps locales
    'apps.usuarios',
    'apps.locales',
    'apps.tickets',
    'apps.reportes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# Usamos SQLite simple y diferenciamos local vs PythonAnywhere
if 'PYTHONANYWHERE_DOMAIN' in os.environ:
    # Producción en PythonAnywhere
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'tickets_prod.sqlite3',
        }
    }
else:
    # Desarrollo local (tu Mac)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Santo_Domingo'  # Ajusta según tu país
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files (uploads de usuarios)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuración de Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"
CRISPY_TEMPLATE_PACK = "bootstrap4"

# Modelo de usuario personalizado
AUTH_USER_MODEL = 'usuarios.Usuario'

# Login URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Configuración de WhatsApp/Twilio
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_WHATSAPP_FROM = config('TWILIO_WHATSAPP_FROM', default='')
WHATSAPP_ENABLED = config('WHATSAPP_ENABLED', default=False, cast=bool)
BASE_URL = config('BASE_URL', default='https://majestiksolutions.pythonanywhere.com')

FIREBASE_CREDENTIALS_FILE = config(
    'FIREBASE_CREDENTIALS_FILE',
    default=None,
)


# Configuración de archivos subidos
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

FIREBASE_PROJECT_ID = "mjk-tickets"  # 👈 el ID de tu proyecto (lo ves en Firebase)
FIREBASE_CREDENTIALS_FILE = BASE_DIR / "config" / "firebase_admin_key.json"


# 🔐 Sesiones basadas en cookies firmadas (para evitar usar la tabla django_session)
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

FCM_SERVER_KEY = config('FCM_SERVER_KEY', default='')

# Configuración de Django Unfold
UNFOLD = {
    "SITE_TITLE": "Tickets Averías",
    "SITE_HEADER": "Administración de Tickets",
    "SITE_URL": "/",
    "SITE_ICON": {
        "light": lambda request: static("images/mjk_tickets_logo.png"),
        "dark": lambda request: static("images/mjk_tickets_logo.png"),
    },
    "SITE_LOGO": {
        "light": lambda request: static("images/mjk_tickets_logo.png"),
        "dark": lambda request: static("images/mjk_tickets_logo.png"),
    },
    "SITE_SYMBOL": "support_agent",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "ENVIRONMENT": "config.settings.environment_callback",
    "DASHBOARD_CALLBACK": "config.settings.dashboard_callback",
    "LOGIN": {
        "image": lambda request: static("images/mjk_tickets_logo.png"),
        "redirect_after": lambda request: reverse_lazy("admin:index"),
    },
    "STYLES": [
        lambda request: static("css/unfold_custom.css"),
    ],
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "es": "🇪🇸",
                "en": "🇬🇧",
            },
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Dashboard",
                "separator": False,
                "items": [
                    {
                        "title": "Inicio",
                        "icon": "dashboard",
                        "link": lambda request: reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": "Gestión de Tickets",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Tickets",
                        "icon": "confirmation_number",
                        "link": lambda request: reverse_lazy("admin:tickets_ticket_changelist"),
                        "badge": "tickets.utils.get_tickets_abiertos_count",
                    },
                    {
                        "title": "Categorías",
                        "icon": "category",
                        "link": lambda request: reverse_lazy("admin:tickets_categoriaaveria_changelist"),
                    },
                    {
                        "title": "Comentarios",
                        "icon": "comment",
                        "link": lambda request: reverse_lazy("admin:tickets_comentarioticket_changelist"),
                    },
                ],
            },
            {
                "title": "Usuarios y Locales",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Usuarios",
                        "icon": "people",
                        "link": lambda request: reverse_lazy("admin:usuarios_usuario_changelist"),
                    },
                    {
                        "title": "Locales",
                        "icon": "store",
                        "link": lambda request: reverse_lazy("admin:locales_local_changelist"),
                    },
                    {
                        "title": "Dispositivos FCM",
                        "icon": "notifications",
                        "link": lambda request: reverse_lazy("admin:usuarios_dispositivonotificacion_changelist"),
                    },
                ],
            },
        ],
    },
}


def environment_callback(request):
    """Muestra el ambiente actual en el header del admin"""
    return ["Producción" if not DEBUG else "Desarrollo", "success" if not DEBUG else "warning"]


def dashboard_callback(request, context):
    """Personaliza el dashboard del admin"""
    from apps.tickets.models import Ticket
    from django.db.models import Count, Q
    
    context.update({
        "navigation": [
            {
                "title": "Estadísticas Generales",
                "items": [
                    {
                        "title": "Tickets Abiertos",
                        "description": Ticket.objects.filter(estado__in=['PENDIENTE', 'EN_PROCESO']).count(),
                        "icon": "confirmation_number",
                    },
                    {
                        "title": "Tickets Vencidos",
                        "description": Ticket.objects.filter(
                            Q(estado__in=['PENDIENTE', 'EN_PROCESO']) & 
                            Q(fecha_limite_sla__lt=timezone.now())
                        ).count(),
                        "icon": "warning",
                    },
                ],
            },
        ],
    })
    return context


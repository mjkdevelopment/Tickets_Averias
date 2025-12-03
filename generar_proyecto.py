#!/usr/bin/env python
"""
Script para generar automáticamente toda la estructura del proyecto
Sistema de Gestión de Tickets de Averías

Ejecutar con: python generar_proyecto.py
"""

import os
import sys


def crear_directorio(ruta):
    """Crea un directorio si no existe"""
    if not os.path.exists(ruta):
        os.makedirs(ruta)
        print(f"✓ Directorio creado: {ruta}")


def crear_archivo(ruta, contenido):
    """Crea un archivo con el contenido especificado"""
    try:
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"✓ Archivo creado: {ruta}")
    except Exception as e:
        print(f"✗ Error al crear {ruta}: {e}")


def generar_estructura():
    """Genera toda la estructura del proyecto"""

    print("\n" + "=" * 60)
    print("  GENERADOR DE PROYECTO - SISTEMA DE TICKETS")
    print("=" * 60 + "\n")

    # Crear directorios principales
    directorios = [
        'config',
        'apps',
        'apps/usuarios',
        'apps/usuarios/migrations',
        'apps/locales',
        'apps/locales/migrations',
        'apps/tickets',
        'apps/tickets/migrations',
        'apps/reportes',
        'apps/reportes/migrations',
        'templates',
        'templates/usuarios',
        'templates/tickets',
        'templates/locales',
        'templates/reportes',
        'static',
        'static/css',
        'static/js',
        'static/images',
        'media',
        'media/fotos_reparaciones',
    ]

    print("📁 Creando estructura de directorios...\n")
    for directorio in directorios:
        crear_directorio(directorio)

    print("\n📄 Creando archivos del proyecto...\n")

    # requirements.txt
    crear_archivo('requirements.txt', """Django==4.2.7
Pillow==10.1.0
python-decouple==3.8
psycopg2-binary==2.9.9
django-crispy-forms==2.1
crispy-bootstrap4==2.0
twilio==8.10.0
django-widget-tweaks==1.5.0
reportlab==4.0.7
openpyxl==3.1.2
django-filter==23.5
""")

    # .env.example
    crear_archivo('.env.example', """# Configuración de Django
SECRET_KEY=tu-clave-secreta-aqui-cambiar-en-produccion
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos (dejar así para desarrollo con SQLite)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# Configuración de WhatsApp con Twilio
TWILIO_ACCOUNT_SID=tu_account_sid
TWILIO_AUTH_TOKEN=tu_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
WHATSAPP_ENABLED=False

# URL base para links en notificaciones
BASE_URL=http://localhost:8000
""")

    # .gitignore
    crear_archivo('.gitignore', """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Django
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
/media
/staticfiles

# Environment variables
.env

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
""")

    # manage.py
    crear_archivo('manage.py', """#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
""")

    # __init__.py vacíos
    archivos_init = [
        'config/__init__.py',
        'apps/__init__.py',
        'apps/usuarios/__init__.py',
        'apps/usuarios/migrations/__init__.py',
        'apps/locales/__init__.py',
        'apps/locales/migrations/__init__.py',
        'apps/tickets/__init__.py',
        'apps/tickets/migrations/__init__.py',
        'apps/reportes/__init__.py',
        'apps/reportes/migrations/__init__.py',
    ]

    for archivo in archivos_init:
        crear_archivo(archivo, '')

    print("\n" + "=" * 60)
    print("  ✅ ¡PROYECTO GENERADO EXITOSAMENTE!")
    print("=" * 60 + "\n")

    print("📝 PRÓXIMOS PASOS:\n")
    print("1. Copia manualmente los archivos de código Python que te mostré")
    print("   (models.py, views.py, forms.py, etc.) a sus respectivas carpetas")
    print("")
    print("2. Copia los archivos HTML a la carpeta templates/")
    print("")
    print("3. Copia el archivo CSS a static/css/custom.css")
    print("")
    print("4. Activa tu entorno virtual:")
    if sys.platform == "win32":
        print("   .venv\\Scripts\\activate")
    else:
        print("   source .venv/bin/activate")
    print("")
    print("5. Instala las dependencias:")
    print("   pip install -r requirements.txt")
    print("")
    print("6. Crea el archivo .env:")
    if sys.platform == "win32":
        print("   copy .env.example .env")
    else:
        print("   cp .env.example .env")
    print("")
    print("7. Ejecuta las migraciones:")
    print("   python manage.py makemigrations")
    print("   python manage.py migrate")
    print("")
    print("8. Crea un superusuario:")
    print("   python manage.py createsuperuser")
    print("")
    print("9. Inicia el servidor:")
    print("   python manage.py runserver")
    print("")
    print("10. Abre tu navegador en: http://localhost:8000")
    print("")
    print("=" * 60 + "\n")

    print("💡 CONSEJO: Guarda todos los mensajes anteriores con el código")
    print("   completo de cada archivo para copiarlos fácilmente.\n")


if __name__ == '__main__':
    try:
        generar_estructura()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
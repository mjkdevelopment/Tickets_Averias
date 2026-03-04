"""
URLs para el sistema de usuarios
"""
from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    # Autenticación
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Gestión de usuarios
    path("usuarios/", views.usuarios_lista, name="usuarios_lista"),
    path("usuarios/crear/", views.usuario_crear, name="usuario_crear"),
    path("usuarios/<int:pk>/", views.usuario_detalle, name="usuario_detalle"),
    path("usuarios/<int:pk>/editar/", views.usuario_editar, name="usuario_editar"),
    path("usuarios/<int:pk>/password/", views.usuario_cambiar_password, name="usuario_cambiar_password"),

    # Gestión de dispositivos
    path("dispositivos/", views.dispositivos_lista, name="dispositivos_lista"),
    path("dispositivos/<int:pk>/toggle/", views.dispositivo_toggle, name="dispositivo_toggle"),
]

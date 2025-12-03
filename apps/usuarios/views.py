"""
Vistas para el sistema de usuarios
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse

from .forms import LoginForm, UsuarioCreateForm, UsuarioUpdateForm

Usuario = get_user_model()


def login_view(request):
    """
    Vista de inicio de sesión
    """
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bienvenido {user.username}")
            return redirect("dashboard")
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
    else:
        form = LoginForm(request)

    return render(request, "usuarios/login.html", {"form": form})


@login_required
def logout_view(request):
    """
    Cerrar sesión
    """
    logout(request)
    messages.info(request, "Sesión cerrada correctamente")
    return redirect("login")


@login_required
def dashboard(request):
    """
    Dashboard principal muy simple por ahora.
    Más adelante le añadimos estadísticas de tickets, etc.
    """
    return render(request, "dashboard.html", {"user": request.user})


@login_required
def usuarios_lista(request):
    """
    Lista de usuarios
    """
    usuarios = Usuario.objects.all().order_by("username")
    return render(
        request,
        "usuarios/usuarios_lista.html",
        {"usuarios": usuarios},
    )


@login_required
def usuario_crear(request):
    """
    Crear un nuevo usuario
    """
    if request.method == "POST":
        form = UsuarioCreateForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f"Usuario {usuario.username} creado correctamente")
            return redirect("usuarios_lista")
    else:
        form = UsuarioCreateForm()

    return render(
        request,
        "usuarios/usuario_form.html",
        {"form": form, "titulo": "Crear usuario"},
    )


@login_required
def usuario_detalle(request, pk):
    """
    Ver detalle de un usuario
    """
    usuario = get_object_or_404(Usuario, pk=pk)
    return render(
        request,
        "usuarios/usuario_detalle.html",
        {"usuario": usuario},
    )


@login_required
def usuario_editar(request, pk):
    """
    Editar un usuario
    """
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == "POST":
        form = UsuarioUpdateForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario actualizado correctamente")
            return redirect("usuario_detalle", pk=usuario.pk)
    else:
        form = UsuarioUpdateForm(instance=usuario)

    return render(
        request,
        "usuarios/usuario_form.html",
        {"form": form, "titulo": "Editar usuario"},
    )

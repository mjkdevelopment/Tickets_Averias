# apps/usuarios/api_fcm.py

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model

from .models import DispositivoNotificacion

User = get_user_model()


@csrf_exempt
def registrar_dispositivo(request):
    """
    Endpoint simple para que la app Flutter registre/actualice
    el token FCM de un usuario.

    Espera un POST JSON como:
    {
        "username": "erick",
        "fcm_token": "AAAA...."
    }
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Método no permitido"}, status=405)

    # Intentar leer JSON del body
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        # Por si acaso viene como form-data
        data = request.POST

    # Aceptamos varios nombres de campos por si acaso
    username = (data.get("username") or data.get("usuario") or "").strip()
    token = (data.get("fcm_token") or data.get("token") or "").strip()

    if not username or not token:
        return JsonResponse(
            {"detail": "username y fcm_token son obligatorios."},
            status=400,
        )

    try:
        usuario = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse(
            {"detail": f"Usuario '{username}' no existe."},
            status=404,
        )

    # Primero eliminamos cualquier dispositivo con este token (puede pertenecer a otro usuario)
    DispositivoNotificacion.objects.filter(fcm_token=token).exclude(usuario=usuario).delete()
    
    # Ahora actualizamos o creamos el dispositivo para este usuario
    dispositivo, creado = DispositivoNotificacion.objects.update_or_create(
        usuario=usuario,
        fcm_token=token,
        defaults={
            "activo": True,
        },
    )

    return JsonResponse(
        {
            "detail": "Dispositivo registrado correctamente.",
            "creado": creado,
        }
    )

@csrf_exempt
def inscribir_dispositivo(request):
    """
    Endpoint para el Enrollment Wizard de la app móvil.
    Crea el dispositivo con activo=False (Pendiente de Aprobación).
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        data = request.POST

    username = (data.get("username") or "").strip()
    token = (data.get("fcm_token") or "").strip()

    if not username or not token:
        return JsonResponse({"detail": "username y fcm_token son obligatorios."}, status=400)

    try:
        usuario = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({"detail": f"Usuario '{username}' no existe."}, status=404)

    # Asegurarnos de que el token no pertenezca a otro usuario
    DispositivoNotificacion.objects.filter(fcm_token=token).exclude(usuario=usuario).delete()
    
    dispositivo = DispositivoNotificacion.objects.filter(usuario=usuario, fcm_token=token).first()
    
    if dispositivo:
        # Si ya existe, devolvemos su estado actual (podría estar ya aprobado)
        return JsonResponse({
            "detail": "Dispositivo ya estaba registrado.",
            "aprobado": dispositivo.activo
        })
    else:
        # Nuevo registro, nace pendiente (activo=False)
        DispositivoNotificacion.objects.create(
            usuario=usuario,
            fcm_token=token,
            activo=False
        )
        return JsonResponse({
            "detail": "Solicitud de inscripción enviada. Pendiente de aprobación.",
            "aprobado": False
        })


@csrf_exempt
def estado_dispositivo(request):
    """
    Endpoint para que la app móvil consulte si su token fue aprobado.
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        data = request.POST

    token = (data.get("fcm_token") or "").strip()

    if not token:
        return JsonResponse({"detail": "fcm_token es obligatorio."}, status=400)

    dispositivo = DispositivoNotificacion.objects.filter(fcm_token=token).first()
    
    if not dispositivo:
        return JsonResponse({"detail": "Dispositivo no encontrado."}, status=404)

    return JsonResponse({
        "aprobado": dispositivo.activo
    })

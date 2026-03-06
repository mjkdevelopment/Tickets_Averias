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
        defaults={
            "fcm_token": token,
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
    Registra o actualiza el token FCM de un dispositivo.
    Llamado desde la app móvil Flutter (OnboardingWizard).
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Método no permitido", "status": "error"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    username = (data.get("username") or data.get("usuario") or "").strip()
    fcm_token = data.get("fcm_token")

    if not username or not fcm_token:
        return JsonResponse({"detail": "username y fcm_token son requeridos", "status": "error"}, status=400)

    try:
        usuario = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({"detail": "El usuario no existe o hubo un problema", "status": "error"}, status=401)

    # Eliminar este token de otros usuarios si existe
    DispositivoNotificacion.objects.filter(fcm_token=fcm_token).exclude(usuario=usuario).delete()

    dispositivo, creado = DispositivoNotificacion.objects.update_or_create(
        usuario=usuario,
        defaults={
            "fcm_token": fcm_token,
            "activo": True
        }
    )

    return JsonResponse({
        "status": "success",
        "detail": "Dispositivo inscrito correctamente",
        "creado": creado,
        "aprobado": dispositivo.activo
    })


@csrf_exempt
def estado_dispositivo(request):
    """
    Verifica el estado de un dispositivo (activo/inactivo/aprobado)
    basado en el token FCM. Llamado desde Flutter (WaitingRoomScreen).
    """
    if request.method != "POST" and request.method != "GET":
        return JsonResponse({"detail": "Método no permitido"}, status=405)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST
        fcm_token = data.get("fcm_token")
    else:
        fcm_token = request.GET.get("fcm_token")

    if not fcm_token:
        return JsonResponse({"detail": "fcm_token es requerido", "status": "error"}, status=400)

    try:
        dispositivo = DispositivoNotificacion.objects.get(fcm_token=fcm_token)
        return JsonResponse({
            "status": "success",
            "activo": dispositivo.activo,
            "aprobado": dispositivo.activo
        })
    except DispositivoNotificacion.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "detail": "Dispositivo no encontrado"
        }, status=404)

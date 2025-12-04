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

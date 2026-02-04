# apps/tickets/fcm.py

import requests
from django.conf import settings
from django.urls import reverse

from apps.usuarios.models import DispositivoNotificacion

from google.oauth2 import service_account
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]


def _get_access_token():
    """
    Obtiene un token de acceso OAuth2 usando el JSON de servicio de Firebase.
    """
    print("[FCM] Obteniendo access token...")

    credentials = service_account.Credentials.from_service_account_file(
        str(settings.FIREBASE_CREDENTIALS_FILE),
        scopes=SCOPES,
    )
    credentials.refresh(Request())
    print("[FCM] Access token obtenido OK.")
    return credentials.token


def enviar_notificacion_nuevo_ticket(ticket):
    """
    Envía una notificación push FCM al técnico asignado al ticket.
    Usa HTTP v1: https://fcm.googleapis.com/v1/projects/PROJECT_ID/messages:send
    """
    try:
        if not ticket.asignado_a:
            print(f"[FCM] Ticket {ticket.id}: sin técnico asignado. No se envía push.")
            return

        # 1) Buscar dispositivos activos del técnico
        dispositivos = DispositivoNotificacion.objects.filter(
            usuario=ticket.asignado_a,
            activo=True,
        ).exclude(fcm_token__isnull=True).exclude(fcm_token__exact="")

        if not dispositivos.exists():
            print(f"[FCM] Ticket {ticket.id}: el técnico {ticket.asignado_a} no tiene dispositivos activos.")
            return

        print(f"[FCM] Ticket {ticket.id}: encontré {dispositivos.count()} dispositivo(s) para {ticket.asignado_a}.")

        # 2) Access token
        access_token = _get_access_token()

        url = f"https://fcm.googleapis.com/v1/projects/{settings.FIREBASE_PROJECT_ID}/messages:send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

        # 3) Construir la URL correcta del ticket usando reverse
        #    En urls.py: path('tickets/<int:pk>/', views.ticket_detalle, name='ticket_detalle')
        relative_url = reverse("ticket_detalle", args=[ticket.pk])
        ticket_url = settings.BASE_URL.rstrip("/") + relative_url
        print(f"[FCM] URL del ticket: {ticket_url}")

        # 4) Enviar a cada dispositivo
        for disp in dispositivos:
            cuerpo = {
                "message": {
                    "token": disp.fcm_token,
                    "notification": {
                        "title": f"Nuevo ticket {ticket.numero_ticket}",
                        "body": f"{ticket.local} - {ticket.categoria.nombre if ticket.categoria else ''}",
                    },
                    "data": {
                        "ticket_id": str(ticket.id),
                        "ticket_url": ticket_url,
                        "estado": ticket.estado,
                        # Esto ayuda a que Android dispare onMessageOpenedApp
                        "click_action": "FLUTTER_NOTIFICATION_CLICK",
                    },
                }
            }

            print(f"[FCM] Enviando a token {disp.fcm_token[:20]}...")

            resp = requests.post(url, headers=headers, json=cuerpo, timeout=10)

            print(f"[FCM] Respuesta FCM: {resp.status_code} - {resp.text}")

    except Exception as e:
        # Cualquier error lo imprimimos para verlo en los logs de PythonAnywhere
        print(f"[FCM] ERROR enviando notificación: {e}")


def enviar_notificacion_sla_vencido(ticket):
    """
    Envía una notificación push FCM a usuarios staff cuando un ticket vence el SLA.
    """
    try:
        dispositivos = DispositivoNotificacion.objects.filter(
            usuario__is_staff=True,
            activo=True,
        ).exclude(fcm_token__isnull=True).exclude(fcm_token__exact="")

        if not dispositivos.exists():
            print("[FCM] No hay dispositivos activos para usuarios staff.")
            return False

        access_token = _get_access_token()

        url = f"https://fcm.googleapis.com/v1/projects/{settings.FIREBASE_PROJECT_ID}/messages:send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

        relative_url = reverse("ticket_detalle", args=[ticket.pk])
        ticket_url = settings.BASE_URL.rstrip("/") + relative_url

        titulo = f"SLA vencido {ticket.numero_ticket}"
        body = f"{ticket.local} - {ticket.categoria.nombre if ticket.categoria else ''}"

        enviados = 0
        for disp in dispositivos:
            cuerpo = {
                "message": {
                    "token": disp.fcm_token,
                    "notification": {
                        "title": titulo,
                        "body": body,
                    },
                    "data": {
                        "ticket_id": str(ticket.id),
                        "ticket_url": ticket_url,
                        "estado": ticket.estado,
                        "tipo": "sla_vencido",
                        "click_action": "FLUTTER_NOTIFICATION_CLICK",
                    },
                }
            }

            resp = requests.post(url, headers=headers, json=cuerpo, timeout=10)
            if resp.status_code >= 200 and resp.status_code < 300:
                enviados += 1
            else:
                print(f"[FCM] Error enviando a staff: {resp.status_code} - {resp.text}")

        return enviados > 0

    except Exception as e:
        print(f"[FCM] ERROR enviando SLA vencido: {e}")
        return False

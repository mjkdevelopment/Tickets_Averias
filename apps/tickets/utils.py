from django.conf import settings
from twilio.rest import Client


def enviar_whatsapp_ticket_asignado(ticket):
    """
    Envía un WhatsApp al técnico asignado cuando se crea un ticket.
    Solo funciona si:
    - WHATSAPP_ENABLED = True
    - el ticket tiene asignado_a
    - el técnico tiene número de WhatsApp
    """
    if not getattr(settings, 'WHATSAPP_ENABLED', False):
        return

    tecnico = ticket.asignado_a
    if not tecnico or not getattr(tecnico, 'whatsapp', None):
        return

    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    from_number = getattr(settings, 'TWILIO_WHATSAPP_FROM', None)

    if not (account_sid and auth_token and from_number):
        return

    client = Client(account_sid, auth_token)

    to_number = f"whatsapp:{tecnico.whatsapp}"
    base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
    url_ticket = f"{base_url}/tickets/{ticket.pk}/"

    body = (
        f"🔔 Nuevo ticket asignado\n\n"
        f"Número: {ticket.numero_ticket}\n"
        f"Categoría: {ticket.categoria.nombre}\n"
        f"Local: {ticket.local}\n"
        f"Prioridad: {ticket.get_prioridad_display()}\n\n"
        f"Descripción:\n{ticket.descripcion}\n\n"
        f"Ver detalles: {url_ticket}"
    )

    client.messages.create(
        from_=from_number,
        to=to_number,
        body=body,
    )

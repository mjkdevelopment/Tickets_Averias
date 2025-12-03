# apps/reportes/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.db.models import Count
from django.utils import timezone

from apps.tickets.models import Ticket
from apps.locales.models import Local
from apps.usuarios.models import Usuario


@login_required
def reportes_dashboard(request):
    """
    Reporte general solo para ADMIN:
    - Totales de tickets por estado
    - Top locales con más averías este mes (reincidencias)
    - Top técnicos con más tickets cerrados
    """
    usuario = request.user
    if not usuario.es_admin():
        return HttpResponseForbidden("Solo los administradores pueden ver los reportes.")

    # Totales por estado
    estados = Ticket.ESTADOS
    tickets_por_estado = []
    for code, label in estados:
        total = Ticket.objects.filter(estado=code).count()
        tickets_por_estado.append({
            "codigo": code,
            "nombre": label,
            "total": total,
        })

    # Mes actual
    ahora = timezone.now()
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Reincidencias: locales con más tickets en el mes
    reincidencias_locales = (
        Local.objects
        .filter(tickets__fecha_creacion__gte=inicio_mes)
        .annotate(total_tickets=Count("tickets"))
        .order_by("-total_tickets")[:10]
    )

    # Técnicos con más tickets cerrados (histórico)
    tecnicos_top = (
        Usuario.objects
        .filter(rol="TECNICO", tickets_asignados__estado="CERRADO")
        .annotate(total_cerrados=Count("tickets_asignados"))
        .order_by("-total_cerrados")[:10]
    )

    contexto = {
        "tickets_por_estado": tickets_por_estado,
        "reincidencias_locales": reincidencias_locales,
        "tecnicos_top": tecnicos_top,
        "inicio_mes": inicio_mes,
        "hoy": ahora,
    }
    return render(request, "reportes/dashboard.html", contexto)

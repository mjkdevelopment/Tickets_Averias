from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.tickets.models import Ticket
from apps.tickets.fcm import enviar_notificacion_sla_vencido


class Command(BaseCommand):
    help = "Envía notificaciones a staff por tickets con SLA vencido y no resueltos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra los tickets a notificar sin enviar.",
        )

    def handle(self, *args, **options):
        ahora = timezone.now()
        dry_run = options["dry_run"]

        qs = (
            Ticket.objects
            .filter(fecha_limite_sla__lt=ahora)
            .exclude(estado__in=["RESUELTO", "CERRADO", "CANCELADO"])
            .filter(notificacion_sla_enviada=False)
            .select_related("local", "categoria")
        )

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("No hay tickets vencidos pendientes de notificación."))
            return

        self.stdout.write(f"Tickets a notificar: {total}")

        enviados = 0
        for ticket in qs:
            if dry_run:
                self.stdout.write(f"[DRY] {ticket.numero_ticket} - {ticket.local}")
                continue

            if enviar_notificacion_sla_vencido(ticket):
                Ticket.objects.filter(pk=ticket.pk).update(notificacion_sla_enviada=True)
                enviados += 1

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run completado. No se enviaron notificaciones."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Notificaciones enviadas para {enviados} ticket(s)."))

"""
Modelos para el sistema de tickets de averías
"""
from datetime import timedelta

from django.db import models
from django.utils import timezone

from apps.usuarios.models import Usuario
from apps.locales.models import Local


class CategoriaAveria(models.Model):
    """
    Categorías de averías (PC, Internet, Eléctrica, etc.)
    """
    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre de la categoría'
    )

    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descripción'
    )

    tiempo_sla_horas = models.IntegerField(
        default=24,
        verbose_name='Tiempo SLA (horas)',
        help_text='Tiempo máximo de respuesta en horas'
    )

    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    color = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name='Color',
        help_text='Color en formato hexadecimal (#RRGGBB)'
    )

    class Meta:
        verbose_name = 'Categoría de avería'
        verbose_name_plural = 'Categorías de averías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Ticket(models.Model):
    """
    Modelo principal para los tickets de averías
    """
    PRIORIDADES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    ]

    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('RESUELTO', 'Resuelto'),
        ('CERRADO', 'Cerrado'),
        ('CANCELADO', 'Cancelado'),
    ]

    # Información básica
    numero_ticket = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name='Número de ticket'
    )

    local = models.ForeignKey(
        Local,
        on_delete=models.PROTECT,
        related_name='tickets',
        verbose_name='Local'
    )

    categoria = models.ForeignKey(
        CategoriaAveria,
        on_delete=models.PROTECT,
        related_name='tickets',
        verbose_name='Categoría'
    )

    # Descripción del problema
    titulo = models.CharField(
        max_length=200,
        verbose_name='Título'
    )

    descripcion = models.TextField(
        verbose_name='Descripción del problema'
    )

    prioridad = models.CharField(
        max_length=20,
        choices=PRIORIDADES,
        default='MEDIA',
        verbose_name='Prioridad'
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='PENDIENTE',
        verbose_name='Estado'
    )

    # Usuarios involucrados
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='tickets_creados',
        verbose_name='Creado por'
    )

    asignado_a = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets_asignados',
        verbose_name='Asignado a',
        limit_choices_to={'rol': 'TECNICO'}
    )

    # Fechas y tiempos
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )

    fecha_asignacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de asignación'
    )

    fecha_inicio_trabajo = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de inicio de trabajo'
    )

    fecha_resolucion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de resolución'
    )

    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de cierre'
    )

    fecha_limite_sla = models.DateTimeField(
        verbose_name='Fecha límite SLA',
        editable=False
    )

    # Resolución
    solucion = models.TextField(
        blank=True,
        null=True,
        verbose_name='Solución aplicada'
    )

    foto_reparacion = models.ImageField(
        upload_to='fotos_reparaciones/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Foto de la reparación'
    )

    # Control
    notificacion_enviada = models.BooleanField(
        default=False,
        verbose_name='Notificación enviada'
    )

    notificacion_sla_enviada = models.BooleanField(
        default=False,
        verbose_name='Notificación SLA enviada'
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de actualización'
    )

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-fecha_creacion']
        permissions = [
            ('puede_asignar_tickets', 'Puede asignar tickets'),
            ('puede_cerrar_tickets', 'Puede cerrar tickets'),
        ]

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para:
        1. Generar número de ticket automático
        2. Calcular fecha límite SLA
        3. Actualizar fechas según cambios de estado
        """
        # Generar número de ticket si es nuevo
        if not self.numero_ticket:
            from django.db.models import Max
            ultimo = Ticket.objects.aggregate(Max('id'))['id__max'] or 0
            self.numero_ticket = f"TKT-{(ultimo + 1):06d}"

        # Calcular fecha límite SLA si es nuevo
        if not self.pk and not self.fecha_limite_sla:
            self.fecha_limite_sla = timezone.now() + timedelta(hours=self.categoria.tiempo_sla_horas)

        # Fecha de asignación
        if self.asignado_a and not self.fecha_asignacion:
            self.fecha_asignacion = timezone.now()

        # Fecha de resolución
        if self.estado == 'RESUELTO' and not self.fecha_resolucion:
            self.fecha_resolucion = timezone.now()

        # Fecha de cierre
        if self.estado == 'CERRADO' and not self.fecha_cierre:
            self.fecha_cierre = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero_ticket} - {self.titulo}"

    def esta_vencido(self):
        """Verifica si el ticket está vencido según el SLA"""
        if self.estado in ['RESUELTO', 'CERRADO', 'CANCELADO']:
            return False
        return timezone.now() > self.fecha_limite_sla

    def tiempo_transcurrido(self):
        """Tiempo transcurrido desde la creación"""
        if self.estado == 'CERRADO' and self.fecha_cierre:
            return self.fecha_cierre - self.fecha_creacion
        return timezone.now() - self.fecha_creacion

    def tiempo_restante_sla(self):
        """Tiempo restante para cumplir el SLA"""
        if self.estado in ['RESUELTO', 'CERRADO', 'CANCELADO']:
            return None
        diferencia = self.fecha_limite_sla - timezone.now()
        return diferencia if diferencia.total_seconds() > 0 else timedelta(0)

    def porcentaje_tiempo_usado(self):
        """Porcentaje de tiempo usado del SLA"""
        tiempo_total = self.fecha_limite_sla - self.fecha_creacion
        tiempo_usado = timezone.now() - self.fecha_creacion

        if tiempo_total.total_seconds() == 0:
            return 100

        porcentaje = (tiempo_usado.total_seconds() / tiempo_total.total_seconds()) * 100
        return min(porcentaje, 100)

    def get_color_sla(self):
        """Color según el estado del SLA"""
        if self.estado in ['RESUELTO', 'CERRADO']:
            return 'success'

        porcentaje = self.porcentaje_tiempo_usado()
        if porcentaje < 50:
            return 'success'
        elif porcentaje < 75:
            return 'warning'
        else:
            return 'danger'


class ComentarioTicket(models.Model):
    """
    Comentarios y seguimiento de los tickets
    """
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comentarios',
        verbose_name='Ticket'
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        verbose_name='Usuario'
    )

    comentario = models.TextField(
        verbose_name='Comentario'
    )

    es_interno = models.BooleanField(
        default=False,
        verbose_name='Comentario interno',
        help_text='Los comentarios internos no son visibles para digitadores'
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['fecha_creacion']

    def __str__(self):
        return f"Comentario de {self.usuario} en {self.ticket.numero_ticket}"

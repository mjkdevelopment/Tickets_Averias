"""
Modelos para la gestión de locales
"""
from django.db import models


class Local(models.Model):
    """
    Modelo para representar cada banca/local del consorcio
    """
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código del local',
        help_text='Código único identificador del local'
    )

    nombre = models.CharField(
        max_length=200,
        verbose_name='Nombre del local'
    )

    direccion = models.TextField(
        verbose_name='Dirección'
    )

    provincia = models.CharField(
        max_length=100,
        verbose_name='Provincia'
    )

    municipio = models.CharField(
        max_length=100,
        verbose_name='Municipio'
    )

    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Teléfono'
    )

    responsable_nombre = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Nombre del responsable'
    )

    responsable_telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Teléfono del responsable'
    )

    activo = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name='Notas adicionales'
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de actualización'
    )

    class Meta:
        verbose_name = 'Local'
        verbose_name_plural = 'Locales'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    def tickets_abiertos(self):
        """Retorna el número de tickets abiertos para este local"""
        return self.tickets.filter(estado__in=['PENDIENTE', 'EN_PROCESO']).count()

    def tickets_mes_actual(self):
        """Retorna el número de tickets del mes actual"""
        from django.utils import timezone
        inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self.tickets.filter(fecha_creacion__gte=inicio_mes).count()

# apps/tickets/admin.py
from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Ticket, ComentarioTicket, CategoriaAveria


@admin.register(CategoriaAveria)
class CategoriaAveriaAdmin(ModelAdmin):
    list_display = ('nombre', 'tiempo_sla_horas', 'activo', 'color')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)


@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    list_display = ('numero_ticket', 'local', 'categoria', 'estado', 'prioridad', 'creado_por', 'asignado_a', 'fecha_creacion')
    list_filter = ('estado', 'prioridad', 'categoria', 'fecha_creacion')
    search_fields = ('numero_ticket', 'titulo', 'descripcion', 'local__codigo', 'local__nombre')
    readonly_fields = ('numero_ticket', 'fecha_creacion', 'fecha_actualizacion', 'fecha_limite_sla')
    date_hierarchy = 'fecha_creacion'
    ordering = ('-fecha_creacion',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('numero_ticket', 'local', 'categoria', 'titulo', 'descripcion')
        }),
        ('Estado y Prioridad', {
            'fields': ('estado', 'prioridad')
        }),
        ('Asignación', {
            'fields': ('creado_por', 'asignado_a')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_asignacion', 'fecha_inicio_trabajo', 'fecha_resolucion', 'fecha_cierre', 'fecha_limite_sla')
        }),
        ('Resolución', {
            'fields': ('solucion', 'foto_reparacion'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ComentarioTicket)
class ComentarioTicketAdmin(ModelAdmin):
    list_display = ('ticket', 'autor', 'fecha_creacion', 'comentario_corto')
    list_filter = ('fecha_creacion',)
    search_fields = ('ticket__numero_ticket', 'comentario', 'autor__username')
    readonly_fields = ('fecha_creacion',)
    date_hierarchy = 'fecha_creacion'
    
    def comentario_corto(self, obj):
        return obj.comentario[:50] + '...' if len(obj.comentario) > 50 else obj.comentario
    comentario_corto.short_description = 'Comentario'

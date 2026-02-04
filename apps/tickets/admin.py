# apps/tickets/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import Ticket, ComentarioTicket, CategoriaAveria


@admin.register(CategoriaAveria)
class CategoriaAveriaAdmin(ModelAdmin):
    list_display = ('nombre', 'tiempo_sla_display', 'color_display', 'activo_display', 'tickets_count')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)
    list_per_page = 25
    
    @display(description='SLA', ordering='tiempo_sla_horas')
    def tiempo_sla_display(self, obj):
        return f"{obj.tiempo_sla_horas}h"
    
    @display(description='Color', ordering='color')
    def color_display(self, obj):
        return format_html(
            '<span style="background:{}; padding:2px 10px; border-radius:3px; color:white;">{}</span>',
            obj.color,
            obj.color
        )
    
    @display(description='Estado', boolean=True, ordering='activo')
    def activo_display(self, obj):
        return obj.activo
    
    @display(description='Tickets')
    def tickets_count(self, obj):
        count = obj.tickets.count()
        return format_html('<strong>{}</strong>', count)


class ComentarioInline(admin.TabularInline):
    model = ComentarioTicket
    extra = 1
    fields = ('usuario', 'comentario', 'fecha_creacion')
    readonly_fields = ('fecha_creacion',)


@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    list_display = ('numero_ticket_display', 'local_link', 'categoria_badge', 'estado_badge', 'prioridad_badge', 
                    'sla_status', 'asignado_display', 'fecha_creacion_display')
    list_filter = ('estado', 'prioridad', 'categoria', 'fecha_creacion', 'asignado_a')
    search_fields = ('numero_ticket', 'titulo', 'descripcion', 'local__codigo', 'local__nombre', 'creado_por__username')
    readonly_fields = ('numero_ticket', 'fecha_creacion', 'fecha_actualizacion', 'fecha_limite_sla', 'sla_visual')
    date_hierarchy = 'fecha_creacion'
    ordering = ('-fecha_creacion',)
    list_per_page = 50
    inlines = [ComentarioInline]
    actions = ['marcar_en_proceso', 'marcar_resuelto', 'marcar_cerrado']
    
    fieldsets = (
        ('Información del Ticket', {
            'fields': ('numero_ticket', ('local', 'categoria'), 'titulo', 'descripcion')
        }),
        ('Estado y Prioridad', {
            'fields': (('estado', 'prioridad'), 'sla_visual')
        }),
        ('Asignación y Usuarios', {
            'fields': (('creado_por', 'asignado_a'),)
        }),
        ('Fechas de Seguimiento', {
            'fields': (('fecha_creacion', 'fecha_limite_sla'), 
                      ('fecha_asignacion', 'fecha_inicio_trabajo'),
                      ('fecha_resolucion', 'fecha_cierre')),
            'classes': ('collapse',)
        }),
        ('Resolución y Evidencia', {
            'fields': ('solucion', 'foto_reparacion'),
            'classes': ('collapse',)
        }),
        ('Control Interno', {
            'fields': (('notificacion_enviada', 'notificacion_sla_enviada'),),
            'classes': ('collapse',)
        }),
    )
    
    @display(description='Ticket', ordering='numero_ticket')
    def numero_ticket_display(self, obj):
        return format_html('<strong style="font-family:monospace">{}</strong>', obj.numero_ticket)
    
    @display(description='Local')
    def local_link(self, obj):
        url = reverse('admin:locales_local_change', args=[obj.local.pk])
        return format_html('<a href="{}">{}</a>', url, obj.local.codigo)
    
    @display(description='Categoría', ordering='categoria')
    def categoria_badge(self, obj):
        return format_html(
            '<span style="background:{}; padding:3px 8px; border-radius:4px; color:white; font-size:11px;">{}</span>',
            obj.categoria.color,
            obj.categoria.nombre
        )
    
    @display(description='Estado', ordering='estado')
    def estado_badge(self, obj):
        colors = {
            'PENDIENTE': '#6c757d',
            'EN_PROCESO': '#ffc107',
            'RESUELTO': '#28a745',
            'CERRADO': '#17a2b8',
            'CANCELADO': '#dc3545',
        }
        return format_html(
            '<span style="background:{}; padding:3px 8px; border-radius:4px; color:white; font-size:11px; font-weight:bold;">{}</span>',
            colors.get(obj.estado, '#6c757d'),
            obj.get_estado_display()
        )
    
    @display(description='Prioridad', ordering='prioridad')
    def prioridad_badge(self, obj):
        colors = {
            'BAJA': '#28a745',
            'MEDIA': '#ffc107',
            'ALTA': '#fd7e14',
            'CRITICA': '#dc3545',
        }
        return format_html(
            '<span style="background:{}; padding:3px 8px; border-radius:4px; color:white; font-size:11px;">{}</span>',
            colors.get(obj.prioridad, '#6c757d'),
            obj.get_prioridad_display()
        )
    
    @display(description='SLA')
    def sla_status(self, obj):
        if obj.esta_vencido():
            return format_html('<span style="color:#dc3545; font-weight:bold;">⚠️ VENCIDO</span>')
        
        tiempo_restante = obj.tiempo_restante_sla()
        if tiempo_restante is None:
            return format_html('<span style="color:#28a745;">✓ Completado</span>')
        
        if tiempo_restante.total_seconds() < 7200:  # menos de 2 horas
            return format_html('<span style="color:#ffc107; font-weight:bold;">⏰ Por vencer</span>')
        
        return format_html('<span style="color:#28a745;">✓ En tiempo</span>')
    
    @display(description='SLA Visual')
    def sla_visual(self, obj):
        if not obj.pk:
            return '-'
        
        ahora = timezone.now()
        tiempo_total = (obj.fecha_limite_sla - obj.fecha_creacion).total_seconds()
        tiempo_transcurrido = (ahora - obj.fecha_creacion).total_seconds()
        porcentaje = min(100, (tiempo_transcurrido / tiempo_total) * 100)
        
        if obj.esta_vencido():
            color = '#dc3545'
            texto = 'VENCIDO'
        elif porcentaje > 80:
            color = '#ffc107'
            texto = 'Por vencer'
        else:
            color = '#28a745'
            texto = 'En tiempo'
        
        return format_html(
            '<div style="width:100%; background:#e9ecef; border-radius:4px; overflow:hidden;">'
            '<div style="width:{}%; background:{}; padding:4px; color:white; font-size:11px; text-align:center;">{}</div>'
            '</div>',
            porcentaje, color, texto
        )
    
    @display(description='Asignado', ordering='asignado_a')
    def asignado_display(self, obj):
        if obj.asignado_a:
            url = reverse('admin:usuarios_usuario_change', args=[obj.asignado_a.pk])
            return format_html('<a href="{}">{}</a>', url, obj.asignado_a.get_full_name() or obj.asignado_a.username)
        return format_html('<span style="color:#999;">Sin asignar</span>')
    
    @display(description='Creado', ordering='fecha_creacion')
    def fecha_creacion_display(self, obj):
        return obj.fecha_creacion.strftime('%d/%m/%Y %H:%M')
    
    @admin.action(description='Marcar como En Proceso')
    def marcar_en_proceso(self, request, queryset):
        updated = queryset.update(estado='EN_PROCESO')
        self.message_user(request, f'{updated} ticket(s) marcado(s) como En Proceso.')
    
    @admin.action(description='Marcar como Resuelto')
    def marcar_resuelto(self, request, queryset):
        updated = queryset.update(estado='RESUELTO', fecha_resolucion=timezone.now())
        self.message_user(request, f'{updated} ticket(s) marcado(s) como Resuelto.')
    
    @admin.action(description='Marcar como Cerrado')
    def marcar_cerrado(self, request, queryset):
        updated = queryset.update(estado='CERRADO', fecha_cierre=timezone.now())
        self.message_user(request, f'{updated} ticket(s) marcado(s) como Cerrado.')


@admin.register(ComentarioTicket)
class ComentarioTicketAdmin(ModelAdmin):
    list_display = ('ticket_link', 'autor_link', 'comentario_preview', 'fecha_creacion_display')
    list_filter = ('fecha_creacion',)
    search_fields = ('ticket__numero_ticket', 'comentario', 'autor__username')
    readonly_fields = ('fecha_creacion',)
    date_hierarchy = 'fecha_creacion'
    list_per_page = 50
    
    @display(description='Ticket', ordering='ticket')
    def ticket_link(self, obj):
        url = reverse('admin:tickets_ticket_change', args=[obj.ticket.pk])
        return format_html('<a href="{}">{}</a>', url, obj.ticket.numero_ticket)
    
    @display(description='Autor', ordering='autor')
    def autor_link(self, obj):
        url = reverse('admin:usuarios_usuario_change', args=[obj.autor.pk])
        return format_html('<a href="{}">{}</a>', url, obj.autor.get_full_name() or obj.autor.username)
    
    @display(description='Comentario')
    def comentario_preview(self, obj):
        preview = obj.comentario[:100] + '...' if len(obj.comentario) > 100 else obj.comentario
        return format_html('<span style="font-style:italic; color:#666;">{}</span>', preview)
    
    @display(description='Fecha', ordering='fecha_creacion')
    def fecha_creacion_display(self, obj):
        return obj.fecha_creacion.strftime('%d/%m/%Y %H:%M')

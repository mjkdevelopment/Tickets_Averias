from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import Local

@admin.register(Local)
class LocalAdmin(ModelAdmin):
    list_display = ('codigo_display', 'nombre_display', 'direccion_preview', 'activo_display', 'tickets_count')
    list_filter = ('activo',)
    search_fields = ('codigo', 'nombre', 'direccion')
    ordering = ('codigo',)
    list_per_page = 50
    actions = ['activar_locales', 'desactivar_locales']
    
    fieldsets = (
        ('Información del Local', {
            'fields': (('codigo', 'nombre'), 'direccion', 'activo')
        }),
    )
    
    @display(description='Código', ordering='codigo')
    def codigo_display(self, obj):
        return format_html('<strong style="font-family:monospace; font-size:13px; color:#007bff;">{}</strong>', obj.codigo)
    
    @display(description='Nombre', ordering='nombre')
    def nombre_display(self, obj):
        return format_html('<span style="font-weight:500;">{}</span>', obj.nombre)
    
    @display(description='Dirección')
    def direccion_preview(self, obj):
        if obj.direccion:
            preview = obj.direccion[:50] + '...' if len(obj.direccion) > 50 else obj.direccion
            return format_html('<span style="color:#666; font-style:italic;">{}</span>', preview)
        return format_html('<span style="color:#ccc;">Sin dirección</span>')
    
    @display(description='Activo', boolean=True, ordering='activo')
    def activo_display(self, obj):
        return obj.activo
    
    @display(description='Tickets')
    def tickets_count(self, obj):
        total = obj.tickets.count()
        abiertos = obj.tickets.filter(estado__in=['PENDIENTE', 'EN_PROCESO']).count()
        
        if abiertos > 0:
            return format_html(
                '<span><strong style="color:#dc3545;">{}</strong> / {}</span>',
                abiertos, total
            )
        return format_html('<span style="color:#999;">{}</span>', total)
    
    @admin.action(description='Activar locales seleccionados')
    def activar_locales(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} local(es) activado(s).')
    
    @admin.action(description='Desactivar locales seleccionados')
    def desactivar_locales(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} local(es) desactivado(s).')

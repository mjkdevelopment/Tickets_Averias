from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django import forms
from unfold.admin import ModelAdmin
from unfold.decorators import display

from .models import Usuario, DispositivoNotificacion


class UsuarioAdminForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get("rol")
        especialidades = cleaned_data.get("especialidades")

        rol_tecnico = getattr(Usuario, "ROL_TECNICO", "TECNICO")

        if rol == rol_tecnico:
            if not especialidades or especialidades.count() == 0:
                raise forms.ValidationError(
                    "Cuando el usuario es TÉCNICO debes seleccionar al menos "
                    "una categoría de avería en el campo 'especialidades'."
                )

        return cleaned_data


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin, ModelAdmin):
    form = UsuarioAdminForm

    list_display = ("username_display", "nombre_completo", "rol_badge", "especialidades_list", 
                    "is_active_display", "is_staff_display", "tickets_asignados")
    list_filter = ("rol", "is_active", "is_staff", "is_superuser", "especialidades")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)
    list_per_page = 50

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Rol y Especialidades", {
            "fields": ("rol", "especialidades"),
            "description": "Configura el rol del usuario y sus especialidades técnicas"
        }),
    )

    filter_horizontal = ("groups", "user_permissions", "especialidades")
    
    @display(description='Usuario', ordering='username')
    def username_display(self, obj):
        return format_html('<strong>{}</strong>', obj.username)
    
    @display(description='Nombre Completo')
    def nombre_completo(self, obj):
        nombre = obj.get_full_name()
        return nombre if nombre else format_html('<span style="color:#999;">Sin nombre</span>')
    
    @display(description='Rol', ordering='rol')
    def rol_badge(self, obj):
        colors = {
            'ADMIN': '#007bff',
            'TECNICO': '#28a745',
            'USUARIO': '#6c757d',
        }
        return format_html(
            '<span style="background:{}; padding:3px 10px; border-radius:4px; color:white; font-size:11px;">{}</span>',
            colors.get(obj.rol, '#6c757d'),
            obj.get_rol_display()
        )
    
    @display(description='Especialidades')
    def especialidades_list(self, obj):
        if obj.rol == 'TECNICO':
            especialidades = obj.especialidades.all()[:3]
            if not especialidades:
                return format_html('<span style="color:#dc3545;">⚠️ Sin especialidades</span>')
            
            badges = ''.join([
                f'<span style="background:#17a2b8; padding:2px 6px; border-radius:3px; color:white; font-size:10px; margin-right:4px;">{e.nombre}</span>'
                for e in especialidades
            ])
            total = obj.especialidades.count()
            if total > 3:
                badges += f'<span style="color:#666; font-size:10px;">+{total-3} más</span>'
            return format_html(badges)
        return '-'
    
    @display(description='Activo', boolean=True, ordering='is_active')
    def is_active_display(self, obj):
        return obj.is_active
    
    @display(description='Staff', boolean=True, ordering='is_staff')
    def is_staff_display(self, obj):
        return obj.is_staff
    
    @display(description='Tickets Asignados')
    def tickets_asignados(self, obj):
        count = obj.tickets_asignados.filter(estado__in=['PENDIENTE', 'EN_PROCESO']).count()
        if count > 0:
            return format_html('<strong style="color:#dc3545;">{}</strong>', count)
        return format_html('<span style="color:#999;">0</span>')


@admin.register(DispositivoNotificacion)
class DispositivoNotificacionAdmin(ModelAdmin):
    list_display = ("usuario_link", "activo_display", "fecha_registro_display", "token_preview")
    list_filter = ("activo", "fecha_registro")
    search_fields = ("usuario__username", "fcm_token")
    readonly_fields = ("fecha_registro", "token_completo")
    ordering = ("-fecha_registro",)
    list_per_page = 50
    actions = ['activar_dispositivos', 'desactivar_dispositivos']
    
    fieldsets = (
        ('Información del Dispositivo', {
            'fields': ('usuario', 'fcm_token', 'activo')
        }),
        ('Detalles', {
            'fields': ('fecha_registro', 'token_completo'),
            'classes': ('collapse',)
        }),
    )
    
    @display(description='Usuario', ordering='usuario')
    def usuario_link(self, obj):
        url = reverse('admin:usuarios_usuario_change', args=[obj.usuario.pk])
        return format_html('<a href="{}">{}</a>', url, obj.usuario.username)
    
    @display(description='Activo', boolean=True, ordering='activo')
    def activo_display(self, obj):
        return obj.activo
    
    @display(description='Registrado', ordering='fecha_registro')
    def fecha_registro_display(self, obj):
        return obj.fecha_registro.strftime('%d/%m/%Y %H:%M')
    
    @display(description='Token FCM')
    def token_preview(self, obj):
        token = obj.fcm_token
        preview = f"{token[:20]}...{token[-20:]}" if len(token) > 40 else token
        return format_html('<code style="font-size:10px; color:#666;">{}</code>', preview)
    
    @display(description='Token Completo')
    def token_completo(self, obj):
        return format_html('<textarea readonly style="width:100%; height:100px; font-family:monospace; font-size:10px;">{}</textarea>', obj.fcm_token)
    
    @admin.action(description='Activar dispositivos seleccionados')
    def activar_dispositivos(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} dispositivo(s) activado(s).')
    
    @admin.action(description='Desactivar dispositivos seleccionados')
    def desactivar_dispositivos(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} dispositivo(s) desactivado(s).')


admin.site.site_header = "Botija Tickets - Administración"
admin.site.site_title = "Botija Tickets"
admin.site.index_title = "Sitio administrativo"


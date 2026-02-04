from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Local

@admin.register(Local)
class LocalAdmin(ModelAdmin):
    list_display = ('codigo', 'nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('codigo', 'nombre', 'direccion')
    ordering = ('codigo',)

from django.urls import path
from . import views

urlpatterns = [
    path('', views.tickets_lista, name='tickets_lista'),
    path('nuevo/', views.ticket_crear, name='ticket_crear'),
    path('<int:pk>/', views.ticket_detalle, name='ticket_detalle'),
    path('<int:pk>/estado/', views.ticket_actualizar_estado, name='ticket_actualizar_estado'),
    path('<int:pk>/tomar/', views.ticket_tomar, name='ticket_tomar'),

    # API: Notificaciones y menciones
    path('api/notificaciones/', views.api_notificaciones, name='api_notificaciones'),
    path('api/notificaciones/leer/', views.api_notificaciones_leer, name='api_notificaciones_leer'),
    path('api/notificaciones/leer/<int:ticket_id>/', views.api_notificaciones_leer_ticket, name='api_notificaciones_leer_ticket'),
    path('api/usuarios/', views.api_usuarios_buscar, name='api_usuarios_buscar'),
]

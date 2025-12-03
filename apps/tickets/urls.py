from django.urls import path
from . import views

urlpatterns = [
    path('', views.tickets_lista, name='tickets_lista'),
    path('nuevo/', views.ticket_crear, name='ticket_crear'),
    path('<int:pk>/', views.ticket_detalle, name='ticket_detalle'),
    path('<int:pk>/estado/', views.ticket_actualizar_estado, name='ticket_actualizar_estado'),
    path('<int:pk>/tomar/', views.ticket_tomar, name='ticket_tomar'),

]

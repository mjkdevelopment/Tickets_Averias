"""
Tests para el módulo de tickets
"""
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.locales.models import Local
from apps.tickets.models import Ticket, CategoriaAveria, ComentarioTicket

User = get_user_model()


class CategoriaAveriaModelTest(TestCase):
    """Tests para el modelo CategoriaAveria"""
    
    def setUp(self):
        self.categoria = CategoriaAveria.objects.create(
            nombre="Test Categoría",
            descripcion="Descripción de prueba",
            tiempo_sla_horas=24,
            activo=True,
            color="#007bff"
        )
    
    def test_categoria_creacion(self):
        """Test creación básica de categoría"""
        self.assertEqual(self.categoria.nombre, "Test Categoría")
        self.assertEqual(self.categoria.tiempo_sla_horas, 24)
        self.assertTrue(self.categoria.activo)
    
    def test_categoria_str(self):
        """Test representación en string"""
        self.assertEqual(str(self.categoria), "Test Categoría")


class TicketModelTest(TestCase):
    """Tests para el modelo Ticket"""
    
    def setUp(self):
        # Crear usuario
        self.usuario = User.objects.create_user(
            username="testuser",
            password="testpass123",
            rol="ADMIN"
        )
        
        # Crear local
        self.local = Local.objects.create(
            codigo="TEST01",
            nombre="Local de prueba",
            activo=True
        )
        
        # Crear categoría
        self.categoria = CategoriaAveria.objects.create(
            nombre="Electricidad",
            tiempo_sla_horas=4,
            activo=True
        )
    
    def test_ticket_creacion_automatica_numero(self):
        """Test que el número de ticket se genera automáticamente"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test ticket",
            descripcion="Descripción de prueba",
            creado_por=self.usuario
        )
        self.assertIsNotNone(ticket.numero_ticket)
        self.assertTrue(ticket.numero_ticket.startswith("TKT-"))
    
    def test_ticket_calculo_sla(self):
        """Test que la fecha límite SLA se calcula correctamente"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test SLA",
            descripcion="Test",
            creado_por=self.usuario
        )
        
        diferencia = ticket.fecha_limite_sla - ticket.fecha_creacion
        horas_diferencia = diferencia.total_seconds() / 3600
        
        self.assertAlmostEqual(horas_diferencia, 4, places=0)
    
    def test_ticket_esta_vencido_false(self):
        """Test ticket no vencido"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test no vencido",
            descripcion="Test",
            creado_por=self.usuario,
            estado="PENDIENTE"
        )
        self.assertFalse(ticket.esta_vencido())
    
    def test_ticket_esta_vencido_true(self):
        """Test ticket vencido"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test vencido",
            descripcion="Test",
            creado_por=self.usuario,
            estado="PENDIENTE"
        )
        # Forzar fecha límite en el pasado
        ticket.fecha_limite_sla = timezone.now() - timedelta(hours=1)
        ticket.save(update_fields=['fecha_limite_sla'])
        
        self.assertTrue(ticket.esta_vencido())
    
    def test_ticket_resuelto_no_vencido(self):
        """Test que tickets resueltos no se consideran vencidos"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test resuelto",
            descripcion="Test",
            creado_por=self.usuario,
            estado="RESUELTO"
        )
        # Aunque la fecha límite esté en el pasado
        ticket.fecha_limite_sla = timezone.now() - timedelta(hours=1)
        ticket.save(update_fields=['fecha_limite_sla'])
        
        self.assertFalse(ticket.esta_vencido())
    
    def test_tiempo_restante_sla_ticket_activo(self):
        """Test cálculo de tiempo restante para ticket activo"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test tiempo restante",
            descripcion="Test",
            creado_por=self.usuario,
            estado="PENDIENTE"
        )
        
        tiempo_restante = ticket.tiempo_restante_sla()
        self.assertIsNotNone(tiempo_restante)
        self.assertGreater(tiempo_restante.total_seconds(), 0)
    
    def test_tiempo_restante_sla_ticket_resuelto(self):
        """Test que tickets resueltos retornan None en tiempo restante"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test resuelto",
            descripcion="Test",
            creado_por=self.usuario,
            estado="RESUELTO"
        )
        
        tiempo_restante = ticket.tiempo_restante_sla()
        self.assertIsNone(tiempo_restante)
    
    def test_ticket_cambio_estado_actualiza_fechas(self):
        """Test que cambiar estado actualiza las fechas correspondientes"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test fechas",
            descripcion="Test",
            creado_por=self.usuario,
            estado="PENDIENTE"
        )
        
        # Marcar como resuelto
        ticket.estado = "RESUELTO"
        ticket.save()
        
        self.assertIsNotNone(ticket.fecha_resolucion)
        
        # Marcar como cerrado
        ticket.estado = "CERRADO"
        ticket.save()
        
        self.assertIsNotNone(ticket.fecha_cierre)


class ComentarioTicketTest(TestCase):
    """Tests para el modelo ComentarioTicket"""
    
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="testuser",
            password="testpass123",
            rol="ADMIN"
        )
        
        self.local = Local.objects.create(
            codigo="TEST01",
            nombre="Local de prueba",
            activo=True
        )
        
        self.categoria = CategoriaAveria.objects.create(
            nombre="Electricidad",
            tiempo_sla_horas=4,
            activo=True
        )
        
        self.ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test ticket",
            descripcion="Test",
            creado_por=self.usuario
        )
    
    def test_comentario_creacion(self):
        """Test creación de comentario"""
        comentario = ComentarioTicket.objects.create(
            ticket=self.ticket,
            usuario=self.usuario,  # Es 'usuario' no 'autor'
            comentario="Este es un comentario de prueba"
        )
        
        self.assertEqual(comentario.ticket, self.ticket)
        self.assertEqual(comentario.usuario, self.usuario)
        self.assertIsNotNone(comentario.fecha_creacion)
    
    def test_comentario_str(self):
        """Test representación en string"""
        comentario = ComentarioTicket.objects.create(
            ticket=self.ticket,
            usuario=self.usuario,  # Es 'usuario' no 'autor'
            comentario="Comentario de prueba"
        )
        
        str_comentario = str(comentario)
        self.assertIn(self.ticket.numero_ticket, str_comentario)
        self.assertIn(self.usuario.username, str_comentario)

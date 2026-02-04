"""
Tests para los admin de la aplicación
"""
from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from apps.tickets.admin import TicketAdmin, CategoriaAveriaAdmin
from apps.tickets.models import Ticket, CategoriaAveria
from apps.locales.models import Local
from apps.locales.admin import LocalAdmin
from apps.usuarios.admin import UsuarioAdmin

User = get_user_model()


class MockRequest:
    """Mock request para tests de admin"""
    def __init__(self, user=None):
        self.user = user


class TicketAdminTest(TestCase):
    """Tests para TicketAdmin"""
    
    def setUp(self):
        self.site = AdminSite()
        self.admin = TicketAdmin(Ticket, self.site)
        self.factory = RequestFactory()
        
        # Crear usuario admin
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="admin123",
            email="admin@test.com"
        )
        
        # Crear local
        self.local = Local.objects.create(
            codigo="TEST01",
            nombre="Local Test"
        )
        
        # Crear categoría
        self.categoria = CategoriaAveria.objects.create(
            nombre="Electricidad",
            tiempo_sla_horas=4
        )
    
    def test_numero_ticket_display(self):
        """Test que numero_ticket_display retorna HTML formateado"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test",
            descripcion="Test",
            creado_por=self.admin_user
        )
        
        resultado = self.admin.numero_ticket_display(ticket)
        self.assertIn(ticket.numero_ticket, resultado)
        self.assertIn('<strong', resultado)  # Usa <strong> no <span>
    
    def test_categoria_badge(self):
        """Test que categoria_badge retorna HTML con estilo"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test",
            descripcion="Test",
            creado_por=self.admin_user
        )
        
        resultado = self.admin.categoria_badge(ticket)
        self.assertIn(self.categoria.nombre, resultado)
        self.assertIn('style=', resultado)
    
    def test_estado_badge_pendiente(self):
        """Test estado badge para ticket pendiente"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test",
            descripcion="Test",
            creado_por=self.admin_user,
            estado="PENDIENTE"
        )
        
        resultado = self.admin.estado_badge(ticket)
        self.assertIn("Pendiente", resultado)  # Es "Pendiente" no "PENDIENTE"
        self.assertIn("#6c757d", resultado)
    
    def test_estado_badge_en_proceso(self):
        """Test estado badge para ticket en proceso"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test",
            descripcion="Test",
            creado_por=self.admin_user,
            estado="EN_PROCESO"
        )
        
        resultado = self.admin.estado_badge(ticket)
        self.assertIn("En Proceso", resultado)  # Es "En Proceso" no "EN PROCESO"
    
    def test_estado_badge_resuelto(self):
        """Test estado badge para ticket resuelto"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test",
            descripcion="Test",
            creado_por=self.admin_user,
            estado="RESUELTO"
        )
        
        resultado = self.admin.estado_badge(ticket)
        self.assertIn("Resuelto", resultado)  # Es "Resuelto" no "RESUELTO"
        self.assertIn("#28a745", resultado)
    
    def test_prioridad_badge(self):
        """Test prioridad badge con diferentes prioridades"""
        ticket_alta = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test Alta",
            descripcion="Test",
            creado_por=self.admin_user,
            prioridad="ALTA"
        )
        
        resultado = self.admin.prioridad_badge(ticket_alta)
        self.assertIn("Alta", resultado)  # Es "Alta" no "ALTA"
        self.assertIn("#fd7e14", resultado)
    
    def test_sla_status_ticket_activo(self):
        """Test SLA status para ticket activo"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test",
            descripcion="Test",
            creado_por=self.admin_user,
            estado="PENDIENTE"
        )
        
        resultado = self.admin.sla_status(ticket)
        self.assertIsNotNone(resultado)
        self.assertIn('<span', resultado)
    
    def test_sla_status_ticket_resuelto_retorna_completado(self):
        """
        Test CRÍTICO: sla_status debe manejar None cuando ticket está resuelto
        Este test verifica que no haya AttributeError
        """
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test Resuelto",
            descripcion="Test",
            creado_por=self.admin_user,
            estado="RESUELTO"
        )
        
        # Este método NO debe lanzar AttributeError
        resultado = self.admin.sla_status(ticket)
        
        self.assertIsNotNone(resultado)
        self.assertIn("Completado", resultado)
        # Verificar que no se intenta llamar .total_seconds() en None
    
    def test_sla_status_ticket_cerrado(self):
        """Test SLA status para ticket cerrado retorna completado"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test Cerrado",
            descripcion="Test",
            creado_por=self.admin_user,
            estado="CERRADO"
        )
        
        resultado = self.admin.sla_status(ticket)
        self.assertIn("Completado", resultado)
    
    def test_sla_status_ticket_cancelado(self):
        """Test SLA status para ticket cancelado retorna completado"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test Cancelado",
            descripcion="Test",
            creado_por=self.admin_user,
            estado="CANCELADO"
        )
        
        resultado = self.admin.sla_status(ticket)
        self.assertIn("Completado", resultado)
    
    def test_sla_status_ticket_critico(self):
        """Test SLA status cuando quedan menos de 2 horas"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test Crítico",
            descripcion="Test",
            creado_por=self.admin_user,
            estado="PENDIENTE"
        )
        
        # Forzar SLA a 1 hora restante
        ticket.fecha_limite_sla = timezone.now() + timedelta(hours=1)
        ticket.save(update_fields=['fecha_limite_sla'])
        
        resultado = self.admin.sla_status(ticket)
        self.assertIn("#ffc107", resultado)  # Color amarillo warning, no danger
    
    def test_sla_visual(self):
        """Test que sla_visual genera barra de progreso"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test",
            descripcion="Test",
            creado_por=self.admin_user
        )
        
        resultado = self.admin.sla_visual(ticket)
        self.assertIsNotNone(resultado)
    
    def test_local_link(self):
        """Test que local_link genera enlace correcto"""
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test",
            descripcion="Test",
            creado_por=self.admin_user
        )
        
        resultado = self.admin.local_link(ticket)
        self.assertIn(self.local.codigo, resultado)  # Muestra código no nombre
        self.assertIn('href=', resultado)


class CategoriaAveriaAdminTest(TestCase):
    """Tests para CategoriaAveriaAdmin"""
    
    def setUp(self):
        self.site = AdminSite()
        self.admin = CategoriaAveriaAdmin(CategoriaAveria, self.site)
    
    def test_tiempo_sla_display(self):
        """Test que tiempo_sla_display formatea correctamente"""
        categoria = CategoriaAveria.objects.create(
            nombre="Plomería",
            tiempo_sla_horas=8
        )
        
        resultado = self.admin.tiempo_sla_display(categoria)
        self.assertEqual(resultado, "8h")
    
    def test_color_display(self):
        """Test que color_display retorna HTML con color"""
        categoria = CategoriaAveria.objects.create(
            nombre="Test",
            tiempo_sla_horas=4,
            color="#28a745"
        )
        
        resultado = self.admin.color_display(categoria)
        self.assertIn("#28a745", resultado)
        self.assertIn("background", resultado)
    
    def test_activo_display(self):
        """Test activo_display retorna estado booleano"""
        categoria = CategoriaAveria.objects.create(
            nombre="Test",
            tiempo_sla_horas=4,
            activo=True
        )
        
        resultado = self.admin.activo_display(categoria)
        self.assertTrue(resultado)


class LocalAdminTest(TestCase):
    """Tests para LocalAdmin"""
    
    def setUp(self):
        self.site = AdminSite()
        self.admin = LocalAdmin(Local, self.site)
        
        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="admin123"
        )
    
    def test_codigo_display(self):
        """Test que codigo_display retorna código formateado"""
        local = Local.objects.create(
            codigo="LOC001",
            nombre="Test Local"
        )
        
        resultado = self.admin.codigo_display(local)
        self.assertIn("LOC001", resultado)
        self.assertIn("font-family", resultado)
    
    def test_tickets_count_sin_tickets(self):
        """Test contador de tickets cuando no hay tickets"""
        local = Local.objects.create(
            codigo="LOC002",
            nombre="Test Local"
        )
        
        resultado = self.admin.tickets_count(local)
        self.assertIn("0", resultado)


class UsuarioAdminTest(TestCase):
    """Tests para UsuarioAdmin"""
    
    def setUp(self):
        self.site = AdminSite()
        self.admin = UsuarioAdmin(User, self.site)
    
    def test_rol_badge_admin(self):
        """Test badge para rol admin"""
        usuario = User.objects.create_user(
            username="admin",
            password="test123",
            rol="ADMIN"
        )
        
        resultado = self.admin.rol_badge(usuario)
        self.assertIn("Administrador", resultado)  # Es "Administrador" no "ADMIN"
    
    def test_rol_badge_tecnico(self):
        """Test badge para rol técnico"""
        usuario = User.objects.create_user(
            username="tecnico",
            password="test123",
            rol="TECNICO"
        )
        
        resultado = self.admin.rol_badge(usuario)
        self.assertIn("Técnico", resultado)  # Es "Técnico" no "TÉCNICO"
    
    def test_especialidades_list_sin_especialidades(self):
        """Test lista de especialidades cuando usuario no tiene"""
        usuario = User.objects.create_user(
            username="user",
            password="test123"
        )
        
        resultado = self.admin.especialidades_list(usuario)
        self.assertEqual(resultado, "-")
    
    def test_especialidades_list_con_especialidades(self):
        """Test lista de especialidades cuando usuario tiene"""
        usuario = User.objects.create_user(
            username="tecnico",
            password="test123",
            rol="TECNICO"
        )
        
        cat1 = CategoriaAveria.objects.create(nombre="Electricidad", tiempo_sla_horas=4)
        cat2 = CategoriaAveria.objects.create(nombre="Plomería", tiempo_sla_horas=8)
        
        usuario.especialidades.add(cat1, cat2)
        # Refrescar para cargar relaciones M2M
        usuario.refresh_from_db()
        
        resultado = self.admin.especialidades_list(usuario)
        self.assertIn("Electricidad", resultado)
        self.assertIn("Plomería", resultado)

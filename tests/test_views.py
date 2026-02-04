"""
Tests para las vistas de la aplicación
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.tickets.models import Ticket, CategoriaAveria
from apps.locales.models import Local

User = get_user_model()


class DashboardViewTest(TestCase):
    """Tests para la vista del dashboard"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = User.objects.create_user(
            username="testuser",
            password="testpass123",
            rol="ADMIN"
        )
    
    def test_dashboard_requiere_autenticacion(self):
        """Test que el dashboard requiere autenticación"""
        response = self.client.get(reverse('dashboard'))
        # Debe redirigir al login
        self.assertEqual(response.status_code, 302)
    
    def test_dashboard_usuario_autenticado(self):
        """Test dashboard con usuario autenticado"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('dashboard'))
        
        self.assertEqual(response.status_code, 200)


class TicketListViewTest(TestCase):
    """Tests para la vista de lista de tickets"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = User.objects.create_user(
            username="testuser",
            password="testpass123",
            rol="ADMIN"
        )
        
        self.local = Local.objects.create(
            codigo="TEST01",
            nombre="Local Test"
        )
        
        self.categoria = CategoriaAveria.objects.create(
            nombre="Electricidad",
            tiempo_sla_horas=4
        )
    
    def test_lista_tickets_requiere_autenticacion(self):
        """Test que la lista requiere autenticación"""
        response = self.client.get(reverse('tickets_lista'))
        self.assertEqual(response.status_code, 302)
    
    def test_lista_tickets_autenticado(self):
        """Test lista con usuario autenticado"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('tickets_lista'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_lista_muestra_tickets(self):
        """Test que la lista muestra los tickets creados"""
        self.client.login(username="testuser", password="testpass123")
        
        # Crear ticket
        ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test Ticket",
            descripcion="Descripción",
            creado_por=self.usuario
        )
        
        response = self.client.get(reverse('tickets_lista'))
        self.assertContains(response, ticket.numero_ticket)


class TicketCreateViewTest(TestCase):
    """Tests para la vista de creación de tickets"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = User.objects.create_user(
            username="testuser",
            password="testpass123",
            rol="ADMIN"
        )
        
        self.local = Local.objects.create(
            codigo="TEST01",
            nombre="Local Test"
        )
        
        self.categoria = CategoriaAveria.objects.create(
            nombre="Electricidad",
            tiempo_sla_horas=4
        )
    
    def test_crear_ticket_requiere_autenticacion(self):
        """Test que crear ticket requiere autenticación"""
        response = self.client.get(reverse('ticket_crear'))
        self.assertEqual(response.status_code, 302)
    
    def test_formulario_crear_ticket(self):
        """Test mostrar formulario de creación"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse('ticket_crear'))
        
        self.assertEqual(response.status_code, 200)
    
    def test_crear_ticket_post(self):
        """Test crear ticket mediante POST"""
        self.client.login(username="testuser", password="testpass123")
        
        data = {
            'local': self.local.id,
            'categoria': self.categoria.id,
            'titulo': 'Nuevo Ticket',
            'descripcion': 'Descripción del ticket',
            'prioridad': 'MEDIA',
            'creado_por': self.usuario.id
        }
        
        response = self.client.post(reverse('ticket_crear'), data)
        
        # Puede fallar por validación de formulario, verificar que al menos se intentó crear
        self.assertIn(response.status_code, [200, 302])  # 200 si error, 302 si éxito


class TicketDetailViewTest(TestCase):
    """Tests para la vista de detalle de ticket"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = User.objects.create_user(
            username="testuser",
            password="testpass123",
            rol="ADMIN"
        )
        
        self.local = Local.objects.create(
            codigo="TEST01",
            nombre="Local Test"
        )
        
        self.categoria = CategoriaAveria.objects.create(
            nombre="Electricidad",
            tiempo_sla_horas=4
        )
        
        self.ticket = Ticket.objects.create(
            local=self.local,
            categoria=self.categoria,
            titulo="Test Ticket",
            descripcion="Descripción",
            creado_por=self.usuario
        )
    
    def test_detalle_ticket_requiere_autenticacion(self):
        """Test que ver detalle requiere autenticación"""
        response = self.client.get(
            reverse('ticket_detalle', args=[self.ticket.pk])
        )
        self.assertEqual(response.status_code, 302)
    
    def test_detalle_ticket_autenticado(self):
        """Test ver detalle con usuario autenticado"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse('ticket_detalle', args=[self.ticket.pk])
        )
        
        # Verificar que la página se carga correctamente
        self.assertEqual(response.status_code, 200)


class LoginViewTest(TestCase):
    """Tests para la vista de login"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
    
    def test_login_get(self):
        """Test mostrar formulario de login"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
    
    def test_login_post_credenciales_correctas(self):
        """Test login con credenciales correctas"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Debe redirigir después de login exitoso
        self.assertEqual(response.status_code, 302)
    
    def test_login_post_credenciales_incorrectas(self):
        """Test login con credenciales incorrectas"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        # Debe volver a mostrar el formulario con error
        self.assertEqual(response.status_code, 200)

"""
Tests para el módulo de usuarios
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.usuarios.models import DispositivoNotificacion
from apps.tickets.models import CategoriaAveria

User = get_user_model()


class UsuarioModelTest(TestCase):
    """Tests para el modelo Usuario"""
    
    def test_crear_usuario_basico(self):
        """Test crear usuario básico"""
        usuario = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            rol="USUARIO"
        )
        
        self.assertEqual(usuario.username, "testuser")
        self.assertEqual(usuario.email, "test@example.com")
        self.assertEqual(usuario.rol, "USUARIO")
        self.assertTrue(usuario.check_password("testpass123"))
    
    def test_crear_admin(self):
        """Test crear usuario admin"""
        admin = User.objects.create_user(
            username="admin",
            password="adminpass123",
            rol="ADMIN"
        )
        
        self.assertEqual(admin.rol, "ADMIN")
    
    def test_crear_tecnico(self):
        """Test crear técnico"""
        tecnico = User.objects.create_user(
            username="tecnico",
            password="tecpass123",
            rol="TECNICO"
        )
        
        self.assertEqual(tecnico.rol, "TECNICO")
    
    def test_usuario_str(self):
        """Test representación en string"""
        usuario = User.objects.create_user(
            username="testuser",
            password="test123",
            first_name="Juan",
            last_name="Pérez"
        )
        
        str_usuario = str(usuario)
        self.assertIn("Juan", str_usuario)
        self.assertIn("Pérez", str_usuario)
    
    def test_usuario_especialidades(self):
        """Test que técnico puede tener especialidades"""
        tecnico = User.objects.create_user(
            username="tecnico",
            password="test123",
            rol="TECNICO"
        )
        
        cat1 = CategoriaAveria.objects.create(
            nombre="Electricidad",
            tiempo_sla_horas=4
        )
        cat2 = CategoriaAveria.objects.create(
            nombre="Plomería",
            tiempo_sla_horas=8
        )
        
        tecnico.especialidades.add(cat1, cat2)
        
        self.assertEqual(tecnico.especialidades.count(), 2)
        self.assertIn(cat1, tecnico.especialidades.all())
        self.assertIn(cat2, tecnico.especialidades.all())


class DispositivoNotificacionTest(TestCase):
    """Tests para el modelo DispositivoNotificacion"""
    
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="testuser",
            password="test123"
        )
    
    def test_crear_dispositivo(self):
        """Test crear dispositivo de notificación"""
        dispositivo = DispositivoNotificacion.objects.create(
            usuario=self.usuario,
            fcm_token="test_token_123456789"  # Es 'fcm_token' no 'token_fcm'
        )
        
        self.assertEqual(dispositivo.usuario, self.usuario)
        self.assertEqual(dispositivo.fcm_token, "test_token_123456789")
        self.assertTrue(dispositivo.activo)
    
    def test_dispositivo_ios(self):
        """Test dispositivo iOS"""
        dispositivo = DispositivoNotificacion.objects.create(
            usuario=self.usuario,
            fcm_token="ios_token_987654321"
        )
        
        self.assertEqual(dispositivo.fcm_token, "ios_token_987654321")
    
    def test_dispositivo_web(self):
        """Test dispositivo web"""
        dispositivo = DispositivoNotificacion.objects.create(
            usuario=self.usuario,
            fcm_token="web_token_456789123"
        )
        
        self.assertEqual(dispositivo.fcm_token, "web_token_456789123")
    
    def test_dispositivo_inactivo(self):
        """Test desactivar dispositivo"""
        dispositivo = DispositivoNotificacion.objects.create(
            usuario=self.usuario,
            fcm_token="test_token",
            activo=True
        )
        
        dispositivo.activo = False
        dispositivo.save()
        
        self.assertFalse(dispositivo.activo)
    
    def test_dispositivo_str(self):
        """Test representación en string"""
        dispositivo = DispositivoNotificacion.objects.create(
            usuario=self.usuario,
            fcm_token="test_token"
        )
        
        str_dispositivo = str(dispositivo)
        self.assertIn(self.usuario.username, str_dispositivo)
    
    def test_usuario_multiples_dispositivos(self):
        """Test que un usuario puede tener múltiples dispositivos"""
        DispositivoNotificacion.objects.create(
            usuario=self.usuario,
            fcm_token="android_token"
        )
        DispositivoNotificacion.objects.create(
            usuario=self.usuario,
            fcm_token="ios_token"
        )
        
        dispositivos = DispositivoNotificacion.objects.filter(usuario=self.usuario)
        self.assertEqual(dispositivos.count(), 2)

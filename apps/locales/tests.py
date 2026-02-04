"""
Tests para el módulo de locales
"""
from django.test import TestCase

from apps.locales.models import Local


class LocalModelTest(TestCase):
    """Tests para el modelo Local"""
    
    def test_crear_local(self):
        """Test crear local básico"""
        local = Local.objects.create(
            codigo="LOC001",
            nombre="Tienda Centro",
            direccion="Calle Principal 123",
            telefono="+1234567890",
            activo=True
        )
        
        self.assertEqual(local.codigo, "LOC001")
        self.assertEqual(local.nombre, "Tienda Centro")
        self.assertTrue(local.activo)
    
    def test_local_str(self):
        """Test representación en string"""
        local = Local.objects.create(
            codigo="LOC002",
            nombre="Tienda Norte"
        )
        
        str_local = str(local)
        self.assertIn("LOC002", str_local)
        self.assertIn("Tienda Norte", str_local)
    
    def test_local_sin_direccion(self):
        """Test local sin dirección con blank"""
        local = Local.objects.create(
            codigo="LOC003",
            nombre="Tienda Sin Dirección",
            direccion="",  # Direccion permite blank pero no null
            provincia="Provincia Test",
            municipio="Municipio Test"
        )
        
        self.assertEqual(local.direccion, "")
    
    def test_local_sin_telefono(self):
        """Test local sin teléfono es válido"""
        local = Local.objects.create(
            codigo="LOC004",
            nombre="Tienda Sin Teléfono"
        )
        
        self.assertIsNone(local.telefono)
    
    def test_local_inactivo(self):
        """Test crear local inactivo"""
        local = Local.objects.create(
            codigo="LOC005",
            nombre="Tienda Cerrada",
            activo=False
        )
        
        self.assertFalse(local.activo)
    
    def test_local_codigo_unico(self):
        """Test que el código de local es único"""
        Local.objects.create(
            codigo="LOC006",
            nombre="Tienda 1"
        )
        
        with self.assertRaises(Exception):
            Local.objects.create(
                codigo="LOC006",  # Mismo código
                nombre="Tienda 2"
            )
    
    def test_filtrar_locales_activos(self):
        """Test filtrar solo locales activos"""
        Local.objects.create(codigo="LOC007", nombre="Activo 1", activo=True)
        Local.objects.create(codigo="LOC008", nombre="Activo 2", activo=True)
        Local.objects.create(codigo="LOC009", nombre="Inactivo", activo=False)
        
        locales_activos = Local.objects.filter(activo=True)
        self.assertEqual(locales_activos.count(), 2)

import pytest
import sys
import os
import logging

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.parser.crud_parser import CRUDParser
from app.parser.sql_parser import SQLParser
from app.translator.sql_to_mongodb import SQLToMongoDBTranslator

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@pytest.mark.order(1)
class TestInsertParser:
    """Pruebas para el parser INSERT."""
    
    def test_insert_parser_unit(self):
        """Prueba unitaria de CRUDParser para INSERT."""
        parser = CRUDParser()
        
        # Probar INSERT con columnas especificadas
        sql = "INSERT INTO usuarios (id, nombre, edad, email) VALUES (1, 'Juan', 30, 'juan@test.com')"
        result = parser.parse_insert(sql)
        
        assert result["operation"] == "INSERT"
        assert result["table"] == "usuarios"
        assert result["values"]["id"] == 1
        assert result["values"]["nombre"] == "Juan"
        assert result["values"]["edad"] == 30
        assert result["values"]["email"] == "juan@test.com"
        
        # Probar INSERT sin columnas especificadas
        sql = "INSERT INTO productos VALUES (101, 'Laptop', 1200.99)"
        result = parser.parse_insert(sql)
        
        assert result["operation"] == "INSERT"
        assert result["table"] == "productos"
        assert len(result["values"]) == 3
        assert result["values"]["column_1"] == 101
        assert result["values"]["column_2"] == "Laptop"
        assert result["values"]["column_3"] == 1200.99
    
    def test_insert_to_mongodb_translation(self):
        """Prueba la traducción de INSERT a MongoDB."""
        sql = "INSERT INTO usuarios (id, nombre, edad, email) VALUES (1, 'Juan', 30, 'juan@test.com')"
        
        # Parsear la consulta
        parser = SQLParser(sql)
        
        # Traducir a MongoDB
        translator = SQLToMongoDBTranslator(parser)
        result = translator.translate()
        
        assert result["operation"] == "insert"
        assert result["collection"] == "usuarios"
        
        # Verificar que document contiene los valores esperados
        # Aceptar cualquiera de las dos estructuras posibles
        if "values" in result["document"]:
            # Si el documento tiene una estructura anidada
            assert result["document"]["values"]["id"] == 1
            assert result["document"]["values"]["nombre"] == "Juan"
        else:
            # Si el documento tiene una estructura plana
            assert result["document"]["id"] == 1
            assert result["document"]["nombre"] == "Juan"


    def test_actual_insert_execution(self, users_collection, products_collection):
        """Prueba la ejecución real de INSERT en MongoDB."""
        # Insertar usuario
        user_data = {
            "id": 1,
            "nombre": "Juan Pérez",
            "edad": 30,
            "rol": "usuario",
            "email": "juan@test.com",
            "activo": True
        }
        result = users_collection.insert_one(user_data)
        assert result.acknowledged
        
        # Verificar que se haya guardado
        saved_user = users_collection.find_one({"id": 1})
        assert saved_user is not None
        assert saved_user["nombre"] == "Juan Pérez"
        
        # Insertar producto
        product_data = {
            "id": 101,
            "nombre": "Laptop Pro",
            "precio": 1299.99,
            "stock": 50,
            "categoria": "tecnología"
        }
        result = products_collection.insert_one(product_data)
        assert result.acknowledged
        
        # Verificar que se haya guardado
        saved_product = products_collection.find_one({"id": 101})
        assert saved_product is not None
        assert saved_product["nombre"] == "Laptop Pro"
        
        # Insertar múltiples usuarios
        users_data = [
            {
                "id": 2,
                "nombre": "María González",
                "edad": 25,
                "rol": "admin",
                "email": "maria@test.com",
                "activo": True
            },
            {
                "id": 3,
                "nombre": "Carlos Rodríguez",
                "edad": 35,
                "rol": "usuario",
                "email": "carlos@test.com",
                "activo": True
            },
            {
                "id": 4,
                "nombre": "Laura Sánchez",
                "edad": 28,
                "rol": "editor",
                "email": "laura@test.com",
                "activo": True
            }
        ]
        result = users_collection.insert_many(users_data)
        assert result.acknowledged
        assert len(result.inserted_ids) == 3
        
        # Insertar múltiples productos
        products_data = [
            {
                "id": 102,
                "nombre": "Smartphone X",
                "precio": 899.99,
                "stock": 100,
                "categoria": "tecnología"
            },
            {
                "id": 103,
                "nombre": "Auriculares Bluetooth",
                "precio": 99.99,
                "stock": 200,
                "categoria": "accesorios"
            },
            {
                "id": 104,
                "nombre": "Teclado Mecánico",
                "precio": 129.99,
                "stock": 50,
                "categoria": "accesorios",
                "disponible": False
            }
        ]
        result = products_collection.insert_many(products_data)
        assert result.acknowledged
        assert len(result.inserted_ids) == 3
        
        # Verificar el total de documentos
        user_count = users_collection.count_documents({})
        assert user_count == 4
        
        product_count = products_collection.count_documents({})
        assert product_count == 4
        
        logger.info(f"Insertados {user_count} usuarios y {product_count} productos")
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

@pytest.mark.order(4)
class TestUpdateParser:
    """Pruebas para el parser UPDATE."""
    
    def test_update_parser_unit(self):
        """Prueba unitaria de CRUDParser para UPDATE."""
        parser = CRUDParser()
        
        # Probar UPDATE simple
        sql = "UPDATE usuarios SET nombre = 'Juan Modificado' WHERE id = 1"
        result = parser.parse_update(sql)
        
        assert result["operation"] == "UPDATE"
        assert result["table"] == "usuarios"
        assert result["values"]["nombre"] == "Juan Modificado"
        assert result["condition"]["id"] == 1
        
        # Probar UPDATE con múltiples campos
        sql = "UPDATE productos SET precio = 1399.99, stock = 45 WHERE id = 101"
        result = parser.parse_update(sql)
        
        assert result["operation"] == "UPDATE"
        assert result["table"] == "productos"
        assert result["values"]["precio"] == 1399.99
        assert result["values"]["stock"] == 45
        assert result["condition"]["id"] == 101
    
    def test_update_to_mongodb_translation(self):
        """Prueba la traducción de UPDATE a MongoDB."""
        sql = "UPDATE usuarios SET nombre = 'Juan Modificado', edad = 31 WHERE id = 1"
        
        # Parsear la consulta
        parser = SQLParser(sql)
        
        # Traducir a MongoDB
        translator = SQLToMongoDBTranslator(parser)
        result = translator.translate()
        
        assert result["operation"] == "update"
        assert result["collection"] == "usuarios"
        assert "query" in result
        assert result["query"]["query"] == {"id": 1}
        assert result["query"]["update"]["$set"] == {"nombre": "Juan Modificado", "edad": 31}
    
    def test_actual_update_execution(self, users_collection, products_collection):
        """Prueba la ejecución real de UPDATE en MongoDB."""
        # Actualizar un usuario
        result = users_collection.update_one(
            {"id": 1},
            {"$set": {"nombre": "Juan Modificado", "edad": 31}}
        )
        assert result.matched_count == 1
        assert result.modified_count == 1
        
        # Verificar la actualización
        user = users_collection.find_one({"id": 1})
        assert user["nombre"] == "Juan Modificado"
        assert user["edad"] == 31
        
        # Actualizar un producto
        result = products_collection.update_one(
            {"id": 101},
            {"$set": {"precio": 1399.99, "stock": 45}}
        )
        assert result.matched_count == 1
        assert result.modified_count == 1
        
        # Verificar la actualización
        product = products_collection.find_one({"id": 101})
        assert product["precio"] == 1399.99
        assert product["stock"] == 45
        
        # Actualizar múltiples documentos
        result = products_collection.update_many(
            {"categoria": "accesorios"},
            {"$set": {"descuento": 0.1}}
        )
        assert result.matched_count == 2
        assert result.modified_count == 2
        
        # Verificar las actualizaciones
        products = list(products_collection.find({"categoria": "accesorios"}))
        for product in products:
            assert "descuento" in product
            assert product["descuento"] == 0.1
        
        logger.info("Ejecutadas varias operaciones UPDATE exitosamente")
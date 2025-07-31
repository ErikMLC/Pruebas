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

@pytest.mark.order(5)
class TestDeleteParser:
    """Pruebas para el parser DELETE."""
    
    def test_delete_parser_unit(self):
        """Prueba unitaria de CRUDParser para DELETE."""
        parser = CRUDParser()
        
        # Probar DELETE simple
        sql = "DELETE FROM usuarios WHERE id = 1"
        result = parser.parse_delete(sql)
        
        assert result["operation"] == "DELETE"
        assert result["table"] == "usuarios"
        assert result["condition"]["id"] == 1
        
        # Probar DELETE sin WHERE
        sql = "DELETE FROM productos"
        result = parser.parse_delete(sql)
        
        assert result["operation"] == "DELETE"
        assert result["table"] == "productos"
        assert result["condition"] == {}
    
    def test_delete_to_mongodb_translation(self):
        """Prueba la traducción de DELETE a MongoDB."""
        sql = "DELETE FROM usuarios WHERE id = 1"
        
        # Parsear la consulta
        parser = SQLParser(sql)
        
        # Traducir a MongoDB
        translator = SQLToMongoDBTranslator(parser)
        result = translator.translate()
        
        assert result["operation"] == "delete"
        assert result["collection"] == "usuarios"
        assert result["query"] == {"id": 1}
        
        # DELETE sin WHERE
        sql = "DELETE FROM productos"
        parser = SQLParser(sql)
        translator = SQLToMongoDBTranslator(parser)
        result = translator.translate()
        
        assert result["operation"] == "delete"
        assert result["collection"] == "productos"
        assert result["query"] == {}
    
    def test_actual_delete_execution(self, users_collection, products_collection):
        """Prueba la ejecución real de DELETE en MongoDB."""
        # Eliminar un usuario
        initial_count = users_collection.count_documents({})
        
        result = users_collection.delete_one({"id": 4})
        assert result.deleted_count == 1
        
        # Verificar que se haya eliminado
        new_count = users_collection.count_documents({})
        assert new_count == initial_count - 1
        assert users_collection.find_one({"id": 4}) is None
        
        # Eliminar múltiples productos
        initial_count = products_collection.count_documents({})
        
        result = products_collection.delete_many({"categoria": "accesorios"})
        assert result.deleted_count == 2
        
        # Verificar que se hayan eliminado
        new_count = products_collection.count_documents({})
        assert new_count == initial_count - 2
        assert products_collection.count_documents({"categoria": "accesorios"}) == 0
        
        logger.info("Ejecutadas varias operaciones DELETE exitosamente")
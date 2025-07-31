import pytest
import os
import time
from pymongo import MongoClient
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def mongo_client():
    """Proporciona un cliente MongoDB para todas las pruebas."""
    mongo_uri = os.environ.get('TEST_MONGO_URI', 'mongodb://localhost:27017/')
    client = MongoClient(mongo_uri)
    
    try:
        # Verificar conexión
        client.admin.command('ping')
        logger.info(f"Conexión exitosa a MongoDB: {mongo_uri}")
        yield client
    finally:
        client.close()
        logger.info("Conexión a MongoDB cerrada")

@pytest.fixture(scope="session")
def test_db(mongo_client):
    """Proporciona una base de datos de prueba."""
    # Crear una base de datos única para esta sesión de pruebas
    db_name = f"test_sql_translator_{int(time.time())}"
    db = mongo_client[db_name]
    logger.info(f"Base de datos de prueba creada: {db_name}")
    
    yield db
    
    # Limpiar al finalizar
    mongo_client.drop_database(db_name)
    logger.info(f"Base de datos de prueba eliminada: {db_name}")

@pytest.fixture(scope="session")
def users_collection(test_db):
    """Proporciona una colección de usuarios para pruebas."""
    collection = test_db["usuarios"]
    yield collection

@pytest.fixture(scope="session")
def products_collection(test_db):
    """Proporciona una colección de productos para pruebas."""
    collection = test_db["productos"]
    yield collection
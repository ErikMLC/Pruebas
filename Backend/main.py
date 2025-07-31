from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os
import logging

# Importar módulos de la aplicación existentes
from app.parser.sql_parser import SQLParser
from app.translator.sql_to_mongodb import SQLToMongoDBTranslator
from app.connector import MongoDBConnector
from app.mongo_shell import MongoShellQueryGenerator
from app.utils import setup_logging, format_error_response

# Importar módulos de autenticación nuevos
from app.models.user import UserModel
from app.auth.routes import create_auth_blueprint
from app.admin.routes import create_admin_blueprint
from app.auth.middleware import auth_required, permission_required, get_current_user_claims

import traceback

# Cargar variables de entorno
load_dotenv()

# Configurar logging
setup_logging(log_level=logging.INFO, log_file='app.log')
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__)
CORS(app, 
     origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "Accept"],
     supports_credentials=True)

# Configuración JWT
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # Los tokens durarán según lo configurado en las rutas
jwt = JWTManager(app)

# Configuración de MongoDB desde variables de entorno o valores por defecto
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
AUTH_DB_NAME = os.environ.get('AUTH_DB_NAME', 'sql_middleware_auth')
DEFAULT_DB = None  # No seleccionar base de datos por defecto

# Inicializar conexiones
try:
    # Conector para queries SQL (tu código existente)
    mongo_connector = MongoDBConnector.get_instance(MONGO_URI)
    logger.info(f"Conector MongoDB inicializado correctamente. URI: {MONGO_URI}")
    
    # Conexión separada para autenticación (nuevo)
    auth_client = mongo_connector.client
    auth_db = auth_client[AUTH_DB_NAME]
    user_model = UserModel(auth_db)
    
    # Crear usuario admin por defecto si no existe (nuevo)
    user_model.create_admin_user()
    
    logger.info(f"Sistema de autenticación inicializado en DB: {AUTH_DB_NAME}")
    
except Exception as e:
    logger.error(f"Error al inicializar el sistema: {e}")
    logger.error(traceback.format_exc())

# Registrar blueprints de autenticación (nuevo)
app.register_blueprint(create_auth_blueprint(user_model), url_prefix='/api/auth')
app.register_blueprint(create_admin_blueprint(user_model))

# Manejadores de errores JWT (nuevo)
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "El token ha expirado"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"error": "Token inválido"}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({"error": "Token de autorización requerido"}), 401

# Endpoints existentes con autenticación añadida

@app.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificar el estado de la aplicación.
    """
    return jsonify({
        "status": "ok",
        "version": "2.0.0",
        "services": {
            "mongodb": mongo_connector.is_connected(),
            "auth": True
        }
    })

@app.route('/databases', methods=['GET'])
@auth_required  # Nuevo: requiere autenticación
def get_databases():
    """
    Endpoint para obtener las bases de datos disponibles.
    """
    try:
        databases = mongo_connector.get_available_databases()
        logger.info(f"Obtenidas {len(databases)} bases de datos")
        return jsonify({"databases": databases})
    except Exception as e:
        logger.error(f"Error al obtener bases de datos: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/database/<database_name>/collections', methods=['GET'])
@auth_required  # Nuevo: requiere autenticación
def get_collections(database_name):
    """
    Endpoint para obtener las colecciones de una base de datos.
    """
    try:
        collections = mongo_connector.get_collections(database_name)
        logger.info(f"Obtenidas {len(collections)} colecciones de la base de datos {database_name}")
        return jsonify({"collections": collections})
    except Exception as e:
        logger.error(f"Error al obtener colecciones: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/connect', methods=['POST'])
@auth_required  # Nuevo: requiere autenticación
def connect_database():
    """
    Endpoint para conectarse a una base de datos específica.
    """
    try:
        data = request.get_json()
        if not data or 'database' not in data:
            return jsonify({"error": "Se requiere el nombre de la base de datos"}), 400
        
        database_name = data['database']
        collections = mongo_connector.set_database(database_name)
        
        logger.info(f"Conexión establecida con la base de datos {database_name}")
        return jsonify({
            "message": f"Conectado a la base de datos {database_name}",
            "collections": collections
        })
    except Exception as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/translate', methods=['POST'])
@auth_required  # Nuevo: requiere autenticación
def translate_sql_to_mongodb():
    """
    Endpoint para traducir y ejecutar consultas SQL en MongoDB.
    Requiere autenticación y permisos específicos según el tipo de operación.
    """
    try:
        # Obtener la consulta SQL del JSON recibido
        data = request.get_json()
        
        # Verificar si se proporciona una base de datos específica para esta consulta
        if 'database' in data:
            database_name = data['database']
            mongo_connector.set_database(database_name)
            logger.info(f"Base de datos seleccionada para esta consulta: {database_name}")
        else:
            # Verificar si hay una base de datos seleccionada
            if not mongo_connector.is_database_selected():
                return jsonify({"error": "No hay una base de datos seleccionada. Proporcione una base de datos en la solicitud o use el endpoint /connect primero"}), 400
        
        if not data or 'query' not in data:
            logger.error("Error: No se proporcionó la consulta SQL en el JSON")
            return jsonify({"error": "Se requiere una consulta SQL en el campo 'query'"}), 400
        
        sql_query = data['query']
        logger.info(f"Consulta SQL recibida: {sql_query}")
        
        # Parsear la consulta SQL para determinar el tipo (tu código existente)
        parser = SQLParser(sql_query)
        query_type = parser.get_query_type()
        
        # Nuevo: Verificar permisos según el tipo de consulta
        permission_map = {
            "SELECT": "select",
            "INSERT": "insert", 
            "UPDATE": "update",
            "DELETE": "delete",
            "CREATE": "create_table",
            "DROP": "drop_table"
        }
        
        required_permission = permission_map.get(query_type)
        if not required_permission:
            return jsonify({"error": f"Tipo de consulta no soportado: {query_type}"}), 400
        
        # Nuevo: Verificar si el usuario tiene el permiso necesario
        claims = get_current_user_claims()
        user_permissions = claims.get("permissions", {})
        
        if not user_permissions.get(required_permission, False):
            return jsonify({
                "error": f"No tienes permisos para realizar operaciones de tipo {query_type}"
            }), 403
        
        # Tu código existente continúa igual...
        # Obtener el nombre de la tabla/colección
        collection_name = parser.get_table_name()
        logger.info(f"Nombre de colección detectado: {collection_name}")
        
        if not collection_name:
            logger.error("Error: No se pudo determinar el nombre de la colección")
            return jsonify({"error": "No se pudo determinar el nombre de la colección"}), 400
        
        # Traducir la consulta a formato MongoDB
        translator = SQLToMongoDBTranslator(parser)
        mongo_query = translator.translate()
        logger.info(f"Consulta MongoDB generada: {mongo_query}")
        
        # Ejecutar la consulta en MongoDB
        result = mongo_connector.execute_query(collection_name, mongo_query)
        logger.info(f"Consulta ejecutada. Resultados: {len(result) if isinstance(result, list) else 1} documentos")
        
        return jsonify(result)
    except ValueError as e:
        logger.error(f"Error de valor: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/generate-shell-query', methods=['POST'])
@auth_required  # Nuevo: requiere autenticación
def generate_shell_query():
    """
    Endpoint para generar una consulta ejecutable para la shell de MongoDB.
    """
    try:
        # Obtener la consulta SQL del JSON recibido
        data = request.get_json()
        
        if not data or 'query' not in data:
            logger.error("Error: No se proporcionó la consulta SQL en el JSON")
            return jsonify({"error": "Se requiere una consulta SQL en el campo 'query'"}), 400
        
        # Verificar si se proporciona una base de datos específica para esta consulta
        if 'database' in data:
            database_name = data['database']
            mongo_connector.set_database(database_name)
            logger.info(f"Base de datos seleccionada para esta consulta: {database_name}")
        else:
            # Verificar si hay una base de datos seleccionada
            if not mongo_connector.is_database_selected():
                return jsonify({"error": "No hay una base de datos seleccionada. Proporcione una base de datos en la solicitud o use el endpoint /connect primero"}), 400
        
        sql_query = data['query']
        logger.info(f"Consulta SQL recibida para generar query shell: {sql_query}")
        
        # Nuevo: Verificar permisos igual que en translate
        parser = SQLParser(sql_query)
        query_type = parser.get_query_type()
        
        permission_map = {
            "SELECT": "select",
            "INSERT": "insert", 
            "UPDATE": "update",
            "DELETE": "delete",
            "CREATE": "create_table",
            "DROP": "drop_table"
        }
        
        required_permission = permission_map.get(query_type)
        if not required_permission:
            return jsonify({"error": f"Tipo de consulta no soportado: {query_type}"}), 400
        
        claims = get_current_user_claims()
        user_permissions = claims.get("permissions", {})
        
        if not user_permissions.get(required_permission, False):
            return jsonify({
                "error": f"No tienes permisos para realizar operaciones de tipo {query_type}"
            }), 403
        
        # Tu código existente continúa igual...
        # Obtener el nombre de la tabla/colección
        collection_name = parser.get_table_name()
        logger.info(f"Nombre de colección detectado: {collection_name}")
        
        if not collection_name:
            logger.error("Error: No se pudo determinar el nombre de la colección")
            return jsonify({"error": "No se pudo determinar el nombre de la colección"}), 400
        
        # Traducir la consulta a formato MongoDB
        translator = SQLToMongoDBTranslator(parser)
        mongo_query = translator.translate()
        logger.info(f"Consulta MongoDB generada: {mongo_query}")
        
        # Generar la consulta para la shell de MongoDB
        shell_query = MongoShellQueryGenerator.generate_shell_query(collection_name, mongo_query)
        logger.info(f"Consulta para la shell de MongoDB generada")
        
        return jsonify({
            "shell_query": shell_query,
            "mongo_query": mongo_query
        })
    except ValueError as e:
        logger.error(f"Error de valor: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/test-connection', methods=['GET'])
@auth_required  # Nuevo: requiere autenticación
def test_connection():
    """
    Endpoint para probar la conexión a MongoDB.
    """
    try:
        status = mongo_connector.is_connected()
        databases = mongo_connector.get_available_databases()
        return jsonify({
            "connected": status,
            "databases": databases,
            "current_database": mongo_connector.get_current_database()
        })
    except Exception as e:
        logger.error(f"Error al probar conexión: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/supported-sql', methods=['GET'])
@auth_required  # Nuevo: requiere autenticación
def get_supported_sql():
    """
    Endpoint para obtener información sobre las características SQL soportadas.
    """
    return jsonify({
        "supported_operations": [
            "SELECT", "INSERT", "UPDATE", "DELETE"
        ],
        "supported_clauses": [
            "WHERE", "ORDER BY", "LIMIT"
        ],
        "supported_operators": [
            "=", "!=", "<>", ">", "<", ">=", "<=", "LIKE", "IN", "NOT IN", "BETWEEN", "IS NULL", "IS NOT NULL"
        ]
    })

if __name__ == "__main__":
    # Obtener puerto de variable de entorno o usar 5000 por defecto
    port = int(os.environ.get('PORT', 5000))
    # Obtener modo de depuración de variable de entorno o usar False por defecto
    debug = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')
    
    logger.info(f"Iniciando servidor en puerto {port} (Debug: {debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
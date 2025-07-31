import re
import logging

# Configurar logging
logger = logging.getLogger(__name__)

def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Configura el sistema de logging para la aplicación.
    
    Args:
        log_level (int): Nivel de logging (default: INFO)
        log_file (str, optional): Ruta al archivo de log
    """
    # Configurar formato de log
    log_format = '%(asctime)s [%(levelname)s] - %(name)s - %(message)s'
    
    # Crear manejadores
    handlers = [logging.StreamHandler()]
    
    # Añadir manejador de archivo si se proporcionó
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    # Aplicar configuración
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )
    
    logger.info(f"Logging configurado con nivel {logging.getLevelName(log_level)}")
    if log_file:
        logger.info(f"Logs se escribirán en {log_file}")

def is_valid_mongo_db_name(name):
    """
    Verifica si un nombre de base de datos es válido para MongoDB.
    
    Args:
        name (str): Nombre a verificar
        
    Returns:
        bool: True si es válido, False en caso contrario
    """
    if not name or not isinstance(name, str):
        return False
        
    # MongoDB tiene restricciones en los nombres de bases de datos
    # No pueden contener espacios, /, \, ., ", $, caracteres nulos, etc.
    invalid_chars = [' ', '/', '\\', '.', '"', '$', '\0']
    return not any(char in name for char in invalid_chars)

def is_valid_collection_name(name):
    """
    Verifica si un nombre de colección es válido para MongoDB.
    
    Args:
        name (str): Nombre a verificar
        
    Returns:
        bool: True si es válido, False en caso contrario
    """
    if not name or not isinstance(name, str):
        return False
        
    # Verificar restricciones específicas de MongoDB
    # Las colecciones no pueden empezar por 'system.'
    if name.startswith('system.'):
        return False
        
    # No debe contener caracteres nulos
    if '\0' in name:
        return False
        
    return True

def sanitize_field_name(field_name):
    """
    Sanitiza el nombre de un campo para MongoDB.
    
    Args:
        field_name (str): Nombre del campo a sanitizar
        
    Returns:
        str: Nombre sanitizado
    """
    if not field_name:
        return field_name
        
    # Eliminar caracteres no válidos o reemplazarlos
    # MongoDB no permite que los nombres de campo contengan puntos
    sanitized = field_name.replace('.', '_')
    
    # Eliminar caracteres $ al inicio (MongoDB no los permite)
    if sanitized.startswith('$'):
        sanitized = '_' + sanitized[1:]
    
    return sanitized

def format_error_response(error_message, status_code=400):
    """
    Formatea un mensaje de error para respuestas API.
    
    Args:
        error_message (str): Mensaje de error
        status_code (int): Código de estado HTTP
        
    Returns:
        tuple: (dict con error, código de estado)
    """
    return {
        "error": error_message,
        "status": "error"
    }, status_code

def parse_connection_string(connection_string):
    """
    Parsea una cadena de conexión MongoDB y extrae sus componentes.
    
    Args:
        connection_string (str): Cadena de conexión
        
    Returns:
        dict: Componentes de la conexión (host, puerto, usuario, etc.)
    """
    try:
        # Formato: mongodb://[username:password@]host1[:port1][,host2[:port2],...]/[database]
        result = {}
        
        # Extraer protocolo
        protocol_pattern = r'^(mongodb(?:\+srv)?):\/\/'
        protocol_match = re.search(protocol_pattern, connection_string)
        if protocol_match:
            result['protocol'] = protocol_match.group(1)
            remainder = connection_string[protocol_match.end():]
        else:
            result['protocol'] = 'mongodb'
            remainder = connection_string
        
        # Extraer credenciales si existen
        auth_pattern = r'^([^:@]+)(?::([^@]+))?@'
        auth_match = re.search(auth_pattern, remainder)
        if auth_match:
            result['username'] = auth_match.group(1)
            result['password'] = auth_match.group(2) if auth_match.group(2) else None
            remainder = remainder[auth_match.end():]
        
        # Extraer hosts
        hosts_pattern = r'^([^\/]+)'
        hosts_match = re.search(hosts_pattern, remainder)
        if hosts_match:
            hosts_str = hosts_match.group(1)
            result['hosts'] = []
            
            for host_part in hosts_str.split(','):
                host_info = {}
                if ':' in host_part:
                    host, port = host_part.split(':', 1)
                    host_info['host'] = host
                    host_info['port'] = int(port)
                else:
                    host_info['host'] = host_part
                    host_info['port'] = 27017  # Puerto por defecto
                
                result['hosts'].append(host_info)
            
            remainder = remainder[hosts_match.end():]
        
        # Extraer base de datos si existe
        if remainder and remainder.startswith('/'):
            db_pattern = r'^\/([^?]+)'
            db_match = re.search(db_pattern, remainder[1:])
            if db_match:
                result['database'] = db_match.group(1)
        
        return result
    except Exception as e:
        logger.error(f"Error al parsear cadena de conexión: {e}")
        return None

def deep_compare_objects(obj1, obj2):
    """
    Compara profundamente dos objetos para detectar diferencias.
    Útil para comparar resultados de consultas.
    
    Args:
        obj1: Primer objeto
        obj2: Segundo objeto
        
    Returns:
        bool: True si son iguales, False en caso contrario
    """
    # Si son tipos diferentes, no son iguales
    if type(obj1) != type(obj2):
        return False
    
    # Si son primitivos, comparación directa
    if not isinstance(obj1, (dict, list)):
        return obj1 == obj2
    
    # Para diccionarios
    if isinstance(obj1, dict):
        if set(obj1.keys()) != set(obj2.keys()):
            return False
        
        for key in obj1:
            if not deep_compare_objects(obj1[key], obj2[key]):
                return False
        
        return True
    
    # Para listas
    if isinstance(obj1, list):
        if len(obj1) != len(obj2):
            return False
        
        # Si el orden es importante (como en MongoDB)
        for i in range(len(obj1)):
            if not deep_compare_objects(obj1[i], obj2[i]):
                return False
        
        return True
    
    # No debería llegar aquí
    return False
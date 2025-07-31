from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
import logging

logger = logging.getLogger(__name__)

def auth_required(f):
    """
    Decorador que requiere autenticación con JWT.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error de autenticación: {e}")
            return jsonify({"error": "Token de acceso requerido o inválido"}), 401
    return decorated_function

def admin_required(f):
    """
    Decorador que requiere permisos de administrador.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") != "admin":
                return jsonify({"error": "Permisos de administrador requeridos"}), 403
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error de autorización: {e}")
            return jsonify({"error": "Token de acceso requerido o inválido"}), 401
    return decorated_function

def permission_required(permission):
    """
    Decorador que requiere un permiso específico.
    
    Args:
        permission (str): Nombre del permiso requerido
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                user_permissions = claims.get("permissions", {})
                
                if not user_permissions.get(permission, False):
                    return jsonify({
                        "error": f"No tienes permisos para realizar esta operación: {permission}"
                    }), 403
                
                return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error de autorización: {e}")
                return jsonify({"error": "Token de acceso requerido o inválido"}), 401
        return decorated_function
    return decorator

def get_current_user():
    """
    Obtiene el ID del usuario actual desde el JWT.
    
    Returns:
        str: ID del usuario actual
    """
    try:
        verify_jwt_in_request()
        return get_jwt_identity()
    except:
        return None

def get_current_user_claims():
    """
    Obtiene los claims del usuario actual desde el JWT.
    
    Returns:
        dict: Claims del usuario actual
    """
    try:
        verify_jwt_in_request()
        return get_jwt()
    except:
        return None
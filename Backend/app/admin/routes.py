from flask import Blueprint, request, jsonify
from app.auth.middleware import admin_required, auth_required, get_current_user
import logging

# Configurar logging
logger = logging.getLogger(__name__)

def create_admin_blueprint(user_model):
    """
    Crea y configura el blueprint de administración.
    
    Args:
        user_model: Instancia del modelo de usuario
    """
    admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
    
    @admin_bp.route('/users', methods=['GET'])
    @admin_required
    def get_all_users():
        """
        Endpoint para obtener todos los usuarios (solo admin).
        """
        try:
            users = user_model.get_all_users()
            return jsonify({"users": users}), 200
            
        except Exception as e:
            logger.error(f"Error al obtener usuarios: {e}")
            return jsonify({"error": "Error interno del servidor"}), 500
    
    @admin_bp.route('/users/<user_id>/permissions', methods=['PUT'])
    @admin_required
    def update_user_permissions(user_id):
        """
        Endpoint para actualizar permisos de un usuario.
        """
        try:
            data = request.get_json()
            
            if not data or 'permissions' not in data:
                return jsonify({"error": "Se requieren los permisos a actualizar"}), 400
            
            # Validar estructura de permisos
            valid_permissions = {
                'select', 'insert', 'update', 'delete', 
                'create_table', 'drop_table', 'manage_users'
            }
            
            permissions = data['permissions']
            if not isinstance(permissions, dict):
                return jsonify({"error": "Los permisos deben ser un objeto"}), 400
            
            # Validar que solo se incluyan permisos válidos
            for perm in permissions:
                if perm not in valid_permissions:
                    return jsonify({"error": f"Permiso inválido: {perm}"}), 400
                if not isinstance(permissions[perm], bool):
                    return jsonify({"error": f"El valor del permiso {perm} debe ser booleano"}), 400
            
            # Actualizar permisos
            success = user_model.update_user_permissions(user_id, permissions)
            
            if success:
                logger.info(f"Permisos actualizados para usuario {user_id}")
                return jsonify({"message": "Permisos actualizados correctamente"}), 200
            else:
                return jsonify({"error": "No se pudieron actualizar los permisos"}), 400
            
        except Exception as e:
            logger.error(f"Error al actualizar permisos: {e}")
            return jsonify({"error": "Error interno del servidor"}), 500
    
    @admin_bp.route('/users/<user_id>/status', methods=['PUT'])
    @admin_required
    def update_user_status(user_id):
        """
        Endpoint para activar/desactivar un usuario.
        """
        try:
            data = request.get_json()
            
            if not data or 'is_active' not in data:
                return jsonify({"error": "Se requiere el estado is_active"}), 400
            
            is_active = data['is_active']
            if not isinstance(is_active, bool):
                return jsonify({"error": "El campo is_active debe ser booleano"}), 400
            
            # No permitir que un admin se desactive a sí mismo
            current_user_id = get_current_user()
            if current_user_id == user_id and not is_active:
                return jsonify({"error": "No puedes desactivarte a ti mismo"}), 400
            
            # Actualizar estado
            success = user_model.update_user_status(user_id, is_active)
            
            if success:
                status_text = "activado" if is_active else "desactivado"
                logger.info(f"Usuario {user_id} {status_text}")
                return jsonify({"message": f"Usuario {status_text} correctamente"}), 200
            else:
                return jsonify({"error": "No se pudo actualizar el estado del usuario"}), 400
            
        except Exception as e:
            logger.error(f"Error al actualizar estado del usuario: {e}")
            return jsonify({"error": "Error interno del servidor"}), 500
    
    @admin_bp.route('/users/<user_id>', methods=['GET'])
    @admin_required
    def get_user_details(user_id):
        """
        Endpoint para obtener detalles de un usuario específico.
        """
        try:
            user = user_model.get_user_by_id(user_id)
            
            if not user:
                return jsonify({"error": "Usuario no encontrado"}), 404
            
            return jsonify({"user": user}), 200
            
        except Exception as e:
            logger.error(f"Error al obtener detalles del usuario: {e}")
            return jsonify({"error": "Error interno del servidor"}), 500
    
    @admin_bp.route('/permissions/available', methods=['GET'])
    @admin_required
    def get_available_permissions():
        """
        Endpoint para obtener la lista de permisos disponibles.
        """
        try:
            permissions = {
                "select": {
                    "name": "Consultar (SELECT)",
                    "description": "Permite realizar consultas SELECT"
                },
                "insert": {
                    "name": "Insertar (INSERT)",
                    "description": "Permite insertar nuevos registros"
                },
                "update": {
                    "name": "Actualizar (UPDATE)",
                    "description": "Permite actualizar registros existentes"
                },
                "delete": {
                    "name": "Eliminar (DELETE)",
                    "description": "Permite eliminar registros"
                },
                "create_table": {
                    "name": "Crear Tabla",
                    "description": "Permite crear nuevas tablas/colecciones"
                },
                "drop_table": {
                    "name": "Eliminar Tabla",
                    "description": "Permite eliminar tablas/colecciones"
                },
                "manage_users": {
                    "name": "Gestionar Usuarios",
                    "description": "Permite gestionar otros usuarios (solo admin)"
                }
            }
            
            return jsonify({"permissions": permissions}), 200
            
        except Exception as e:
            logger.error(f"Error al obtener permisos disponibles: {e}")
            return jsonify({"error": "Error interno del servidor"}), 500
    
    @admin_bp.route('/stats', methods=['GET'])
    @admin_required
    def get_admin_stats():
        """
        Endpoint para obtener estadísticas del sistema.
        """
        try:
            users = user_model.get_all_users()
            
            stats = {
                "total_users": len(users),
                "active_users": len([u for u in users if u.get('is_active', True)]),
                "admin_users": len([u for u in users if u.get('role') == 'admin']),
                "regular_users": len([u for u in users if u.get('role') == 'user'])
            }
            
            return jsonify({"stats": stats}), 200
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return jsonify({"error": "Error interno del servidor"}), 500
    
    return admin_bp
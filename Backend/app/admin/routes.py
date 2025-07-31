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
    # ✅ CORREGIDO: Cambiar prefijo para que coincida con frontend
    admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
    
    # ✅ NUEVA RUTA: Verificar si el usuario es admin
    @admin_bp.route('/verify', methods=['GET'])
    @auth_required
    def verify_admin():
        """
        Endpoint para verificar si el usuario actual es administrador.
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return jsonify({"error": "Usuario no encontrado"}), 404
            
            # Obtener datos completos del usuario
            user_data = user_model.get_user_by_id(current_user)
            
            if not user_data:
                return jsonify({"error": "Datos de usuario no encontrados"}), 404
            
            is_admin = user_data.get('role') == 'admin'
            
            logger.info(f"Verificación admin para usuario {current_user}: {is_admin}")
            
            return jsonify({
                "is_admin": is_admin,
                "user_id": current_user,
                "role": user_data.get('role', 'user'),
                "username": user_data.get('username', ''),
                "permissions": user_data.get('permissions', {})
            }), 200
            
        except Exception as e:
            logger.error(f"Error al verificar admin: {e}")
            return jsonify({"error": "Error interno del servidor"}), 500
    
    @admin_bp.route('/users', methods=['GET'])
    @admin_required
    def get_all_users():
        """
        Endpoint para obtener todos los usuarios (solo admin).
        """
        try:
            users = user_model.get_all_users()
            
            # ✅ MEJORADO: Asegurar que todos los usuarios tengan permisos
            processed_users = []
            for user in users:
                # Asegurar que permissions existe
                if 'permissions' not in user or not user['permissions']:
                    user['permissions'] = {
                        'select': False,
                        'insert': False,
                        'update': False,
                        'delete': False,
                        'create_table': False,
                        'drop_table': False
                    }
                
                # Asegurar que is_active existe
                if 'is_active' not in user:
                    user['is_active'] = True
                
                processed_users.append(user)
            
            logger.info(f"Enviando {len(processed_users)} usuarios al frontend")
            return jsonify({"users": processed_users}), 200
            
        except Exception as e:
            logger.error(f"Error al obtener usuarios: {e}")
            return jsonify({"error": "Error interno del servidor"}), 500
    
    # ✅ CORREGIDO: Cambiar PUT por PATCH y lógica para un solo permiso
    @admin_bp.route('/users/<user_id>/permissions', methods=['PATCH'])
    @admin_required
    def update_user_permissions(user_id):
        """
        Endpoint para actualizar UN permiso específico de un usuario.
        Frontend envía: {"permission": "select", "granted": true}
        """
        try:
            data = request.get_json()
            
            # ✅ CORREGIDO: Validar datos que envía el frontend
            if not data or 'permission' not in data or 'granted' not in data:
                return jsonify({"error": "Se requiere 'permission' y 'granted'"}), 400
            
            permission = data['permission']
            granted = bool(data['granted'])
            
            # Validar que el permiso es válido
            valid_permissions = {
                'select', 'insert', 'update', 'delete', 
                'create_table', 'drop_table'
            }
            
            if permission not in valid_permissions:
                return jsonify({"error": f"Permiso inválido: {permission}"}), 400
            
            # Verificar que el usuario existe
            target_user = user_model.get_user_by_id(user_id)
            if not target_user:
                return jsonify({"error": "Usuario no encontrado"}), 404
            
            # No permitir modificar permisos de otros admins
            current_user_id = get_current_user()
            if target_user.get('role') == 'admin' and target_user.get('_id') != current_user_id:
                return jsonify({"error": "No se pueden modificar permisos de otros administradores"}), 403
            
            # ✅ CORREGIDO: Actualizar solo el permiso específico
            # Obtener permisos actuales del usuario
            current_permissions = target_user.get('permissions', {})
            
            # Actualizar solo el permiso que cambió
            current_permissions[permission] = granted
            
            # Guardar los permisos actualizados
            success = user_model.update_user_permissions(user_id, current_permissions)
            
            if success:
                action = "otorgado" if granted else "revocado"
                logger.info(f"Permiso {permission} {action} para usuario {user_id}")
                return jsonify({
                    "message": f"Permiso {permission} {action} correctamente",
                    "user_id": user_id,
                    "permission": permission,
                    "granted": granted
                }), 200
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
            
            # ✅ MEJORADO: Asegurar permisos por defecto
            if 'permissions' not in user or not user['permissions']:
                user['permissions'] = {
                    'select': False,
                    'insert': False,
                    'update': False,
                    'delete': False,
                    'create_table': False,
                    'drop_table': False
                }
            
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
                }
            }
            
            return jsonify({"permissions": permissions}), 200
            
        except Exception as e:
            logger.error(f"Error al obtener permisos disponibles: {e}")
            return jsonify({"error": "Error interno del servidor"}), 500


    @admin_bp.route('/users/<user_id>', methods=['DELETE'])
    @admin_required
    def delete_user(user_id):
        """
        Endpoint para eliminar un usuario permanentemente.
        """
        try:
            current_user_id = get_current_user()
            
            # Verificar que el usuario objetivo existe
            target_user = user_model.get_user_by_id(user_id)
            if not target_user:
                return jsonify({"error": "Usuario no encontrado"}), 404
            
            # No permitir eliminar a sí mismo
            if str(target_user.get('_id')) == current_user_id:
                return jsonify({"error": "No puedes eliminarte a ti mismo"}), 400
            
            # No permitir eliminar otros admins
            if target_user.get('role') == 'admin':
                return jsonify({"error": "No se pueden eliminar administradores"}), 403
            
            # Eliminar usuario
            success = user_model.delete_user(user_id)
            
            if success:
                logger.info(f"Usuario {user_id} eliminado por admin {current_user_id}")
                return jsonify({
                    "message": "Usuario eliminado exitosamente",
                    "deleted_user_id": user_id
                }), 200
            else:
                return jsonify({"error": "No se pudo eliminar el usuario"}), 500
            
        except Exception as e:
            logger.error(f"Error eliminando usuario: {e}")
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
            
            logger.info(f"Estadísticas enviadas: {stats}")
            return jsonify({"stats": stats}), 200
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return jsonify({"error": "Error interno del servidor"}), 500
    

    return admin_bp
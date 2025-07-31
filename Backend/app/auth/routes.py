from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from datetime import timedelta
from app.models.reset import PasswordReset
from app.services.email_service import EmailService

import logging

# Configurar logging
logger = logging.getLogger(__name__)

def create_auth_blueprint(user_model):
    """
    Crea y configura el blueprint de autenticación.
    
    Args:
        user_model: Instancia del modelo de usuario
    """
    auth_bp = Blueprint('auth', __name__)
    
    @auth_bp.route('/register', methods=['POST'])
    def register():
        """
        Endpoint para registrar un nuevo usuario.
        """
        try:
            data = request.get_json()
            
            # Validar datos requeridos
            required_fields = ['username', 'email', 'password']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({"error": f"El campo {field} es requerido"}), 400
            
            # Validar longitud de contraseña
            if len(data['password']) < 6:
                return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400
            
            # Crear usuario (por defecto como 'user')
            result = user_model.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                role='user'
            )
            
            if 'error' in result:
                return jsonify(result), 400
            
            logger.info(f"Usuario registrado: {data['username']}")
            return jsonify({
                "message": "Usuario registrado exitosamente",
                "user": result
            }), 201
            
        except Exception as e:
            logger.error(f"Error en registro: {e}")
            return jsonify({"error": "Error interno del servidor"}), 500
    

    @auth_bp.route('/login', methods=['POST'])
    def login():
        """
        Endpoint para iniciar sesión con email o username.
        """
        try:
            data = request.get_json()
            
            # Validar datos requeridos - CAMBIADO: aceptar tanto username como email
            username_or_email = data.get('username') or data.get('email')
            password = data.get('password')
            
            if not username_or_email or not password:
                return jsonify({"error": "Usuario/Email y contraseña son requeridos"}), 400
            
            # Autenticar usuario - MODIFICADO: buscar por email o username
            user = user_model.authenticate_user(username_or_email, password)
            
            if not user:
                return jsonify({"error": "Credenciales inválidas"}), 401
            
            # Crear tokens JWT
            additional_claims = {
                "role": user["role"],
                "permissions": user["permissions"]
            }
            
            access_token = create_access_token(
                identity=user["_id"],
                additional_claims=additional_claims,
                expires_delta=timedelta(hours=24)
            )
            
            refresh_token = create_refresh_token(
                identity=user["_id"],
                expires_delta=timedelta(days=30)
            )
            
            logger.info(f"Usuario autenticado: {user['username']}")
            return jsonify({
                "message": "Inicio de sesión exitoso",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user["_id"],
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"],
                    "permissions": user["permissions"]
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Error en login: {e}")
            return jsonify({"error": "Error interno del servidor"}), 500

    
    @auth_bp.route('/refresh', methods=['POST'])
    @jwt_required(refresh=True)
    def refresh():
        """
        Endpoint para renovar token de acceso.
        """
        try:
            user_id = get_jwt_identity()
            user = user_model.get_user_by_id(user_id)
            
            if not user:
                return jsonify({"error": "Usuario no encontrado"}), 404
            
            # Crear nuevo token de acceso
            additional_claims = {
                "role": user["role"],
                "permissions": user["permissions"]
            }
            
            new_token = create_access_token(
                identity=user_id,
                additional_claims=additional_claims,
                expires_delta=timedelta(hours=24)
            )
            
            return jsonify({"access_token": new_token}), 200
            
        except Exception as e:
            logger.error(f"Error en refresh: {e}")
            return jsonify({"error": "Error interno del servidor"}), 500
    
    @auth_bp.route('/profile', methods=['GET'])
    @jwt_required()
    def get_profile():
        """
        Endpoint para obtener el perfil del usuario actual.
        """
        try:
            user_id = get_jwt_identity()
            user = user_model.get_user_by_id(user_id)
            
            if not user:
                return jsonify({"error": "Usuario no encontrado"}), 404
            
            return jsonify({"user": user}), 200
            
        except Exception as e:
            logger.error(f"Error al obtener perfil: {e}")
            return jsonify({"error": "Error interno del servidor"}), 500
    
   
    @auth_bp.route('/forgot-password', methods=['POST'])
    def forgot_password():
        """
        Inicia proceso de recuperación de contraseña
        """
        try:
            data = request.get_json()
            email = data.get('email')
            
            if not email:
                return jsonify({
                    'success': False,
                    'message': 'Email es requerido'
                }), 400
            
            # Verificar si el usuario existe
            user = user_model.get_user_by_email(email)
            
            if not user:
                # Por seguridad, no revelar si el email existe
                return jsonify({
                    'success': True,
                    'message': 'Si el email existe, recibirás un código de verificación'
                }), 200
            
            # Crear código de reset
            reset_model = PasswordReset(user_model.db)
            code = reset_model.create_reset_request(email)
            
            if not code:
                return jsonify({
                    'success': False,
                    'message': 'Error generando código de verificación'
                }), 500
            
            # Enviar email (simulado por ahora)
            try:
                email_sent = EmailService.send_reset_code(
                    email, 
                    code, 
                    user.get('username')
                )
            except Exception as e:
                # Si falla el email, continuar pero loggearlo
                logger.warning(f"Error enviando email: {e}")
                email_sent = True  # Simular que se envió para no bloquear el flujo
            
            if not email_sent:
                return jsonify({
                    'success': False,
                    'message': 'Error enviando email'
                }), 500
            
            return jsonify({
                'success': True,
                'message': f'Código de verificación enviado. Código temporal: {code}',  # Solo para testing
                'temp_code': code  # Solo para testing - REMOVER en producción
            }), 200
            
        except Exception as e:
            logger.error(f"Error en forgot_password: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Error interno del servidor'
            }), 500


    @auth_bp.route('/verify-reset-code', methods=['POST'])
    def verify_reset_code():
        """
        Verifica el código de reset
        """
        try:
            data = request.get_json()
            email = data.get('email')
            code = data.get('code')
            
            if not email or not code:
                return jsonify({
                    'success': False,
                    'message': 'Email y código son requeridos'
                }), 400
            
            # Verificar código
            reset_model = PasswordReset(user_model.db)
            
            # Verificar intentos fallidos
            attempts = reset_model.get_attempts(email)
            if attempts >= 3:
                return jsonify({
                    'success': False,
                    'message': 'Demasiados intentos fallidos. Solicita un nuevo código'
                }), 429
            
            # Verificar código
            is_valid = reset_model.verify_code(email, code)
            
            if not is_valid:
                return jsonify({
                    'success': False,
                    'message': 'Código inválido o expirado'
                }), 400
            
            return jsonify({
                'success': True,
                'message': 'Código verificado correctamente'
            }), 200
            
        except Exception as e:
            logger.error(f"Error en verify_reset_code: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Error interno del servidor'
            }), 500

    @auth_bp.route('/reset-password', methods=['POST'])
    def reset_password():
        """
        Cambia la contraseña después de verificar código
        """
        try:
            data = request.get_json()
            email = data.get('email')
            new_password = data.get('new_password')
            
            if not email or not new_password:
                return jsonify({
                    'success': False,
                    'message': 'Email y nueva contraseña son requeridos'
                }), 400
            
            # Validar contraseña
            if len(new_password) < 6:
                return jsonify({
                    'success': False,
                    'message': 'La contraseña debe tener al menos 6 caracteres'
                }), 400
            
            # Actualizar contraseña
            success = user_model.update_password(email, new_password)
            
            if not success:
                return jsonify({
                    'success': False,
                    'message': 'Error actualizando contraseña'
                }), 500
            
            # Limpiar códigos de reset
            reset_model = PasswordReset(user_model.db)
            reset_model.collection.delete_many({"email": email})
            
            # Enviar notificación
            user = user_model.get_user_by_email(email)
            EmailService.send_password_changed_notification(
                email, 
                user.get('username')
            )
            
            return jsonify({
                'success': True,
                'message': 'Contraseña actualizada exitosamente'
            }), 200
            
        except Exception as e:
            logger.error(f"Error en reset_password: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Error interno del servidor'
            }), 500
    
    return auth_bp
"""
Servicio de envío de emails (versión simplificada para testing)
"""
import logging

logger = logging.getLogger(__name__)

class EmailService:
    
    @staticmethod
    def send_reset_code(email, code, user_name=None):
        """
        Envía código de reset por email (simulado para testing)
        """
        try:
            # ✅ VERSIÓN SIMULADA - En producción usar Flask-Mail o servicio real
            logger.info(f"[EMAIL SIMULADO] Enviando código {code} a {email}")
            
            # Simular email enviado
            email_content = f"""
Para: {email}
Asunto: Código de recuperación - SQL Translator

Hola {user_name or 'Usuario'},

Tu código de verificación para recuperar tu contraseña es:

{code}

Este código expirará en 10 minutos por seguridad.

Si no solicitaste este cambio, puedes ignorar este email de forma segura.

Saludos,
Equipo SQL-MongoDB Translator
            """
            
            logger.info(f"Email simulado enviado:\n{email_content}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email de reset a {email}: {str(e)}")
            return False
    
    @staticmethod
    def send_password_changed_notification(email, user_name=None):
        """
        Envía notificación de contraseña cambiada (simulado)
        """
        try:
            logger.info(f"[EMAIL SIMULADO] Notificación de cambio de contraseña a {email}")
            
            email_content = f"""
Para: {email}
Asunto: Contraseña actualizada - SQL Translator

Hola {user_name or 'Usuario'},

Tu contraseña ha sido actualizada exitosamente.

Si no realizaste este cambio, contacta con soporte inmediatamente.

Saludos,
Equipo SQL-MongoDB Translator
            """
            
            logger.info(f"Notificación simulada enviada:\n{email_content}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando notificación a {email}: {str(e)}")
            return False
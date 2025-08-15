import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    
    # CONFIGURACIÓN: Ruta de SharePoint sincronizada
    SHAREPOINT_PATH = r"C:\Users\User\OneDrive - Escuela Politécnica Nacional\Escuela Politécnica Nacional - Documentos\EmailService"
    
    @staticmethod
    def send_reset_code(email, code, user_name=None):
        """
        NUEVA VERSIÓN: Crea archivo para Power Automate
        Genera archivo .txt en SharePoint que será procesado por Power Automate
        """
        try:
            # DATOS DEL EMAIL
            email_data = {
                "type": "password_reset",
                "to_email": email,
                "user_name": user_name or "Usuario",
                "reset_code": code,
                "timestamp": datetime.utcnow().isoformat(),
                "subject": "Código de recuperación - SQL Translator"
            }
            
            # CONTENIDO DEL EMAIL (mismo formato que tenías)
            email_content = f"""Para: {email}
Asunto: Código de recuperación - SQL Translator

Hola {user_name or 'Usuario'},

Tu código de verificación para recuperar tu contraseña es:

{code}

Este código expirará en 10 minutos por seguridad.

Si no solicitaste este cambio, puedes ignorar este email de forma segura.

Saludos,
Equipo SQL-MongoDB Translator

---
METADATA (para Power Automate):
EMAIL: {email}
CODE: {code}
USER: {user_name or 'Usuario'}
TYPE: password_reset
TIMESTAMP: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
"""

            # CREAR ARCHIVO ÚNICO para evitar conflictos
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # milisegundos
            filename = f"reset_code_{timestamp}_{email.replace('@', '_').replace('.', '_')}.txt"
            
            # VERIFICAR QUE EXISTE LA CARPETA
            if not os.path.exists(EmailService.SHAREPOINT_PATH):
                logger.error(f"[SHAREPOINT] Carpeta SharePoint no encontrada: {EmailService.SHAREPOINT_PATH}")
                return False
            
            # ESCRIBIR ARCHIVO
            file_path = os.path.join(EmailService.SHAREPOINT_PATH, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(email_content)
            
            logger.info(f"[SHAREPOINT] Archivo creado: {filename}")
            logger.info(f"[SHAREPOINT] Email para: {email} con código: {code}")
            logger.info(f"[SHAREPOINT] Ruta: {file_path}")
            
            # VERIFICAR QUE EL ARCHIVO SE CREÓ
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                logger.info(f"[SHAREPOINT] Archivo confirmado ({file_size} bytes)")
                return True
            else:
                logger.error(f"[SHAREPOINT] Error: Archivo no se creó")
                return False
            
        except Exception as e:
            logger.error(f"[SHAREPOINT] Error creando archivo de reset: {str(e)}")
            return False
    
    @staticmethod
    def send_password_changed_notification(email, user_name=None):
        """
        NUEVA VERSIÓN: Notificación de cambio exitoso via SharePoint
        """
        try:
            # CONTENIDO DE NOTIFICACIÓN
            email_content = f"""Para: {email}
Asunto: Contraseña actualizada - SQL Translator

Hola {user_name or 'Usuario'},

Tu contraseña ha sido actualizada exitosamente.

Si no realizaste este cambio, contacta con soporte inmediatamente.

Saludos,
Equipo SQL-MongoDB Translator

---
METADATA (para Power Automate):
EMAIL: {email}
USER: {user_name or 'Usuario'}
TYPE: password_changed
TIMESTAMP: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
"""

            # CREAR ARCHIVO ÚNICO
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            filename = f"password_changed_{timestamp}_{email.replace('@', '_').replace('.', '_')}.txt"
            
            # VERIFICAR CARPETA
            if not os.path.exists(EmailService.SHAREPOINT_PATH):
                logger.error(f"[SHAREPOINT] Carpeta SharePoint no encontrada: {EmailService.SHAREPOINT_PATH}")
                return False
            
            # ESCRIBIR ARCHIVO
            file_path = os.path.join(EmailService.SHAREPOINT_PATH, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(email_content)
            
            logger.info(f"[SHAREPOINT] Notificación creada: {filename}")
            logger.info(f"[SHAREPOINT] Notificación para: {email}")
            
            return os.path.exists(file_path)
            
        except Exception as e:
            logger.error(f"[SHAREPOINT] Error creando notificación: {str(e)}")
            return False
    
    @staticmethod
    def test_sharepoint_connection():
        """
        MÉTODO DE PRUEBA: Verificar conexión con SharePoint
        """
        try:
            test_content = f"""ARCHIVO DE PRUEBA
Timestamp: {datetime.utcnow().isoformat()}
Sistema: SQL-MongoDB Translator
Estado: Conexión OK

Este archivo fue creado para probar la integración con Power Automate.
"""
            
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"test_connection_{timestamp}.txt"
            file_path = os.path.join(EmailService.SHAREPOINT_PATH, filename)
            
            # Verificar carpeta
            if not os.path.exists(EmailService.SHAREPOINT_PATH):
                return {
                    "success": False,
                    "error": f"Carpeta no encontrada: {EmailService.SHAREPOINT_PATH}",
                    "suggestion": "Verificar que OneDrive esté sincronizado"
                }
            
            # Crear archivo de prueba
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # Verificar creación
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                return {
                    "success": True,
                    "message": "Conexión SharePoint OK",
                    "file_created": filename,
                    "file_size": file_size,
                    "path": file_path
                }
            else:
                return {
                    "success": False,
                    "error": "Archivo no se pudo crear",
                    "path": file_path
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "suggestion": "Verificar permisos de escritura en OneDrive"
            }

# FUNCIÓN PARA TESTING DESDE TERMINAL
if __name__ == "__main__":
    # Prueba rápida
    result = EmailService.test_sharepoint_connection()
    print("Test de conexión SharePoint:")
    print(f"Éxito: {result['success']}")
    if result['success']:
        print(f"Archivo: {result['file_created']}")
        print(f"Tamaño: {result['file_size']} bytes")
    else:
        print(f"Error: {result['error']}")
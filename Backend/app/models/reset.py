"""
Modelo para manejo de códigos de reset de contraseña
"""
from datetime import datetime, timedelta
from bson import ObjectId
import secrets
import logging

logger = logging.getLogger(__name__)

class PasswordReset:
    def __init__(self, db):  # ✅ CORREGIDO: recibe db en lugar de connector
        self.db = db
        self.collection = db.password_resets  # ✅ CORREGIDO: acceso directo a collection
    
    def create_reset_request(self, email):
        """
        Crea una nueva solicitud de reset
        """
        try:
            # Generar código de 6 dígitos
            code = f"{secrets.randbelow(900000) + 100000:06d}"
            
            # Limpiar requests anteriores para este email
            self.collection.delete_many({"email": email})
            
            # Crear nuevo request
            reset_data = {
                "email": email,
                "code": code,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=10),
                "used": False,
                "attempts": 0
            }
            
            result = self.collection.insert_one(reset_data)
            logger.info(f"Código de reset creado para {email}: {code}")
            return code if result.inserted_id else None
            
        except Exception as e:
            logger.error(f"Error creando reset request: {e}")
            return None
    
    def verify_code(self, email, code):
        """
        Verifica si el código es válido
        """
        try:
            reset_request = self.collection.find_one({
                "email": email,
                "code": code,
                "used": False,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if reset_request:
                # Marcar como usado
                self.collection.update_one(
                    {"_id": reset_request["_id"]},
                    {"$set": {"used": True}}
                )
                logger.info(f"Código verificado exitosamente para {email}")
                return True
            
            # Incrementar intentos fallidos
            self.collection.update_one(
                {"email": email, "used": False},
                {"$inc": {"attempts": 1}}
            )
            logger.warning(f"Código inválido para {email}")
            return False
            
        except Exception as e:
            logger.error(f"Error verificando código: {e}")
            return False
    
    def cleanup_expired(self):
        """
        Limpia códigos expirados
        """
        try:
            result = self.collection.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            logger.info(f"Limpiados {result.deleted_count} códigos expirados")
        except Exception as e:
            logger.error(f"Error limpiando códigos expirados: {e}")
    
    def get_attempts(self, email):
        """
        Obtiene número de intentos para un email
        """
        try:
            reset_request = self.collection.find_one(
                {"email": email, "used": False}
            )
            return reset_request.get("attempts", 0) if reset_request else 0
        except Exception as e:
            logger.error(f"Error obteniendo intentos: {e}")
            return 0
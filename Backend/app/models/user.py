from datetime import datetime
from bson import ObjectId
import bcrypt
import logging

logger = logging.getLogger(__name__)

class UserModel:
    """
    Modelo para usuarios del sistema.
    Maneja operaciones CRUD y validaciones de usuarios.
    """
    
    def __init__(self, db):
        self.db = db
        self.collection = db.users
        
        # Crear índices únicos
        self.collection.create_index("username", unique=True)
        self.collection.create_index("email", unique=True)
    
    @staticmethod
    def hash_password(password):
        """Encripta una contraseña usando bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)
    
    @staticmethod
    def verify_password(password, hashed):
        """Verifica una contraseña contra su hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    def create_user(self, username, email, password, role='user'):
        """
        Crea un nuevo usuario.
        
        Args:
            username (str): Nombre de usuario único
            email (str): Email único del usuario
            password (str): Contraseña en texto plano
            role (str): Rol del usuario ('admin' o 'user')
        
        Returns:
            dict: Usuario creado o error
        """
        try:
            # Validar que no exista el usuario
            if self.collection.find_one({"username": username}):
                return {"error": "El nombre de usuario ya existe"}
            
            if self.collection.find_one({"email": email}):
                return {"error": "El email ya está registrado"}
            
            # Encriptar contraseña
            hashed_password = self.hash_password(password)
            
            # Crear usuario
            user_data = {
                "username": username,
                "email": email,
                "password": hashed_password,
                "role": role,
                "permissions": self._get_default_permissions(role),
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = self.collection.insert_one(user_data)
            
            # Retornar usuario sin la contraseña
            user_data["_id"] = str(result.inserted_id)
            del user_data["password"]
            
            logger.info(f"Usuario creado: {username}")
            return user_data
            
        except Exception as e:
            logger.error(f"Error al crear usuario: {e}")
            return {"error": str(e)}
    
    def authenticate_user(self, username, password):
        """
        Autentica un usuario.
        
        Args:
            username (str): Nombre de usuario o email
            password (str): Contraseña
        
        Returns:
            dict: Usuario autenticado o None
        """
        try:
            # Buscar por username o email
            user = self.collection.find_one({
                "$or": [
                    {"username": username},
                    {"email": username}
                ]
            })
            
            if not user:
                return None
            
            # Verificar contraseña
            if not self.verify_password(password, user["password"]):
                return None
            
            # Verificar si el usuario está activo
            if not user.get("is_active", True):
                return None
            
            # Retornar usuario sin contraseña
            user["_id"] = str(user["_id"])
            del user["password"]
            return user
            
        except Exception as e:
            logger.error(f"Error al autenticar usuario: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Obtiene un usuario por su ID."""
        try:
            user = self.collection.find_one({"_id": ObjectId(user_id)})
            if user:
                user["_id"] = str(user["_id"])
                del user["password"]
                return user
            return None
        except Exception as e:
            logger.error(f"Error al obtener usuario: {e}")
            return None
    
    def get_all_users(self):
        """Obtiene todos los usuarios (solo para admin)."""
        try:
            users = []
            for user in self.collection.find({}, {"password": 0}):
                user["_id"] = str(user["_id"])
                users.append(user)
            return users
        except Exception as e:
            logger.error(f"Error al obtener usuarios: {e}")
            return []
    
    def update_user_permissions(self, user_id, permissions):
        """
        Actualiza los permisos de un usuario.
        
        Args:
            user_id (str): ID del usuario
            permissions (dict): Nuevos permisos
        
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "permissions": permissions,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error al actualizar permisos: {e}")
            return False
    
    def update_user_status(self, user_id, is_active):
        """
        Actualiza el estado activo/inactivo de un usuario.
        
        Args:
            user_id (str): ID del usuario
            is_active (bool): Estado del usuario
        
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "is_active": is_active,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error al actualizar estado del usuario: {e}")
            return False
    
    def _get_default_permissions(self, role):
        """Obtiene los permisos por defecto según el rol."""
        if role == 'admin':
            return {
                "select": True,
                "insert": True,
                "update": True,
                "delete": True,
                "create_table": True,
                "drop_table": True,
                "manage_users": True
            }
        else:  # user
            return {
                "select": True,
                "insert": False,
                "update": False,
                "delete": False,
                "create_table": False,
                "drop_table": False,
                "manage_users": False
            }
    
    def create_admin_user(self):
        """Crea el usuario administrador por defecto si no existe."""
        admin_user = self.collection.find_one({"role": "admin"})
        if not admin_user:
            self.create_user(
                username="admin",
                email="admin@localhost",
                password="admin123",
                role="admin"
            )
            logger.info("Usuario administrador creado con credenciales por defecto")
    

    def update_password(self, email, new_password):
        """
        Actualiza la contraseña de un usuario
        """
        try:
            hashed_password = bcrypt.hashpw(
                new_password.encode('utf-8'), 
                bcrypt.gensalt()
            )
            
            result = self.collection.update_one(
                {"email": email},
                {"$set": {"password": hashed_password}}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error actualizando contraseña: {str(e)}")
            return False

    
    def get_user_by_email(self, email):
        """
        Obtiene un usuario por su email.
        
        Args:
            email (str): Email del usuario
        
        Returns:
            dict: Usuario encontrado o None
        """
        try:
            user = self.collection.find_one({"email": email})
            if user:
                user["_id"] = str(user["_id"])
                del user["password"]  # No incluir la contraseña
                return user
            return None
        except Exception as e:
            logger.error(f"Error al obtener usuario por email: {e}")
            return None
from bson import ObjectId
from pymongo import MongoClient
import time
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Variable global para el patrón singleton
_instance = None

class MongoDBConnector:
    """
    Conector para MongoDB que implementa el patrón singleton.
    Proporciona métodos para interactuar con la base de datos MongoDB.
    """
    
    @staticmethod
    def get_instance(uri, database_name=None):
        """
        Método estático para obtener la instancia singleton del conector.
        
        Args:
            uri (str): URI de conexión a MongoDB.
            database_name (str, optional): Nombre de la base de datos.
            
        Returns:
            MongoDBConnector: Instancia única del conector.
        """
        global _instance
        if _instance is None:
            _instance = MongoDBConnector(uri, database_name)
        elif database_name and _instance.database_name != database_name:
            # Si se solicita cambiar la base de datos en la instancia existente
            _instance.set_database(database_name)
        return _instance
    
    def __init__(self, uri, database_name=None):
        """
        Inicializa el conector con MongoDB.
        
        Args:
            uri (str): URI de conexión a MongoDB.
            database_name (str, optional): Nombre de la base de datos.
        """
        try:
            logger.info(f"Iniciando conexión a MongoDB: {uri}")
            # Opciones de conexión para mayor estabilidad
            self.client = MongoClient(
                uri, 
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=30000,
                maxPoolSize=50,
                retryWrites=True
            )
            self.uri = uri
            self.db = None
            self.database_name = None
            
            # Verificar conexión
            self.client.admin.command('ping')
            logger.info("Conexión exitosa a MongoDB")
            
            # Listar bases de datos disponibles (excluyendo bases del sistema)
            self.available_databases = self._filter_system_databases(self.client.list_database_names())
            logger.info(f"Bases de datos disponibles: {self.available_databases}")
            
            # Establecer la base de datos si se proporcionó
            if database_name:
                self.set_database(database_name)
            else:
                logger.info("No se ha seleccionado ninguna base de datos. Use set_database() para seleccionar una.")
                
        except Exception as e:
            logger.error(f"Error al conectar a MongoDB: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def is_connected(self):
        """
        Verifica si la conexión a MongoDB está activa.
        
        Returns:
            bool: True si está conectado, False en caso contrario.
        """
        try:
            # Intentar ejecutar un comando simple
            self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Error de conexión: {e}")
            return False
    
    def is_database_selected(self):
        """
        Verifica si hay una base de datos seleccionada actualmente.
        
        Returns:
            bool: True si hay una base de datos seleccionada.
        """
        return self.db is not None and self.database_name is not None
    
    def get_current_database(self):
        """
        Obtiene el nombre de la base de datos actualmente seleccionada.
        
        Returns:
            str: Nombre de la base de datos actual o None.
        """
        return self.database_name
    
    def _filter_system_databases(self, databases):
        """
        Filtra las bases de datos del sistema.
        
        Args:
            databases (list): Lista de nombres de bases de datos.
            
        Returns:
            list: Lista filtrada.
        """
        # Bases de datos del sistema a excluir
        system_dbs = ['admin', 'local', 'config']
        return [db for db in databases if db not in system_dbs]
    
    def set_database(self, database_name):
        """
        Establece la base de datos a utilizar.
        
        Args:
            database_name (str): Nombre de la base de datos.
            
        Returns:
            list: Lista de colecciones disponibles.
        """
        try:
            self.db = self.client[database_name]
            self.database_name = database_name
            
            # Listar colecciones disponibles
            collections = self.db.list_collection_names()
            logger.info(f"Conexión establecida con base de datos: {database_name}")
            logger.info(f"Colecciones disponibles en {database_name}: {collections}")
            
            return collections
        except Exception as e:
            logger.error(f"Error al seleccionar la base de datos {database_name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def get_available_databases(self):
        """
        Obtiene la lista de bases de datos disponibles.
        
        Returns:
            list: Lista de bases de datos.
        """
        try:
            # Actualizar la lista de bases de datos
            all_databases = self.client.list_database_names()
            self.available_databases = self._filter_system_databases(all_databases)
            return self.available_databases
        except Exception as e:
            logger.error(f"Error al obtener bases de datos disponibles: {e}")
            self._try_reconnect()
            # Intentar nuevamente después de reconectar
            try:
                all_databases = self.client.list_database_names()
                return self._filter_system_databases(all_databases)
            except:
                return []
    
    def _try_reconnect(self):
        """
        Intenta reconectar al servidor MongoDB.
        """
        try:
            logger.info("Intentando reconectar a MongoDB...")
            self.client = MongoClient(
                self.uri, 
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=30000,
                maxPoolSize=50,
                retryWrites=True
            )
            self.client.admin.command('ping')
            logger.info("Reconexión exitosa")
            
            # Si había una base de datos seleccionada, volver a seleccionarla
            if hasattr(self, 'database_name') and self.database_name:
                self.set_database(self.database_name)
        except Exception as e:
            logger.error(f"Error al reconectar: {e}")
    
    def get_collections(self, database_name=None):
        """
        Obtiene las colecciones disponibles en una base de datos.
        
        Args:
            database_name (str, optional): Nombre de la base de datos.
            
        Returns:
            list: Lista de colecciones.
        """
        try:
            if database_name:
                db = self.client[database_name]
            elif hasattr(self, 'db') and self.db:
                db = self.db
            else:
                return []
            
            return db.list_collection_names()
        except Exception as e:
            logger.error(f"Error al obtener colecciones: {e}")
            self._try_reconnect()
            # Intentar nuevamente después de reconectar
            try:
                if database_name:
                    return self.client[database_name].list_collection_names()
                elif hasattr(self, 'db') and self.db:
                    return self.db.list_collection_names()
                return []
            except:
                return []

    def execute_query(self, collection_name, query):
        """
        Ejecuta una consulta en MongoDB.
        🔧 ACTUALIZADO: Soporte para INSERT_MANY
        
        Args:
            collection_name (str): Nombre de la colección.
            query (dict): Consulta en formato MongoDB.
            
        Returns:
            Resultado de la consulta.
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Verificar si hay una base de datos seleccionada
                if not self.is_database_selected():
                    raise ValueError("No se ha seleccionado ninguna base de datos. Use set_database() primero.")
                
                # Verificar si la colección existe y crearla si es necesario
                if collection_name not in self.db.list_collection_names():
                    # Si la colección no existe, verificar si es una operación de creación
                    if query.get("operation") == "create_collection":
                        # Crear la colección explícitamente
                        options = query.get("options", {})
                        self.db.create_collection(collection_name, **options)
                        return {"created": True, "collection_name": collection_name}
                    else:
                        # Para otras operaciones, crear la colección vacía automáticamente
                        logger.warning(f"La colección {collection_name} no existe. Se creará automáticamente.")
                
                collection = self.db[collection_name]
                operation = query.get("operation")
                logger.info(f"Ejecutando operación {operation} en la colección {collection_name}")
                
                # Manejar cada tipo de operación
                if operation == "find":
                    return self._execute_find(collection, query)
                elif operation == "aggregate":
                    return self._execute_aggregate(collection, query)
                elif operation == "insert":
                    return self._execute_insert(collection, query)
                elif operation == "INSERT_MANY":
                    # 🔧 NUEVO: Soporte para INSERT múltiple
                    return self._execute_insert_many(collection, query)
                elif operation == "update":
                    return self._execute_update(collection, query)
                elif operation == "delete":
                    return self._execute_delete(collection, query)
                elif operation == "create_collection":
                    # Ya manejado arriba si la colección no existe
                    return {"created": True, "collection_name": collection_name}
                elif operation == "drop_collection":
                    return self._execute_drop_collection(collection)
                else:
                    raise ValueError(f"Operación no soportada: {operation}")
                
            except Exception as e:
                logger.error(f"Error al ejecutar consulta (intento {retry_count+1}): {e}")
                retry_count += 1
                
                if "MongoClient after close" in str(e) or "not connected" in str(e).lower():
                    logger.warning("Detectado error de conexión. Intentando reconectar...")
                    self._try_reconnect()
                    time.sleep(1)  # Esperar un momento antes de reintentar
                elif retry_count >= max_retries:
                    import traceback
                    logger.error(traceback.format_exc())
                    raise
                else:
                    time.sleep(0.5)  # Esperar un poco antes de reintentar para otros errores
        
        raise Exception("Se excedió el número máximo de intentos de consulta")
    
    def _serialize_results(self, results):
        """
        Serializa los resultados para que sean compatibles con JSON.
        
        Args:
            results: Resultados de la consulta.
            
        Returns:
            Resultados serializados.
        """
        if isinstance(results, list):
            for result in results:
                if isinstance(result, dict):
                    for key, value in list(result.items()):
                        if isinstance(value, ObjectId):
                            result[key] = str(value)
                        elif isinstance(value, dict):
                            # Recursivamente procesar subdocumentos
                            self._serialize_dict(value)
        elif isinstance(results, dict):
            self._serialize_dict(results)
        return results
    
    def _serialize_dict(self, document):
        """
        Serializa un diccionario recursivamente.
        
        Args:
            document (dict): Diccionario a serializar.
        """
        for key, value in list(document.items()):
            if isinstance(value, ObjectId):
                document[key] = str(value)
            elif isinstance(value, dict):
                self._serialize_dict(value)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        self._serialize_dict(item)
                    elif isinstance(item, ObjectId):
                        value[i] = str(item)
    
    def _execute_find(self, collection, query):
        """
        Ejecuta una operación find() en MongoDB.
        
        Args:
            collection (Collection): Colección de MongoDB.
            query (dict): Consulta en formato MongoDB.
            
        Returns:
            list: Resultados de la consulta.
        """
        mongo_query = query.get("query", {})
        projection = query.get("projection", None)
        sort = query.get("sort", None)
        limit = query.get("limit", None)
        skip = query.get("skip", None)
        
        logger.info(f"Ejecutando find con filtro: {mongo_query}")
        
        # Preparar la consulta
        cursor = collection.find(mongo_query, projection)
        
        # Aplicar ordenamiento si existe
        if sort:
            logger.info(f"Ordenamiento: {sort}")
            cursor = cursor.sort(list(sort.items()))
        
        # Aplicar skip si existe
        if skip:
            logger.info(f"Skip: {skip}")
            cursor = cursor.skip(skip)
        
        # Aplicar límite si existe
        if limit is not None:
            logger.info(f"Límite: {limit}")
            cursor = cursor.limit(limit)
        
        # Ejecutar la consulta y convertir el cursor a lista
        results = list(cursor)
        logger.info(f"Resultados encontrados: {len(results)}")
        
        # Serializar resultados para JSON
        return self._serialize_results(results)
    
    def _execute_aggregate(self, collection, query):
        """
        Ejecuta una operación aggregate() en MongoDB.
        
        Args:
            collection (Collection): Colección de MongoDB.
            query (dict): Consulta en formato MongoDB.
            
        Returns:
            list: Resultados de la consulta.
        """
        pipeline = query.get("pipeline", [])
        logger.info(f"Ejecutando aggregate con pipeline: {pipeline}")
        
        # Ejecutar la agregación
        results = list(collection.aggregate(pipeline))
        logger.info(f"Resultados de agregación: {len(results)}")
        
        # Serializar resultados para JSON
        return self._serialize_results(results)
    
    def _execute_insert(self, collection, query):
        """
        Ejecuta una operación insertOne() en MongoDB.
        
        Args:
            collection (Collection): Colección de MongoDB.
            query (dict): Consulta en formato MongoDB.
            
        Returns:
            dict: Resultado de la operación.
        """
        document = query.get("document", {})
        logger.info(f"Insertando documento: {document}")
        
        # Ejecutar la inserción
        result = collection.insert_one(document)
        return {"inserted_id": str(result.inserted_id)}
    
    def _execute_insert_many(self, collection, query):
        """
        🔧 NUEVO: Ejecuta una operación insertMany() en MongoDB.
        
        Args:
            collection (Collection): Colección de MongoDB.
            query (dict): Consulta en formato MongoDB.
            
        Returns:
            dict: Resultado de la operación.
        """
        documents = query.get("documents", [])
        count = len(documents)
        
        logger.info(f"Insertando {count} documentos: {documents}")
        
        if count == 0:
            return {
                "acknowledged": True,
                "inserted_ids": [],
                "insertedCount": 0
            }
        
        # Ejecutar la inserción múltiple
        result = collection.insert_many(documents)
        inserted_ids = [str(id) for id in result.inserted_ids]
        
        logger.info(f"{len(inserted_ids)} documentos insertados con IDs: {inserted_ids}")
        
        return {
            "acknowledged": result.acknowledged,
            "inserted_ids": inserted_ids,
            "insertedCount": len(inserted_ids)
        }
    
    def _execute_update(self, collection, query):
        """
        Ejecuta una operación updateMany() en MongoDB.
        
        Args:
            collection (Collection): Colección de MongoDB.
            query (dict): Consulta en formato MongoDB.
            
        Returns:
            dict: Resultado de la operación.
        """
        update_query = query.get("query", {})
        
        filter_query = update_query.get("query", {})
        update_data = update_query.get("update", {})
        
        logger.info(f"Actualizando documentos con filtro: {filter_query}")
        logger.info(f"Datos de actualización: {update_data}")
        
        # Si update_data no tiene operadores de actualización, usar $set
        if update_data and not any(key.startswith("$") for key in update_data.keys()):
            update_data = {"$set": update_data}
            logger.info(f"Añadiendo operador $set implícito: {update_data}")
        
        # Ejecutar la actualización
        result = collection.update_many(filter_query, update_data)
        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None
        }
    
    def _execute_delete(self, collection, query):
        """
        Ejecuta una operación deleteMany() en MongoDB.
        
        Args:
            collection (Collection): Colección de MongoDB.
            query (dict): Consulta en formato MongoDB.
            
        Returns:
            dict: Resultado de la operación.
        """
        delete_query = query.get("query", {})
        logger.info(f"Eliminando documentos con filtro: {delete_query}")
        
        # Ejecutar la eliminación
        result = collection.delete_many(delete_query)
        return {"deleted_count": result.deleted_count}
    

    def create_collection_with_schema(self, collection_name, options=None, indexes=None):
        """
        Crea una colección con validación de esquema e índices.
        🔧 CORREGIDO: Maneja colecciones existentes
        
        Args:
            collection_name (str): Nombre de la colección
            options (dict): Opciones de creación incluyendo validator
            indexes (list): Lista de índices a crear
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            if not self.is_database_selected():
                raise Exception("No hay base de datos seleccionada")
            
            # 🔧 NUEVO: Verificar si la colección ya existe
            existing_collections = self.db.list_collection_names()
            collection_exists = collection_name in existing_collections
            
            if collection_exists:
                logger.warning(f"La colección '{collection_name}' ya existe")
                
                # 🔧 OPCIÓN 1: Devolver información de la colección existente
                result = {
                    "acknowledged": True,
                    "collection_created": False,
                    "collection_name": collection_name,
                    "already_exists": True,
                    "message": f"La colección '{collection_name}' ya existe",
                    "has_validator": False,
                    "indexes_created": [],
                    "total_indexes": 0
                }
                
                # Obtener información de la colección existente
                try:
                    existing_schema = self.get_collection_schema(collection_name)
                    if existing_schema and existing_schema.get("has_validator"):
                        result["has_validator"] = True
                        result["existing_validator"] = existing_schema.get("validator")
                except Exception as e:
                    logger.warning(f"No se pudo obtener esquema existente: {e}")
                
                # Obtener índices existentes
                try:
                    existing_indexes = self.get_collection_indexes(collection_name)
                    result["existing_indexes"] = existing_indexes
                    result["total_existing_indexes"] = len(existing_indexes)
                except Exception as e:
                    logger.warning(f"No se pudo obtener índices existentes: {e}")
                
                return result
            
            # 🔧 NUEVO: Solo crear si no existe
            # 1. Crear la colección con opciones
            if options:
                self.db.create_collection(collection_name, **options)
                logger.info(f"Colección '{collection_name}' creada con validador de esquema")
            else:
                self.db.create_collection(collection_name)
                logger.info(f"Colección '{collection_name}' creada sin esquema")
            
            collection = self.db[collection_name]
            
            # 2. Crear índices si se especificaron
            indexes_created = []
            if indexes:
                for index_spec in indexes:
                    try:
                        index_name = collection.create_index(
                            list(index_spec["key"].items()),
                            unique=index_spec.get("unique", False),
                            name=index_spec.get("name")
                        )
                        indexes_created.append({
                            "name": index_name,
                            "specification": index_spec
                        })
                        logger.info(f"Índice creado: {index_name}")
                    except Exception as e:
                        logger.warning(f"Error creando índice {index_spec.get('name', 'unknown')}: {e}")
            
            # 3. Verificar que la colección fue creada
            collection_info = self.db.list_collection_names()
            created_successfully = collection_name in collection_info
            
            result = {
                "acknowledged": True,
                "collection_created": created_successfully,
                "collection_name": collection_name,
                "already_exists": False,
                "has_validator": bool(options and "validator" in options),
                "indexes_created": indexes_created,
                "total_indexes": len(indexes_created)
            }
            
            # 4. Obtener información del validador si existe
            if options and "validator" in options:
                try:
                    result["validator_info"] = {
                        "validation_level": options.get("validationLevel", "moderate"),
                        "validation_action": options.get("validationAction", "warn"),
                        "has_schema": "$jsonSchema" in options["validator"]
                    }
                except Exception as e:
                    logger.warning(f"No se pudo obtener información del validador: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error creando colección con esquema: {e}")
            raise e


    # 🔧 MÉTODO ADICIONAL: Opción para recrear colección
    def recreate_collection_with_schema(self, collection_name, options=None, indexes=None):
        """
        🔧 NUEVO: Recrea una colección eliminando la existente primero.
        ⚠️ PELIGROSO: Esto eliminará todos los datos existentes.
        
        Args:
            collection_name (str): Nombre de la colección
            options (dict): Opciones de creación
            indexes (list): Lista de índices
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # 1. Verificar si existe y eliminarla
            existing_collections = self.db.list_collection_names()
            if collection_name in existing_collections:
                logger.warning(f"🗑️ Eliminando colección existente '{collection_name}'")
                self.db.drop_collection(collection_name)
            
            # 2. Crear nueva colección
            return self.create_collection_with_schema(collection_name, options, indexes)
            
        except Exception as e:
            logger.error(f"Error recreando colección: {e}")
            raise e


    def get_collection_schema(self, collection_name):
        """
        Obtiene el esquema de validación de una colección.
        
        Args:
            collection_name (str): Nombre de la colección
            
        Returns:
            dict: Información del esquema o None si no tiene
        """
        try:
            if not self.is_database_selected():
                raise Exception("No hay base de datos seleccionada")
            
            # Obtener información de la colección
            collections = self.db.list_collections(filter={"name": collection_name})
            collection_info = list(collections)
            
            if not collection_info:
                return None
            
            collection_data = collection_info[0]
            
            if "options" in collection_data and "validator" in collection_data["options"]:
                return {
                    "has_validator": True,
                    "validator": collection_data["options"]["validator"],
                    "validation_level": collection_data["options"].get("validationLevel", "moderate"),
                    "validation_action": collection_data["options"].get("validationAction", "warn")
                }
            
            return {"has_validator": False}
            
        except Exception as e:
            logger.error(f"Error obteniendo esquema de colección: {e}")
            return None

    def get_collection_indexes(self, collection_name):
        """
        Obtiene los índices de una colección.
        
        Args:
            collection_name (str): Nombre de la colección
            
        Returns:
            list: Lista de índices
        """
        try:
            if not self.is_database_selected():
                raise Exception("No hay base de datos seleccionada")
            
            collection = self.db[collection_name]
            indexes = list(collection.list_indexes())
            
            # Limpiar información de índices
            cleaned_indexes = []
            for index in indexes:
                cleaned_index = {
                    "name": index.get("name"),
                    "key": index.get("key"),
                    "unique": index.get("unique", False),
                    "sparse": index.get("sparse", False)
                }
                cleaned_indexes.append(cleaned_index)
            
            return cleaned_indexes
            
        except Exception as e:
            logger.error(f"Error obteniendo índices de colección: {e}")
            return []

    def insert_sample_document(self, collection_name, document):
        """
        Inserta un documento de ejemplo en una colección.
        
        Args:
            collection_name (str): Nombre de la colección
            document (dict): Documento a insertar
            
        Returns:
            dict: Resultado de la inserción
        """
        try:
            if not self.is_database_selected():
                raise Exception("No hay base de datos seleccionada")
            
            collection = self.db[collection_name]
            result = collection.insert_one(document)
            
            logger.info(f"Documento de ejemplo insertado con ID: {result.inserted_id}")
            
            return {
                "acknowledged": result.acknowledged,
                "inserted_id": str(result.inserted_id),
                "document": document
            }
            
        except Exception as e:
            logger.error(f"Error insertando documento de ejemplo: {e}")
            return {
                "acknowledged": False,
                "error": str(e)
            }

    # Método modificado para manejar create_collection_with_schema
    def execute_query(self, collection_name, query):
        """
        Ejecuta una consulta en MongoDB.
        🔧 ACTUALIZADO: Soporte para CREATE TABLE con esquema
        
        Args:
            collection_name (str): Nombre de la colección.
            query (dict): Consulta en formato MongoDB.
            
        Returns:
            Resultado de la consulta.
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Verificar si hay una base de datos seleccionada
                if not self.is_database_selected():
                    raise ValueError("No se ha seleccionado ninguna base de datos. Use set_database() primero.")
                
                operation = query.get("operation")
                logger.info(f"Ejecutando operación {operation} en la colección {collection_name}")
                
                # 🆕 NUEVO: Manejar create_collection_with_schema
                if operation == "create_collection_with_schema":
                    options = query.get("options", {})
                    indexes = query.get("indexes_to_create", [])
                    
                    result = self.create_collection_with_schema(collection_name, options, indexes)
                    
                    # Si hay documento de ejemplo, insertarlo
                    sample_document = query.get("sample_document")
                    if sample_document:
                        try:
                            sample_result = self.insert_sample_document(collection_name, sample_document)
                            result["sample_document_inserted"] = sample_result
                        except Exception as e:
                            logger.warning(f"No se pudo insertar documento de ejemplo: {e}")
                            result["sample_document_error"] = str(e)
                    
                    return result
                
                # Verificar si la colección existe para otras operaciones
                if collection_name not in self.db.list_collection_names():
                    # Si la colección no existe, verificar si es una operación de creación
                    if operation == "create_collection":
                        # Crear la colección explícitamente
                        options = query.get("options", {})
                        self.db.create_collection(collection_name, **options)
                        return {"created": True, "collection_name": collection_name}
                    else:
                        # Para otras operaciones, crear la colección vacía automáticamente
                        logger.warning(f"La colección {collection_name} no existe. Se creará automáticamente.")
                
                collection = self.db[collection_name]
                
                # Manejar cada tipo de operación (resto del código igual)
                if operation == "find":
                    return self._execute_find(collection, query)
                elif operation == "aggregate":
                    return self._execute_aggregate(collection, query)
                elif operation == "insert":
                    return self._execute_insert(collection, query)
                elif operation == "INSERT_MANY":
                    return self._execute_insert_many(collection, query)
                elif operation == "update":
                    return self._execute_update(collection, query)
                elif operation == "delete":
                    return self._execute_delete(collection, query)
                elif operation == "create_collection":
                    # Ya manejado arriba si la colección no existe
                    return {"created": True, "collection_name": collection_name}
                elif operation == "drop_collection":
                    return self._execute_drop_collection(collection)
                else:
                    raise ValueError(f"Operación no soportada: {operation}")
                
            except Exception as e:
                logger.error(f"Error al ejecutar consulta (intento {retry_count+1}): {e}")
                retry_count += 1
                
                if "MongoClient after close" in str(e) or "not connected" in str(e).lower():
                    logger.warning("Detectado error de conexión. Intentando reconectar...")
                    self._try_reconnect()
                    time.sleep(1)
                elif retry_count >= max_retries:
                    import traceback
                    logger.error(traceback.format_exc())
                    raise
                else:
                    time.sleep(0.5)
        
        raise Exception("Se excedió el número máximo de intentos de consulta")

    def _execute_drop_collection(self, collection):
        """
        Ejecuta una operación drop() en una colección de MongoDB.
        
        Args:
            collection (Collection): Colección de MongoDB.
            
        Returns:
            dict: Resultado de la operación.
        """
        logger.info(f"Eliminando colección: {collection.name}")
        collection.drop()
        return {"dropped": True, "collection_name": collection.name}
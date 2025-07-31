import logging
from app.parser.sql_parser import SQLParser

# Configurar logging
logger = logging.getLogger(__name__)

class SQLToMongoDBTranslator:
    """
    Traductor de consultas SQL a operaciones MongoDB.
    Convierte los resultados del parser SQL en operaciones MongoDB equivalentes.
    🆕 EXTENDIDO con soporte para funciones, JOINs, DISTINCT, HAVING y más.
    """
    
    def __init__(self, sql_parser=None):
        """
        Inicializa el traductor con un parser SQL opcional.
        
        Args:
            sql_parser (SQLParser, optional): Parser SQL preconfigurado
        """
        self.sql_parser = sql_parser
        # 🆕 Lista para almacenar advertencias durante la traducción
        self.warnings = []
    
    def translate(self, sql_query=None):
        """
        Traduce una consulta SQL a formato MongoDB.
        🆕 EXTENDIDO con detección automática de características avanzadas.
        
        Args:
            sql_query (str, optional): Consulta SQL a traducir. Si no se proporciona,
                                      se utiliza la consulta del parser proporcionado en la inicialización.
        
        Returns:
            dict: Diccionario con la operación MongoDB equivalente
        """
        # Si se proporciona una nueva consulta, crear un nuevo parser
        if sql_query:
            self.sql_parser = SQLParser(sql_query)
        
        if not self.sql_parser:
            raise ValueError("No se ha proporcionado una consulta SQL ni un parser")
        
        # 🆕 Limpiar advertencias anteriores
        self.warnings = []
        
        # 🆕 Analizar complejidad de la consulta
        complexity_info = self.sql_parser.analyze_query_complexity()
        logger.info(f"Complejidad de consulta: {complexity_info['complexity_level']}")
        
        # Determinar el tipo de consulta y llamar al método de traducción adecuado
        query_type = self.sql_parser.get_query_type()
        logger.info(f"Traduciendo consulta de tipo: {query_type}")
        
        if query_type == "SELECT":
            return self.translate_select()
        elif query_type == "INSERT":
            return self.translate_insert()
        elif query_type == "UPDATE":
            return self.translate_update()
        elif query_type == "DELETE":
            return self.translate_delete()
        elif query_type == "CREATE":
            return self.translate_create_table()
        elif query_type == "DROP":
            return self.translate_drop_table()
        else:
            raise ValueError(f"Tipo de consulta no soportado: {query_type}")
    

    def translate_select(self):
        """
        Traduce una consulta SELECT a operaciones de MongoDB.
        ✅ CORREGIDO con detección mejorada de agregaciones.
        """
        # Obtener el nombre de la tabla (colección en MongoDB)
        collection = self.sql_parser.get_table_name()
        
        # Obtener los campos a seleccionar
        select_fields = self.sql_parser.get_select_fields()
        
        # Obtener la cláusula WHERE
        where_clause = self.sql_parser.get_where_clause()
        
        # ✅ CORREGIDO: Verificar características avanzadas
        has_functions = self.sql_parser.has_functions()
        has_joins = self.sql_parser.has_joins() if hasattr(self.sql_parser, 'has_joins') else False
        has_distinct = self.sql_parser.has_distinct() if hasattr(self.sql_parser, 'has_distinct') else False
        has_having = self.sql_parser.has_having() if hasattr(self.sql_parser, 'has_having') else False
        has_union = self.sql_parser.has_union() if hasattr(self.sql_parser, 'has_union') else False
        has_subquery = self.sql_parser.has_subquery() if hasattr(self.sql_parser, 'has_subquery') else False
        has_order_by = bool(self.sql_parser.get_order_by())
        
        # ✅ NUEVO: Detectar funciones de agregación específicamente
        has_aggregate = False
        if has_functions:
            functions = self.sql_parser.get_functions()
            # Buscar funciones de agregación
            aggregate_function_names = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP_CONCAT']
            for func in functions:
                func_name = func.get('function_name', '').upper()
                if func_name in aggregate_function_names:
                    has_aggregate = True
                    logger.info(f"🔢 Función de agregación detectada: {func_name}")
                    break
        
        # ✅ NUEVO: Detectar GROUP BY
        has_group_by = False
        if hasattr(self.sql_parser, 'get_group_by'):
            group_by = self.sql_parser.get_group_by()
            has_group_by = len(group_by) > 0 if group_by else False
        
        logger.info(f"📊 Características detectadas - Agregaciones: {has_aggregate}, GROUP BY: {has_group_by}, ORDER BY: {has_order_by}")
        
        # ✅ CORREGIDA: Lógica de decisión para determinar el tipo de operación
        if has_union:
            # UNION requiere manejo especial
            self.warnings.append("UNION detectado - requiere MongoDB 4.4+ o queries separadas")
            return self._translate_select_union()
        
        elif has_joins:
            # JOINs requieren pipeline de agregación con $lookup
            logger.info("JOINs detectados - usando pipeline de agregación")
            return self._translate_select_with_joins()
        
        elif has_aggregate or has_group_by or has_having or has_distinct or has_order_by:
            # ✅ CRÍTICO: Usar aggregate para consultas con funciones agregadas
            logger.info("Características avanzadas detectadas (agregaciones/ORDER BY) - usando pipeline de agregación")
            return self._translate_select_aggregate()
        
        else:
            # Usar find para consultas simples
            logger.info("Consulta simple - usando operación find")
            return self._translate_select_find()

    def _translate_select_find(self):
        """
        Traduce una consulta SELECT simple a una operación find() de MongoDB.
        """
        result = {
            "operation": "find",
            "query": {}
        }
        
        # Obtener el nombre de la tabla (colección)
        collection = self.sql_parser.get_table_name()
        if collection:
            result["collection"] = collection
        
        # Obtener cláusula WHERE
        where_clause = self.sql_parser.get_where_clause()
        if where_clause:
            result["query"] = where_clause
        
        # Obtener campos a seleccionar
        select_fields = self.sql_parser.get_select_fields()
        
        # Asegurarnos de que select_fields sea una lista
        if isinstance(select_fields, list):
            # Verificar si hay un campo con valor "*"
            if not any(isinstance(field, dict) and field.get("field") == "*" for field in select_fields):
                projection = {}
                
                for field_info in select_fields:
                    if isinstance(field_info, dict) and "field" in field_info:
                        field = field_info["field"]
                        alias = field_info.get("alias", field)
                        
                        # Verificar si el campo contiene funciones
                        if self._has_sql_functions_in_field(field):
                            # Si hay funciones, esta consulta debe usar aggregate
                            logger.info("Funciones detectadas en SELECT - redirigiendo a aggregate")
                            return self._translate_select_aggregate()
                        else:
                            # Campo simple
                            projection[alias] = 1
                
                if projection:
                    result["projection"] = projection
        
        # ✅ CORREGIDO: Obtener ORDER BY
        order_by = self.sql_parser.get_order_by()
        if order_by:
            logger.info(f"🔍 ORDER BY detectado: {order_by}")
            
            # ✅ NUEVO: Verificar el tipo de datos que devuelve get_order_by()
            if isinstance(order_by, dict):
                # Si es un diccionario directo como {'edad': -1}
                result["sort"] = order_by
                logger.info(f"📊 ORDER BY aplicado como dict: {order_by}")
                
            elif isinstance(order_by, list):
                # Si es una lista de objetos con estructura [{"field": "edad", "order": "DESC"}]
                sort_dict = {}
                for order_info in order_by:
                    if isinstance(order_info, dict):
                        field = order_info.get("field")
                        direction = order_info.get("order", "ASC")
                        if field:
                            sort_dict[field] = -1 if direction.upper() == "DESC" else 1
                    elif isinstance(order_info, str):
                        # Si es un string simple, asumir ASC
                        sort_dict[order_info] = 1
                
                if sort_dict:
                    result["sort"] = sort_dict
                    logger.info(f"📊 ORDER BY aplicado como dict convertido: {sort_dict}")
            
            else:
                # Fallback: intentar convertir a string y parsear
                logger.warning(f"⚠️ Tipo inesperado para ORDER BY: {type(order_by)}, valor: {order_by}")
                try:
                    # Intentar usar directamente si es string o similar
                    result["sort"] = order_by
                except Exception as e:
                    logger.error(f"❌ Error procesando ORDER BY: {e}")
        
        # Obtener LIMIT
        limit = self.sql_parser.get_limit()
        if limit is not None:
            logger.debug(f"Traduciendo LIMIT {limit} a MongoDB")
            result["limit"] = limit
        
        # Agregar advertencias si las hay
        if self.warnings:
            result["warnings"] = self.warnings
                
        logger.debug(f"Consulta MongoDB generada: {result}")
        return result


    def _translate_select_aggregate(self):
        """
        Traduce una consulta SELECT compleja a una operación aggregate() de MongoDB.
        🆕 EXTENDIDO con soporte para DISTINCT, HAVING, funciones SQL y más.
        
        Returns:
            dict: Diccionario con la operación aggregate de MongoDB
        """
        pipeline = []
        
        # Obtener el nombre de la tabla (colección)
        collection = self.sql_parser.get_table_name()
        
        # 🆕 1. Etapa $match inicial (WHERE) - siempre primero para optimización
        where_clause = self.sql_parser.get_where_clause()
        if where_clause:
            pipeline.append({
                "$match": where_clause
            })
        
        # 🆕 2. Manejar DISTINCT si está presente
        if self.sql_parser.has_distinct():
            distinct_pipeline = self._build_distinct_pipeline()
            pipeline.extend(distinct_pipeline)
        
        # 🆕 3. Etapa $group (GROUP BY y funciones de agregación)
        group_stage = self._build_group_stage()
        if group_stage:
            pipeline.append(group_stage)
        
        # 🆕 4. Etapa $match para HAVING (después de $group)
        if self.sql_parser.has_having():
            having_clause = self.sql_parser.get_having_clause()
            if having_clause:
                pipeline.append({
                    "$match": having_clause
                })
        
        # 🆕 5. Proyección con funciones SQL
        project_stage = self._build_project_stage()
        if project_stage:
            pipeline.append(project_stage)
        
        # ✅ 6. CORREGIDO: Etapa $sort para ORDER BY
        if hasattr(self.sql_parser, 'get_order_by'):
            order_by = self.sql_parser.get_order_by()
            if order_by:
                logger.info(f"🔍 ORDER BY en aggregate detectado: {order_by}, tipo: {type(order_by)}")
                
                sort_stage = {"$sort": {}}
                
                # ✅ NUEVO: Manejar diferentes formatos de ORDER BY
                if isinstance(order_by, dict):
                    # Si ya es un diccionario como {'edad': -1, 'nombre': 1}
                    sort_stage["$sort"] = order_by
                    logger.info(f"📊 ORDER BY aplicado directamente: {order_by}")
                    
                elif isinstance(order_by, list):
                    # Si es una lista de objetos [{"field": "edad", "order": "DESC"}]
                    for order_info in order_by:
                        if isinstance(order_info, dict):
                            field = order_info.get("field")
                            direction = order_info.get("order", "ASC")
                            if field:
                                sort_stage["$sort"][field] = -1 if direction.upper() == "DESC" else 1
                        elif isinstance(order_info, str):
                            # Si es un string simple
                            sort_stage["$sort"][order_info] = 1
                    
                    logger.info(f"📊 ORDER BY procesado desde lista: {sort_stage['$sort']}")
                
                else:
                    # Fallback para otros tipos
                    logger.warning(f"⚠️ Tipo inesperado ORDER BY en aggregate: {type(order_by)}")
                    try:
                        sort_stage["$sort"] = order_by
                    except Exception as e:
                        logger.error(f"❌ Error procesando ORDER BY en aggregate: {e}")
                        sort_stage = None
                
                # Solo agregar si se configuró correctamente
                if sort_stage and sort_stage["$sort"]:
                    pipeline.append(sort_stage)
                    logger.info(f"✅ $sort agregado al pipeline: {sort_stage}")
        
        # ✅ 7. CORREGIDO: Etapa $limit para LIMIT
        if hasattr(self.sql_parser, 'get_limit'):
            limit = self.sql_parser.get_limit()
            if limit is not None:
                pipeline.append({
                    "$limit": limit
                })
                logger.info(f"📏 $limit agregado: {limit}")
        
        result = {
            "operation": "aggregate",
            "collection": collection,
            "pipeline": pipeline
        }
        
        # 🆕 Agregar advertencias si las hay
        if self.warnings:
            result["warnings"] = self.warnings
        
        logger.info(f"🏗️ Pipeline completo generado: {len(pipeline)} etapas")
        return result


    # 🆕 =================== NUEVOS MÉTODOS PARA CARACTERÍSTICAS AVANZADAS ===================
    
    def _translate_select_with_joins(self):
        """
        Traduce una consulta SELECT con JOINs usando $lookup.
        
        Returns:
            dict: Pipeline de agregación con operaciones $lookup
        """
        pipeline = []
        
        # Obtener información de JOINs
        joins = self.sql_parser.get_joins()
        join_parser = self.sql_parser._get_join_parser()
        
        if not joins or not join_parser:
            self.warnings.append("No se pudieron procesar los JOINs correctamente")
            return self._translate_select_aggregate()
        
        # Obtener tabla principal
        collection = self.sql_parser.get_table_name()
        
        # 1. $match inicial para WHERE en tabla principal
        where_clause = self.sql_parser.get_where_clause()
        if where_clause:
            pipeline.append({"$match": where_clause})
        
        # 2. Generar pipeline de JOINs
        join_pipeline = join_parser.translate_joins_to_mongodb(self.sql_parser.sql_query, joins)
        pipeline.extend(join_pipeline)
        
        # 3. Proyección final
        project_stage = self._build_project_stage_for_joins(joins)
        if project_stage:
            pipeline.append(project_stage)
        
        # 4. ORDER BY y LIMIT
        if hasattr(self.sql_parser, 'get_order_by'):
            order_by = self.sql_parser.get_order_by()
            if order_by:
                sort_stage = {"$sort": {}}
                for order_info in order_by:
                    field = order_info.get("field")
                    direction = -1 if order_info.get("order") == "DESC" else 1
                    sort_stage["$sort"][field] = direction
                pipeline.append(sort_stage)
        
        if hasattr(self.sql_parser, 'get_limit'):
            limit = self.sql_parser.get_limit()
            if limit is not None:
                pipeline.append({"$limit": limit})
        
        return {
            "operation": "aggregate",
            "collection": collection,
            "pipeline": pipeline,
            "warnings": self.warnings,
            "join_info": {
                "join_count": len(joins),
                "join_types": [j.get("type") for j in joins]
            }
        }
    
    def _translate_select_union(self):
        """
        Traduce una consulta SELECT con UNION.
        
        Returns:
            dict: Información sobre cómo manejar UNION
        """
        union_info = self.sql_parser.get_union_info()
        
        if "error" in union_info:
            raise ValueError(f"Error procesando UNION: {union_info['error']}")
        
        # UNION en MongoDB requiere $unionWith (4.4+) o queries separadas
        return {
            "operation": "union",
            "collection": self.sql_parser.get_table_name(),
            "union_type": "union_all" if union_info.get("union_all") else "union",
            "queries": union_info.get("queries", []),
            "warnings": self.warnings + [
                "UNION requiere MongoDB 4.4+ con $unionWith",
                "Alternativamente, ejecutar queries separadas y unir resultados"
            ],
            "mongodb_version_required": "4.4+",
            "alternative_strategy": "separate_queries"
        }
    
    def _build_distinct_pipeline(self):
        """
        Construye pipeline para SELECT DISTINCT.
        
        Returns:
            list: Etapas del pipeline para DISTINCT
        """
        advanced_parser = self.sql_parser._get_advanced_parser()
        if not advanced_parser:
            return []
        
        return advanced_parser.translate_distinct_to_mongodb(self.sql_parser.sql_query)
    

    def _build_group_stage(self):
        """
        ✅ CORREGIDO: Construye la etapa $group del pipeline para agregaciones.
        """
        group_stage = None
        
        # Verificar si hay funciones de agregación
        functions = self.sql_parser.get_functions()
        aggregate_functions = []
        
        if functions:
            aggregate_function_names = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP_CONCAT']
            aggregate_functions = [f for f in functions if f.get('function_name', '').upper() in aggregate_function_names]
        
        if aggregate_functions:
            # Crear etapa $group
            group_stage = {"$group": {"_id": None}}  # Sin agrupación, solo agregación
            
            for func in aggregate_functions:
                func_name = func.get('function_name', '').upper()
                args = func.get('args', '')
                alias = func.get('alias', f"{func_name.lower()}_result")
                
                logger.info(f"🔢 Procesando {func_name}({args}) -> {alias}")
                
                if func_name == 'COUNT':
                    if args.strip() == '*':
                        # COUNT(*) - contar todos los documentos
                        group_stage["$group"][alias] = {"$sum": 1}
                        logger.info(f"✅ COUNT(*) configurado como $sum: 1")
                    else:
                        # COUNT(campo) - contar valores no nulos
                        field_name = args.strip()
                        group_stage["$group"][alias] = {
                            "$sum": {"$cond": [{"$ne": [f"${field_name}", None]}, 1, 0]}
                        }
                        logger.info(f"✅ COUNT({field_name}) configurado")
                
                elif func_name == 'SUM':
                    field_name = args.strip()
                    group_stage["$group"][alias] = {"$sum": f"${field_name}"}
                    
                elif func_name == 'AVG':
                    field_name = args.strip()
                    group_stage["$group"][alias] = {"$avg": f"${field_name}"}
                    
                elif func_name in ['MIN', 'MAX']:
                    field_name = args.strip()
                    group_stage["$group"][alias] = {f"${func_name.lower()}": f"${field_name}"}
            
            logger.info(f"📊 Etapa $group generada: {group_stage}")
        
        return group_stage


    def _build_project_stage(self):
        """
        ✅ CORREGIDO: Construye la etapa $project para agregaciones.
        """
        functions = self.sql_parser.get_functions()
        aggregate_functions = []
        
        if functions:
            aggregate_function_names = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP_CONCAT']
            aggregate_functions = [f for f in functions if f.get('function_name', '').upper() in aggregate_function_names]
        
        if aggregate_functions:
            project_stage = {"$project": {"_id": 0}}  # Ocultar _id
            
            for func in aggregate_functions:
                alias = func.get('alias', f"{func.get('function_name', '').lower()}_result")
                project_stage["$project"][alias] = 1
                logger.info(f"📋 Proyectando agregación: {alias}")
            
            return project_stage
        
        return None


    def _build_project_stage_for_joins(self, joins):
        """
        Construye proyección específica para consultas con JOINs.
        
        Args:
            joins (list): Lista de información de JOINs
            
        Returns:
            dict: Etapa $project para JOINs
        """
        select_fields = self.sql_parser.get_select_fields()
        
        if not select_fields or any(f.get("field") == "*" for f in select_fields):
            # Para SELECT *, incluir campos principales y de JOINs
            project_stage = {"$project": {}}
            
            # Incluir campos de la tabla principal
            main_table = self.sql_parser.get_table_name()
            for field in ["_id"]:  # Incluir campos básicos
                project_stage["$project"][field] = 1
            
            # Incluir campos de tablas joinadas
            for join in joins:
                join_alias = join.get("alias", join.get("table"))
                project_stage["$project"][f"{join_alias}_data"] = f"${join_alias}_joined"
            
            return project_stage
        
        # Proyección específica de campos
        project_stage = {"$project": {"_id": 0}}
        
        for field_info in select_fields:
            field = field_info.get("field")
            alias = field_info.get("alias", field)
            
            # Determinar si el campo pertenece a tabla principal o JOIN
            if "." in field:
                # Campo con prefijo de tabla (ej: u.name)
                table_prefix, field_name = field.split(".", 1)
                
                # Buscar en JOINs
                for join in joins:
                    if join.get("alias") == table_prefix:
                        project_stage["$project"][alias] = f"${join['alias']}_joined.{field_name}"
                        break
                else:
                    # Campo de tabla principal
                    project_stage["$project"][alias] = f"${field_name}"
            else:
                # Campo sin prefijo - asumir tabla principal
                project_stage["$project"][alias] = f"${field}"
        
        return project_stage
    
    def _has_sql_functions_in_field(self, field):
        """
        Verifica si un campo contiene funciones SQL.
        
        Args:
            field (str): Campo a verificar
            
        Returns:
            bool: True si contiene funciones SQL
        """
        function_parser = self.sql_parser._get_function_parser()
        if function_parser:
            return function_parser.has_functions(field)
        
        # Fallback: verificación básica
        sql_functions = ["UPPER", "LOWER", "LENGTH", "CONCAT", "YEAR", "MONTH", "DAY", "NOW", "COUNT", "SUM", "AVG", "MIN", "MAX"]
        field_upper = field.upper()
        return any(f"{func}(" in field_upper for func in sql_functions)
    
    # =================== MÉTODOS EXISTENTES (sin cambios) ===================
    
    def translate_insert(self):
        """
        Traduce una consulta INSERT a operaciones de MongoDB.
        🔧 CORREGIDO: Soporte completo para INSERT múltiple
        
        Returns:
            dict: Diccionario con la operación MongoDB
        """
        # Obtener el nombre de la tabla (colección)
        collection = self.sql_parser.get_table_name()
        
        # Obtener los valores a insertar usando crud_parser
        insert_values = self.sql_parser.get_insert_values()
        
        if not insert_values:
            raise ValueError("No se pudieron extraer valores para insertar")
        
        logger.info(f"Datos de inserción recibidos: {insert_values}")
        
        # 🔧 NUEVO: Manejar INSERT_MANY vs INSERT simple
        operation_type = insert_values.get("operation")
        
        if operation_type == "INSERT_MANY":
            # Múltiples documentos
            documents = insert_values.get("documents", [])
            
            if not documents:
                raise ValueError("No se encontraron documentos para insertar")
            
            logger.info(f"INSERT múltiple: {len(documents)} documentos")
            
            return {
                "operation": "INSERT_MANY",
                "collection": collection,
                "documents": documents
            }
        
        else:
            # Un solo documento (comportamiento original)
            document = insert_values.get("values", {})
            
            if not document:
                raise ValueError("No se encontraron valores para insertar")
            
            logger.info(f"INSERT simple: 1 documento")
            
            return {
                "operation": "insert",
                "collection": collection,
                "document": document
            }


    def translate_update(self):
        """
        Traduce una consulta UPDATE a operaciones de MongoDB.
        
        Returns:
            dict: Diccionario con la operación MongoDB
        """
        # Obtener el nombre de la tabla (colección)
        collection = self.sql_parser.get_table_name()
        
        # Obtener valores a actualizar
        update_values = self.sql_parser.get_update_values()
        
        # Obtener condición WHERE
        where_clause = self.sql_parser.get_where_clause()
        
        if not update_values:
            raise ValueError("No se pudieron extraer valores para actualizar")
        
        return {
            "operation": "update",
            "collection": collection,
            "query": {
                "query": where_clause or {},
                "update": {"$set": update_values["values"]}
            }
        }

    def translate_delete(self):
        """
        Traduce una consulta DELETE a operaciones de MongoDB.
        
        Returns:
            dict: Diccionario con la operación MongoDB
        """
        # Obtener el nombre de la tabla (colección)
        collection = self.sql_parser.get_table_name()
        
        # Obtener condición WHERE
        where_clause = self.sql_parser.get_where_clause()
        
        return {
            "operation": "delete",
            "collection": collection,
            "query": where_clause or {}
        }
    

    def translate_create_table(self):
        """
        Traduce una consulta CREATE TABLE a operaciones de MongoDB con esquema.
        🔧 CORREGIDO: Usar 'table_name' en lugar de 'table'
        
        Returns:
            dict: Diccionario con la operación MongoDB y esquema
        """
        # Obtener información detallada de CREATE TABLE
        create_info = self.sql_parser.get_create_table_info()
        
        if not create_info:
            # Fallback al método anterior si no hay DDL parser
            collection = self.sql_parser.get_table_name()
            if not collection:
                raise ValueError("No se pudo determinar el nombre de la colección")
            
            return {
                "operation": "create_collection",
                "collection": collection,
                "options": {}
            }
        
        # 🔧 CORRECCIÓN CRÍTICA: Usar 'table_name' en lugar de 'table'
        collection = create_info["table_name"]  # ← CAMBIO AQUÍ
        columns = create_info["columns"]
        constraints = create_info["constraints"]
        schema = create_info.get("schema")  # Usar get() por seguridad
        
        logger.info(f"Creando colección '{collection}' con {len(columns)} columnas")
        
        # Construir opciones de MongoDB
        options = {}
        
        # 1. Agregar validación de esquema si hay columnas definidas
        if columns and schema:
            options["validator"] = schema
            options["validationLevel"] = "moderate"  # moderate|strict|off
            options["validationAction"] = "warn"     # warn|error
            logger.info("Schema de validación agregado")
        
        # 2. Agregar información de índices
        indexes_to_create = []
        
        # Índice para PRIMARY KEY
        if constraints.get("primary_keys"):
            pk_index = {
                "key": {field: 1 for field in constraints["primary_keys"]},
                "unique": True,
                "name": "primary_key_index"
            }
            indexes_to_create.append(pk_index)
            logger.info(f"Índice PRIMARY KEY: {constraints['primary_keys']}")
        
        # Índices para campos UNIQUE
        for i, column in enumerate(columns):
            if column.get("unique", False):
                unique_index = {
                    "key": {column["name"]: 1},
                    "unique": True,
                    "name": f"unique_{column['name']}_index"
                }
                indexes_to_create.append(unique_index)
        
        # 3. Crear documento de ejemplo con valores por defecto
        sample_document = {}
        for column in columns:
            col_name = column["name"]
            
            if "default" in column and column["default"] is not None:
                sample_document[col_name] = column["default"]
            elif not column.get("nullable", True):  # NOT NULL
                # Valores por defecto según tipo para campos NOT NULL
                mongo_type = column.get("mongo_type", {}).get("type", "string")
                if mongo_type == "number":
                    sample_document[col_name] = 0
                elif mongo_type == "string":
                    sample_document[col_name] = ""
                elif mongo_type == "boolean":
                    sample_document[col_name] = False
                else:
                    sample_document[col_name] = None
        
        result = {
            "operation": "create_collection_with_schema",
            "collection": collection,
            "options": options,
            "schema_info": {
                "columns": columns,
                "constraints": constraints,
                "total_columns": len(columns),
                "required_fields": [col["name"] for col in columns if not col.get("nullable", True)],
                "primary_keys": constraints.get("primary_keys", []),
                "foreign_keys": constraints.get("foreign_keys", [])
            },
            "indexes_to_create": indexes_to_create,
            "sample_document": sample_document if sample_document else None
        }
        
        # Agregar advertencias si las hay
        warnings = []
        
        if constraints.get("foreign_keys"):
            warnings.append("Foreign keys detectadas - MongoDB no las soporta nativamente")
            warnings.append("Considera implementar referencias manuales o usar $lookup")
        
        if any(col.get("auto_increment", False) for col in columns):
            warnings.append("AUTO_INCREMENT detectado - usar ObjectId o secuencias manuales")
        
        if warnings:
            result["warnings"] = warnings
            self.warnings.extend(warnings)
        
        logger.info(f"Traducción CREATE TABLE completada: {len(columns)} columnas, {len(indexes_to_create)} índices")
        return result

    def translate_drop_table(self):
        """
        Traduce una consulta DROP TABLE a operaciones de MongoDB.
        
        Returns:
            dict: Diccionario con la operación MongoDB
        """
        # Obtener el nombre de la tabla (colección)
        collection = self.sql_parser.get_table_name()
        
        if not collection:
            raise ValueError("No se pudo determinar el nombre de la colección")
        
        return {
            "operation": "drop_collection",
            "collection": collection
        }
    
    # 🆕 =================== NUEVOS MÉTODOS UTILITARIOS ===================
    
    def get_translation_warnings(self):
        """
        Obtiene las advertencias generadas durante la traducción.
        
        Returns:
            list: Lista de advertencias
        """
        return self.warnings.copy()
    
    def get_translation_info(self):
        """
        Obtiene información detallada sobre la traducción realizada.
        
        Returns:
            dict: Información de la traducción
        """
        if not self.sql_parser:
            return {}
        
        features = self.sql_parser.get_all_features_used()
        complexity = self.sql_parser.analyze_query_complexity()
        
        return {
            "query_type": self.sql_parser.get_query_type(),
            "collection": self.sql_parser.get_table_name(),
            "complexity": complexity,
            "features_used": features,
            "warnings": self.warnings,
            "supports_find_optimization": not any([
                features["advanced_features"]["has_distinct"],
                features["advanced_features"]["has_having"],
                features["joins"]["has_joins"],
                features["functions"]["has_functions"]
            ])
        }
    
    def validate_translation_feasibility(self):
        """
        Valida si la traducción es factible y eficiente.
        
        Returns:
            dict: Resultado de validación
        """
        issues = []
        warnings = []
        
        if not self.sql_parser:
            issues.append("No hay parser SQL disponible")
            return {"is_feasible": False, "issues": issues, "warnings": warnings}
        
        # Verificar características problemáticas
        if self.sql_parser.has_union():
            warnings.append("UNION requiere MongoDB 4.4+ o queries separadas")
        
        if self.sql_parser.has_subquery():
            warnings.append("Subqueries pueden requerir múltiples queries o reestructuración")
        
        if self.sql_parser.has_joins():
            joins = self.sql_parser.get_joins()
            if len(joins) > 3:
                warnings.append("Múltiples JOINs pueden afectar significativamente el rendimiento")
            
            # Verificar JOINs problemáticos
            for join in joins:
                if join.get("type") in ["right", "full"]:
                    warnings.append(f"JOIN tipo {join['type']} requiere optimización especial")
        
        complexity = self.sql_parser.analyze_query_complexity()
        if complexity["complexity_level"] == "complex":
            warnings.append("Consulta compleja - considerar optimización y testing de rendimiento")
        
        return {
            "is_feasible": len(issues) == 0,
            "complexity_level": complexity["complexity_level"],
            "issues": issues,
            "warnings": warnings,
            "recommendation": self._get_optimization_recommendation(complexity, warnings)
        }
    
    def _get_optimization_recommendation(self, complexity, warnings):
        """
        Genera recomendaciones de optimización.
        
        Args:
            complexity (dict): Información de complejidad
            warnings (list): Lista de advertencias
            
        Returns:
            str: Recomendación de optimización
        """
        if complexity["complexity_level"] == "simple":
            return "Consulta óptima para MongoDB"
        elif complexity["complexity_level"] == "moderate":
            return "Consulta traducible con buen rendimiento esperado"
        else:
            recommendations = [
                "Considerar desnormalización de datos",
                "Verificar índices en campos de filtro y JOIN",
                "Testing de rendimiento con datos reales recomendado"
            ]
            
            if len(warnings) > 2:
                recommendations.append("Evaluar división en múltiples queries más simples")
            
            return "; ".join(recommendations)
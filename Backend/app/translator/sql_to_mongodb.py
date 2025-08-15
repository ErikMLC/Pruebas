import logging
import re as regex
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
        
        logger.info(f"Características detectadas - Agregaciones: {has_aggregate}, GROUP BY: {has_group_by}, ORDER BY: {has_order_by}")
        
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
        🔧 CORREGIDO: Detecta funciones de transformación y redirige a aggregate
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
        
        # 🔧 CRÍTICO: Verificar TODAS las funciones ANTES de procesar campos
        if isinstance(select_fields, list):
            for field_info in select_fields:
                if isinstance(field_info, dict) and "field" in field_info:
                    field = field_info["field"]
                    field_upper = field.upper().strip()
                    
                    # 🆕 DETECTAR cualquier función SQL
                    sql_functions = [
                        "COUNT(", "SUM(", "AVG(", "MIN(", "MAX(",  # Agregación
                        "LENGTH(", "UPPER(", "LOWER(", "CONCAT(",  # Transformación
                        "YEAR(", "MONTH(", "DAY(",                 # Fecha
                        "SUBSTRING(", "SUBSTR(", "TRIM("           # String
                    ]
                    
                    if any(func in field_upper for func in sql_functions):
                        logger.info(f" Función SQL detectada en '{field}' - redirigiendo a aggregate")
                        return self._translate_select_aggregate()
        
        # Si llegamos aquí, es una consulta simple sin funciones
        # Continuar con el procesamiento normal de find()
        if isinstance(select_fields, list):
            if not any(isinstance(field, dict) and field.get("field") == "*" for field in select_fields):
                projection = {}
                
                for field_info in select_fields:
                    if isinstance(field_info, dict) and "field" in field_info:
                        field = field_info["field"]
                        alias = field_info.get("alias", field)
                        projection[alias] = 1
                
                if projection:
                    result["projection"] = projection
        
        # ORDER BY, LIMIT, etc. (mantener código existente)
        order_by = self.sql_parser.get_order_by()
        if order_by:
            result["sort"] = order_by
        
        limit = self.sql_parser.get_limit()
        if limit is not None:
            result["limit"] = limit
        
        if self.warnings:
            result["warnings"] = self.warnings
                
        logger.debug(f"Consulta MongoDB generada: {result}")
        return result


    def _translate_select_aggregate(self):
        """
        Traduce una consulta SELECT compleja a una operación aggregate() de MongoDB.
        🔧 CORREGIDO: Convierte campos numéricos almacenados como string antes de ORDER BY
        
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
        
        # 🔧 NUEVO: 2. Detectar si ORDER BY usa campos que podrían ser numéricos almacenados como string
        order_by = None
        if hasattr(self.sql_parser, 'get_order_by'):
            order_by = self.sql_parser.get_order_by()
        
        needs_numeric_conversion = False
        if order_by:
            # Lista de campos que suelen ser numéricos pero pueden estar como string
            numeric_fields = ['salario', 'precio', 'cantidad', 'edad', 'id', 'numero', 'monto', 'total']
            
            for field_name in order_by.keys():
                if any(numeric_field in field_name.lower() for numeric_field in numeric_fields):
                    needs_numeric_conversion = True
                    logger.info(f" Campo numérico detectado para ORDER BY: {field_name}")
                    break
        
        # 🔧 NUEVO: 2.5. Agregar conversión de tipos si es necesario para ORDER BY
        if needs_numeric_conversion and order_by:
            conversion_stage = {"$addFields": {}}
            
            for field_name in order_by.keys():
                numeric_fields = ['salario', 'precio', 'cantidad', 'edad', 'id', 'numero', 'monto', 'total']
                if any(numeric_field in field_name.lower() for numeric_field in numeric_fields):
                    # Crear campo temporal numérico para ordenamiento
                    conversion_stage["$addFields"][f"{field_name}_numeric"] = {
                        "$convert": {
                            "input": f"${field_name}",
                            "to": "double",
                            "onError": 0,  # Si falla la conversión, usar 0
                            "onNull": 0    # Si es null, usar 0
                        }
                    }
                    logger.info(f" Conversión agregada: {field_name} -> {field_name}_numeric")
            
            if conversion_stage["$addFields"]:
                pipeline.append(conversion_stage)
        
        # 🆕 3. Manejar DISTINCT si está presente
        if self.sql_parser.has_distinct():
            distinct_pipeline = self._build_distinct_pipeline()
            pipeline.extend(distinct_pipeline)
        
        # 🆕 4. Etapa $group (GROUP BY y funciones de agregación)
        group_stage = self._build_group_stage()
        if group_stage:
            pipeline.append(group_stage)
        
        # 🆕 5. Etapa $match para HAVING (después de $group)
        if self.sql_parser.has_having():
            having_clause = self.sql_parser.get_having_clause()
            if having_clause:
                pipeline.append({
                    "$match": having_clause
                })
        
        # 🆕 6. Proyección con funciones SQL
        project_stage = self._build_project_stage()
        if project_stage:
            pipeline.append(project_stage)
        
        # ✅ 7. CORREGIDO: Etapa $sort para ORDER BY con conversión numérica
        if order_by:
            logger.info(f" ORDER BY en aggregate detectado: {order_by}, tipo: {type(order_by)}")
            
            sort_stage = {"$sort": {}}
            
            # ✅ NUEVO: Manejar diferentes formatos de ORDER BY
            if isinstance(order_by, dict):
                # Si ya es un diccionario como {'salario': -1}
                for field_name, direction in order_by.items():
                    # 🔧 CLAVE: Usar campo convertido si existe
                    if needs_numeric_conversion:
                        numeric_fields = ['salario', 'precio', 'cantidad', 'edad', 'id', 'numero', 'monto', 'total']
                        if any(numeric_field in field_name.lower() for numeric_field in numeric_fields):
                            sort_field = f"{field_name}_numeric"
                            logger.info(f" Usando campo convertido para ORDER BY: {sort_field}")
                        else:
                            sort_field = field_name
                    else:
                        sort_field = field_name
                    
                    sort_stage["$sort"][sort_field] = direction
                
                logger.info(f" ORDER BY aplicado: {sort_stage['$sort']}")
                
            elif isinstance(order_by, list):
                # Si es una lista de objetos [{"field": "salario", "order": "DESC"}]
                for order_info in order_by:
                    if isinstance(order_info, dict):
                        field = order_info.get("field")
                        direction = order_info.get("order", "ASC")
                        if field:
                            # Usar campo convertido si es necesario
                            if needs_numeric_conversion:
                                numeric_fields = ['salario', 'precio', 'cantidad', 'edad', 'id', 'numero', 'monto', 'total']
                                if any(numeric_field in field.lower() for numeric_field in numeric_fields):
                                    sort_field = f"{field}_numeric"
                                else:
                                    sort_field = field
                            else:
                                sort_field = field
                            
                            sort_stage["$sort"][sort_field] = -1 if direction.upper() == "DESC" else 1
                    elif isinstance(order_info, str):
                        # Si es un string simple
                        sort_stage["$sort"][order_info] = 1
                
                logger.info(f" ORDER BY procesado desde lista: {sort_stage['$sort']}")
            
            # Solo agregar si se configuró correctamente
            if sort_stage["$sort"]:
                pipeline.append(sort_stage)
                logger.info(f" $sort agregado al pipeline: {sort_stage}")
        
        # 🔧 NUEVO: 7.5. Limpiar campos temporales de conversión si se agregaron
        if needs_numeric_conversion and order_by:
            cleanup_stage = {"$unset": []}
            
            for field_name in order_by.keys():
                numeric_fields = ['salario', 'precio', 'cantidad', 'edad', 'id', 'numero', 'monto', 'total']
                if any(numeric_field in field_name.lower() for numeric_field in numeric_fields):
                    cleanup_stage["$unset"].append(f"{field_name}_numeric")
            
            if cleanup_stage["$unset"]:
                pipeline.append(cleanup_stage)
                logger.info(f" Limpiando campos temporales: {cleanup_stage['$unset']}")
        
        # ✅ 8. CORREGIDO: Etapa $limit para LIMIT
        if hasattr(self.sql_parser, 'get_limit'):
            limit = self.sql_parser.get_limit()
            if limit is not None:
                pipeline.append({
                    "$limit": limit
                })
                logger.info(f" $limit agregado: {limit}")
        
        result = {
            "operation": "aggregate",
            "collection": collection,
            "pipeline": pipeline
        }
        
        # 🆕 Agregar advertencias si las hay
        if self.warnings:
            result["warnings"] = self.warnings
        
        logger.info(f" Pipeline completo generado: {len(pipeline)} etapas")
        return result

    
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
        Maneja correctamente SUM con operaciones matemáticas como precio * stock.
        """
        group_stage = None
        
        # Obtener campos SELECT para detectar funciones
        select_fields = self.sql_parser.get_select_fields()
        
        if not select_fields:
            return None
        
        # Buscar funciones de agregación en los campos SELECT
        has_aggregation = False
        
        for field_info in select_fields:
            if isinstance(field_info, dict) and "field" in field_info:
                field = field_info["field"].upper().strip()
                
                # Detectar cualquier función de agregación
                agg_functions = ["COUNT(", "SUM(", "AVG(", "MIN(", "MAX("]
                if any(func in field for func in agg_functions):
                    has_aggregation = True
                    break
        
        if has_aggregation:
            # Crear etapa $group
            group_stage = {"$group": {"_id": None}}  # Sin agrupación, solo agregación
            
            for field_info in select_fields:
                if isinstance(field_info, dict) and "field" in field_info:
                    field = field_info["field"]
                    field_upper = field.upper().strip()
                    alias = field_info.get("alias", field)
                    
                    logger.info(f" Procesando campo de agregación: {field}")
                    
                    # 🔧 COUNT(*) - Conteo total
                    if field_upper == "COUNT(*)":
                        group_field_name = alias if alias != field else "count_all"
                        group_stage["$group"][group_field_name] = {"$sum": 1}
                        logger.info(f" COUNT(*) configurado: {group_field_name}")
                    
                    # 🔧 COUNT(DISTINCT campo) - Conteo de valores únicos
                    elif "COUNT(DISTINCT " in field_upper:
                        match = regex.search(r'COUNT\s*\(\s*DISTINCT\s+([^)]+)\s*\)', field, regex.IGNORECASE)
                        if match:
                            distinct_field = match.group(1).strip()
                            group_field_name = alias if alias != field else f"count_distinct_{distinct_field}"
                            
                            # Para COUNT DISTINCT, usar $addToSet seguido de $size
                            group_stage["$group"][f"{group_field_name}_set"] = {"$addToSet": f"${distinct_field}"}
                            logger.info(f" COUNT(DISTINCT {distinct_field}) configurado: {group_field_name}")
                    
                    # 🔧 COUNT(campo) - Conteo con condición
                    elif "COUNT(" in field_upper:
                        match = regex.search(r'COUNT\s*\(\s*([^)]+)\s*\)', field, regex.IGNORECASE)
                        if match:
                            inner_field = match.group(1).strip()
                            group_field_name = alias if alias != field else f"count_{inner_field}"
                            if inner_field != "*":
                                group_stage["$group"][group_field_name] = {
                                    "$sum": {"$cond": [{"$ne": [f"${inner_field}", None]}, 1, 0]}
                                }
                            else:
                                group_stage["$group"][group_field_name] = {"$sum": 1}
                            logger.info(f" COUNT({inner_field}) configurado: {group_field_name}")
                    
                    # 🔧 SUM(campo) - CORREGIDO PARA OPERACIONES MATEMÁTICAS
                    elif "SUM(" in field_upper:
                        match = regex.search(r'SUM\s*\(\s*([^)]+)\s*\)', field, regex.IGNORECASE)
                        if match:
                            inner_expression = match.group(1).strip()
                            group_field_name = alias if alias != field else f"sum_{inner_expression.replace(' ', '_').replace('*', '_mult_')}"
                            
                            logger.info(f" Analizando expresión SUM: '{inner_expression}'")
                            
                            # 🔧 CRÍTICO: Detectar multiplicación precio * stock
                            if '*' in inner_expression:
                                parts = [p.strip() for p in inner_expression.split('*')]
                                if len(parts) == 2:
                                    field1 = parts[0]
                                    field2 = parts[1]
                                    
                                    # Convertir a números si es necesario y multiplicar
                                    group_stage["$group"][group_field_name] = {
                                        "$sum": {
                                            "$multiply": [
                                                {"$toDouble": f"${field1}"},
                                                {"$toDouble": f"${field2}"}
                                            ]
                                        }
                                    }
                                    logger.info(f" SUM con multiplicación: {field1} * {field2} -> {group_field_name}")
                                else:
                                    # Más de 2 campos - manejo básico
                                    group_stage["$group"][group_field_name] = {"$sum": f"${inner_expression}"}
                                    logger.warning(f" Multiplicación compleja: {inner_expression}")
                            
                            # 🔧 Detectar suma: campo1 + campo2
                            elif '+' in inner_expression:
                                parts = [p.strip() for p in inner_expression.split('+')]
                                if len(parts) == 2:
                                    field1 = parts[0]
                                    field2 = parts[1]
                                    group_stage["$group"][group_field_name] = {
                                        "$sum": {
                                            "$add": [
                                                {"$toDouble": f"${field1}"},
                                                {"$toDouble": f"${field2}"}
                                            ]
                                        }
                                    }
                                    logger.info(f" SUM con suma: {field1} + {field2} -> {group_field_name}")
                                else:
                                    group_stage["$group"][group_field_name] = {"$sum": f"${inner_expression}"}
                            
                            # 🔧 Detectar resta: campo1 - campo2
                            elif '-' in inner_expression:
                                parts = [p.strip() for p in inner_expression.split('-')]
                                if len(parts) == 2:
                                    field1 = parts[0]
                                    field2 = parts[1]
                                    group_stage["$group"][group_field_name] = {
                                        "$sum": {
                                            "$subtract": [
                                                {"$toDouble": f"${field1}"},
                                                {"$toDouble": f"${field2}"}
                                            ]
                                        }
                                    }
                                    logger.info(f" SUM con resta: {field1} - {field2} -> {group_field_name}")
                                else:
                                    group_stage["$group"][group_field_name] = {"$sum": f"${inner_expression}"}
                            
                            else:
                                # SUM(campo) simple sin operaciones
                                if inner_expression != "*":
                                    # Convertir a número por si acaso
                                    group_stage["$group"][group_field_name] = {
                                        "$sum": {"$toDouble": f"${inner_expression}"}
                                    }
                                else:
                                    group_stage["$group"][group_field_name] = {"$sum": 1}
                                logger.info(f" SUM simple: {inner_expression} -> {group_field_name}")
                    
                    # 🔧 AVG(campo)
                    elif "AVG(" in field_upper:
                        match = regex.search(r'AVG\s*\(\s*([^)]+)\s*\)', field, regex.IGNORECASE)
                        if match:
                            inner_field = match.group(1).strip()
                            group_field_name = alias if alias != field else f"avg_{inner_field}"
                            # Convertir a número para promedio
                            group_stage["$group"][group_field_name] = {
                                "$avg": {"$toDouble": f"${inner_field}"}
                            }
                            logger.info(f" AVG({inner_field}) configurado: {group_field_name}")
                    
                    # 🔧 MIN(campo)
                    elif "MIN(" in field_upper:
                        match = regex.search(r'MIN\s*\(\s*([^)]+)\s*\)', field, regex.IGNORECASE)
                        if match:
                            inner_field = match.group(1).strip()
                            group_field_name = alias if alias != field else f"min_{inner_field}"
                            # Convertir a número para comparación
                            group_stage["$group"][group_field_name] = {
                                "$min": {"$toDouble": f"${inner_field}"}
                            }
                            logger.info(f" MIN({inner_field}) configurado: {group_field_name}")
                    
                    # 🔧 MAX(campo)
                    elif "MAX(" in field_upper:
                        match = regex.search(r'MAX\s*\(\s*([^)]+)\s*\)', field, regex.IGNORECASE)
                        if match:
                            inner_field = match.group(1).strip()
                            group_field_name = alias if alias != field else f"max_{inner_field}"
                            # Convertir a número para comparación
                            group_stage["$group"][group_field_name] = {
                                "$max": {"$toDouble": f"${inner_field}"}
                            }
                            logger.info(f" MAX({inner_field}) configurado: {group_field_name}")
            
            logger.info(f" Etapa $group con múltiples agregaciones generada: {group_stage}")
        
        return group_stage

    def _build_project_stage(self):
        """
        ✅ ACTUALIZADO: Maneja proyección de múltiples agregaciones y COUNT DISTINCT.
        """
        select_fields = self.sql_parser.get_select_fields()
        
        if not select_fields:
            return None
        
        # Verificar si hay funciones de transformación o agregación
        has_transformation_functions = False
        has_aggregation_functions = False
        
        for field_info in select_fields:
            if isinstance(field_info, dict) and "field" in field_info:
                field = field_info["field"].upper().strip()
                
                # Funciones de transformación
                transformation_funcs = ["CONCAT(", "LENGTH(", "UPPER(", "LOWER(", "SUBSTRING(", "YEAR(", "MONTH(", "DAY("]
                if any(func in field for func in transformation_funcs):
                    has_transformation_functions = True
                
                # Funciones de agregación
                aggregation_funcs = ["COUNT(", "SUM(", "AVG(", "MIN(", "MAX("]
                if any(func in field for func in aggregation_funcs):
                    has_aggregation_functions = True
        
        # Solo crear $project si hay funciones de transformación O si hay agregaciones
        if has_transformation_functions or has_aggregation_functions:
            project_stage = {"$project": {"_id": 0}}  # Ocultar _id por defecto
            
            for field_info in select_fields:
                if isinstance(field_info, dict) and "field" in field_info:
                    field = field_info["field"]
                    field_upper = field.upper().strip()
                    alias = field_info.get("alias", field)
                    
                    logger.info(f" Procesando campo de proyección: '{field}' con alias: '{alias}'")
                    
                    # 🔧 COUNT(DISTINCT campo) - Proyección especial
                    if "COUNT(DISTINCT " in field_upper:
                        match = regex.search(r'COUNT\s*\(\s*DISTINCT\s+([^)]+)\s*\)', field, regex.IGNORECASE)
                        if match:
                            distinct_field = match.group(1).strip()
                            group_field_name = alias if alias != field else f"count_distinct_{distinct_field}"
                            
                            # Proyectar el tamaño del set creado en $group
                            project_stage["$project"][alias] = {"$size": f"${group_field_name}_set"}
                            logger.info(f" COUNT(DISTINCT) proyectado: {alias} = $size(${group_field_name}_set)")
                    
                    # 🔧 COUNT(*) y otras agregaciones simples
                    elif field_upper == "COUNT(*)":
                        group_field_name = alias if alias != field else "count_all"
                        project_stage["$project"][alias] = f"${group_field_name}"
                        logger.info(f" COUNT(*) proyectado: {alias} = ${group_field_name}")
                    
                    elif any(func in field_upper for func in ["COUNT(", "SUM(", "AVG(", "MIN(", "MAX("]):
                        # Usar el alias como nombre del campo en $group
                        group_field_name = alias if alias != field else alias
                        project_stage["$project"][alias] = f"${group_field_name}"
                        logger.info(f" Función de agregación proyectada: {alias} = ${group_field_name}")
                    
                    # 🔧 FUNCIONES DE TRANSFORMACIÓN (sin cambios del código anterior)
                    elif "UPPER(" in field_upper:
                        match = regex.search(r'UPPER\s*\(\s*([^)]+)\s*\)', field, regex.IGNORECASE)
                        if match:
                            inner_field = match.group(1).strip()
                            project_stage["$project"][alias] = {"$toUpper": f"${inner_field}"}
                            logger.info(f" UPPER({inner_field}) traducido a $toUpper")
                    
                    elif "LOWER(" in field_upper:
                        match = regex.search(r'LOWER\s*\(\s*([^)]+)\s*\)', field, regex.IGNORECASE)
                        if match:
                            inner_field = match.group(1).strip()
                            project_stage["$project"][alias] = {"$toLower": f"${inner_field}"}
                            logger.info(f" LOWER({inner_field}) traducido a $toLower")
                    
                    elif "LENGTH(" in field_upper:
                        match = regex.search(r'LENGTH\s*\(\s*([^)]+)\s*\)', field, regex.IGNORECASE)
                        if match:
                            inner_field = match.group(1).strip()
                            project_stage["$project"][alias] = {"$strLenCP": f"${inner_field}"}
                            logger.info(f" LENGTH({inner_field}) traducido a $strLenCP")
                    
                    elif "CONCAT(" in field_upper:
                        concat_expression = self._translate_concat_function(field)
                        if concat_expression:
                            project_stage["$project"][alias] = concat_expression
                            logger.info(f" CONCAT traducido: {alias} = {concat_expression}")
                        else:
                            project_stage["$project"][alias] = f"${field}"
                            logger.warning(f" CONCAT fallback para: {field}")
                    
                    else:
                        # Campo normal sin función
                        project_stage["$project"][alias] = f"${field}"
                        logger.info(f"Campo normal: {field}")
            
            logger.info(f" Etapa $project generada: {project_stage}")
            return project_stage
        
        return None


    def _translate_concat_function(self, field):
        """
        ✅ CORREGIDO: Traduce la función CONCAT a sintaxis MongoDB.
        Maneja correctamente literales, campos y funciones anidadas.
        
        Args:
            field (str): Campo con función CONCAT, ej: "CONCAT(nombre, ' ', apellido)"
            
        Returns:
            dict: Expresión MongoDB para $concat
        """
        try:
            # Extraer contenido entre paréntesis de CONCAT
            match = regex.search(r'CONCAT\s*\(\s*(.*)\s*\)', field, regex.IGNORECASE)
            if not match:
                logger.error(f"No se pudo extraer contenido de CONCAT: {field}")
                return None
            
            # Obtener argumentos de CONCAT
            args_str = match.group(1).strip()
            logger.info(f"Argumentos de CONCAT extraídos: '{args_str}'")
            
            # Dividir argumentos respetando comillas
            args = self._parse_concat_arguments(args_str)
            logger.info(f"Argumentos parseados: {args}")
            
            if not args:
                logger.error("No se pudieron parsear argumentos de CONCAT")
                return None
            
            # Convertir argumentos a formato MongoDB
            mongo_args = []
            for arg in args:
                arg = arg.strip()
                
                # CRÍTICO: Detectar literales entre comillas
                if (arg.startswith("'") and arg.endswith("'")) or (arg.startswith('"') and arg.endswith('"')):
                    literal = arg[1:-1]  # Quitar comillas externas
                    mongo_args.append(literal)  # Agregar SOLO el literal, SIN $
                    logger.info(f"   Literal: '{literal}'")
                
                # NUEVO: Detectar funciones anidadas como UPPER()
                elif "UPPER(" in arg.upper():
                    # UPPER(campo) dentro de CONCAT
                    upper_match = regex.search(r'UPPER\s*\(\s*([^)]+)\s*\)', arg, regex.IGNORECASE)
                    if upper_match:
                        inner_field = upper_match.group(1).strip()
                        mongo_args.append({"$toUpper": f"${inner_field}"})
                        logger.info(f"   UPPER anidado: UPPER({inner_field})")
                    else:
                        mongo_args.append(f"${arg}")
                        logger.warning(f"   UPPER fallback: ${arg}")
                
                elif "LOWER(" in arg.upper():
                    lower_match = regex.search(r'LOWER\s*\(\s*([^)]+)\s*\)', arg, regex.IGNORECASE)
                    if lower_match:
                        inner_field = lower_match.group(1).strip()
                        mongo_args.append({"$toLower": f"${inner_field}"})
                        logger.info(f"   LOWER anidado: LOWER({inner_field})")
                    else:
                        mongo_args.append(f"${arg}")
                        logger.warning(f"   LOWER fallback: ${arg}")
                
                else:
                    # Es un campo de la base de datos normal
                    mongo_args.append(f"${arg}")
                    logger.info(f"   Campo: ${arg}")
            
            result = {"$concat": mongo_args}
            logger.info(f" CONCAT traducido exitosamente: {result}")
            return result
            
        except Exception as e:
            logger.error(f" Error traduciendo CONCAT: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None


    def _parse_concat_arguments(self, args_str):
        """
        ✅ MEJORADO: Parsea argumentos de CONCAT respetando comillas y paréntesis anidados.
        
        Args:
            args_str (str): String con argumentos separados por comas
            
        Returns:
            list: Lista de argumentos parseados
        """
        args = []
        current_arg = ""
        in_quotes = False
        quote_char = None
        paren_level = 0
        
        for char in args_str + ',':  # Añadir coma al final para capturar último argumento
            if char in ["'", '"'] and (not in_quotes or char == quote_char):
                # Manejo de comillas
                in_quotes = not in_quotes
                if in_quotes:
                    quote_char = char
                else:
                    quote_char = None
                current_arg += char
            elif char == '(' and not in_quotes:
                # Paréntesis de funciones anidadas
                paren_level += 1
                current_arg += char
            elif char == ')' and not in_quotes:
                paren_level -= 1
                current_arg += char
            elif char == ',' and not in_quotes and paren_level == 0:
                # Separador de argumentos (solo a nivel superior)
                if current_arg.strip():
                    args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += char
        
        logger.info(f" Argumentos finales parseados: {args}")
        return args


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
        🔧 CORREGIDO: Verifica si un campo contiene funciones SQL.
        Distingue entre funciones de agregación y funciones de transformación.
        """
        if not field:
            return False
        
        field_upper = field.upper().strip()
        
        # 🆕 DETECTAR COUNT(*) específicamente
        if field_upper == "COUNT(*)":
            logger.info("COUNT(*) detectado")
            return True
        
        # 🆕 Lista de funciones de AGREGACIÓN (requieren $group)
        aggregate_functions = [
            "COUNT(", "SUM(", "AVG(", "MIN(", "MAX(", 
            "GROUP_CONCAT(", "STRING_AGG("
        ]
        
        # 🆕 Lista de funciones de TRANSFORMACIÓN (requieren $project, NO $group)
        transformation_functions = [
            "UPPER(", "LOWER(", "LENGTH(", "CONCAT(", 
            "YEAR(", "MONTH(", "DAY(", "NOW(", "CURRENT_DATE(",
            "SUBSTRING(", "SUBSTR(", "LEFT(", "RIGHT(",
            "LTRIM(", "RTRIM(", "TRIM(", "REPLACE("
        ]
        
        # 🔧 CRÍTICO: Solo detectar funciones de AGREGACIÓN para _translate_select_aggregate
        for func in aggregate_functions:
            if func in field_upper:
                logger.info(f"Función de AGREGACIÓN detectada: {func} en '{field}'")
                return True
        
        # 🔧 NUEVO: Las funciones de transformación NO van a aggregate
        for func in transformation_functions:
            if func in field_upper:
                logger.info(f"Función de TRANSFORMACIÓN detectada: {func} en '{field}' - usando find con projection especial")
                return False  # ← CRÍTICO: retornar False para funciones de transformación
        
        return False


    def _translate_select_with_transformations(self):
        """
        🆕 NUEVO: Traduce SELECT con funciones de transformación usando $project
        """
        pipeline = []
        collection = self.sql_parser.get_table_name()
        
        # 1. $match para WHERE
        where_clause = self.sql_parser.get_where_clause()
        if where_clause:
            pipeline.append({"$match": where_clause})
        
        # 2. $project para transformaciones
        select_fields = self.sql_parser.get_select_fields()
        project_stage = {"$project": {}}
        
        for field_info in select_fields:
            if isinstance(field_info, dict) and "field" in field_info:
                field = field_info["field"]
                alias = field_info.get("alias", field)
                
                # Detectar y traducir funciones de transformación
                if "UPPER(" in field.upper():
                    # UPPER(campo) -> {$toUpper: "$campo"}
                    match = regex.search(r'UPPER\s*\(\s*([^)]+)\s*\)', field, regex.IGNORECASE)
                    if match:
                        inner_field = match.group(1).strip()
                        project_stage["$project"][alias] = {"$toUpper": f"${inner_field}"}
                        logger.info(f"UPPER({inner_field}) traducido a $toUpper")
                
                elif "LOWER(" in field.upper():
                    # LOWER(campo) -> {$toLower: "$campo"}
                    match = regex.search(r'LOWER\s*\(\s*([^)]+)\s*\)', field, regex.IGNORECASE)
                    if match:
                        inner_field = match.group(1).strip()
                        project_stage["$project"][alias] = {"$toLower": f"${inner_field}"}
                        logger.info(f"LOWER({inner_field}) traducido a $toLower")
                
                else:
                    # Campo normal
                    project_stage["$project"][alias] = f"${field}"
        
        if project_stage["$project"]:
            pipeline.append(project_stage)
        
        # 3. ORDER BY y LIMIT
        order_by = self.sql_parser.get_order_by()
        if order_by:
            pipeline.append({"$sort": order_by})
        
        limit = self.sql_parser.get_limit()
        if limit is not None:
            pipeline.append({"$limit": limit})
        
        return {
            "operation": "aggregate",
            "collection": collection,
            "pipeline": pipeline
        }

    
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
        🔧 CORREGIDO: Usa aggregate + $merge para operaciones matemáticas complejas
        
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
        
        # 🔧 NUEVO: Detectar si hay operaciones matemáticas que requieren cálculo
        has_math_operations = self._has_math_operations(update_values["values"])
        
        if has_math_operations:
            # Usar aggregate + $merge para operaciones matemáticas
            return self._translate_update_with_aggregate(collection, update_values["values"], where_clause)
        else:
            # Usar update normal para valores simples
            return {
                "operation": "update",
                "collection": collection,
                "query": {
                    "query": where_clause or {},
                    "update": {"$set": update_values["values"]}
                }
            }

    def _has_math_operations(self, update_values):
        """
        Detecta si hay operaciones matemáticas en los valores de UPDATE.
        
        Args:
            update_values (dict): Valores a actualizar
            
        Returns:
            bool: True si hay operaciones matemáticas
        """
        for field, value in update_values.items():
            value_str = str(value).strip()
            if any(op in value_str for op in [" * ", " + ", " - ", " / "]):
                return True
        return False

    def _translate_update_with_aggregate(self, collection, update_values, where_clause):
        """
        🔧 NUEVO: Traduce UPDATE con operaciones matemáticas usando aggregate + $merge.
        
        Args:
            collection (str): Nombre de la colección
            update_values (dict): Valores a actualizar
            where_clause (dict): Condición WHERE
            
        Returns:
            dict: Operación usando aggregate con $merge
        """
        pipeline = []
        
        # 1. $match para filtrar documentos a actualizar
        if where_clause:
            pipeline.append({"$match": where_clause})
        
        # 2. $addFields para calcular nuevos valores
        add_fields_stage = {"$addFields": {}}
        
        for field, value in update_values.items():
            value_str = str(value).strip()
            
            logger.info(f"Procesando operación matemática: {field} = {value_str}")
            
            # 🔧 DETECTAR MULTIPLICACIÓN: campo * número
            if " * " in value_str:
                multiplication_pattern = r'(\w+)\s*\*\s*([\d.]+)'
                match = regex.search(multiplication_pattern, value_str, regex.IGNORECASE)
                
                if match:
                    source_field = match.group(1).strip()
                    multiplier = float(match.group(2).strip())
                    
                    if source_field.lower() == field.lower():
                        # salario = salario * 1.15
                        add_fields_stage["$addFields"][field] = {
                            "$multiply": [
                                {"$toDouble": f"${source_field}"},
                                multiplier
                            ]
                        }
                        logger.info(f" Multiplicación: {field} = {source_field} * {multiplier}")
            
            # 🔧 DETECTAR SUMA: campo + número
            elif " + " in value_str:
                addition_pattern = r'(\w+)\s*\+\s*([\d.]+)'
                match = regex.search(addition_pattern, value_str, regex.IGNORECASE)
                
                if match:
                    source_field = match.group(1).strip()
                    increment = float(match.group(2).strip())
                    
                    add_fields_stage["$addFields"][field] = {
                        "$add": [
                            {"$toDouble": f"${source_field}"},
                            increment
                        ]
                    }
                    logger.info(f" Suma: {field} = {source_field} + {increment}")
            
            # 🔧 DETECTAR RESTA: campo - número
            elif " - " in value_str:
                subtraction_pattern = r'(\w+)\s*-\s*([\d.]+)'
                match = regex.search(subtraction_pattern, value_str, regex.IGNORECASE)
                
                if match:
                    source_field = match.group(1).strip()
                    decrement = float(match.group(2).strip())
                    
                    add_fields_stage["$addFields"][field] = {
                        "$subtract": [
                            {"$toDouble": f"${source_field}"},
                            decrement
                        ]
                    }
                    logger.info(f" Resta: {field} = {source_field} - {decrement}")
            
            # 🔧 DETECTAR DIVISIÓN: campo / número
            elif " / " in value_str:
                division_pattern = r'(\w+)\s*/\s*([\d.]+)'
                match = regex.search(division_pattern, value_str, regex.IGNORECASE)
                
                if match:
                    source_field = match.group(1).strip()
                    divisor = float(match.group(2).strip())
                    
                    add_fields_stage["$addFields"][field] = {
                        "$divide": [
                            {"$toDouble": f"${source_field}"},
                            divisor
                        ]
                    }
                    logger.info(f" División: {field} = {source_field} / {divisor}")
            
            else:
                # Valor literal
                try:
                    if '.' in value_str:
                        numeric_value = float(value_str)
                    else:
                        numeric_value = int(value_str)
                    add_fields_stage["$addFields"][field] = numeric_value
                    logger.info(f" Valor literal: {field} = {numeric_value}")
                except ValueError:
                    add_fields_stage["$addFields"][field] = value_str
                    logger.info(f" Valor string: {field} = '{value_str}'")
        
        if add_fields_stage["$addFields"]:
            pipeline.append(add_fields_stage)
        
        # 3. $merge para actualizar los documentos en la misma colección
        merge_stage = {
            "$merge": {
                "into": collection,
                "whenMatched": "replace",
                "whenNotMatched": "discard"
            }
        }
        pipeline.append(merge_stage)
        
        logger.info(f"Pipeline UPDATE con cálculo: {pipeline}")
        
        return {
            "operation": "aggregate",
            "collection": collection,
            "pipeline": pipeline,
            "update_type": "math_operations"
        }

    def _process_update_operations(self, update_values):
        """
        🔧 CORREGIDO: Procesa operaciones matemáticas en UPDATE SET.
        Incluye conversión automática de string a número para operaciones matemáticas.
        
        Args:
            update_values (dict): Valores a actualizar del parser
            
        Returns:
            dict: Operaciones MongoDB procesadas
        """
        mongo_update = {}
        set_operations = {}
        
        for field, value in update_values.items():
            # Convertir a string para procesar
            value_str = str(value).strip()
            
            logger.info(f" Procesando actualización: {field} = {value_str}")
            
            # 🔧 DETECTAR MULTIPLICACIÓN: campo * número
            if " * " in value_str:
                # Patrón: salario * 1.15, precio * 0.9, etc.
                multiplication_pattern = r'(\w+)\s*\*\s*([\d.]+)'
                match = regex.search(multiplication_pattern, value_str, regex.IGNORECASE)
                
                if match:
                    source_field = match.group(1).strip()
                    multiplier = float(match.group(2).strip())
                    
                    # Verificar que el campo fuente sea el mismo que se está actualizando
                    if source_field.lower() == field.lower():
                        # 🔧 CLAVE: Usar $set con conversión y multiplicación para manejar strings
                        set_operations[field] = {
                            "$multiply": [
                                {"$toDouble": f"${source_field}"},  # Convertir string a número
                                multiplier
                            ]
                        }
                        logger.info(f" Multiplicación con conversión: {field} = toDouble(${source_field}) * {multiplier}")
                    else:
                        # Si es diferente, usar $set con $multiply
                        set_operations[field] = {
                            "$multiply": [
                                {"$toDouble": f"${source_field}"},
                                multiplier
                            ]
                        }
                        logger.info(f" Multiplicación cruzada con conversión: {field} = toDouble(${source_field}) * {multiplier}")
                    continue
            
            # 🔧 DETECTAR SUMA: campo + número
            elif " + " in value_str:
                addition_pattern = r'(\w+)\s*\+\s*([\d.]+)'
                match = regex.search(addition_pattern, value_str, regex.IGNORECASE)
                
                if match:
                    source_field = match.group(1).strip()
                    increment = float(match.group(2).strip())
                    
                    set_operations[field] = {
                        "$add": [
                            {"$toDouble": f"${source_field}"},
                            increment
                        ]
                    }
                    logger.info(f" Suma con conversión: {field} = toDouble(${source_field}) + {increment}")
                    continue
            
            # 🔧 DETECTAR RESTA: campo - número
            elif " - " in value_str:
                subtraction_pattern = r'(\w+)\s*-\s*([\d.]+)'
                match = regex.search(subtraction_pattern, value_str, regex.IGNORECASE)
                
                if match:
                    source_field = match.group(1).strip()
                    decrement = float(match.group(2).strip())
                    
                    set_operations[field] = {
                        "$subtract": [
                            {"$toDouble": f"${source_field}"},
                            decrement
                        ]
                    }
                    logger.info(f" Resta con conversión: {field} = toDouble(${source_field}) - {decrement}")
                    continue
            
            # 🔧 DETECTAR DIVISIÓN: campo / número
            elif " / " in value_str:
                division_pattern = r'(\w+)\s*/\s*([\d.]+)'
                match = regex.search(division_pattern, value_str, regex.IGNORECASE)
                
                if match:
                    source_field = match.group(1).strip()
                    divisor = float(match.group(2).strip())
                    
                    set_operations[field] = {
                        "$divide": [
                            {"$toDouble": f"${source_field}"},
                            divisor
                        ]
                    }
                    logger.info(f" División con conversión: {field} = toDouble(${source_field}) / {divisor}")
                    continue
            
            # Si no es una operación matemática, es un valor literal
            else:
                # Intentar convertir a número si es posible
                try:
                    if '.' in value_str:
                        numeric_value = float(value_str)
                    else:
                        numeric_value = int(value_str)
                    set_operations[field] = numeric_value
                    logger.info(f" Valor numérico: {field} = {numeric_value}")
                except ValueError:
                    # Es un string
                    set_operations[field] = value_str
                    logger.info(f" Valor string: {field} = '{value_str}'")
        
        # 🔧 CONSTRUIR OPERACIÓN MONGODB FINAL
        # Solo usar $set ya que estamos manejando las conversiones manualmente
        
        if set_operations:
            mongo_update["$set"] = set_operations
            logger.info(f" Operaciones $set: {set_operations}")
        
        # Si no hay operaciones específicas, usar $set por defecto
        if not mongo_update:
            mongo_update["$set"] = update_values
            logger.warning(" No se detectaron operaciones matemáticas, usando $set por defecto")
        
        logger.info(f" Operación UPDATE final: {mongo_update}")
        return mongo_update


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
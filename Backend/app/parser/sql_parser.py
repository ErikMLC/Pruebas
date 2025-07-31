import sqlparse
import re
import logging
from .base_parser import BaseParser

# Configurar logging
logger = logging.getLogger(__name__)

class SQLParser:
    """
    Parser principal que coordina el análisis de consultas SQL.
    Utiliza parsers especializados para diferentes tipos de consultas.
    """
    
    def __init__(self, sql_query):
        """
        Inicializa el parser con una consulta SQL.
        
        Args:
            sql_query (str): La consulta SQL a analizar
        """
        self.sql_query = sql_query
        self.parsed = sqlparse.parse(sql_query)
        logger.info(f"Consulta SQL recibida para analizar: {sql_query}")
        
        # Los parsers especializados se importarán y configurarán según sea necesario
        # 🆕 Nuevos parsers (lazy loading para evitar dependencias circulares)
        self._function_parser = None
        self._advanced_parser = None
        self._join_parser = None
        self._formatter = None
    
    def get_tokens(self):
        """
        Obtiene los tokens de la consulta SQL.
        
        Returns:
            list: Lista de tokens de la consulta.
        """
        if self.parsed:
            return self.parsed[0].tokens
        return []
    
    def get_query_type(self):
        """
        Determina el tipo de consulta SQL (SELECT, INSERT, UPDATE, DELETE).
        
        Returns:
            str: Tipo de consulta en mayúsculas.
        """
        if not self.parsed:
            return None
            
        # Obtener el tipo directamente de sqlparse
        query_type = self.parsed[0].get_type()
        
        # Si sqlparse no pudo determinar el tipo, hacer un análisis manual
        if not query_type:
            sql_upper = self.sql_query.upper().strip()
            if sql_upper.startswith("SELECT"):
                query_type = "SELECT"
            elif sql_upper.startswith("INSERT"):
                query_type = "INSERT"
            elif sql_upper.startswith("UPDATE"):
                query_type = "UPDATE"
            elif sql_upper.startswith("DELETE"):
                query_type = "DELETE"
            elif sql_upper.startswith("CREATE"):
                query_type = "CREATE"
            elif sql_upper.startswith("DROP"):
                query_type = "DROP"
            elif sql_upper.startswith("ALTER"):
                query_type = "ALTER"
        
        return query_type
    
    def get_table_name(self):
        """
        Obtiene el nombre de la tabla (colección) de la consulta SQL.
        
        Returns:
            str: Nombre de la tabla como cadena (str).
        """
        query_type = self.get_query_type()
        logger.info(f"Tipo de consulta detectado: {query_type}")
        
        # Normalizar la consulta para el análisis
        sql = " " + self.sql_query.strip() + " "
        
        # Patrones de expresiones regulares para diferentes tipos de consultas
        patterns = {
            "SELECT": [
                r"FROM\s+([^\s,;()]+)",  # FROM tabla
                r"FROM\s+([^\s]+)\s+",   # FROM tabla WHERE/GROUP/ORDER/etc
            ],
            "INSERT": [
                r"INSERT\s+INTO\s+([^\s(]+)",  # INSERT INTO tabla
                r"INSERT\s+INTO\s+([^\s]+)\s+", # INSERT INTO tabla VALUES/SELECT
            ],
            "UPDATE": [
                r"UPDATE\s+([^\s,;()]+)",  # UPDATE tabla
                r"UPDATE\s+([^\s]+)\s+",   # UPDATE tabla SET
            ],
            "DELETE": [
                r"DELETE\s+FROM\s+([^\s,;()]+)",  # DELETE FROM tabla
                r"DELETE\s+FROM\s+([^\s]+)\s+",   # DELETE FROM tabla WHERE
            ],
            "CREATE": [
                r"CREATE\s+TABLE\s+([^\s(]+)",  # CREATE TABLE tabla
                r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+([^\s(]+)",  # CREATE TABLE IF NOT EXISTS tabla
            ],
            "DROP": [
                r"DROP\s+TABLE\s+([^\s;]+)",  # DROP TABLE tabla
            ],
            "ALTER": [
                r"ALTER\s+TABLE\s+([^\s;]+)",  # ALTER TABLE tabla
            ]
        }
        
        # Buscar patrones según el tipo de consulta
        if query_type in patterns:
            for pattern in patterns[query_type]:
                match = re.search(pattern, sql, re.IGNORECASE)
                if match:
                    table_name = match.group(1).strip('`[]"\'')
                    # Limpiar cualquier otra sintaxis SQL (como alias)
                    if ' ' in table_name:
                        table_name = table_name.split(' ')[0]
                    logger.info(f"Nombre de tabla extraído con regex: {table_name}")
                    return table_name.lower()
        
        # Si no se encontró con regex, intentar con un enfoque basado en tokens
        try:
            if query_type == "SELECT":
                for i, token in enumerate(self.get_tokens()):
                    if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == "FROM":
                        # El siguiente token después de FROM debería ser la tabla
                        j = i + 1
                        while j < len(self.get_tokens()):
                            table_token = self.get_tokens()[j]
                            if table_token.ttype is not sqlparse.tokens.Whitespace:
                                if isinstance(table_token, sqlparse.sql.Identifier):
                                    table_name = table_token.get_real_name()
                                else:
                                    table_name = str(table_token).strip('`[]"\'')
                                logger.info(f"Nombre de tabla extraído con tokens: {table_name}")
                                return table_name.lower()
                            j += 1
        except Exception as e:
            logger.error(f"Error al extraer nombre de tabla con tokens: {e}")
        
        logger.warning("No se pudo determinar el nombre de la tabla")
        return None


    def get_order_by(self):
        """
        Extrae ORDER BY de la consulta SQL
        
        Returns:
            dict: Diccionario con los campos y direcciones de ordenamiento
            Ejemplo: {'edad': -1, 'nombre': 1}
        """
        logger.info("Extrayendo cláusula ORDER BY de la consulta")
        
        # Limpiar y normalizar la consulta
        query = " " + self.sql_query.strip() + " "
        
        # Regex que captura ORDER BY hasta el final o antes de LIMIT
        pattern = r'\sORDER\s+BY\s+(.*?)(?:\s+LIMIT|\s*;|\s*$)'
        match = re.search(pattern, query, re.IGNORECASE | re.DOTALL)
        
        if not match:
            logger.info("No se encontró cláusula ORDER BY en la consulta")
            return {}
        
        order_clause = match.group(1).strip()
        logger.info(f"Cláusula ORDER BY extraída: '{order_clause}'")
        
        # Parsear campos de ordenamiento
        order_dict = self._parse_order_fields(order_clause)
        
        logger.info(f"ORDER BY parseado: {order_dict}")
        return order_dict

    def _parse_order_fields(self, order_clause):
        """
        Parsea los campos de ORDER BY
        """
        order_dict = {}
        
        # Limpiar punto y coma si existe
        if order_clause.endswith(';'):
            order_clause = order_clause[:-1].strip()
        
        # Dividir por comas para múltiples campos
        fields = [field.strip() for field in order_clause.split(',')]
        
        for field in fields:
            if not field:
                continue
            
            # Separar campo y dirección
            parts = field.strip().split()
            
            if len(parts) == 1:
                # Solo campo, por defecto ASC
                field_name = parts[0]
                direction = 1  # ASC en MongoDB
            elif len(parts) == 2:
                # Campo y dirección
                field_name = parts[0]
                direction_str = parts[1].upper()
                
                if direction_str == "DESC":
                    direction = -1  # DESC en MongoDB
                elif direction_str == "ASC":
                    direction = 1   # ASC en MongoDB
                else:
                    logger.warning(f"Dirección de orden desconocida: {direction_str}, usando ASC")
                    direction = 1
            else:
                logger.warning(f"Formato de campo ORDER BY inválido: {field}")
                continue
            
            order_dict[field_name] = direction
            logger.debug(f"Campo de orden parseado: {field_name} -> {direction}")
        
        return order_dict


    def get_where_clause(self):
        """
        Obtiene la cláusula WHERE de una consulta SQL.
        Redirige a where_parser cuando está disponible.
        
        Returns:
            dict: Diccionario con las condiciones.
        """
        # Importación perezosa para evitar dependencias circulares
        from .where_parser import WhereParser
        
        where_parser = WhereParser()
        return where_parser.parse(self.sql_query)
    
    def get_select_fields(self):
        """
        Obtiene los campos a seleccionar de una consulta SELECT.
        Redirige a select_parser cuando está disponible.
        
        Returns:
            list: Lista de campos a seleccionar.
        """
        # Importación perezosa para evitar dependencias circulares
        from .select_parser import SelectParser
        
        select_parser = SelectParser()
        return select_parser.get_select_fields(self.sql_query)
    
    def get_insert_values(self):
        """
        Obtiene los valores a insertar de una consulta INSERT INTO.
        Redirige a crud_parser cuando está disponible.
        
        Returns:
            dict: Diccionario con los valores a insertar.
        """
        # Importación perezosa para evitar dependencias circulares
        from .crud_parser import CRUDParser
        
        crud_parser = CRUDParser()
        return crud_parser.parse_insert(self.sql_query)
    
    def get_update_values(self):
        """
        Obtiene los valores a actualizar de una consulta UPDATE.
        Redirige a crud_parser cuando está disponible.
        
        Returns:
            dict: Diccionario con los valores a actualizar.
        """
        # Importación perezosa para evitar dependencias circulares
        from .crud_parser import CRUDParser
        
        crud_parser = CRUDParser()
        return crud_parser.parse_update(self.sql_query)
    
    def get_delete_condition(self):
        """
        Obtiene la condición para eliminar de una consulta DELETE.
        Redirige a crud_parser cuando está disponible.
        
        Returns:
            dict: Diccionario con la condición para eliminar.
        """
        # Importación perezosa para evitar dependencias circulares
        from .crud_parser import CRUDParser
        
        crud_parser = CRUDParser()
        return crud_parser.parse_delete(self.sql_query)

    def get_limit(self):
        """
        Obtiene el valor de LIMIT de una consulta SQL.
        
        Returns:
            int or None: Valor numérico del límite, o None si no hay cláusula LIMIT.
        """
        # Normalizar la consulta
        query = " " + self.sql_query.strip() + " "
        
        # Expresión regular para extraer la cláusula LIMIT
        pattern = r'\sLIMIT\s+(\d+)(?:\s|;|$)'
        match = re.search(pattern, query, re.IGNORECASE)
        
        if match:
            limit_str = match.group(1).strip()
            try:
                limit = int(limit_str)
                logger.info(f"Límite extraído: {limit}")
                return limit
            except ValueError:
                logger.error(f"No se pudo convertir el límite '{limit_str}' a entero")
        
        logger.info("No se encontró cláusula LIMIT en la consulta")
        return None

    # =================== 🆕 NUEVOS MÉTODOS AGREGADOS ===================
    
    # --- Lazy Loading de Parsers ---
    
    def _get_function_parser(self):
        """Obtiene el parser de funciones (lazy loading)."""
        if not self._function_parser:
            try:
                from .function_parser import FunctionParser
                self._function_parser = FunctionParser()
            except ImportError:
                logger.warning("FunctionParser no disponible")
                self._function_parser = None
        return self._function_parser
    
    def _get_advanced_parser(self):
        """Obtiene el parser avanzado (lazy loading)."""
        if not self._advanced_parser:
            try:
                from .advanced_parser import AdvancedParser
                self._advanced_parser = AdvancedParser()
            except ImportError:
                logger.warning("AdvancedParser no disponible")
                self._advanced_parser = None
        return self._advanced_parser
    
    def _get_join_parser(self):
        """Obtiene el parser de JOINs (lazy loading)."""
        if not self._join_parser:
            try:
                from .join_parser import JoinParser
                self._join_parser = JoinParser()
            except ImportError:
                logger.warning("JoinParser no disponible")
                self._join_parser = None
        return self._join_parser
    
    def _get_formatter(self):
        """Obtiene el formateador de respuestas (lazy loading)."""
        if not self._formatter:
            try:
                from .formatter import ResponseFormatter
                self._formatter = ResponseFormatter()
            except ImportError:
                logger.warning("ResponseFormatter no disponible")
                self._formatter = None
        return self._formatter
    
    # --- Métodos de Funciones SQL ---
    
    def has_functions(self):
        """
        Verifica si la consulta contiene funciones SQL.
        
        Returns:
            bool: True si hay funciones, False en caso contrario
        """
        parser = self._get_function_parser()
        if parser:
            return parser.has_functions(self.sql_query)
        return False
    
    def get_functions(self):
        """
        Obtiene información sobre las funciones en la consulta.
        
        Returns:
            list: Lista de funciones encontradas con sus traducciones
        """
        parser = self._get_function_parser()
        if parser:
            return parser.parse_functions(self.sql_query)
        return []
    
    def get_supported_functions(self):
        """
        Obtiene información sobre las funciones SQL soportadas.
        
        Returns:
            dict: Diccionario con funciones soportadas por categoría
        """
        parser = self._get_function_parser()
        if parser:
            return parser.get_supported_functions()
        return {}
    
    # --- Métodos de Características Avanzadas ---
    
    def has_distinct(self):
        """
        Verifica si la consulta contiene SELECT DISTINCT.
        
        Returns:
            bool: True si hay DISTINCT, False en caso contrario
        """
        parser = self._get_advanced_parser()
        if parser:
            return parser.has_distinct(self.sql_query)
        return False
    
    def get_distinct_info(self):
        """
        Obtiene información sobre SELECT DISTINCT.
        
        Returns:
            dict: Información sobre la consulta DISTINCT
        """
        parser = self._get_advanced_parser()
        if parser:
            return parser.parse_distinct(self.sql_query)
        return {}
    
    def has_having(self):
        """
        Verifica si la consulta contiene cláusula HAVING.
        
        Returns:
            bool: True si hay HAVING, False en caso contrario
        """
        parser = self._get_advanced_parser()
        if parser:
            return parser.has_having(self.sql_query)
        return False
    
    def get_having_clause(self):
        """
        Obtiene la cláusula HAVING parseada.
        
        Returns:
            dict: Condiciones HAVING en formato MongoDB
        """
        parser = self._get_advanced_parser()
        if parser:
            return parser.parse_having(self.sql_query)
        return {}
    
    def has_union(self):
        """
        Verifica si la consulta contiene UNION.
        
        Returns:
            bool: True si hay UNION, False en caso contrario
        """
        parser = self._get_advanced_parser()
        if parser:
            return parser.has_union(self.sql_query)
        return False
    
    def get_union_info(self):
        """
        Obtiene información sobre UNION.
        
        Returns:
            dict: Información sobre la consulta UNION
        """
        parser = self._get_advanced_parser()
        if parser:
            return parser.parse_union(self.sql_query)
        return {}
    
    def has_subquery(self):
        """
        Verifica si la consulta contiene subqueries.
        
        Returns:
            bool: True si hay subqueries, False en caso contrario
        """
        parser = self._get_advanced_parser()
        if parser:
            return parser.has_subquery(self.sql_query)
        return False
    
    def get_subqueries(self):
        """
        Obtiene información sobre subqueries.
        
        Returns:
            list: Lista de subqueries encontradas
        """
        parser = self._get_advanced_parser()
        if parser:
            return parser.parse_subqueries(self.sql_query)
        return []
    
    # --- Métodos de JOINs ---
    
    def has_joins(self):
        """
        Verifica si la consulta contiene operaciones JOIN.
        
        Returns:
            bool: True si hay JOINs, False en caso contrario
        """
        parser = self._get_join_parser()
        if parser:
            return parser.has_joins(self.sql_query)
        return False
    
    def get_joins(self):
        """
        Obtiene información sobre los JOINs.
        
        Returns:
            list: Lista de JOINs encontrados con información detallada
        """
        parser = self._get_join_parser()
        if parser:
            return parser.parse_joins(self.sql_query)
        return []
    
    def get_main_table(self):
        """
        Obtiene información sobre la tabla principal (FROM).
        
        Returns:
            dict: Información de la tabla principal
        """
        parser = self._get_join_parser()
        if parser:
            return parser.get_main_table_from_query(self.sql_query)
        return None
    
    def validate_joins(self):
        """
        Valida si los JOINs en la consulta son traducibles.
        
        Returns:
            dict: Resultado de validación
        """
        parser = self._get_join_parser()
        if parser:
            return parser.validate_join_query(self.sql_query)
        return {"is_valid": True, "issues": [], "warnings": []}
    
    # --- Métodos de Formateo de Respuestas ---
    
    def format_success_response(self, data, metadata=None, execution_time=None):
        """
        Formatea una respuesta exitosa.
        
        Args:
            data: Datos de la respuesta
            metadata: Metadatos adicionales
            execution_time: Tiempo de ejecución
            
        Returns:
            dict: Respuesta formateada
        """
        formatter = self._get_formatter()
        if formatter:
            return formatter.format_success(data, metadata, execution_time)
        return {"success": True, "data": data}
    
    def format_error_response(self, error, error_type="UNKNOWN_ERROR", context=None):
        """
        Formatea una respuesta de error.
        
        Args:
            error: Error o mensaje de error
            error_type: Tipo de error
            context: Contexto adicional
            
        Returns:
            dict: Respuesta de error formateada
        """
        formatter = self._get_formatter()
        if formatter:
            return formatter.format_error(error, error_type, context)
        return {"success": False, "error": str(error)}
    
    def format_translation_response(self, mongo_operation, execution_time=None, warnings=None):
        """
        Formatea el resultado de una traducción SQL→MongoDB.
        
        Args:
            mongo_operation: Operación MongoDB generada
            execution_time: Tiempo de traducción
            warnings: Advertencias durante la traducción
            
        Returns:
            dict: Resultado de traducción formateado
        """
        formatter = self._get_formatter()
        if formatter:
            return formatter.format_translation_result(
                sql_query=self.sql_query,
                mongo_operation=mongo_operation,
                query_type=self.get_query_type(),
                collection=self.get_table_name(),
                execution_time=execution_time,
                warnings=warnings
            )
        return {"success": True, "data": mongo_operation}
    
    # --- Métodos de Análisis Integral ---
    
    def analyze_query_complexity(self):
        """
        Analiza la complejidad general de la consulta.
        
        Returns:
            dict: Análisis de complejidad
        """
        complexity_factors = {
            "has_functions": self.has_functions(),
            "has_joins": self.has_joins(),
            "has_distinct": self.has_distinct(),
            "has_having": self.has_having(),
            "has_union": self.has_union(),
            "has_subquery": self.has_subquery(),
            "query_type": self.get_query_type()
        }
        
        # Calcular puntuación de complejidad
        score = 0
        if complexity_factors["has_functions"]:
            score += 1
        if complexity_factors["has_joins"]:
            score += 2
        if complexity_factors["has_distinct"]:
            score += 1
        if complexity_factors["has_having"]:
            score += 1
        if complexity_factors["has_union"]:
            score += 3
        if complexity_factors["has_subquery"]:
            score += 3
        
        # Determinar nivel de complejidad
        if score == 0:
            complexity_level = "simple"
        elif score <= 3:
            complexity_level = "moderate"
        else:
            complexity_level = "complex"
        
        return {
            "complexity_level": complexity_level,
            "complexity_score": score,
            "factors": complexity_factors,
            "requires_advanced_translation": score > 0
        }
    
    def get_all_features_used(self):
        """
        Obtiene todas las características SQL utilizadas en la consulta.
        
        Returns:
            dict: Diccionario completo con todas las características detectadas
        """
        features = {
            "basic_info": {
                "query_type": self.get_query_type(),
                "table_name": self.get_table_name(),
                "has_where": bool(self.get_where_clause()),
                "has_limit": self.get_limit() is not None
            },
            "functions": {
                "has_functions": self.has_functions(),
                "function_list": self.get_functions() if self.has_functions() else []
            },
            "advanced_features": {
                "has_distinct": self.has_distinct(),
                "has_having": self.has_having(),
                "has_union": self.has_union(),
                "has_subquery": self.has_subquery()
            },
            "joins": {
                "has_joins": self.has_joins(),
                "join_list": self.get_joins() if self.has_joins() else [],
                "join_validation": self.validate_joins() if self.has_joins() else None
            }
        }
        
        return features
    

    def get_create_table_info(self):
        """
        ✅ NUEVO: Extrae información detallada de CREATE TABLE
        Returns:
            dict: Información completa de la tabla
        """
        try:
            # Extraer nombre de tabla
            table_name = self.get_table_name()
            
            # Extraer definición de columnas entre paréntesis
            columns_match = re.search(r'CREATE\s+TABLE\s+\w+\s*\((.*)\)', self.sql_query, re.IGNORECASE | re.DOTALL)
            if not columns_match:
                raise ValueError("No se encontró definición de columnas en CREATE TABLE")
            
            columns_str = columns_match.group(1).strip()
            
            # Parsear columnas individuales
            columns = self.parse_columns_definition(columns_str)
            
            # Extraer constraints y índices
            constraints = self.extract_constraints(columns_str)
            
            create_info = {
                'table_name': table_name,
                'columns': columns,
                'constraints': constraints,
                'total_columns': len(columns),
                'has_primary_key': any(col.get('is_primary_key', False) for col in columns),
                'has_indexes': len(constraints.get('indexes', [])) > 0,
                'original_definition': columns_str
            }
            
            logger.info(f"Información de CREATE TABLE extraída: {table_name} con {len(columns)} columnas")
            return create_info
            
        except Exception as e:
            logger.error(f"Error extrayendo información de CREATE TABLE: {e}")
            return {
                'table_name': self.get_table_name(),
                'columns': [],
                'constraints': {},
                'total_columns': 0,
                'has_primary_key': False,
                'has_indexes': False,
                'original_definition': '',
                'error': str(e)
            }

    def parse_columns_definition(self, columns_str):
        """
        ✅ NUEVO: Parsea la definición de columnas
        """
        columns = []
        
        # Dividir por comas (pero respetando paréntesis anidados)
        column_definitions = self.split_columns(columns_str)
        
        for col_def in column_definitions:
            col_def = col_def.strip()
            if not col_def:
                continue
                
            # Saltar constraints globales (PRIMARY KEY, FOREIGN KEY, etc.)
            if any(keyword in col_def.upper() for keyword in ['PRIMARY KEY (', 'FOREIGN KEY', 'INDEX', 'KEY']):
                continue
            
            column_info = self.parse_single_column(col_def)
            if column_info:
                columns.append(column_info)
        
        return columns

    def split_columns(self, columns_str):
        """
        ✅ NUEVO: Divide columnas respetando paréntesis
        """
        columns = []
        current_column = ""
        paren_count = 0
        
        for char in columns_str:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ',' and paren_count == 0:
                columns.append(current_column.strip())
                current_column = ""
                continue
            
            current_column += char
        
        if current_column.strip():
            columns.append(current_column.strip())
        
        return columns

    def parse_single_column(self, col_def):
        """
        ✅ NUEVO: Parsea una sola columna
        """
        try:
            parts = col_def.split()
            if len(parts) < 2:
                return None
            
            column_name = parts[0]
            data_type = parts[1]
            
            # Extraer información adicional
            is_primary_key = 'PRIMARY KEY' in col_def.upper()
            is_not_null = 'NOT NULL' in col_def.upper()
            is_unique = 'UNIQUE' in col_def.upper()
            
            # Extraer valor por defecto
            default_value = None
            default_match = re.search(r'DEFAULT\s+(\S+)', col_def, re.IGNORECASE)
            if default_match:
                default_value = default_match.group(1)
            
            return {
                'name': column_name,
                'type': data_type,
                'is_primary_key': is_primary_key,
                'is_not_null': is_not_null,
                'is_unique': is_unique,
                'default_value': default_value,
                'mongo_type': self.map_sql_to_mongo_type(data_type)
            }
            
        except Exception as e:
            logger.warning(f"Error parseando columna '{col_def}': {e}")
            return None

    def map_sql_to_mongo_type(self, sql_type):
        """
        ✅ NUEVO: Mapea tipos SQL a MongoDB
        """
        sql_type_upper = sql_type.upper()
        
        if 'INT' in sql_type_upper:
            return 'int'
        elif 'VARCHAR' in sql_type_upper or 'TEXT' in sql_type_upper:
            return 'string'
        elif 'DECIMAL' in sql_type_upper or 'FLOAT' in sql_type_upper or 'DOUBLE' in sql_type_upper:
            return 'number'
        elif 'BOOLEAN' in sql_type_upper or 'BOOL' in sql_type_upper:
            return 'bool'
        elif 'DATE' in sql_type_upper or 'TIMESTAMP' in sql_type_upper:
            return 'date'
        else:
            return 'mixed'

    def extract_constraints(self, columns_str):
        """
        ✅ NUEVO: Extrae constraints y índices
        """
        constraints = {
            'primary_keys': [],
            'foreign_keys': [],
            'indexes': [],
            'unique_constraints': []
        }
        
        # Buscar PRIMARY KEY
        pk_match = re.search(r'PRIMARY\s+KEY\s*\(([^)]+)\)', columns_str, re.IGNORECASE)
        if pk_match:
            pk_fields = [field.strip() for field in pk_match.group(1).split(',')]
            constraints['primary_keys'] = pk_fields
        
        # Buscar FOREIGN KEY
        fk_matches = re.finditer(r'FOREIGN\s+KEY\s*\(([^)]+)\)\s+REFERENCES\s+(\w+)\s*\(([^)]+)\)', columns_str, re.IGNORECASE)
        for fk_match in fk_matches:
            constraints['foreign_keys'].append({
                'columns': [col.strip() for col in fk_match.group(1).split(',')],
                'referenced_table': fk_match.group(2),
                'referenced_columns': [col.strip() for col in fk_match.group(3).split(',')]
            })
        
        return constraints
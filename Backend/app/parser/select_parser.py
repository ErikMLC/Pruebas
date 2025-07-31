import re
import logging
from .base_parser import BaseParser

# Configurar logging
logger = logging.getLogger(__name__)

class SelectParser(BaseParser):
    """
    Parser especializado para consultas SELECT de SQL.
    Analiza y extrae los campos y componentes de una consulta SELECT.
    """
    
    def parse(self, query):
        """
        Analiza una consulta SELECT y extrae sus componentes.
        
        Args:
            query (str): Consulta SELECT a analizar
            
        Returns:
            dict: Diccionario con información de los campos SELECT
        """
        logger.info(f"Analizando consulta SELECT: {query}")
        
        # Extraer los campos a seleccionar
        fields = self.get_select_fields(query)
        
        # Extraer el nombre de la tabla
        table = self.get_table_name(query)
        
        return {
            "operation": "SELECT",
            "fields": fields,
            "table": table
        }
    
    def get_select_fields(self, query):
        """
        Extrae los campos a seleccionar de una consulta SELECT.
        
        Args:
            query (str): Consulta SELECT a analizar
            
        Returns:
            list: Lista de diccionarios con campos y alias
        """
        # Normalizar la consulta
        query = query.strip()
        
        # Obtener la parte entre SELECT y FROM
        select_pattern = r'SELECT\s+(.*?)\s+FROM'
        select_match = re.search(select_pattern, query, re.IGNORECASE | re.DOTALL)
        
        if not select_match:
            logger.warning("No se pudo extraer campos SELECT")
            return [{"field": "*"}]  # Asumir SELECT * si no se puede analizar
        
        fields_str = select_match.group(1).strip()
        
        # Si es SELECT *, devolver un indicador especial
        if fields_str == "*":
            return [{"field": "*"}]
        
        # Dividir los campos por comas, respetando funciones y paréntesis
        fields = self._split_select_fields(fields_str)
        select_fields = []
        
        for field in fields:
            field = field.strip()
            
            # Detectar alias (campo AS alias o campo alias)
            alias_match = re.search(r'(.*?)\s+AS\s+([\w]+)$', field, re.IGNORECASE)
            if not alias_match:
                # Intentar con formato sin AS (campo alias)
                alias_match = re.search(r'(.*?)\s+([\w]+)$', field)
            
            if alias_match:
                field_name = alias_match.group(1).strip()
                alias = alias_match.group(2).strip()
                select_fields.append({"field": field_name, "alias": alias})
            else:
                select_fields.append({"field": field})
        
        logger.info(f"Campos SELECT extraídos: {select_fields}")
        return select_fields
    
    def get_table_name(self, query):
        """
        Extrae el nombre de la tabla de una consulta SELECT.
        
        Args:
            query (str): Consulta SELECT a analizar
            
        Returns:
            str: Nombre de la tabla
        """
        # Normalizar la consulta
        query = query.strip()
        
        # Extraer la parte después de FROM y antes de la siguiente cláusula
        from_pattern = r'FROM\s+([^\s,;()]+)(?:\s+(?:WHERE|GROUP BY|HAVING|ORDER BY|LIMIT|JOIN)|\s*$)'
        from_match = re.search(from_pattern, query, re.IGNORECASE)
        
        if from_match:
            table_name = from_match.group(1).strip('`[]"\'')
            logger.info(f"Tabla extraída: {table_name}")
            return table_name.lower()
        
        # Si el patrón anterior falla, intentar un patrón más simple
        simple_pattern = r'FROM\s+([^\s,;()]+)'
        simple_match = re.search(simple_pattern, query, re.IGNORECASE)
        
        if simple_match:
            table_name = simple_match.group(1).strip('`[]"\'')
            logger.info(f"Tabla extraída (patrón simple): {table_name}")
            return table_name.lower()
        
        logger.warning("No se pudo extraer tabla de SELECT")
        return None
    
    def _split_select_fields(self, fields_str):
        """
        Divide los campos de una cláusula SELECT, respetando funciones y paréntesis.
        
        Args:
            fields_str (str): Cadena con los campos a dividir
            
        Returns:
            list: Lista de campos individuales
        """
        fields = []
        current = ""
        in_quotes = False
        quote_char = None
        level = 0
        
        for char in fields_str + ',':  # Añadir coma al final para capturar el último campo
            if char in ["'", '"'] and (not in_quotes or char == quote_char):
                in_quotes = not in_quotes
                if in_quotes:
                    quote_char = char
                else:
                    quote_char = None
                current += char
            elif char == '(' and not in_quotes:
                level += 1
                current += char
            elif char == ')' and not in_quotes:
                level -= 1
                current += char
            elif char == ',' and level == 0 and not in_quotes:
                fields.append(current.strip())
                current = ""
            else:
                current += char
        
        return fields
    
    def has_aggregate_functions(self, fields):
        """
        Verifica si hay funciones de agregación en los campos seleccionados.
        
        Args:
            fields (list): Lista de diccionarios con campos
            
        Returns:
            bool: True si hay funciones de agregación, False en caso contrario
        """
        agg_functions = ["COUNT", "SUM", "AVG", "MIN", "MAX"]
        
        for field_info in fields:
            field = field_info.get("field", "").upper()
            for func in agg_functions:
                if f"{func}(" in field:
                    return True
        
        return False
    

    def _get_ddl_parser(self):
        """Obtiene el parser DDL (lazy loading)."""
        if not hasattr(self, '_ddl_parser') or self._ddl_parser is None:
            try:
                from .ddl_parser import DDLParser
                self._ddl_parser = DDLParser()
            except ImportError:
                logger.warning("DDLParser no disponible")
                self._ddl_parser = None
        return self._ddl_parser


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
            columns_match = re.search(r'CREATE\s+TABLE\s+\w+\s*\((.*)\)', self.query, re.IGNORECASE | re.DOTALL)
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

    def get_drop_table_info(self):
        """
        Obtiene información de una consulta DROP TABLE.
        
        Returns:
            dict: Información de la tabla a eliminar
        """
        parser = self._get_ddl_parser()
        if parser and self.get_query_type() == "DROP":
            return parser.parse_drop_table(self.sql_query)
        return None

    def get_supported_sql_types(self):
        """
        Obtiene los tipos SQL soportados.
        
        Returns:
            dict: Tipos SQL soportados por categoría
        """
        parser = self._get_ddl_parser()
        if parser:
            return parser.get_supported_sql_types()
        return {}

    def extract_functions(self, fields):
        """
        Extrae información de las funciones de agregación en los campos.
        
        Args:
            fields (list): Lista de diccionarios con campos
            
        Returns:
            list: Lista de diccionarios con información de funciones
        """
        functions = []
        agg_functions = ["COUNT", "SUM", "AVG", "MIN", "MAX"]
        
        for field_info in fields:
            field = field_info.get("field", "")
            alias = field_info.get("alias", "")
            
            for func in agg_functions:
                func_pattern = fr'{func}\s*\((.*?)\)'
                match = re.search(func_pattern, field, re.IGNORECASE)
                
                if match:
                    inner_field = match.group(1).strip()
                    # Si no hay alias, generar uno
                    if not alias:
                        alias = f"{func.lower()}_{inner_field.lower()}"
                        if inner_field == "*":
                            alias = f"{func.lower()}_all"
                    
                    functions.append({
                        "function": func.lower(),
                        "field": inner_field,
                        "alias": alias
                    })
        
        return functions
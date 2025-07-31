import re
import logging
from .base_parser import BaseParser

# Configurar logging
logger = logging.getLogger(__name__)

class DDLParser(BaseParser):
    """
    Parser especializado para operaciones DDL (Data Definition Language).
    Maneja CREATE TABLE, DROP TABLE, ALTER TABLE, etc.
    """
    
    def __init__(self):
        """Inicializar el parser con mapeos de tipos de datos."""
        
        # Mapeo de tipos SQL a tipos MongoDB/JSON Schema
        self.sql_to_mongo_types = {
            # Tipos numéricos
            'INT': {'type': 'number', 'bsonType': 'int'},
            'INTEGER': {'type': 'number', 'bsonType': 'int'},
            'BIGINT': {'type': 'number', 'bsonType': 'long'},
            'SMALLINT': {'type': 'number', 'bsonType': 'int'},
            'TINYINT': {'type': 'number', 'bsonType': 'int'},
            'DECIMAL': {'type': 'number', 'bsonType': 'decimal'},
            'NUMERIC': {'type': 'number', 'bsonType': 'decimal'},
            'FLOAT': {'type': 'number', 'bsonType': 'double'},
            'DOUBLE': {'type': 'number', 'bsonType': 'double'},
            'REAL': {'type': 'number', 'bsonType': 'double'},
            
            # Tipos de texto
            'VARCHAR': {'type': 'string', 'bsonType': 'string'},
            'CHAR': {'type': 'string', 'bsonType': 'string'},
            'TEXT': {'type': 'string', 'bsonType': 'string'},
            'LONGTEXT': {'type': 'string', 'bsonType': 'string'},
            'MEDIUMTEXT': {'type': 'string', 'bsonType': 'string'},
            'TINYTEXT': {'type': 'string', 'bsonType': 'string'},
            
            # Tipos de fecha
            'DATE': {'type': 'string', 'bsonType': 'date', 'format': 'date'},
            'DATETIME': {'type': 'string', 'bsonType': 'date', 'format': 'date-time'},
            'TIMESTAMP': {'type': 'string', 'bsonType': 'date', 'format': 'date-time'},
            'TIME': {'type': 'string', 'bsonType': 'string', 'format': 'time'},
            
            # Tipos booleanos
            'BOOLEAN': {'type': 'boolean', 'bsonType': 'bool'},
            'BOOL': {'type': 'boolean', 'bsonType': 'bool'},
            
            # Tipos JSON
            'JSON': {'type': 'object', 'bsonType': 'object'},
            
            # Tipos binarios
            'BLOB': {'type': 'string', 'bsonType': 'binData'},
            'LONGBLOB': {'type': 'string', 'bsonType': 'binData'},
            'MEDIUMBLOB': {'type': 'string', 'bsonType': 'binData'},
            'TINYBLOB': {'type': 'string', 'bsonType': 'binData'},
        }
    
    def parse(self, query):
        """
        Analiza una consulta DDL.
        
        Args:
            query (str): Consulta DDL a analizar
            
        Returns:
            dict: Información sobre la operación DDL
        """
        query_upper = query.upper().strip()
        
        if query_upper.startswith('CREATE TABLE'):
            return self.parse_create_table(query)
        elif query_upper.startswith('DROP TABLE'):
            return self.parse_drop_table(query)
        elif query_upper.startswith('ALTER TABLE'):
            return self.parse_alter_table(query)
        else:
            raise ValueError(f"Operación DDL no soportada: {query}")
    
    def parse_create_table(self, query):
        """
        Analiza una consulta CREATE TABLE y extrae la estructura de la tabla.
        
        Args:
            query (str): Consulta CREATE TABLE
            
        Returns:
            dict: Estructura de la tabla con columnas y tipos
        """
        logger.info(f"Analizando CREATE TABLE: {query}")
        
        # Extraer nombre de tabla
        table_match = re.search(
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([^\s(]+)', 
            query, 
            re.IGNORECASE
        )
        
        if not table_match:
            raise ValueError("No se pudo extraer nombre de tabla")
        
        table_name = table_match.group(1).strip('`[]"\'')
        
        # Extraer definición de columnas
        columns_match = re.search(
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[^\s(]+\s*\((.*)\)',
            query,
            re.IGNORECASE | re.DOTALL
        )
        
        if not columns_match:
            raise ValueError("No se pudo extraer definición de columnas")
        
        columns_definition = columns_match.group(1).strip()
        
        # Parsear columnas
        columns = self._parse_columns(columns_definition)
        
        # Detectar constraints
        constraints = self._parse_constraints(columns_definition)
        
        return {
            "operation": "CREATE_TABLE",
            "table": table_name.lower(),
            "columns": columns,
            "constraints": constraints,
            "schema": self._build_json_schema(columns, constraints)
        }
    
    def parse_drop_table(self, query):
        """
        Analiza una consulta DROP TABLE.
        
        Args:
            query (str): Consulta DROP TABLE
            
        Returns:
            dict: Información sobre DROP TABLE
        """
        table_match = re.search(
            r'DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([^\s;]+)',
            query,
            re.IGNORECASE
        )
        
        if not table_match:
            raise ValueError("No se pudo extraer nombre de tabla para DROP")
        
        table_name = table_match.group(1).strip('`[]"\'')
        
        return {
            "operation": "DROP_TABLE",
            "table": table_name.lower()
        }
    
    def parse_alter_table(self, query):
        """
        Analiza una consulta ALTER TABLE (implementación básica).
        
        Args:
            query (str): Consulta ALTER TABLE
            
        Returns:
            dict: Información sobre ALTER TABLE
        """
        # Implementación básica - puede expandirse
        return {
            "operation": "ALTER_TABLE",
            "message": "ALTER TABLE requiere implementación específica para MongoDB"
        }
    
    def _parse_columns(self, columns_definition):
        """
        Parsea la definición de columnas.
        
        Args:
            columns_definition (str): Definición de columnas
            
        Returns:
            list: Lista de diccionarios con información de columnas
        """
        columns = []
        
        # Dividir por comas respetando paréntesis
        column_definitions = self._split_column_definitions(columns_definition)
        
        for col_def in column_definitions:
            col_def = col_def.strip()
            
            # Saltar constraints que no son definiciones de columna
            if any(keyword in col_def.upper() for keyword in ['PRIMARY KEY', 'FOREIGN KEY', 'INDEX', 'UNIQUE', 'CHECK']):
                continue
            
            column_info = self._parse_single_column(col_def)
            if column_info:
                columns.append(column_info)
        
        return columns
    
    def _parse_single_column(self, column_definition):
        """
        Parsea una definición de columna individual.
        
        Args:
            column_definition (str): Definición de una columna
            
        Returns:
            dict: Información de la columna
        """
        # Patrón para extraer nombre, tipo y constraints
        # Ejemplo: nombre VARCHAR(100) NOT NULL DEFAULT 'valor'
        pattern = r'^(\w+)\s+(\w+)(?:\(([^)]+)\))?\s*(.*)?$'
        match = re.match(pattern, column_definition.strip(), re.IGNORECASE)
        
        if not match:
            logger.warning(f"No se pudo parsear columna: {column_definition}")
            return None
        
        column_name = match.group(1)
        data_type = match.group(2).upper()
        size_info = match.group(3)
        constraints = match.group(4) or ""
        
        # Obtener información del tipo
        type_info = self.sql_to_mongo_types.get(data_type, {
            'type': 'string', 
            'bsonType': 'string'
        })
        
        column_info = {
            "name": column_name.lower(),
            "sql_type": data_type,
            "mongo_type": type_info,
            "nullable": "NOT NULL" not in constraints.upper(),
            "primary_key": "PRIMARY KEY" in constraints.upper(),
            "auto_increment": "AUTO_INCREMENT" in constraints.upper(),
        }
        
        # Procesar tamaño/precisión
        if size_info:
            column_info["size"] = self._parse_size_info(size_info, data_type)
        
        # Procesar valor por defecto
        default_match = re.search(r'DEFAULT\s+(.+?)(?:\s|$)', constraints, re.IGNORECASE)
        if default_match:
            default_value = default_match.group(1).strip()
            column_info["default"] = self._parse_default_value(default_value, data_type)
        
        return column_info
    
    def _parse_size_info(self, size_info, data_type):
        """
        Parsea información de tamaño para un tipo de datos.
        
        Args:
            size_info (str): Información de tamaño (ej: "100", "10,2")
            data_type (str): Tipo de dato SQL
            
        Returns:
            dict: Información de tamaño parseada
        """
        if ',' in size_info:
            # Tipos como DECIMAL(10,2)
            parts = [p.strip() for p in size_info.split(',')]
            return {
                "precision": int(parts[0]),
                "scale": int(parts[1]) if len(parts) > 1 else 0
            }
        else:
            # Tipos como VARCHAR(100)
            return {
                "length": int(size_info)
            }
    
    def _parse_default_value(self, default_value, data_type):
        """
        Parsea un valor por defecto según el tipo de dato.
        
        Args:
            default_value (str): Valor por defecto en SQL
            data_type (str): Tipo de dato SQL
            
        Returns:
            any: Valor por defecto convertido
        """
        default_value = default_value.strip()
        
        # Remover comillas si las tiene
        if (default_value.startswith("'") and default_value.endswith("'")) or \
           (default_value.startswith('"') and default_value.endswith('"')):
            default_value = default_value[1:-1]
        
        # Valores especiales
        if default_value.upper() in ['NULL', 'CURRENT_TIMESTAMP', 'NOW()']:
            return default_value.upper()
        
        # Convertir según tipo
        if data_type in ['INT', 'INTEGER', 'BIGINT', 'SMALLINT', 'TINYINT']:
            try:
                return int(default_value)
            except ValueError:
                return default_value
        
        elif data_type in ['DECIMAL', 'NUMERIC', 'FLOAT', 'DOUBLE', 'REAL']:
            try:
                return float(default_value)
            except ValueError:
                return default_value
        
        elif data_type in ['BOOLEAN', 'BOOL']:
            return default_value.upper() in ['TRUE', '1', 'YES']
        
        else:
            return default_value
    
    def _parse_constraints(self, columns_definition):
        """
        Parsea constraints de tabla.
        
        Args:
            columns_definition (str): Definición completa de columnas
            
        Returns:
            dict: Información de constraints
        """
        constraints = {
            "primary_keys": [],
            "foreign_keys": [],
            "unique_keys": [],
            "indexes": []
        }
        
        # Buscar PRIMARY KEY constraint
        pk_match = re.search(
            r'PRIMARY\s+KEY\s*\(([^)]+)\)',
            columns_definition,
            re.IGNORECASE
        )
        if pk_match:
            pk_fields = [f.strip().strip('`[]"\'') for f in pk_match.group(1).split(',')]
            constraints["primary_keys"] = pk_fields
        
        # Buscar FOREIGN KEY constraints
        fk_matches = re.finditer(
            r'FOREIGN\s+KEY\s*\(([^)]+)\)\s+REFERENCES\s+(\w+)\s*\(([^)]+)\)',
            columns_definition,
            re.IGNORECASE
        )
        for fk_match in fk_matches:
            local_fields = [f.strip().strip('`[]"\'') for f in fk_match.group(1).split(',')]
            ref_table = fk_match.group(2).strip('`[]"\'')
            ref_fields = [f.strip().strip('`[]"\'') for f in fk_match.group(3).split(',')]
            
            constraints["foreign_keys"].append({
                "local_fields": local_fields,
                "reference_table": ref_table,
                "reference_fields": ref_fields
            })
        
        return constraints
    
    def _split_column_definitions(self, columns_definition):
        """
        Divide las definiciones de columnas respetando paréntesis.
        
        Args:
            columns_definition (str): Definición completa
            
        Returns:
            list: Lista de definiciones individuales
        """
        definitions = []
        current = ""
        level = 0
        in_quotes = False
        quote_char = None
        
        for char in columns_definition + ',':
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
                definitions.append(current.strip())
                current = ""
            else:
                current += char
        
        return [d for d in definitions if d.strip()]
    
    def _build_json_schema(self, columns, constraints):
        """
        Construye un JSON Schema para validación en MongoDB.
        
        Args:
            columns (list): Lista de columnas
            constraints (dict): Constraints de la tabla
            
        Returns:
            dict: JSON Schema para MongoDB
        """
        schema = {
            "$jsonSchema": {
                "bsonType": "object",
                "title": "Generated schema from CREATE TABLE",
                "properties": {},
                "required": []
            }
        }
        
        # Agregar propiedades de columnas
        for column in columns:
            prop_name = column["name"]
            mongo_type = column["mongo_type"]
            
            property_def = {
                "bsonType": mongo_type["bsonType"],
                "description": f"Column {prop_name} ({column['sql_type']})"
            }
            
            # Agregar restricciones de tamaño
            if "size" in column and "length" in column["size"]:
                if mongo_type["type"] == "string":
                    property_def["maxLength"] = column["size"]["length"]
            
            # Agregar valor por defecto
            if "default" in column:
                property_def["default"] = column["default"]
            
            schema["$jsonSchema"]["properties"][prop_name] = property_def
            
            # Agregar a campos requeridos si NO es nullable
            if not column["nullable"]:
                schema["$jsonSchema"]["required"].append(prop_name)
        
        return schema
    
    def get_supported_sql_types(self):
        """
        Retorna los tipos SQL soportados.
        
        Returns:
            dict: Tipos soportados organizados por categoría
        """
        return {
            "numeric_types": ["INT", "INTEGER", "BIGINT", "SMALLINT", "TINYINT", 
                             "DECIMAL", "NUMERIC", "FLOAT", "DOUBLE", "REAL"],
            "string_types": ["VARCHAR", "CHAR", "TEXT", "LONGTEXT", "MEDIUMTEXT", "TINYTEXT"],
            "date_types": ["DATE", "DATETIME", "TIMESTAMP", "TIME"],
            "boolean_types": ["BOOLEAN", "BOOL"],
            "json_types": ["JSON"],
            "binary_types": ["BLOB", "LONGBLOB", "MEDIUMBLOB", "TINYBLOB"]
        }
import re
import logging
from .base_parser import BaseParser

# Configurar logging
logger = logging.getLogger(__name__)

class FunctionParser(BaseParser):
    """
    Parser especializado para funciones SQL.
    Maneja funciones de fecha, string, matemáticas y las convierte a MongoDB.
    """
    
    def __init__(self):
        """Inicializar el parser con mapeos de funciones."""
        
        # Funciones de fecha SQL → MongoDB
        self.date_functions = {
            'NOW': {'mongo': 'new Date()', 'type': 'current_date'},
            'CURRENT_DATE': {'mongo': 'new Date()', 'type': 'current_date'},
            'CURRENT_TIMESTAMP': {'mongo': 'new Date()', 'type': 'current_date'},
            'DATE': {'mongo': '$dateToString', 'type': 'date_format'},
            'YEAR': {'mongo': '$year', 'type': 'date_extract'},
            'MONTH': {'mongo': '$month', 'type': 'date_extract'},
            'DAY': {'mongo': '$dayOfMonth', 'type': 'date_extract'},
            'HOUR': {'mongo': '$hour', 'type': 'date_extract'},
            'MINUTE': {'mongo': '$minute', 'type': 'date_extract'},
            'SECOND': {'mongo': '$second', 'type': 'date_extract'},
            'DAYOFWEEK': {'mongo': '$dayOfWeek', 'type': 'date_extract'},
            'DAYOFYEAR': {'mongo': '$dayOfYear', 'type': 'date_extract'},
            'WEEK': {'mongo': '$week', 'type': 'date_extract'},
            'DATEADD': {'mongo': '$dateAdd', 'type': 'date_arithmetic'},
            'DATEDIFF': {'mongo': '$dateDiff', 'type': 'date_arithmetic'}
        }
        
        # Funciones de string SQL → MongoDB
        self.string_functions = {
            'UPPER': {'mongo': '$toUpper', 'type': 'string_transform'},
            'LOWER': {'mongo': '$toLower', 'type': 'string_transform'},
            'LENGTH': {'mongo': '$strLenCP', 'type': 'string_info'},
            'LEN': {'mongo': '$strLenCP', 'type': 'string_info'},
            'CONCAT': {'mongo': '$concat', 'type': 'string_combine'},
            'SUBSTRING': {'mongo': '$substr', 'type': 'string_extract'},
            'SUBSTR': {'mongo': '$substr', 'type': 'string_extract'},
            'LEFT': {'mongo': '$substr', 'type': 'string_extract'},
            'RIGHT': {'mongo': '$substr', 'type': 'string_extract'},
            'LTRIM': {'mongo': '$ltrim', 'type': 'string_clean'},
            'RTRIM': {'mongo': '$rtrim', 'type': 'string_clean'},
            'TRIM': {'mongo': '$trim', 'type': 'string_clean'},
            'REPLACE': {'mongo': '$replaceOne', 'type': 'string_modify'},
            'CHARINDEX': {'mongo': '$indexOfCP', 'type': 'string_search'},
            'LOCATE': {'mongo': '$indexOfCP', 'type': 'string_search'}
        }
        
        # Funciones matemáticas SQL → MongoDB
        self.math_functions = {
            'ABS': {'mongo': '$abs', 'type': 'math_basic'},
            'ROUND': {'mongo': '$round', 'type': 'math_round'},
            'CEIL': {'mongo': '$ceil', 'type': 'math_round'},
            'CEILING': {'mongo': '$ceil', 'type': 'math_round'},
            'FLOOR': {'mongo': '$floor', 'type': 'math_round'},
            'SQRT': {'mongo': '$sqrt', 'type': 'math_advanced'},
            'POWER': {'mongo': '$pow', 'type': 'math_advanced'},
            'POW': {'mongo': '$pow', 'type': 'math_advanced'},
            'MOD': {'mongo': '$mod', 'type': 'math_basic'},
            'SIGN': {'mongo': '$sign', 'type': 'math_basic'},
            'SIN': {'mongo': '$sin', 'type': 'math_trig'},
            'COS': {'mongo': '$cos', 'type': 'math_trig'},
            'TAN': {'mongo': '$tan', 'type': 'math_trig'},
            'LOG': {'mongo': '$log', 'type': 'math_log'},
            'LOG10': {'mongo': '$log10', 'type': 'math_log'},
            'EXP': {'mongo': '$exp', 'type': 'math_log'},
            'RAND': {'mongo': '$rand', 'type': 'math_random'},
            'RANDOM': {'mongo': '$rand', 'type': 'math_random'}
        }
        
        # Todas las funciones combinadas
        self.all_functions = {
            **self.date_functions,
            **self.string_functions, 
            **self.math_functions
        }
    
    def parse(self, query_or_clause):
        """
        Método principal para analizar funciones en una consulta.
        
        Args:
            query_or_clause (str): Consulta SQL o cláusula
            
        Returns:
            dict: Diccionario con funciones encontradas y traducciones
        """
        return self.parse_functions(query_or_clause)
    
    def has_functions(self, query):
        """
        Verifica si una consulta contiene funciones SQL.
        
        Args:
            query (str): Consulta SQL a analizar
            
        Returns:
            bool: True si contiene funciones, False en caso contrario
        """
        query_upper = query.upper()
        
        # Buscar patrones de funciones con paréntesis
        for func_name in self.all_functions.keys():
            pattern = rf'\b{func_name}\s*\('
            if re.search(pattern, query_upper):
                logger.debug(f"Función detectada: {func_name}")
                return True
        
        return False
    
    def parse_functions(self, query):
        """
        Extrae y analiza todas las funciones de una consulta SQL.
        
        Args:
            query (str): Consulta SQL a analizar
            
        Returns:
            list: Lista de diccionarios con información de funciones
        """
        functions = []
        
        # Buscar cada tipo de función
        functions.extend(self._find_date_functions(query))
        functions.extend(self._find_string_functions(query))
        functions.extend(self._find_math_functions(query))
        
        logger.info(f"Funciones encontradas: {len(functions)}")
        return functions
    
    def _find_date_functions(self, query):
        """Encuentra funciones de fecha en la consulta."""
        functions = []
        
        for func_name, func_info in self.date_functions.items():
            pattern = rf'\b{func_name}\s*\((.*?)\)'
            matches = re.finditer(pattern, query, re.IGNORECASE)
            
            for match in matches:
                args = match.group(1).strip() if match.group(1) else ""
                mongo_expr = self._translate_date_function(func_name, args, func_info)
                
                functions.append({
                    'original': match.group(0),
                    'function_name': func_name.lower(),
                    'function_type': 'date',
                    'args': args,
                    'mongo_expression': mongo_expr,
                    'category': func_info['type']
                })
        
        return functions
    
    def _find_string_functions(self, query):
        """Encuentra funciones de string en la consulta."""
        functions = []
        
        for func_name, func_info in self.string_functions.items():
            pattern = rf'\b{func_name}\s*\((.*?)\)'
            matches = re.finditer(pattern, query, re.IGNORECASE)
            
            for match in matches:
                args = match.group(1).strip() if match.group(1) else ""
                mongo_expr = self._translate_string_function(func_name, args, func_info)
                
                functions.append({
                    'original': match.group(0),
                    'function_name': func_name.lower(),
                    'function_type': 'string',
                    'args': args,
                    'mongo_expression': mongo_expr,
                    'category': func_info['type']
                })
        
        return functions
    
    def _find_math_functions(self, query):
        """Encuentra funciones matemáticas en la consulta."""
        functions = []
        
        for func_name, func_info in self.math_functions.items():
            pattern = rf'\b{func_name}\s*\((.*?)\)'
            matches = re.finditer(pattern, query, re.IGNORECASE)
            
            for match in matches:
                args = match.group(1).strip() if match.group(1) else ""
                mongo_expr = self._translate_math_function(func_name, args, func_info)
                
                functions.append({
                    'original': match.group(0),
                    'function_name': func_name.lower(),
                    'function_type': 'math',
                    'args': args,
                    'mongo_expression': mongo_expr,
                    'category': func_info['type']
                })
        
        return functions
    
    def _translate_date_function(self, func_name, args, func_info):
        """Traduce una función de fecha a MongoDB."""
        func_type = func_info['type']
        mongo_op = func_info['mongo']
        
        if func_type == 'current_date':
            # NOW(), CURRENT_DATE, etc.
            return "$$NOW"  # MongoDB 4.2+
        
        elif func_type == 'date_extract':
            # YEAR(field), MONTH(field), etc.
            field = self._clean_field_name(args)
            return {mongo_op: f"${field}"}
        
        elif func_type == 'date_format':
            # DATE(field) o DATE(field, format)
            field = self._clean_field_name(args)
            return {
                "$dateToString": {
                    "format": "%Y-%m-%d",
                    "date": f"${field}"
                }
            }
        
        elif func_type == 'date_arithmetic':
            # DATEADD, DATEDIFF (implementación básica)
            return {mongo_op: args}  # Requiere implementación específica
        
        return {mongo_op: args}
    
    def _translate_string_function(self, func_name, args, func_info):
        """Traduce una función de string a MongoDB."""
        func_type = func_info['type']
        mongo_op = func_info['mongo']
        
        if func_type == 'string_transform':
            # UPPER(field), LOWER(field)
            field = self._clean_field_name(args)
            return {mongo_op: f"${field}"}
        
        elif func_type == 'string_info':
            # LENGTH(field), LEN(field)
            field = self._clean_field_name(args)
            return {mongo_op: f"${field}"}
        
        elif func_type == 'string_combine':
            # CONCAT(field1, field2, ...)
            fields = self._parse_function_args(args)
            mongo_args = []
            for field in fields:
                if field.startswith("'") and field.endswith("'"):
                    mongo_args.append(field[1:-1])  # String literal
                else:
                    mongo_args.append(f"${self._clean_field_name(field)}")  # Field reference
            return {mongo_op: mongo_args}
        
        elif func_type == 'string_extract':
            # SUBSTRING(field, start, length), LEFT(field, length), RIGHT(field, length)
            fields = self._parse_function_args(args)
            if func_name.upper() == 'SUBSTRING' and len(fields) >= 3:
                field = self._clean_field_name(fields[0])
                start = int(fields[1]) - 1  # SQL es 1-indexed, MongoDB es 0-indexed
                length = int(fields[2])
                return {mongo_op: [f"${field}", start, length]}
            
            elif func_name.upper() == 'LEFT' and len(fields) >= 2:
                field = self._clean_field_name(fields[0])
                length = int(fields[1])
                return {mongo_op: [f"${field}", 0, length]}
            
            elif func_name.upper() == 'RIGHT' and len(fields) >= 2:
                field = self._clean_field_name(fields[0])
                length = int(fields[1])
                return {
                    "$substr": [
                        f"${field}",
                        {"$subtract": [{"$strLenCP": f"${field}"}, length]},
                        length
                    ]
                }
        
        elif func_type == 'string_clean':
            # TRIM(field), LTRIM(field), RTRIM(field)
            field = self._clean_field_name(args)
            return {mongo_op: {"input": f"${field}"}}
        
        elif func_type == 'string_modify':
            # REPLACE(field, old, new)
            fields = self._parse_function_args(args)
            if len(fields) >= 3:
                field = self._clean_field_name(fields[0])
                old_str = fields[1].strip("'\"")
                new_str = fields[2].strip("'\"")
                return {
                    mongo_op: {
                        "input": f"${field}",
                        "find": old_str,
                        "replacement": new_str
                    }
                }
        
        elif func_type == 'string_search':
            # CHARINDEX(substring, field), LOCATE(substring, field)
            fields = self._parse_function_args(args)
            if len(fields) >= 2:
                substring = fields[0].strip("'\"")
                field = self._clean_field_name(fields[1])
                return {
                    "$add": [
                        {mongo_op: [f"${field}", substring]},
                        1  # SQL devuelve 1-indexed
                    ]
                }
        
        return {mongo_op: args}
    
    def _translate_math_function(self, func_name, args, func_info):
        """Traduce una función matemática a MongoDB."""
        func_type = func_info['type']
        mongo_op = func_info['mongo']
        
        if func_type in ['math_basic', 'math_round', 'math_advanced', 'math_trig', 'math_log']:
            fields = self._parse_function_args(args)
            
            if len(fields) == 1:
                # Funciones de un argumento: ABS(field), SQRT(field), etc.
                field = self._clean_field_name(fields[0])
                if field.replace('.', '').replace('-', '').isdigit():
                    # Es un número literal
                    return {mongo_op: float(field)}
                else:
                    # Es un campo
                    return {mongo_op: f"${field}"}
            
            elif len(fields) == 2:
                # Funciones de dos argumentos: POWER(base, exp), MOD(a, b), etc.
                arg1 = self._parse_numeric_arg(fields[0])
                arg2 = self._parse_numeric_arg(fields[1])
                return {mongo_op: [arg1, arg2]}
        
        elif func_type == 'math_random':
            # RAND(), RANDOM()
            return {mongo_op: {}}
        
        return {mongo_op: args}
    
    def _parse_function_args(self, args_str):
        """
        Parsea argumentos de función separados por comas.
        Maneja comillas y espacios correctamente.
        """
        if not args_str.strip():
            return []
        
        args = []
        current_arg = ""
        in_quotes = False
        quote_char = None
        paren_level = 0
        
        for char in args_str:
            if char in ["'", '"'] and (not in_quotes or char == quote_char):
                in_quotes = not in_quotes
                if in_quotes:
                    quote_char = char
                else:
                    quote_char = None
                current_arg += char
            elif char == '(' and not in_quotes:
                paren_level += 1
                current_arg += char
            elif char == ')' and not in_quotes:
                paren_level -= 1
                current_arg += char
            elif char == ',' and not in_quotes and paren_level == 0:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += char
        
        if current_arg.strip():
            args.append(current_arg.strip())
        
        return args
    
    def _clean_field_name(self, field):
        """Limpia el nombre de campo eliminando comillas y espacios."""
        if not field:
            return field
        
        field = field.strip()
        
        # Eliminar comillas si las tiene
        if (field.startswith("'") and field.endswith("'")) or \
           (field.startswith('"') and field.endswith('"')):
            return field[1:-1]
        
        return field
    
    def _parse_numeric_arg(self, arg):
        """Parsea un argumento que puede ser número o campo."""
        cleaned = self._clean_field_name(arg)
        
        # Intentar convertir a número
        try:
            if '.' in cleaned:
                return float(cleaned)
            else:
                return int(cleaned)
        except ValueError:
            # Es un campo, no un número
            return f"${cleaned}"
    
    def get_supported_functions(self):
        """
        Retorna información sobre las funciones soportadas.
        
        Returns:
            dict: Diccionario con funciones organizadas por categoría
        """
        return {
            "date_functions": {
                "current_date": ["NOW", "CURRENT_DATE", "CURRENT_TIMESTAMP"],
                "date_extract": ["YEAR", "MONTH", "DAY", "HOUR", "MINUTE", "SECOND", "DAYOFWEEK", "WEEK"],
                "date_format": ["DATE"],
                "date_arithmetic": ["DATEADD", "DATEDIFF"]
            },
            "string_functions": {
                "string_transform": ["UPPER", "LOWER"],
                "string_info": ["LENGTH", "LEN"],
                "string_combine": ["CONCAT"],
                "string_extract": ["SUBSTRING", "SUBSTR", "LEFT", "RIGHT"],
                "string_clean": ["TRIM", "LTRIM", "RTRIM"],
                "string_modify": ["REPLACE"],
                "string_search": ["CHARINDEX", "LOCATE"]
            },
            "math_functions": {
                "math_basic": ["ABS", "MOD", "SIGN"],
                "math_round": ["ROUND", "CEIL", "CEILING", "FLOOR"],
                "math_advanced": ["SQRT", "POWER", "POW"],
                "math_trig": ["SIN", "COS", "TAN"],
                "math_log": ["LOG", "LOG10", "EXP"],
                "math_random": ["RAND", "RANDOM"]
            }
        }
    
    def translate_field_with_functions(self, field_expression):
        """
        Traduce una expresión de campo que puede contener funciones.
        
        Args:
            field_expression (str): Expresión SQL con posibles funciones
            
        Returns:
            dict: Expresión MongoDB equivalente
        """
        if not self.has_functions(field_expression):
            # Si no hay funciones, devolver el campo tal como está
            return self._clean_field_name(field_expression)
        
        # Si hay funciones, analizarlas y crear la expresión MongoDB
        functions = self.parse_functions(field_expression)
        
        if len(functions) == 1:
            # Una sola función, devolver su traducción directamente
            return functions[0]['mongo_expression']
        
        elif len(functions) > 1:
            # Múltiples funciones, necesita manejo más complejo
            # Por ahora, devolver la primera función
            logger.warning(f"Múltiples funciones en una expresión no completamente soportado: {field_expression}")
            return functions[0]['mongo_expression']
        
        return field_expression
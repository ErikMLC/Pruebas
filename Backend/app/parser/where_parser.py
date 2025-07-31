import re
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class WhereParser:
    """
    Parser especializado para cláusulas WHERE de SQL.
    Analiza condiciones WHERE y las convierte a formato MongoDB.
    """
    
    def parse(self, query):
        """
        Analiza la cláusula WHERE de una consulta SQL.
        
        Args:
            query (str): Consulta SQL completa
            
        Returns:
            dict: Diccionario con las condiciones en formato MongoDB
        """
        logger.info(f"Analizando cláusula WHERE de consulta: {query}")
        
        # Extraer la parte WHERE
        where_clause = self.extract_where_clause(query)
        
        if not where_clause:
            return {}
        
        # Analizar las condiciones
        conditions = {}
        self._parse_conditions(where_clause, conditions)
        
        logger.info(f"Condiciones WHERE traducidas: {conditions}")
        return conditions
    

    def extract_where_clause(self, query):
        """
        🔧 MÉTODO CORREGIDO: Extrae WHERE sin incluir punto y coma
        """
        query = " " + query.strip() + " "
        
        # Regex corregido que excluye el punto y coma
        pattern = r'\sWHERE\s+(.*?)(?:\s+GROUP\s+BY|\s+HAVING|\s+ORDER\s+BY|\s+LIMIT|\s+OFFSET|\s*;|\s*$)'
        match = re.search(pattern, query, re.IGNORECASE | re.DOTALL)
        
        if match:
            where_clause = match.group(1).strip()
            
            # 🆕 LIMPIEZA ADICIONAL: Remover punto y coma final
            if where_clause.endswith(';'):
                where_clause = where_clause[:-1].strip()
            
            logger.info(f"Cláusula WHERE extraída y limpia: '{where_clause}'")
            return where_clause
        
        return None


    def _parse_conditions(self, conditions_str, result):
        """
        Analiza las condiciones de una cláusula WHERE.
        
        Args:
            conditions_str (str): String con las condiciones
            result (dict): Diccionario donde se almacenarán las condiciones
        """
        # Normalizar la condición
        conditions_str = conditions_str.strip()
        
        # Verificar si hay operadores lógicos a nivel superior
        if self._has_top_level_operator(conditions_str, "OR"):
            # Manejar condiciones OR
            parts = self._split_by_top_level_operator(conditions_str, "OR")
            or_conditions = []
            
            for part in parts:
                part_dict = {}
                self._parse_conditions(part.strip(), part_dict)
                if part_dict:
                    or_conditions.append(part_dict)
            
            if or_conditions:
                result["$or"] = or_conditions
            return
            
        if self._has_top_level_operator(conditions_str, "AND"):
            # Manejar condiciones AND
            parts = self._split_by_top_level_operator(conditions_str, "AND")
            
            for part in parts:
                sub_condition = {}
                self._parse_conditions(part.strip(), sub_condition)
                # Mezclar condiciones AND en el resultado principal
                result.update(sub_condition)
            return
        
        # Si llegamos aquí, es una condición simple
        self._parse_simple_condition(conditions_str, result)


    
    def _parse_simple_condition(self, condition_str, result):
        """
        🔧 MÉTODO CORREGIDO: Analiza una condición simple con limpieza de punto y coma
        
        Args:
            condition_str (str): String con la condición simple
            result (dict): Diccionario donde se almacenará la condición
        """
        logger.debug(f"Parseando condición simple: '{condition_str}'")
        
        # 🆕 LIMPIEZA INICIAL: Remover punto y coma de toda la condición
        condition_str = condition_str.strip()
        if condition_str.endswith(';'):
            condition_str = condition_str[:-1].strip()
        
        # Operadores de comparación estándar
        operators = {
            ">=": "$gte",
            "<=": "$lte", 
            "<>": "$ne",
            "!=": "$ne",
            "=": "$eq",
            ">": "$gt",
            "<": "$lt"
        }
        
        # Manejar operadores especiales PRIMERO
        
        # BETWEEN
        between_match = re.search(r'([\w.]+)\s+BETWEEN\s+(.*?)\s+AND\s+(.*?)(?:\s*;|\s*$)', condition_str, re.IGNORECASE)
        if between_match:
            field = between_match.group(1).strip()
            min_val_str = between_match.group(2).strip()
            max_val_str = between_match.group(3).strip()
            
            # 🔧 LIMPIAR VALORES
            min_val = self._parse_value(self._clean_value(min_val_str))
            max_val = self._parse_value(self._clean_value(max_val_str))
            
            result[field] = {"$gte": min_val, "$lte": max_val}
            logger.debug(f"BETWEEN parseado: {field} BETWEEN {min_val} AND {max_val}")
            return
        
        # IN
        in_match = re.search(r'([\w.]+)\s+IN\s+\((.*?)\)', condition_str, re.IGNORECASE)
        if in_match:
            field = in_match.group(1).strip()
            values_str = in_match.group(2).strip()
            
            # 🔧 LIMPIAR CADA VALOR EN LA LISTA
            values = []
            for v in self._split_values(values_str):
                cleaned_value = self._clean_value(v.strip())
                parsed_value = self._parse_value(cleaned_value)
                values.append(parsed_value)
            
            result[field] = {"$in": values}
            logger.debug(f"IN parseado: {field} IN {values}")
            return
        
        # NOT IN - Corregido para usar $nin
        not_in_match = re.search(r'([\w.]+)\s+NOT\s+IN\s+\((.*?)\)', condition_str, re.IGNORECASE)
        if not_in_match:
            field = not_in_match.group(1).strip()
            values_str = not_in_match.group(2).strip()
            
            # 🔧 LIMPIAR CADA VALOR EN LA LISTA
            values = []
            for v in self._split_values(values_str):
                cleaned_value = self._clean_value(v.strip())
                parsed_value = self._parse_value(cleaned_value)
                values.append(parsed_value)
            
            result[field] = {"$nin": values}
            logger.debug(f"NOT IN parseado: {field} NOT IN {values}")
            return
        
        # LIKE
        like_match = re.search(r'([\w.]+)\s+LIKE\s+(.*?)(?:\s*;|\s*$)', condition_str, re.IGNORECASE)
        if like_match:
            field = like_match.group(1).strip()
            pattern_str = like_match.group(2).strip()
            
            # 🔧 LIMPIAR PATRÓN
            pattern_str = self._clean_value(pattern_str)
            
            if (pattern_str.startswith("'") and pattern_str.endswith("'")) or \
            (pattern_str.startswith('"') and pattern_str.endswith('"')):
                pattern = pattern_str[1:-1]  # Quitar comillas
            else:
                pattern = pattern_str
            
            # Convertir patrón SQL a regex MongoDB
            mongo_pattern = pattern.replace("%", ".*").replace("_", ".")
            result[field] = {"$regex": mongo_pattern, "$options": "i"}
            logger.debug(f"LIKE parseado: {field} LIKE '{pattern}' -> regex: {mongo_pattern}")
            return
        
        # IS NULL
        is_null_match = re.search(r'([\w.]+)\s+IS\s+NULL(?:\s*;|\s*$)', condition_str, re.IGNORECASE)
        if is_null_match:
            field = is_null_match.group(1).strip()
            result[field] = {"$exists": False}
            logger.debug(f"IS NULL parseado: {field}")
            return
        
        # IS NOT NULL
        is_not_null_match = re.search(r'([\w.]+)\s+IS\s+NOT\s+NULL(?:\s*;|\s*$)', condition_str, re.IGNORECASE)
        if is_not_null_match:
            field = is_not_null_match.group(1).strip()
            result[field] = {"$exists": True}
            logger.debug(f"IS NOT NULL parseado: {field}")
            return
        
        # Operadores de comparación estándar
        for op in sorted(operators.keys(), key=len, reverse=True):
            if op in condition_str:
                parts = condition_str.split(op, 1)
                if len(parts) == 2:
                    field = parts[0].strip()
                    value_str = parts[1].strip()
                    
                    # 🔧 CRÍTICO: LIMPIAR EL VALOR ANTES DE PARSEARLO
                    cleaned_value_str = self._clean_value(value_str)
                    value = self._parse_value(cleaned_value_str)
                    
                    # Si el operador es '=', podemos usar el valor directamente en MongoDB
                    if op == "=":
                        result[field] = value
                    else:
                        result[field] = {operators[op]: value}
                    
                    logger.debug(f"Condición parseada: {field} {op} '{cleaned_value_str}' -> {value}")
                    return
        
        logger.warning(f"No se pudo analizar la condición: {condition_str}")

    def _clean_value(self, value_str):
        """
        🆕 NUEVO: Método auxiliar para limpiar valores individuales
        
        Args:
            value_str (str): Valor a limpiar
            
        Returns:
            str: Valor limpio sin punto y coma
        """
        if not value_str:
            return value_str
        
        # Remover espacios
        cleaned = value_str.strip()
        
        # 🔧 CRÍTICO: Remover punto y coma final solo si NO está entre comillas
        if cleaned.endswith(';'):
            # Verificar que no esté entre comillas
            if not ((cleaned.startswith("'") and cleaned.count("'") >= 2) or
                    (cleaned.startswith('"') and cleaned.count('"') >= 2)):
                cleaned = cleaned[:-1].strip()
        
        logger.debug(f"Valor limpio: '{value_str}' -> '{cleaned}'")
        return cleaned 



    def _has_top_level_operator(self, text, operator):
        """
        Verifica si hay un operador específico a nivel superior (fuera de paréntesis).
        
        Args:
            text (str): Texto a analizar
            operator (str): Operador a buscar (AND/OR)
            
        Returns:
            bool: True si hay operador a nivel superior, False en caso contrario
        """
        pattern = r'\s' + operator + r'\s'
        level = 0
        
        for i in range(len(text) - len(operator)):
            if text[i] == '(':
                level += 1
            elif text[i] == ')':
                level -= 1
            elif level == 0 and re.match(pattern, text[i:i+len(operator)+2], re.IGNORECASE):
                return True
        
        return False
    
    def _split_by_top_level_operator(self, text, operator):
        """
        Divide el texto por un operador específico a nivel superior.
        
        Args:
            text (str): Texto a dividir
            operator (str): Operador para dividir (AND/OR)
            
        Returns:
            list: Lista de partes divididas
        """
        result = []
        current = ""
        level = 0
        i = 0
        
        op_pattern = r'\s' + operator + r'\s'
        text = " " + text + " "  # Añadir espacios para facilitar la coincidencia
        
        while i < len(text):
            if text[i] == '(':
                level += 1
                current += text[i]
            elif text[i] == ')':
                level -= 1
                current += text[i]
            elif level == 0 and i <= len(text) - len(operator) - 2:
                # Verificar si esta parte coincide con el operador (con espacios)
                part = text[i:i+len(operator)+2]
                if re.match(op_pattern, part, re.IGNORECASE):
                    # Encontramos el operador, guardamos la parte actual
                    if current.strip():
                        result.append(current.strip())
                    current = ""
                    # Saltar el operador
                    i += len(operator)
                else:
                    current += text[i]
            else:
                current += text[i]
            i += 1
        
        # Añadir la última parte si no está vacía
        if current.strip():
            result.append(current.strip())
        
        return result
    
    def _split_values(self, values_str):
        """
        Divide una lista de valores separados por comas, respetando comillas.
        
        Args:
            values_str (str): String con valores separados por comas
            
        Returns:
            list: Lista de valores individuales
        """
        if not values_str:
            return []
            
        values = []
        current = ""
        in_quotes = False
        quote_char = None
        
        for char in values_str + ',':  # Añadir coma al final para capturar el último valor
            if char in ["'", '"'] and (not in_quotes or char == quote_char):
                in_quotes = not in_quotes
                current += char
            elif char == ',' and not in_quotes:
                values.append(current.strip())
                current = ""
            else:
                current += char
        
        return values
    
    def _parse_value(self, value_str):
        """
        Parsea un valor desde un string a su tipo adecuado (int, float, bool, None, str).
        
        Args:
            value_str (str): Valor a convertir
            
        Returns:
            El valor convertido al tipo apropiado
        """
        if value_str is None:
            return None
            
        # Limpiar espacios
        value_str = value_str.strip()
        
        # Si está entre comillas, es una cadena
        if (value_str.startswith("'") and value_str.endswith("'")) or \
           (value_str.startswith('"') and value_str.endswith('"')):
            return value_str[1:-1]
        
        # Si es NULL, devolver None
        if value_str.upper() == "NULL":
            return None
        
        # Si es TRUE o FALSE, devolver booleano
        if value_str.upper() == "TRUE":
            return True
        if value_str.upper() == "FALSE":
            return False
        
        # Si tiene punto decimal, intentar convertir a float
        if "." in value_str:
            try:
                return float(value_str)
            except ValueError:
                pass
        
        # Intentar convertir a entero
        try:
            return int(value_str)
        except ValueError:
            pass
        
        # Si no coincide con ningún tipo, devolver como string
        return value_str
import re
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class WhereParser:
    """
    Parser especializado para cláusulas WHERE de SQL.
    Analiza condiciones WHERE y las convierte a formato MongoDB.
    🔧 CORREGIDO: Manejo mejorado de BETWEEN
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
        🔧 MÉTODO CORREGIDO: Manejo mejorado de paréntesis y operadores anidados
        """
        # Normalizar la condición
        conditions_str = conditions_str.strip()
        
        # 🆕 PASO 1: Limpiar paréntesis externos si envuelven toda la expresión
        conditions_str = self._remove_outer_parentheses(conditions_str)
        
        # 🔧 CRÍTICO: Verificar si es una condición BETWEEN completa PRIMERO
        between_pattern = r'\w+\s+BETWEEN\s+.+?\s+AND\s+.+?(?:\s*;|\s*$)'
        if re.search(between_pattern, conditions_str, re.IGNORECASE):
            logger.debug("🔍 Condición BETWEEN detectada, procesando como condición simple")
            self._parse_simple_condition(conditions_str, result)
            return
        
        # 🔧 MEJORADO: Solo si NO es BETWEEN, proceder con la lógica de AND/OR
        if self._has_top_level_operator(conditions_str, "OR"):
            logger.debug(f"🔄 Procesando condiciones OR: {conditions_str}")
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
            logger.debug(f"🔄 Procesando condiciones AND: {conditions_str}")
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


    def _remove_outer_parentheses(self, text):
        """
        🆕 NUEVO: Remueve paréntesis externos que envuelven toda la expresión
        """
        text = text.strip()
        
        # Verificar si toda la expresión está envuelta en paréntesis
        if text.startswith('(') and text.endswith(')'):
            # Verificar que los paréntesis estén balanceados
            paren_count = 0
            for i, char in enumerate(text):
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                    # Si llegamos a 0 antes del final, los paréntesis externos no envuelven todo
                    if paren_count == 0 and i < len(text) - 1:
                        return text
            
            # Si llegamos aquí, los paréntesis externos sí envuelven toda la expresión
            return text[1:-1].strip()
        
        return text



    def _parse_simple_condition(self, condition_str, result):
        """
        🔧 MÉTODO CORREGIDO: Análisis mejorado de condiciones simples con BETWEEN
        
        Args:
            condition_str (str): String con la condición simple
            result (dict): Diccionario donde se almacenará la condición
        """
        logger.debug(f"Parseando condición simple: '{condition_str}'")
        
        # 🆕 LIMPIEZA INICIAL: Remover punto y coma de toda la condición
        condition_str = condition_str.strip()
        if condition_str.endswith(';'):
            condition_str = condition_str[:-1].strip()
        
        # 🔧 CRÍTICO: Manejo mejorado de BETWEEN
        # Patrón más robusto que captura correctamente los valores
        between_pattern = r'(\w+)\s+BETWEEN\s+([^A]+?)\s+AND\s+(.+?)(?:\s*;|\s*$)'
        between_match = re.search(between_pattern, condition_str, re.IGNORECASE)
        
        if between_match:
            field = between_match.group(1).strip()
            min_val_str = between_match.group(2).strip()
            max_val_str = between_match.group(3).strip()
            
            logger.debug(f"🔍 BETWEEN detectado - Campo: '{field}', Min: '{min_val_str}', Max: '{max_val_str}'")
            
            # 🔧 LIMPIAR Y PARSEAR VALORES
            min_val = self._parse_value(self._clean_value(min_val_str))
            max_val = self._parse_value(self._clean_value(max_val_str))
            
            # 🔧 VALIDACIÓN: Asegurar que los valores son numéricos para BETWEEN
            try:
                # Intentar convertir a números si no lo son ya
                if isinstance(min_val, str) and min_val.replace('.', '').replace('-', '').isdigit():
                    min_val = float(min_val) if '.' in min_val else int(min_val)
                if isinstance(max_val, str) and max_val.replace('.', '').replace('-', '').isdigit():
                    max_val = float(max_val) if '.' in max_val else int(max_val)
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Valores BETWEEN no numéricos: min={min_val}, max={max_val}")
            
            result[field] = {"$gte": min_val, "$lte": max_val}
            logger.debug(f"✅ BETWEEN parseado: {field} BETWEEN {min_val} AND {max_val}")
            return
        
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
            
            # 🔧 CORREGIDO: Convertir patrón SQL a regex MongoDB más preciso
            mongo_pattern = pattern.replace("%", ".*").replace("_", ".")
            
            # 🔧 CRÍTICO: Hacer que 'M%' sea case-sensitive para match exacto
            if pattern.endswith('%') and not pattern.startswith('%'):
                # Patrón como 'M%' - debe empezar con M exactamente
                mongo_pattern = "^" + mongo_pattern  # Añadir ^ para inicio de string
                result[field] = {"$regex": mongo_pattern}  # SIN $options: 'i' para case-sensitive
            else:
                # Otros patrones LIKE mantienen case-insensitive
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
        🆕 MÉTODO MEJORADO: Limpieza robusta de valores
        
        Args:
            value_str (str): Valor a limpiar
            
        Returns:
            str: Valor limpio sin punto y coma ni espacios extra
        """
        if not value_str:
            return value_str
        
        # Remover espacios al inicio y final
        cleaned = value_str.strip()
        
        # 🔧 CRÍTICO: Remover punto y coma final solo si NO está entre comillas
        if cleaned.endswith(';'):
            # Verificar que no esté entre comillas
            quote_count_single = cleaned.count("'")
            quote_count_double = cleaned.count('"')
            
            # Si no hay comillas o están balanceadas, es seguro remover el punto y coma
            if (quote_count_single == 0 or quote_count_single % 2 == 0) and \
               (quote_count_double == 0 or quote_count_double % 2 == 0):
                cleaned = cleaned[:-1].strip()
        
        logger.debug(f"🧹 Valor limpio: '{value_str}' -> '{cleaned}'")
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
        🔧 MÉTODO CORREGIDO: Divide texto por operador a nivel superior con mejor manejo de paréntesis
        """
        result = []
        current = ""
        paren_level = 0
        i = 0
        
        # Patrón del operador con espacios alrededor
        op_pattern = rf'\s+{operator}\s+'
        
        while i < len(text):
            char = text[i]
            
            # Contar paréntesis
            if char == '(':
                paren_level += 1
            elif char == ')':
                paren_level -= 1
            
            # Solo buscar operador si estamos a nivel 0 (fuera de paréntesis)
            if paren_level == 0:
                # Verificar si encontramos el operador en esta posición
                remaining = text[i:]
                match = re.match(op_pattern, remaining, re.IGNORECASE)
                
                if match:
                    # Encontramos el operador a nivel superior
                    if current.strip():
                        result.append(current.strip())
                    current = ""
                    # Saltar el operador
                    i += len(match.group(0))
                    continue
            
            current += char
            i += 1
        
        # Añadir la última parte si no está vacía
        if current.strip():
            result.append(current.strip())
        
        logger.debug(f"🔧 División por {operator}: {result}")
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
                if in_quotes:
                    quote_char = char
                else:
                    quote_char = None
                current += char
            elif char == ',' and not in_quotes:
                values.append(current.strip())
                current = ""
            else:
                current += char
        
        return values
    
    def _parse_value(self, value_str):
        """
        🔧 MÉTODO MEJORADO: Parsea un valor con mejor manejo de tipos
        
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
        
        # 🔧 MEJORADO: Manejo más robusto de números
        # Verificar si es un número decimal
        if re.match(r'^-?\d+\.\d+$', value_str):
            try:
                return float(value_str)
            except ValueError:
                pass
        
        # Verificar si es un número entero
        if re.match(r'^-?\d+$', value_str):
            try:
                return int(value_str)
            except ValueError:
                pass
        
        # Si no coincide con ningún tipo, devolver como string
        return value_str
    
    def test_between_parsing(self, condition_str):
        """
        🆕 MÉTODO DE PRUEBA: Para depurar problemas con BETWEEN
        
        Args:
            condition_str (str): Condición BETWEEN a probar
            
        Returns:
            dict: Resultado del parsing
        """
        logger.info(f"🧪 Probando BETWEEN: '{condition_str}'")
        
        result = {}
        self._parse_simple_condition(condition_str, result)
        
        logger.info(f"🧪 Resultado: {result}")
        return result
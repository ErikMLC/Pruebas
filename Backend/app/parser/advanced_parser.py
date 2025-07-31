import re
import logging
from .base_parser import BaseParser

# Configurar logging
logger = logging.getLogger(__name__)

class AdvancedParser(BaseParser):
    """
    Parser especializado para funcionalidades SQL avanzadas.
    Maneja DISTINCT, HAVING, subqueries básicas, UNION y otras características avanzadas.
    """
    
    def __init__(self):
        """Inicializar el parser con patrones y configuraciones."""
        
        # Patrones de expresiones regulares para diferentes funcionalidades
        self.distinct_pattern = r'\bSELECT\s+DISTINCT\s+'
        self.having_pattern = r'\bHAVING\s+(.*?)(?:\s+ORDER\s+BY|\s+LIMIT|\s+UNION|\s*;|\s*$)'
        self.union_pattern = r'\bUNION(?:\s+ALL)?\s+'
        self.subquery_pattern = r'\(\s*SELECT\s+.*?\)'
        
        # Funciones de agregación para validación con HAVING
        self.aggregate_functions = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP_CONCAT']
    
    def parse(self, query_or_clause):
        """
        Método principal para analizar funcionalidades avanzadas en una consulta.
        
        Args:
            query_or_clause (str): Consulta SQL o cláusula
            
        Returns:
            dict: Diccionario con funcionalidades avanzadas encontradas
        """
        result = {
            'has_distinct': self.has_distinct(query_or_clause),
            'has_having': self.has_having(query_or_clause),
            'has_union': self.has_union(query_or_clause),
            'has_subquery': self.has_subquery(query_or_clause)
        }
        
        if result['has_distinct']:
            result['distinct_info'] = self.parse_distinct(query_or_clause)
        
        if result['has_having']:
            result['having_clause'] = self.parse_having(query_or_clause)
        
        if result['has_union']:
            result['union_info'] = self.parse_union(query_or_clause)
        
        if result['has_subquery']:
            result['subqueries'] = self.parse_subqueries(query_or_clause)
        
        return result
    
    # =================== DISTINCT ===================
    
    def has_distinct(self, query):
        """
        Verifica si una consulta contiene SELECT DISTINCT.
        
        Args:
            query (str): Consulta SQL a analizar
            
        Returns:
            bool: True si contiene DISTINCT, False en caso contrario
        """
        return bool(re.search(self.distinct_pattern, query, re.IGNORECASE))
    
    def parse_distinct(self, query):
        """
        Analiza una consulta SELECT DISTINCT y extrae información.
        
        Args:
            query (str): Consulta SQL con DISTINCT
            
        Returns:
            dict: Información sobre la consulta DISTINCT
        """
        logger.info(f"Analizando consulta DISTINCT: {query}")
        
        # Extraer los campos después de DISTINCT
        distinct_match = re.search(
            r'SELECT\s+DISTINCT\s+(.*?)\s+FROM', 
            query, 
            re.IGNORECASE | re.DOTALL
        )
        
        if not distinct_match:
            logger.warning("No se pudo extraer campos DISTINCT")
            return {"error": "No se pudo extraer campos DISTINCT"}
        
        fields_str = distinct_match.group(1).strip()
        
        # Parsear los campos
        fields = self._parse_select_fields(fields_str)
        
        return {
            "operation": "DISTINCT",
            "fields": fields,
            "mongo_operation": "aggregate",
            "requires_grouping": True
        }
    
    def translate_distinct_to_mongodb(self, query, base_pipeline=None):
        """
        Traduce SELECT DISTINCT a pipeline de agregación MongoDB.
        
        Args:
            query (str): Consulta SQL con DISTINCT
            base_pipeline (list): Pipeline base opcional
            
        Returns:
            list: Pipeline de agregación MongoDB
        """
        distinct_info = self.parse_distinct(query)
        if "error" in distinct_info:
            return []
        
        pipeline = base_pipeline or []
        
        # Crear etapa $group para DISTINCT
        group_stage = {"$group": {"_id": {}}}
        
        # Agregar campos al _id para hacer DISTINCT
        for field_info in distinct_info["fields"]:
            field = field_info.get("field", "")
            if field and field != "*":
                # Limpiar el nombre del campo
                clean_field = field.strip('`[]"\'')
                group_stage["$group"]["_id"][clean_field] = f"${clean_field}"
        
        pipeline.append(group_stage)
        
        # Proyectar los campos de vuelta
        project_stage = {"$project": {}}
        for field_info in distinct_info["fields"]:
            field = field_info.get("field", "")
            alias = field_info.get("alias", field)
            if field and field != "*":
                clean_field = field.strip('`[]"\'')
                project_stage["$project"][alias] = f"$_id.{clean_field}"
        
        # Ocultar el _id
        project_stage["$project"]["_id"] = 0
        pipeline.append(project_stage)
        
        logger.info(f"Pipeline DISTINCT generado: {pipeline}")
        return pipeline
    
    # =================== HAVING ===================
    
    def has_having(self, query):
        """
        Verifica si una consulta contiene cláusula HAVING.
        
        Args:
            query (str): Consulta SQL a analizar
            
        Returns:
            bool: True si contiene HAVING, False en caso contrario
        """
        return bool(re.search(self.having_pattern, query, re.IGNORECASE))
    
    def parse_having(self, query):
        """
        Analiza una cláusula HAVING y la convierte a formato MongoDB.
        
        Args:
            query (str): Consulta SQL con HAVING
            
        Returns:
            dict: Condiciones HAVING en formato MongoDB
        """
        logger.info(f"Analizando cláusula HAVING: {query}")
        
        # Extraer la cláusula HAVING
        having_match = re.search(self.having_pattern, query, re.IGNORECASE | re.DOTALL)
        
        if not having_match:
            logger.warning("No se pudo extraer cláusula HAVING")
            return {}
        
        having_clause = having_match.group(1).strip()
        logger.debug(f"Cláusula HAVING extraída: {having_clause}")
        
        # Analizar las condiciones HAVING
        conditions = self._parse_having_conditions(having_clause)
        
        return conditions
    
    def _parse_having_conditions(self, having_clause):
        """
        Analiza las condiciones de una cláusula HAVING.
        
        Args:
            having_clause (str): String con las condiciones HAVING
            
        Returns:
            dict: Condiciones en formato MongoDB para $match después de $group
        """
        conditions = {}
        
        # Verificar operadores lógicos
        if self._has_top_level_operator(having_clause, "OR"):
            # Manejar condiciones OR
            parts = self._split_by_top_level_operator(having_clause, "OR")
            or_conditions = []
            
            for part in parts:
                part_dict = self._parse_simple_having_condition(part.strip())
                if part_dict:
                    or_conditions.append(part_dict)
            
            if or_conditions:
                conditions["$or"] = or_conditions
        
        elif self._has_top_level_operator(having_clause, "AND"):
            # Manejar condiciones AND
            parts = self._split_by_top_level_operator(having_clause, "AND")
            
            for part in parts:
                part_condition = self._parse_simple_having_condition(part.strip())
                conditions.update(part_condition)
        
        else:
            # Condición simple
            conditions = self._parse_simple_having_condition(having_clause)
        
        return conditions
    
    def _parse_simple_having_condition(self, condition_str):
        """
        Analiza una condición simple de HAVING.
        
        Args:
            condition_str (str): Condición HAVING simple
            
        Returns:
            dict: Condición en formato MongoDB
        """
        result = {}
        
        # Operadores de comparación
        operators = {
            ">=": "$gte",
            "<=": "$lte", 
            "<>": "$ne",
            "!=": "$ne",
            "=": "$eq",
            ">": "$gt",
            "<": "$lt"
        }
        
        # Buscar operadores de comparación
        for op in sorted(operators.keys(), key=len, reverse=True):
            if op in condition_str:
                parts = condition_str.split(op, 1)
                if len(parts) == 2:
                    left_part = parts[0].strip()
                    right_part = parts[1].strip()
                    
                    # El lado izquierdo debe ser una función de agregación o alias
                    field_name = self._extract_having_field(left_part)
                    value = self._parse_value(right_part)
                    
                    if op == "=":
                        result[field_name] = value
                    else:
                        result[field_name] = {operators[op]: value}
                    
                    break
        
        return result
    
    def _extract_having_field(self, field_expr):
        """
        Extrae el nombre del campo de una expresión HAVING.
        Para funciones de agregación, usa el alias o genera uno.
        
        Args:
            field_expr (str): Expresión del campo
            
        Returns:
            str: Nombre del campo para usar en MongoDB
        """
        # Si es una función de agregación, extraer el alias o generar uno
        for func in self.aggregate_functions:
            pattern = rf'{func}\s*\((.*?)\)'
            match = re.search(pattern, field_expr, re.IGNORECASE)
            if match:
                inner_field = match.group(1).strip()
                if inner_field == "*":
                    return f"{func.lower()}_all"
                else:
                    return f"{func.lower()}_{inner_field.lower()}"
        
        # Si no es una función, asumir que es un alias o campo simple
        return field_expr.strip().lower()
    
    # =================== UNION ===================
    
    def has_union(self, query):
        """
        Verifica si una consulta contiene UNION.
        
        Args:
            query (str): Consulta SQL a analizar
            
        Returns:
            bool: True si contiene UNION, False en caso contrario
        """
        return bool(re.search(self.union_pattern, query, re.IGNORECASE))
    
    def parse_union(self, query):
        """
        Analiza una consulta con UNION.
        
        Args:
            query (str): Consulta SQL con UNION
            
        Returns:
            dict: Información sobre la consulta UNION
        """
        logger.info(f"Analizando consulta UNION: {query}")
        
        # Dividir por UNION
        union_parts = re.split(self.union_pattern, query, flags=re.IGNORECASE)
        
        if len(union_parts) < 2:
            return {"error": "No se pudieron extraer partes de UNION"}
        
        # Verificar si es UNION ALL
        is_union_all = bool(re.search(r'\bUNION\s+ALL\s+', query, re.IGNORECASE))
        
        return {
            "operation": "UNION",
            "union_all": is_union_all,
            "queries": [part.strip() for part in union_parts],
            "mongo_operation": "aggregate",
            "requires_union_pipeline": True
        }
    
    def translate_union_to_mongodb(self, query):
        """
        Traduce UNION a pipeline de agregación MongoDB.
        Nota: MongoDB no tiene UNION nativo, requiere $unionWith (MongoDB 4.4+)
        
        Args:
            query (str): Consulta SQL con UNION
            
        Returns:
            dict: Información sobre cómo manejar UNION en MongoDB
        """
        union_info = self.parse_union(query)
        
        if "error" in union_info:
            return union_info
        
        # MongoDB 4.4+ soporta $unionWith
        return {
            "operation": "union",
            "requires_mongodb_44": True,
            "union_all": union_info["union_all"],
            "queries": union_info["queries"],
            "recommendation": "Use $unionWith operator or execute separate queries and merge results"
        }
    
    # =================== SUBQUERIES ===================
    
    def has_subquery(self, query):
        """
        Verifica si una consulta contiene subqueries.
        
        Args:
            query (str): Consulta SQL a analizar
            
        Returns:
            bool: True si contiene subqueries, False en caso contrario
        """
        return bool(re.search(self.subquery_pattern, query, re.IGNORECASE | re.DOTALL))
    
    def parse_subqueries(self, query):
        """
        Analiza subqueries en una consulta SQL.
        
        Args:
            query (str): Consulta SQL con subqueries
            
        Returns:
            list: Lista de subqueries encontradas
        """
        logger.info(f"Analizando subqueries: {query}")
        
        subqueries = []
        matches = re.finditer(self.subquery_pattern, query, re.IGNORECASE | re.DOTALL)
        
        for i, match in enumerate(matches):
            subquery_text = match.group(0)
            
            # Limpiar paréntesis externos
            clean_subquery = subquery_text.strip('()')
            
            # Determinar el contexto de la subquery
            context = self._determine_subquery_context(query, match.start(), match.end())
            
            subqueries.append({
                "index": i,
                "subquery": clean_subquery.strip(),
                "context": context,
                "start_pos": match.start(),
                "end_pos": match.end()
            })
        
        return subqueries
    
    def _determine_subquery_context(self, query, start_pos, end_pos):
        """
        Determina el contexto de una subquery (WHERE, FROM, SELECT, etc.).
        
        Args:
            query (str): Consulta completa
            start_pos (int): Posición de inicio de la subquery
            end_pos (int): Posición de fin de la subquery
            
        Returns:
            str: Contexto de la subquery
        """
        # Buscar hacia atrás para encontrar el contexto
        prefix = query[:start_pos].upper()
        
        # Buscar las últimas palabras clave
        keywords = ['WHERE', 'FROM', 'SELECT', 'IN', 'EXISTS', 'ANY', 'ALL']
        
        for keyword in keywords:
            last_pos = prefix.rfind(keyword)
            if last_pos != -1:
                # Verificar que no hay otra palabra clave más reciente
                is_most_recent = True
                for other_keyword in keywords:
                    if other_keyword != keyword:
                        other_pos = prefix.rfind(other_keyword)
                        if other_pos > last_pos:
                            is_most_recent = False
                            break
                
                if is_most_recent:
                    return keyword.lower()
        
        return "unknown"
    
    def translate_subquery_to_mongodb(self, subquery_info):
        """
        Traduce una subquery a operaciones MongoDB.
        
        Args:
            subquery_info (dict): Información de la subquery
            
        Returns:
            dict: Estrategia de traducción para MongoDB
        """
        context = subquery_info.get("context", "unknown")
        subquery = subquery_info.get("subquery", "")
        
        if context == "where":
            # Subquery en WHERE - usar $lookup o $in
            return {
                "strategy": "lookup_or_in",
                "context": context,
                "subquery": subquery,
                "mongo_operation": "$lookup or separate query with $in"
            }
        
        elif context == "from":
            # Subquery en FROM - usar pipeline de agregación
            return {
                "strategy": "aggregate_pipeline", 
                "context": context,
                "subquery": subquery,
                "mongo_operation": "nested aggregation pipeline"
            }
        
        elif context == "select":
            # Subquery en SELECT - usar $lookup o $map
            return {
                "strategy": "lookup_or_map",
                "context": context, 
                "subquery": subquery,
                "mongo_operation": "$lookup with projection or $map"
            }
        
        else:
            return {
                "strategy": "complex",
                "context": context,
                "subquery": subquery,
                "mongo_operation": "requires manual translation"
            }
    
    # =================== UTILIDADES ===================
    
    def _parse_select_fields(self, fields_str):
        """
        Parsea campos de SELECT, similar al SelectParser pero simplificado.
        
        Args:
            fields_str (str): String con campos separados por comas
            
        Returns:
            list: Lista de diccionarios con información de campos
        """
        if fields_str.strip() == "*":
            return [{"field": "*"}]
        
        fields = self._split_fields(fields_str)
        select_fields = []
        
        for field in fields:
            field = field.strip()
            
            # Detectar alias
            alias_match = re.search(r'(.*?)\s+AS\s+([\w]+)$', field, re.IGNORECASE)
            if not alias_match:
                alias_match = re.search(r'(.*?)\s+([\w]+)$', field)
            
            if alias_match:
                field_name = alias_match.group(1).strip()
                alias = alias_match.group(2).strip()
                select_fields.append({"field": field_name, "alias": alias})
            else:
                select_fields.append({"field": field})
        
        return select_fields
    
    def _split_fields(self, fields_str):
        """Divide campos respetando paréntesis y comillas."""
        fields = []
        current = ""
        in_quotes = False
        quote_char = None
        level = 0
        
        for char in fields_str + ',':
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
    
    def _has_top_level_operator(self, text, operator):
        """Verifica operadores a nivel superior (fuera de paréntesis)."""
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
        """Divide texto por operador a nivel superior."""
        result = []
        current = ""
        level = 0
        i = 0
        
        op_pattern = r'\s' + operator + r'\s'
        text = " " + text + " "
        
        while i < len(text):
            if text[i] == '(':
                level += 1
                current += text[i]
            elif text[i] == ')':
                level -= 1
                current += text[i]
            elif level == 0 and i <= len(text) - len(operator) - 2:
                part = text[i:i+len(operator)+2]
                if re.match(op_pattern, part, re.IGNORECASE):
                    if current.strip():
                        result.append(current.strip())
                    current = ""
                    i += len(operator)
                else:
                    current += text[i]
            else:
                current += text[i]
            i += 1
        
        if current.strip():
            result.append(current.strip())
        
        return result
    
    def get_supported_features(self):
        """
        Retorna información sobre las funcionalidades avanzadas soportadas.
        
        Returns:
            dict: Diccionario con funcionalidades organizadas por categoría
        """
        return {
            "distinct": {
                "supported": True,
                "description": "SELECT DISTINCT fields",
                "mongo_translation": "Uses $group with fields as _id"
            },
            "having": {
                "supported": True,
                "description": "HAVING clause after GROUP BY",
                "mongo_translation": "Uses $match stage after $group",
                "supported_operators": ["=", "!=", ">", "<", ">=", "<="]
            },
            "union": {
                "supported": "partial",
                "description": "UNION and UNION ALL",
                "mongo_translation": "Requires MongoDB 4.4+ $unionWith or separate queries",
                "limitations": "Complex unions may require manual handling"
            },
            "subqueries": {
                "supported": "basic",
                "description": "Basic subqueries in WHERE, FROM, SELECT",
                "mongo_translation": "Various strategies: $lookup, $in, nested pipelines",
                "limitations": "Complex correlated subqueries need manual translation"
            }
        }
import re
import logging
from .base_parser import BaseParser

# Configurar logging
logger = logging.getLogger(__name__)

class JoinParser(BaseParser):
    """
    Parser especializado para operaciones JOIN de SQL.
    Convierte JOINs a pipelines de agregación MongoDB usando $lookup.
    """
    
    def __init__(self):
        """Inicializar el parser con patrones y configuraciones."""
        
        # Tipos de JOIN soportados
        self.join_types = {
            'INNER JOIN': 'inner',
            'LEFT JOIN': 'left',
            'LEFT OUTER JOIN': 'left',
            'RIGHT JOIN': 'right', 
            'RIGHT OUTER JOIN': 'right',
            'FULL JOIN': 'full',
            'FULL OUTER JOIN': 'full',
            'CROSS JOIN': 'cross',
            'JOIN': 'inner'  # JOIN sin especificar es INNER JOIN
        }
        
        # Patrón general para detectar JOINs
        self.join_pattern = r'\b(?:INNER\s+)?(?:LEFT\s+(?:OUTER\s+)?|RIGHT\s+(?:OUTER\s+)?|FULL\s+(?:OUTER\s+)?|CROSS\s+)?JOIN\s+'
        
        # Patrón para extraer información completa de JOIN
        self.full_join_pattern = r'(?P<join_type>(?:INNER\s+)?(?:LEFT\s+(?:OUTER\s+)?|RIGHT\s+(?:OUTER\s+)?|FULL\s+(?:OUTER\s+)?|CROSS\s+)?JOIN)\s+(?P<table>[\w`\[\]"\'\.]+)(?:\s+(?:AS\s+)?(?P<alias>[\w]+))?\s+ON\s+(?P<condition>.*?)(?=\s+(?:INNER\s+)?(?:LEFT\s+(?:OUTER\s+)?|RIGHT\s+(?:OUTER\s+)?|FULL\s+(?:OUTER\s+)?|CROSS\s+)?JOIN\s+|\s+WHERE\s+|\s+GROUP\s+BY\s+|\s+ORDER\s+BY\s+|\s+HAVING\s+|\s+LIMIT\s+|\s*;|\s*$)'
    
    def parse(self, query_or_clause):
        """
        Método principal para analizar JOINs en una consulta.
        
        Args:
            query_or_clause (str): Consulta SQL o cláusula
            
        Returns:
            dict: Información sobre los JOINs encontrados
        """
        joins = self.parse_joins(query_or_clause)
        return {
            'has_joins': len(joins) > 0,
            'join_count': len(joins),
            'joins': joins,
            'requires_lookup': len(joins) > 0
        }
    
    def has_joins(self, query):
        """
        Verifica si una consulta contiene operaciones JOIN.
        
        Args:
            query (str): Consulta SQL a analizar
            
        Returns:
            bool: True si contiene JOINs, False en caso contrario
        """
        return bool(re.search(self.join_pattern, query, re.IGNORECASE))
    
    def parse_joins(self, query):
        """
        Extrae y analiza todas las operaciones JOIN de una consulta SQL.
        
        Args:
            query (str): Consulta SQL a analizar
            
        Returns:
            list: Lista de diccionarios con información de cada JOIN
        """
        logger.info(f"Analizando JOINs en consulta: {query}")
        
        joins = []
        
        # Buscar todos los JOINs en la consulta
        matches = re.finditer(self.full_join_pattern, query, re.IGNORECASE | re.DOTALL)
        
        for i, match in enumerate(matches):
            join_info = self._parse_single_join(match, i)
            if join_info:
                joins.append(join_info)
        
        logger.info(f"JOINs encontrados: {len(joins)}")
        return joins
    
    def _parse_single_join(self, match, index):
        """
        Analiza un solo JOIN extraído de la consulta.
        
        Args:
            match: Objeto Match de regex con información del JOIN
            index (int): Índice del JOIN en la consulta
            
        Returns:
            dict: Información detallada del JOIN
        """
        join_type_str = match.group('join_type').strip()
        table = match.group('table').strip()
        alias = match.group('alias')
        condition = match.group('condition').strip()
        
        # Limpiar nombre de tabla
        clean_table = table.strip('`[]"\'')
        
        # Determinar tipo de JOIN
        join_type = self._determine_join_type(join_type_str)
        
        # Analizar condición ON
        join_condition = self._parse_join_condition(condition)
        
        join_info = {
            'index': index,
            'type': join_type,
            'table': clean_table,
            'alias': alias if alias else clean_table,
            'condition': join_condition,
            'raw_condition': condition,
            'mongo_strategy': self._get_mongo_strategy(join_type)
        }
        
        logger.debug(f"JOIN analizado: {join_info}")
        return join_info
    
    def _determine_join_type(self, join_type_str):
        """
        Determina el tipo de JOIN basado en la cadena extraída.
        
        Args:
            join_type_str (str): Cadena con el tipo de JOIN
            
        Returns:
            str: Tipo de JOIN normalizado
        """
        join_type_upper = join_type_str.upper().strip()
        
        # Buscar coincidencia exacta
        for pattern, join_type in self.join_types.items():
            if pattern == join_type_upper:
                return join_type
        
        # Si no hay coincidencia exacta, asumir INNER JOIN
        return 'inner'
    
    def _parse_join_condition(self, condition):
        """
        Analiza la condición ON del JOIN.
        
        Args:
            condition (str): Condición del JOIN
            
        Returns:
            dict: Información de la condición parseada
        """
        # Patrón básico: tabla1.campo = tabla2.campo
        basic_pattern = r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)'
        match = re.search(basic_pattern, condition, re.IGNORECASE)
        
        if match:
            left_table = match.group(1)
            left_field = match.group(2)
            right_table = match.group(3)
            right_field = match.group(4)
            
            return {
                'type': 'equality',
                'left_table': left_table,
                'left_field': left_field,
                'right_table': right_table,
                'right_field': right_field,
                'operator': '='
            }
        
        # Patrón con alias: alias.campo = tabla.campo
        alias_pattern = r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)'
        match = re.search(alias_pattern, condition, re.IGNORECASE)
        
        if match:
            return {
                'type': 'equality',
                'left_table': match.group(1),
                'left_field': match.group(2),
                'right_table': match.group(3),
                'right_field': match.group(4),
                'operator': '='
            }
        
        # Si no se puede parsear, devolver información básica
        return {
            'type': 'complex',
            'raw_condition': condition,
            'operator': 'unknown'
        }
    
    def _get_mongo_strategy(self, join_type):
        """
        Determina la estrategia MongoDB para el tipo de JOIN.
        
        Args:
            join_type (str): Tipo de JOIN
            
        Returns:
            str: Estrategia MongoDB a usar
        """
        strategies = {
            'inner': 'lookup_with_match',
            'left': 'lookup_preserve_null',
            'right': 'lookup_swap_collections',
            'full': 'lookup_union_strategy',
            'cross': 'lookup_cartesian'
        }
        
        return strategies.get(join_type, 'lookup_with_match')
    
    def translate_joins_to_mongodb(self, query, joins_info=None):
        """
        Traduce JOINs a pipeline de agregación MongoDB.
        
        Args:
            query (str): Consulta SQL original
            joins_info (list): Información de JOINs (opcional)
            
        Returns:
            list: Pipeline de agregación MongoDB
        """
        if not joins_info:
            joins_info = self.parse_joins(query)
        
        if not joins_info:
            return []
        
        pipeline = []
        
        # Procesar cada JOIN secuencialmente
        for join in joins_info:
            join_stages = self._create_lookup_stages(join)
            pipeline.extend(join_stages)
        
        logger.info(f"Pipeline de JOINs generado con {len(pipeline)} etapas")
        return pipeline
    
    def _create_lookup_stages(self, join_info):
        """
        Crea las etapas de $lookup para un JOIN específico.
        
        Args:
            join_info (dict): Información del JOIN
            
        Returns:
            list: Lista de etapas del pipeline
        """
        stages = []
        join_type = join_info['type']
        condition = join_info['condition']
        
        if condition['type'] != 'equality':
            logger.warning(f"Condición de JOIN compleja no completamente soportada: {condition}")
            return []
        
        # Crear etapa $lookup básica
        lookup_stage = {
            "$lookup": {
                "from": join_info['table'],
                "localField": condition['left_field'],
                "foreignField": condition['right_field'],
                "as": join_info['alias'] + "_joined"
            }
        }
        
        stages.append(lookup_stage)
        
        # Agregar etapas específicas según el tipo de JOIN
        if join_type == 'inner':
            # INNER JOIN: filtrar documentos sin matches
            match_stage = {
                "$match": {
                    join_info['alias'] + "_joined": {"$ne": []}
                }
            }
            stages.append(match_stage)
        
        elif join_type == 'left':
            # LEFT JOIN: preservar documentos sin matches (ya está por defecto en $lookup)
            pass
        
        elif join_type == 'right':
            # RIGHT JOIN: requiere estrategia especial
            logger.warning("RIGHT JOIN requiere intercambio de colecciones")
            # Agregar comentario sobre la estrategia necesaria
            stages.append({
                "$addFields": {
                    "_right_join_note": "RIGHT JOIN requires swapping collections in query"
                }
            })
        
        # Descomponer el array resultado (para INNER y LEFT JOIN)
        if join_type in ['inner', 'left']:
            unwind_stage = {
                "$unwind": {
                    "path": "$" + join_info['alias'] + "_joined",
                    "preserveNullAndEmptyArrays": join_type == 'left'
                }
            }
            stages.append(unwind_stage)
        
        return stages
    
    def get_main_table_from_query(self, query):
        """
        Extrae la tabla principal (FROM) de una consulta con JOINs.
        
        Args:
            query (str): Consulta SQL
            
        Returns:
            dict: Información de la tabla principal
        """
        # Buscar la cláusula FROM
        from_pattern = r'FROM\s+([\w`\[\]"\'\.]+)(?:\s+(?:AS\s+)?([\w]+))?\s*(?:(?:INNER\s+)?(?:LEFT\s+(?:OUTER\s+)?|RIGHT\s+(?:OUTER\s+)?|FULL\s+(?:OUTER\s+)?|CROSS\s+)?JOIN|WHERE|GROUP\s+BY|ORDER\s+BY|HAVING|LIMIT|$)'
        
        match = re.search(from_pattern, query, re.IGNORECASE)
        
        if match:
            table = match.group(1).strip('`[]"\'')
            alias = match.group(2) if match.group(2) else table
            
            return {
                'table': table,
                'alias': alias,
                'is_main_table': True
            }
        
        return None
    
    def optimize_join_pipeline(self, pipeline):
        """
        Optimiza el pipeline de JOINs para mejor rendimiento.
        
        Args:
            pipeline (list): Pipeline de agregación
            
        Returns:
            list: Pipeline optimizado
        """
        optimized = []
        
        for stage in pipeline:
            # Optimización 1: Agregar hint sobre índices
            if "$lookup" in stage:
                lookup = stage["$lookup"]
                # Sugerir índice en el campo de lookup
                lookup["_index_hint"] = f"Consider index on {lookup['from']}.{lookup['foreignField']}"
            
            optimized.append(stage)
        
        return optimized
    
    def generate_join_explanation(self, joins_info):
        """
        Genera una explicación en texto de los JOINs encontrados.
        
        Args:
            joins_info (list): Lista de JOINs
            
        Returns:
            dict: Explicación detallada de los JOINs
        """
        explanations = []
        
        for join in joins_info:
            join_type = join['type'].upper()
            table = join['table']
            condition = join['condition']
            
            if condition['type'] == 'equality':
                explanation = f"{join_type} JOIN with {table} on {condition['left_table']}.{condition['left_field']} = {condition['right_table']}.{condition['right_field']}"
            else:
                explanation = f"{join_type} JOIN with {table} on complex condition"
            
            explanations.append({
                'join_index': join['index'],
                'explanation': explanation,
                'mongo_strategy': join['mongo_strategy'],
                'complexity': 'simple' if condition['type'] == 'equality' else 'complex'
            })
        
        return {
            'total_joins': len(joins_info),
            'join_explanations': explanations,
            'overall_complexity': 'complex' if len(joins_info) > 2 else 'moderate' if len(joins_info) > 1 else 'simple'
        }
    
    def get_supported_joins(self):
        """
        Retorna información sobre los tipos de JOIN soportados.
        
        Returns:
            dict: Información sobre JOINs soportados
        """
        return {
            "supported_types": {
                "INNER JOIN": {
                    "supported": True,
                    "mongo_translation": "$lookup + $match to filter unmatched",
                    "performance": "Good"
                },
                "LEFT JOIN": {
                    "supported": True,
                    "mongo_translation": "$lookup + $unwind with preserveNullAndEmptyArrays",
                    "performance": "Good"
                },
                "RIGHT JOIN": {
                    "supported": "Limited",
                    "mongo_translation": "Requires swapping collections or complex pipeline",
                    "performance": "Requires optimization"
                },
                "FULL OUTER JOIN": {
                    "supported": "Complex",
                    "mongo_translation": "Requires $unionWith or multiple pipelines",
                    "performance": "May require MongoDB 4.4+"
                },
                "CROSS JOIN": {
                    "supported": "Limited",
                    "mongo_translation": "$lookup without condition (cartesian product)",
                    "performance": "Use with caution - can be expensive"
                }
            },
            "limitations": [
                "Complex join conditions with functions not fully supported",
                "Multiple joins may require optimization",
                "RIGHT and FULL OUTER JOINs require special handling",
                "Non-equality joins require custom implementation"
            ],
            "recommendations": [
                "Use INNER and LEFT JOINs when possible",
                "Ensure proper indexes on join fields",
                "Consider denormalization for frequently joined data",
                "Test performance with realistic data volumes"
            ]
        }
    
    def validate_join_query(self, query):
        """
        Valida si una consulta con JOINs es traducible a MongoDB.
        
        Args:
            query (str): Consulta SQL con JOINs
            
        Returns:
            dict: Resultado de validación
        """
        joins = self.parse_joins(query)
        issues = []
        warnings = []
        
        for join in joins:
            # Verificar tipo de JOIN
            if join['type'] in ['right', 'full']:
                warnings.append(f"JOIN tipo {join['type']} requiere manejo especial en MongoDB")
            
            # Verificar condición
            if join['condition']['type'] == 'complex':
                issues.append(f"Condición de JOIN compleja en tabla {join['table']}: {join['raw_condition']}")
            
            # Verificar si hay muchos JOINs
            if len(joins) > 3:
                warnings.append("Múltiples JOINs pueden afectar el rendimiento")
        
        return {
            "is_valid": len(issues) == 0,
            "is_optimal": len(warnings) == 0,
            "issues": issues,
            "warnings": warnings,
            "join_count": len(joins),
            "complexity_score": len(joins) + len(issues) * 2 + len(warnings)
        }
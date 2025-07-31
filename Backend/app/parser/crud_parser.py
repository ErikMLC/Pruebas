import re
import logging
from .base_parser import BaseParser

# Configurar logging
logger = logging.getLogger(__name__)

class CRUDParser(BaseParser):
    """
    Parser especializado para operaciones CRUD (Create, Read, Update, Delete).
    Analiza consultas INSERT, UPDATE y DELETE.
    🔧 CORREGIDO: Soporte completo para INSERT múltiple
    """
    
    def parse(self, query):
        """
        Determina el tipo de operación CRUD y redirige al método específico.
        
        Args:
            query (str): Consulta SQL a analizar
            
        Returns:
            dict: Resultado del análisis
        """
        query = query.strip()
        query_upper = query.upper()
        
        if query_upper.startswith('INSERT'):
            return self.parse_insert(query)
        elif query_upper.startswith('UPDATE'):
            return self.parse_update(query)
        elif query_upper.startswith('DELETE'):
            return self.parse_delete(query)
        else:
            raise ValueError(f"Consulta no soportada por CRUDParser: {query}")
    

    def parse_insert(self, query):
        """
        Analiza una consulta INSERT y extrae los valores a insertar.
        🔧 CORREGIDO: Maneja INSERT múltiple correctamente
        
        Args:
            query (str): Consulta INSERT a analizar
            
        Returns:
            dict: Diccionario con tabla y valores a insertar
        """
        logger.info(f"Analizando consulta INSERT: {query}")
        
        # Normalizar la consulta
        query = query.strip()
        
        # Extraer nombre de tabla
        table_pattern = r'INSERT\s+INTO\s+([^\s(]+)'
        table_match = re.search(table_pattern, query, re.IGNORECASE)
        
        if not table_match:
            logger.error("No se pudo extraer tabla de INSERT")
            return {"error": "No se pudo extraer tabla"}
            
        table_name = table_match.group(1).strip('`[]"\'').lower()
        
        # 🔧 NUEVO: Extraer columnas y múltiples valores
        columns_pattern = r'INSERT\s+INTO\s+[^\s(]+\s*\((.*?)\)\s*VALUES\s*(.*?)(?:;|$)'
        columns_match = re.search(columns_pattern, query, re.IGNORECASE | re.DOTALL)
        
        if columns_match:
            # INSERT INTO tabla (col1, col2) VALUES (val1, val2), (val3, val4), ...
            columns_str = columns_match.group(1).strip()
            values_section = columns_match.group(2).strip()
            
            # Parsear columnas
            columns = [col.strip().strip('`[]"\'') for col in self._split_values(columns_str)]
            logger.info(f"Columnas extraídas: {columns}")
            
            # 🔧 NUEVO: Extraer TODOS los conjuntos de valores
            all_values = self._extract_all_value_sets(values_section)
            logger.info(f"Conjuntos de valores encontrados: {len(all_values)}")
            
            if not all_values:
                logger.error("No se pudieron extraer valores de INSERT")
                return {"error": "No se pudieron extraer valores"}
            
            # 🔧 NUEVO: Procesar múltiples registros
            insert_documents = []
            
            for i, value_set in enumerate(all_values):
                logger.debug(f"Procesando conjunto {i+1}: {value_set}")
                values = [self._parse_value(val) for val in value_set]
                
                if len(columns) != len(values):
                    logger.error(f"Número de columnas ({len(columns)}) no coincide con número de valores ({len(values)}) en conjunto {i+1}: {values}")
                    continue  # Saltar este conjunto y continuar con los demás
                
                # Crear diccionario de valores para este registro
                document = dict(zip(columns, values))
                insert_documents.append(document)
                logger.debug(f"Documento {i+1} creado: {document}")
            
            if not insert_documents:
                return {"error": "No se pudo procesar ningún conjunto de valores válido"}
            
            logger.info(f"Total de documentos procesados exitosamente: {len(insert_documents)}")
            
            # 🔧 NUEVO: Retornar múltiples documentos o uno solo según el caso
            if len(insert_documents) == 1:
                # Un solo documento - mantener compatibilidad con formato anterior
                return {
                    "operation": "INSERT",
                    "table": table_name,
                    "values": insert_documents[0]
                }
            else:
                # Múltiples documentos - nuevo formato
                return {
                    "operation": "INSERT_MANY",
                    "table": table_name,
                    "documents": insert_documents,
                    "count": len(insert_documents)
                }
        else:
            # Intentar con formato sin columnas: INSERT INTO tabla VALUES (val1, val2)
            simple_pattern = r'INSERT\s+INTO\s+[^\s(]+\s+VALUES\s*(.*?)(?:;|$)'
            simple_match = re.search(simple_pattern, query, re.IGNORECASE | re.DOTALL)
            
            if simple_match:
                values_section = simple_match.group(1).strip()
                
                # 🔧 NUEVO: Extraer múltiples conjuntos de valores
                all_values = self._extract_all_value_sets(values_section)
                
                if not all_values:
                    logger.error("No se pudieron extraer valores de INSERT simple")
                    return {"error": "No se pudieron extraer valores"}
                
                insert_documents = []
                
                for i, value_set in enumerate(all_values):
                    values = [self._parse_value(val) for val in value_set]
                    
                    # Usar nombres genéricos de columnas
                    columns = [f"column_{i+1}" for i in range(len(values))]
                    document = dict(zip(columns, values))
                    insert_documents.append(document)
                
                if len(insert_documents) == 1:
                    return {
                        "operation": "INSERT",
                        "table": table_name,
                        "values": insert_documents[0]
                    }
                else:
                    return {
                        "operation": "INSERT_MANY",
                        "table": table_name,
                        "documents": insert_documents,
                        "count": len(insert_documents)
                    }
            
            logger.error("No se pudo extraer valores de INSERT")
            return {"error": "No se pudo extraer valores"}

    def _extract_all_value_sets(self, values_section):
        """
        🔧 NUEVO: Extrae TODOS los conjuntos de valores de una sección VALUES.
        Maneja: VALUES (val1, val2), (val3, val4), (val5, val6)
        
        Args:
            values_section (str): Sección VALUES completa
            
        Returns:
            list: Lista de listas, cada una conteniendo los valores de un conjunto
        """
        all_value_sets = []
        
        # Buscar todos los conjuntos entre paréntesis
        # Patrón: \(([^)]+)\) - busca contenido entre paréntesis
        value_sets_pattern = r'\(([^)]+)\)'
        matches = re.finditer(value_sets_pattern, values_section)
        
        for match in matches:
            values_str = match.group(1).strip()
            logger.debug(f"Conjunto de valores encontrado: {values_str}")
            
            # Dividir por comas respetando comillas
            value_set = self._split_values(values_str)
            
            if value_set:  # Solo agregar si no está vacío
                all_value_sets.append(value_set)
        
        logger.info(f"Total de conjuntos de valores extraídos: {len(all_value_sets)}")
        return all_value_sets
    
    def parse_update(self, query):
        """
        Analiza una consulta UPDATE y extrae los valores a actualizar.
        
        Args:
            query (str): Consulta UPDATE a analizar
            
        Returns:
            dict: Diccionario con tabla, valores y condición
        """
        logger.info(f"Analizando consulta UPDATE: {query}")
        
        # Normalizar la consulta
        query = query.strip()
        
        # Extraer nombre de tabla
        table_pattern = r'UPDATE\s+([^\s,;()]+)'
        table_match = re.search(table_pattern, query, re.IGNORECASE)
        
        if not table_match:
            logger.error("No se pudo extraer tabla de UPDATE")
            return {"error": "No se pudo extraer tabla"}
            
        table_name = table_match.group(1).strip('`[]"\'').lower()
        
        # Extraer valores a actualizar (SET)
        set_pattern = r'SET\s+(.*?)(?:\sWHERE|\s;|\Z)'
        set_match = re.search(set_pattern, query, re.IGNORECASE | re.DOTALL)
        
        if not set_match:
            logger.error("No se pudo extraer cláusula SET de UPDATE")
            return {"error": "No se pudo extraer valores a actualizar"}
            
        set_str = set_match.group(1).strip()
        
        # Dividir las asignaciones por comas
        assignments = self._split_values(set_str)
        update_values = {}
        
        for assignment in assignments:
            if '=' in assignment:
                field, value_str = [part.strip() for part in assignment.split('=', 1)]
                value = self._parse_value(value_str)
                update_values[field.lower()] = value
        
        # Extraer condición WHERE
        where_pattern = r'WHERE\s+(.*?)(?:\s;|\Z)'
        where_match = re.search(where_pattern, query, re.IGNORECASE | re.DOTALL)
        
        where_condition = {}
        if where_match:
            # Utilizaríamos WhereParser, pero para evitar dependencias circulares,
            # implementamos una versión simplificada aquí.
            where_str = where_match.group(1).strip()
            
            # Procesamiento básico de condición (para consultas simples)
            if '=' in where_str and 'AND' not in where_str.upper() and 'OR' not in where_str.upper():
                field, value_str = [part.strip() for part in where_str.split('=', 1)]
                value = self._parse_value(value_str)
                where_condition[field.lower()] = value
        
        return {
            "operation": "UPDATE",
            "table": table_name,
            "values": update_values,
            "condition": where_condition
        }
    
    def parse_delete(self, query):
        """
        Analiza una consulta DELETE y extrae la condición.
        
        Args:
            query (str): Consulta DELETE a analizar
            
        Returns:
            dict: Diccionario con tabla y condición
        """
        logger.info(f"Analizando consulta DELETE: {query}")
        
        # Normalizar la consulta
        query = query.strip()
        
        # Extraer nombre de tabla
        table_pattern = r'DELETE\s+FROM\s+([^\s,;()]+)'
        table_match = re.search(table_pattern, query, re.IGNORECASE)
        
        if not table_match:
            logger.error("No se pudo extraer tabla de DELETE")
            return {"error": "No se pudo extraer tabla"}
            
        table_name = table_match.group(1).strip('`[]"\'').lower()
        
        # Extraer condición WHERE
        where_pattern = r'WHERE\s+(.*?)(?:\s;|\Z)'
        where_match = re.search(where_pattern, query, re.IGNORECASE | re.DOTALL)
        
        where_condition = {}
        if where_match:
            # Utilizaríamos WhereParser, pero para evitar dependencias circulares,
            # implementamos una versión simplificada aquí.
            where_str = where_match.group(1).strip()
            
            # Procesamiento básico de condición (para consultas simples)
            if '=' in where_str and 'AND' not in where_str.upper() and 'OR' not in where_str.upper():
                field, value_str = [part.strip() for part in where_str.split('=', 1)]
                value = self._parse_value(value_str)
                where_condition[field.lower()] = value
        
        return {
            "operation": "DELETE",
            "table": table_name,
            "condition": where_condition
        }
    
    def _split_values(self, values_str):
        """
        Divide una cadena de valores separados por comas, respetando comillas y paréntesis.
        
        Args:
            values_str (str): Cadena de valores a dividir
            
        Returns:
            list: Lista de valores individuales
        """
        values = []
        current = ""
        in_quotes = False
        quote_char = None
        level = 0
        
        for char in values_str + ',':  # Añadir coma al final para capturar el último valor
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
                values.append(current.strip())
                current = ""
            else:
                current += char
        
        return values
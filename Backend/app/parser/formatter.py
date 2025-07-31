import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Configurar logging
logger = logging.getLogger(__name__)

class ResponseFormatter:
    """
    Formateador de respuestas estandarizadas para el traductor SQL→MongoDB.
    Proporciona formatos consistentes para éxito, errores y metadatos.
    """
    
    def __init__(self):
        """Inicializar el formateador con configuraciones por defecto."""
        
        # Configuración de formatos
        self.success_format = {
            "include_metadata": True,
            "include_timing": True,
            "include_query_info": True,
            "include_performance_hints": True
        }
        
        self.error_format = {
            "include_context": True,
            "include_suggestions": True,
            "include_error_code": True,
            "mask_sensitive_data": True
        }
        
        # Códigos de error estandarizados
        self.error_codes = {
            "PARSE_ERROR": "E001",
            "TRANSLATION_ERROR": "E002", 
            "VALIDATION_ERROR": "E003",
            "SECURITY_ERROR": "E004",
            "FUNCTION_NOT_SUPPORTED": "E005",
            "JOIN_NOT_SUPPORTED": "E006",
            "SYNTAX_ERROR": "E007",
            "PERMISSION_DENIED": "E008",
            "DATABASE_ERROR": "E009",
            "UNKNOWN_ERROR": "E999"
        }
        
        # Mapeo de tipos de consulta a descripciones
        self.query_descriptions = {
            "SELECT": "Consulta de lectura de datos",
            "INSERT": "Inserción de nuevos registros",
            "UPDATE": "Actualización de registros existentes", 
            "DELETE": "Eliminación de registros",
            "CREATE": "Creación de tabla/colección",
            "DROP": "Eliminación de tabla/colección"
        }
    
    def format_success(self, data: Any, metadata: Optional[Dict] = None, 
                      execution_time: Optional[float] = None) -> Dict:
        """
        Formatea una respuesta exitosa con estructura estandarizada.
        
        Args:
            data: Datos de la respuesta (resultado de la consulta)
            metadata: Metadatos adicionales (opcional)
            execution_time: Tiempo de ejecución en segundos (opcional)
            
        Returns:
            Dict: Respuesta formateada
        """
        response = {
            "success": True,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data
        }
        
        # Agregar metadatos si están habilitados
        if self.success_format["include_metadata"] and metadata:
            response["metadata"] = self._format_metadata(metadata)
        
        # Agregar información de timing
        if self.success_format["include_timing"] and execution_time is not None:
            response["execution"] = {
                "time_ms": round(execution_time * 1000, 2),
                "time_seconds": round(execution_time, 4)
            }
        
        # Agregar estadísticas de datos
        response["stats"] = self._calculate_data_stats(data)
        
        return response
    
    def format_error(self, error: Union[Exception, str], error_type: str = "UNKNOWN_ERROR",
                    context: Optional[Dict] = None, suggestions: Optional[List[str]] = None) -> Dict:
        """
        Formatea una respuesta de error con información útil para debugging.
        
        Args:
            error: Excepción o mensaje de error
            error_type: Tipo de error (debe estar en error_codes)
            context: Contexto adicional del error
            suggestions: Sugerencias para resolver el error
            
        Returns:
            Dict: Respuesta de error formateada
        """
        # Obtener mensaje de error
        if isinstance(error, Exception):
            error_message = str(error)
            error_class = error.__class__.__name__
        else:
            error_message = str(error)
            error_class = "GenericError"
        
        response = {
            "success": False,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": {
                "code": self.error_codes.get(error_type, self.error_codes["UNKNOWN_ERROR"]),
                "type": error_type,
                "message": error_message,
                "class": error_class
            }
        }
        
        # Agregar contexto si está habilitado
        if self.error_format["include_context"] and context:
            # Enmascarar datos sensibles
            safe_context = self._sanitize_context(context) if self.error_format["mask_sensitive_data"] else context
            response["error"]["context"] = safe_context
        
        # Agregar sugerencias
        if self.error_format["include_suggestions"]:
            response["error"]["suggestions"] = suggestions or self._get_default_suggestions(error_type)
        
        return response
    
    def format_translation_result(self, sql_query: str, mongo_operation: Dict,
                                query_type: str, collection: str,
                                execution_time: Optional[float] = None,
                                warnings: Optional[List[str]] = None) -> Dict:
        """
        Formatea el resultado de una traducción SQL→MongoDB.
        
        Args:
            sql_query: Consulta SQL original
            mongo_operation: Operación MongoDB generada
            query_type: Tipo de consulta (SELECT, INSERT, etc.)
            collection: Nombre de la colección
            execution_time: Tiempo de traducción
            warnings: Advertencias durante la traducción
            
        Returns:
            Dict: Resultado de traducción formateado
        """
        metadata = {
            "query_type": query_type,
            "collection": collection,
            "sql_query": sql_query,
            "complexity": self._calculate_complexity(mongo_operation),
            "features_used": self._detect_features_used(mongo_operation),
            "optimization_hints": self._generate_optimization_hints(mongo_operation)
        }
        
        if warnings:
            metadata["warnings"] = warnings
        
        return self.format_success(
            data=mongo_operation,
            metadata=metadata,
            execution_time=execution_time
        )
    
    def format_query_result(self, result_data: Any, query_info: Dict,
                          execution_time: Optional[float] = None) -> Dict:
        """
        Formatea el resultado de ejecutar una consulta en MongoDB.
        
        Args:
            result_data: Datos devueltos por MongoDB
            query_info: Información sobre la consulta ejecutada
            execution_time: Tiempo de ejecución
            
        Returns:
            Dict: Resultado de consulta formateado
        """
        metadata = {
            "query_info": query_info,
            "result_type": self._determine_result_type(result_data),
            "performance": self._analyze_performance(result_data, execution_time)
        }
        
        return self.format_success(
            data=result_data,
            metadata=metadata,
            execution_time=execution_time
        )
    
    def format_validation_result(self, is_valid: bool, issues: List[str],
                               warnings: List[str], query: str) -> Dict:
        """
        Formatea el resultado de validación de una consulta.
        
        Args:
            is_valid: Si la consulta es válida
            issues: Lista de problemas encontrados
            warnings: Lista de advertencias
            query: Consulta SQL validada
            
        Returns:
            Dict: Resultado de validación formateado
        """
        if is_valid:
            return self.format_success(
                data={"valid": True, "warnings": warnings},
                metadata={"query": query, "validation_passed": True}
            )
        else:
            return self.format_error(
                error="Validation failed",
                error_type="VALIDATION_ERROR",
                context={"query": query, "issues": issues, "warnings": warnings},
                suggestions=self._generate_validation_suggestions(issues)
            )
    
    def format_feature_info(self, supported_features: Dict) -> Dict:
        """
        Formatea información sobre características soportadas.
        
        Args:
            supported_features: Diccionario con características soportadas
            
        Returns:
            Dict: Información de características formateada
        """
        return self.format_success(
            data=supported_features,
            metadata={
                "category": "feature_support",
                "version": "2.0.0",
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    def _format_metadata(self, metadata: Dict) -> Dict:
        """Formatea y enriquece metadatos."""
        formatted = metadata.copy()
        
        # Agregar descripción del tipo de consulta
        if "query_type" in formatted:
            query_type = formatted["query_type"]
            formatted["query_description"] = self.query_descriptions.get(query_type, "Operación desconocida")
        
        # Agregar timestamp de metadatos
        formatted["metadata_generated_at"] = datetime.utcnow().isoformat() + "Z"
        
        return formatted
    
    def _calculate_data_stats(self, data: Any) -> Dict:
        """Calcula estadísticas básicas de los datos."""
        stats = {}
        
        if isinstance(data, list):
            stats["type"] = "array"
            stats["count"] = len(data)
            stats["is_empty"] = len(data) == 0
        elif isinstance(data, dict):
            stats["type"] = "object" 
            stats["keys"] = len(data.keys()) if data else 0
            stats["is_empty"] = len(data) == 0
        else:
            stats["type"] = type(data).__name__
            stats["is_empty"] = data is None
        
        return stats
    
    def _sanitize_context(self, context: Dict) -> Dict:
        """Enmascara datos sensibles del contexto."""
        sanitized = context.copy()
        
        # Campos sensibles que deben ser enmascarados
        sensitive_fields = ["password", "token", "secret", "key", "credential"]
        
        for key, value in sanitized.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                sanitized[key] = "*" * 8
            elif isinstance(value, str) and len(value) > 100:
                # Truncar valores muy largos
                sanitized[key] = value[:100] + "..."
        
        return sanitized
    
    def _get_default_suggestions(self, error_type: str) -> List[str]:
        """Obtiene sugerencias por defecto según el tipo de error."""
        suggestions_map = {
            "PARSE_ERROR": [
                "Verifica la sintaxis de la consulta SQL",
                "Asegúrate de que todos los paréntesis estén balanceados",
                "Revisa que las palabras clave estén correctamente escritas"
            ],
            "TRANSLATION_ERROR": [
                "La consulta puede contener características no soportadas",
                "Intenta simplificar la consulta",
                "Consulta la documentación de características soportadas"
            ],
            "VALIDATION_ERROR": [
                "Revisa los permisos de usuario",
                "Verifica que la consulta sea segura",
                "Asegúrate de que todos los campos requeridos estén presentes"
            ],
            "SECURITY_ERROR": [
                "La consulta contiene patrones potencialmente peligrosos", 
                "Evita usar caracteres especiales sin escapar",
                "Contacta al administrador si necesitas permisos adicionales"
            ],
            "FUNCTION_NOT_SUPPORTED": [
                "Consulta la lista de funciones SQL soportadas",
                "Considera usar una función alternativa",
                "Algunos funciones pueden requerir procesamiento adicional"
            ]
        }
        
        return suggestions_map.get(error_type, [
            "Revisa la consulta y vuelve a intentar",
            "Consulta la documentación para más información",
            "Contacta soporte técnico si el problema persiste"
        ])
    
    def _calculate_complexity(self, mongo_operation: Dict) -> str:
        """Calcula la complejidad de una operación MongoDB."""
        complexity_score = 0
        
        # Factores que aumentan la complejidad
        if isinstance(mongo_operation, dict):
            if "pipeline" in mongo_operation:
                pipeline = mongo_operation["pipeline"]
                complexity_score += len(pipeline)
                
                # Operaciones complejas
                for stage in pipeline:
                    if "$lookup" in stage:
                        complexity_score += 2
                    if "$group" in stage:
                        complexity_score += 1
                    if "$match" in stage and isinstance(stage["$match"], dict):
                        complexity_score += len(stage["$match"])
            
            if "query" in mongo_operation and isinstance(mongo_operation["query"], dict):
                complexity_score += len(mongo_operation["query"])
        
        # Clasificar complejidad
        if complexity_score <= 2:
            return "simple"
        elif complexity_score <= 5:
            return "moderate" 
        else:
            return "complex"
    
    def _detect_features_used(self, mongo_operation: Dict) -> List[str]:
        """Detecta qué características se están usando."""
        features = []
        
        if isinstance(mongo_operation, dict):
            operation = mongo_operation.get("operation", "")
            
            if operation == "find":
                features.append("basic_query")
            elif operation == "aggregate":
                features.append("aggregation_pipeline")
            elif operation in ["insert", "update", "delete"]:
                features.append("data_modification")
            
            # Detectar características específicas
            if "pipeline" in mongo_operation:
                pipeline = mongo_operation["pipeline"]
                for stage in pipeline:
                    if "$lookup" in stage:
                        features.append("joins")
                    if "$group" in stage:
                        features.append("grouping")
                    if "$sort" in stage:
                        features.append("sorting")
                    if "$limit" in stage:
                        features.append("pagination")
                    if "$match" in stage:
                        features.append("filtering")
            
            if "projection" in mongo_operation:
                features.append("field_selection")
        
        return list(set(features))  # Eliminar duplicados
    
    def _generate_optimization_hints(self, mongo_operation: Dict) -> List[str]:
        """Genera consejos de optimización."""
        hints = []
        
        if isinstance(mongo_operation, dict):
            # Hints para queries simples
            if mongo_operation.get("operation") == "find":
                if "query" in mongo_operation and mongo_operation["query"]:
                    hints.append("Considera crear índices en los campos de filtro")
                
                if "sort" in mongo_operation:
                    hints.append("Los índices compuestos pueden mejorar el rendimiento del ORDER BY")
            
            # Hints para agregaciones
            elif mongo_operation.get("operation") == "aggregate":
                pipeline = mongo_operation.get("pipeline", [])
                
                # Buscar $match al inicio
                if pipeline and "$match" not in pipeline[0]:
                    hints.append("Considera agregar filtros ($match) al inicio del pipeline")
                
                # Buscar múltiples $lookup
                lookup_count = sum(1 for stage in pipeline if "$lookup" in stage)
                if lookup_count > 1:
                    hints.append("Múltiples JOINs pueden afectar el rendimiento - considera desnormalización")
                
                # Buscar $sort después de $group
                for i, stage in enumerate(pipeline[:-1]):
                    if "$group" in stage and "$sort" in pipeline[i + 1]:
                        hints.append("Ordenar después de agrupar puede ser costoso en datasets grandes")
        
        return hints
    
    def _determine_result_type(self, result_data: Any) -> str:
        """Determina el tipo de resultado."""
        if isinstance(result_data, list):
            if len(result_data) == 0:
                return "empty_resultset"
            elif len(result_data) == 1:
                return "single_record"
            else:
                return "multiple_records"
        elif isinstance(result_data, dict):
            if "acknowledged" in result_data:
                return "operation_result"
            else:
                return "single_document"
        else:
            return "scalar_value"
    
    def _analyze_performance(self, result_data: Any, execution_time: Optional[float]) -> Dict:
        """Analiza el rendimiento de la consulta."""
        performance = {}
        
        if execution_time is not None:
            performance["execution_time_ms"] = round(execution_time * 1000, 2)
            
            # Clasificar rendimiento
            if execution_time < 0.1:
                performance["speed"] = "fast"
            elif execution_time < 0.5:
                performance["speed"] = "moderate"
            else:
                performance["speed"] = "slow"
        
        # Analizar tamaño de resultado
        if isinstance(result_data, list):
            performance["result_size"] = len(result_data)
            if len(result_data) > 1000:
                performance["size_warning"] = "Large result set - consider pagination"
        
        return performance
    
    def _generate_validation_suggestions(self, issues: List[str]) -> List[str]:
        """Genera sugerencias específicas para problemas de validación."""
        suggestions = []
        
        for issue in issues:
            if "injection" in issue.lower():
                suggestions.append("Evita usar caracteres especiales sin escapar")
            elif "permission" in issue.lower():
                suggestions.append("Contacta al administrador para obtener los permisos necesarios")
            elif "syntax" in issue.lower():
                suggestions.append("Revisa la sintaxis de la consulta SQL")
            else:
                suggestions.append("Revisa la consulta y corrige los errores identificados")
        
        return suggestions
    
    def create_summary_response(self, operations: List[Dict]) -> Dict:
        """
        Crea un resumen de múltiples operaciones.
        
        Args:
            operations: Lista de operaciones realizadas
            
        Returns:
            Dict: Resumen formateado
        """
        successful = [op for op in operations if op.get("success", False)]
        failed = [op for op in operations if not op.get("success", False)]
        
        summary = {
            "total_operations": len(operations),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": round(len(successful) / len(operations) * 100, 2) if operations else 0
        }
        
        return self.format_success(
            data=summary,
            metadata={
                "operation_type": "batch_summary",
                "operations_detail": operations
            }
        )
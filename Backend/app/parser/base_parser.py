from abc import ABC, abstractmethod

class BaseParser(ABC):
    """
    Clase base abstracta para todos los parsers SQL.
    Define la interfaz común que deben implementar todos los parsers específicos.
    """
    
    @abstractmethod
    def parse(self, query_or_clause):
        """
        Método abstracto que debe ser implementado por todas las subclases.
        Analiza una consulta o cláusula SQL y devuelve una estructura de datos adecuada.
        
        Args:
            query_or_clause: Consulta o fragmento SQL a analizar
            
        Returns:
            Estructura de datos con el resultado del análisis
        """
        pass
    
    def _remove_quotes(self, text):
        """
        Elimina comillas simples o dobles que rodean un texto.
        
        Args:
            text (str): Texto a procesar
            
        Returns:
            str: Texto sin comillas externas
        """
        if text is None:
            return None
            
        text = text.strip()
        if (text.startswith("'") and text.endswith("'")) or \
           (text.startswith('"') and text.endswith('"')):
            return text[1:-1]
        return text
    
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

import { translatorAPI } from './api.js';

export const readParser = {
    // Referencia al coordinador principal
    main: null,
    
    /**
     * Inicializa el parser READ
     */
    init(mainCoordinator) {
        this.main = mainCoordinator;
        console.log('📊 Parser READ inicializado');
    },
    
    /**
     * Valida permisos para operaciones SELECT/READ
     */
    validatePermissions(permissions, query) {
        if (!permissions.select) {
            throw new Error('❌ No tienes permisos para realizar consultas SELECT');
        }
        console.log('✅ Permisos validados para operación SELECT');
    },
    
    /**
     * ✅ CORREGIDO: Ejecuta consulta con detección mejorada de agregaciones
     */
    async execute(query, database, token) {
        try {
            console.log('📊 Ejecutando consulta read/SELECT...');
            
            // 1. ✅ CRÍTICO: Detectar si realmente es una consulta simple
            if (this.shouldUseAdvancedParser(query)) {
                console.log('🔄 Derivando a parser SELECT avanzado...');
                return await this.main.parsers.select.execute(query, database, token);
            }
            
            // 2. Validar sintaxis básica
            this.validateSyntax(query);
            
            // 3. Analizar consulta simple
            const analysis = this.analyzeSimpleQuery(query);
            console.log('📋 Análisis de consulta READ simple:', analysis);
            
            // 4. Ejecutar en backend
            const result = await translatorAPI.executeSelect(query, database, token);
            
            // 5. Procesar resultado
            return this.processSimpleResult(result, analysis);
            
        } catch (error) {
            console.error('❌ Error en consulta read/SELECT:', error);
            throw error;
        }
    },
    
    /**
     * ✅ NUEVO: Determina si debe usar el parser avanzado
     */
    shouldUseAdvancedParser(query) {
        const upperQuery = query.toUpperCase();
        
        // ✅ CRÍTICO: Detectar funciones de agregación
        const hasAggregation = /\b(COUNT|SUM|AVG|MAX|MIN|GROUP_CONCAT)\s*\(/i.test(query);
        
        // Detectar otras características avanzadas
        const hasGroupBy = upperQuery.includes('GROUP BY');
        const hasHaving = upperQuery.includes('HAVING');
        const hasJoin = upperQuery.includes('JOIN');
        const hasUnion = upperQuery.includes('UNION');
        const hasDistinct = upperQuery.includes('SELECT DISTINCT');
        const hasSubquery = /\(\s*SELECT\s+/i.test(query);
        
        // Si tiene cualquiera de estas características, usar parser avanzado
        if (hasAggregation || hasGroupBy || hasHaving || hasJoin || hasUnion || hasDistinct || hasSubquery) {
            console.log('🔍 Características avanzadas detectadas:', {
                hasAggregation,
                hasGroupBy,
                hasHaving,
                hasJoin,
                hasUnion,
                hasDistinct,
                hasSubquery
            });
            return true;
        }
        
        return false;
    },
    
    /**
     * Valida sintaxis básica de SELECT
     */
    validateSyntax(query) {
        const upperQuery = query.trim().toUpperCase();
        
        if (!upperQuery.startsWith('SELECT')) {
            throw new Error('La consulta debe comenzar con SELECT');
        }
        
        if (!upperQuery.includes('FROM')) {
            throw new Error('Sintaxis incorrecta: SELECT debe incluir FROM');
        }
        
        console.log('✅ Sintaxis SELECT simple validada');
    },
    
    /**
     * ✅ ACTUALIZADO: Analiza consulta SELECT simple
     */
    analyzeSimpleQuery(query) {
        const upperQuery = query.trim().toUpperCase();
        const analysis = {
            type: 'SELECT_SIMPLE',
            table: null,
            fields: [],
            hasWhere: false,
            hasOrderBy: false,
            hasLimit: false,
            complexity: 'simple',
            conditions: [],
            limit: null,
            orderBy: [],
            estimatedResultSize: 'unknown'
        };
        
        try {
            // Extraer tabla principal
            const tableMatch = query.match(/FROM\s+(\w+)/i);
            if (tableMatch) {
                analysis.table = tableMatch[1];
            }
            
            // Extraer campos SELECT
            const selectMatch = query.match(/SELECT\s+(.*?)\s+FROM/i);
            if (selectMatch) {
                const fieldsStr = selectMatch[1].trim();
                if (fieldsStr === '*') {
                    analysis.fields = ['*'];
                } else {
                    analysis.fields = fieldsStr.split(',').map(f => f.trim());
                }
            }
            
            // Verificar cláusulas
            analysis.hasWhere = upperQuery.includes('WHERE');
            analysis.hasOrderBy = upperQuery.includes('ORDER BY');
            analysis.hasLimit = upperQuery.includes('LIMIT');
            
            // Extraer LIMIT
            if (analysis.hasLimit) {
                const limitMatch = query.match(/LIMIT\s+(\d+)/i);
                if (limitMatch) {
                    analysis.limit = parseInt(limitMatch[1]);
                }
            }
            
            // ✅ NUEVO: Extraer ORDER BY detallado
            if (analysis.hasOrderBy) {
                analysis.orderBy = this.parseOrderBy(query);
            }
            
            // Extraer condiciones WHERE
            if (analysis.hasWhere) {
                const whereMatch = query.match(/WHERE\s+(.+?)(?:\s+ORDER|\s+LIMIT|$)/i);
                if (whereMatch) {
                    analysis.conditions = this.parseWhereConditions(whereMatch[1]);
                }
            }
            
            // Estimar tamaño de resultado
            analysis.estimatedResultSize = this.estimateResultSize(analysis);
            
        } catch (error) {
            console.warn('⚠️ Error analizando consulta simple:', error);
        }
        
        return analysis;
    },
    
    /**
     * ✅ NUEVO: Parsea ORDER BY para consultas simples
     */
    parseOrderBy(query) {
        try {
            const orderByMatch = query.match(/ORDER\s+BY\s+(.+?)(?:\s+LIMIT|\s*;|\s*$)/i);
            if (!orderByMatch) return [];
            
            const orderClause = orderByMatch[1].trim();
            const fields = orderClause.split(',').map(field => field.trim());
            
            return fields.map(field => {
                const parts = field.trim().split(/\s+/);
                const fieldName = parts[0];
                const direction = parts.length > 1 && parts[1].toUpperCase() === 'DESC' ? 'DESC' : 'ASC';
                
                return {
                    field: fieldName,
                    direction: direction,
                    mongoDirection: direction === 'DESC' ? -1 : 1
                };
            });
        } catch (error) {
            console.warn('⚠️ Error parseando ORDER BY:', error);
            return [];
        }
    },
    
    /**
     * Parsea condiciones WHERE
     */
    parseWhereConditions(whereClause) {
        try {
            return whereClause
                .split(/\s+AND\s+|\s+OR\s+/i)
                .map(condition => condition.trim())
                .filter(condition => condition.length > 0);
        } catch (error) {
            return [whereClause.trim()];
        }
    },
    
    /**
     * Estima el tamaño del resultado
     */
    estimateResultSize(analysis) {
        if (analysis.limit) {
            if (analysis.limit <= 10) return 'small';
            if (analysis.limit <= 100) return 'medium';
            return 'large';
        }
        
        if (analysis.hasWhere) return 'medium';
        return 'large';
    },
    
    /**
     * ✅ ACTUALIZADO: Procesa resultado de consulta simple
     */
    processSimpleResult(result, analysis) {
        const processed = {
            success: true,
            type: 'SELECT_SIMPLE',
            table: analysis.table,
            result: result,
            summary: null,
            metadata: {
                complexity: analysis.complexity,
                estimatedSize: analysis.estimatedResultSize,
                hasLimit: analysis.hasLimit,
                hasOrderBy: analysis.hasOrderBy,
                orderByFields: analysis.orderBy // ✅ NUEVO
            }
        };
        
        // Determinar estructura del resultado
        let data = result;
        if (result.results) data = result.results;
        if (result.data) data = result.data;
        
        const count = Array.isArray(data) ? data.length : (data ? 1 : 0);
        
        // ✅ ACTUALIZADO: Generar resumen con información de ORDER BY
        if (count === 0) {
            processed.summary = `📊 No se encontraron resultados en ${analysis.table}`;
        } else if (count === 1) {
            processed.summary = `📊 1 registro encontrado en ${analysis.table}`;
        } else {
            processed.summary = `📊 ${count} registros encontrados en ${analysis.table}`;
        }
        
        // Agregar información de ORDER BY al resumen
        if (analysis.hasOrderBy && analysis.orderBy.length > 0) {
            const orderInfo = analysis.orderBy.map(o => `${o.field} ${o.direction}`).join(', ');
            processed.summary += ` (ordenado por: ${orderInfo})`;
        }
        
        // Agregar advertencias si es necesario
        if (analysis.hasLimit && count === analysis.limit) {
            processed.summary += ` (limitado a ${analysis.limit})`;
        }
        
        processed.count = count;
        processed.data = data;
        
        console.log('📋 Resultado SELECT simple procesado:', processed.summary);
        return processed;
    },
    
    /**
     * ✅ ACTUALIZADO: Genera ejemplos de consultas SELECT simples
     */
    getExamples(permissions, currentTable = 'projects') {
        if (!permissions.select) {
            return ['-- No tienes permisos SELECT'];
        }
        
        return [
            // Ejemplos básicos sin agregaciones
            `SELECT * FROM ${currentTable} LIMIT 5;`,
            `SELECT * FROM ${currentTable} ORDER BY name ASC LIMIT 10;`,
            `SELECT * FROM ${currentTable} ORDER BY created_date DESC;`,
            `SELECT name, status FROM ${currentTable} ORDER BY status, name;`,
            `SELECT * FROM ${currentTable} WHERE status = 'In Progress' ORDER BY priority DESC;`,
            `SELECT name, status FROM ${currentTable};`,
            `SELECT * FROM ${currentTable} WHERE status = 'In Progress';`,
            `SELECT name FROM ${currentTable} WHERE status = 'Completed';`,
            `SELECT * FROM restaurants WHERE rating > 4 ORDER BY rating DESC LIMIT 5;`,
            `SELECT name, cuisine_type FROM restaurants WHERE rating >= 4.5;`,
            
            // ✅ NOTA: Las consultas con COUNT, SUM, etc. se manejan en select.js
            // Estos ejemplos son solo para SELECT simples
        ];
    },
    
    /**
     * ✅ ACTUALIZADO: Consejos para consultas SELECT simples
     */
    getTips() {
        return [
            "💡 Usa LIMIT para evitar resultados masivos: SELECT * FROM tabla LIMIT 10;",
            "💡 ORDER BY para ordenar resultados: SELECT * FROM tabla ORDER BY campo ASC;",
            "💡 Múltiples campos ORDER BY: SELECT * FROM tabla ORDER BY campo1, campo2 DESC;",
            "💡 Combina WHERE y ORDER BY: SELECT * FROM tabla WHERE condicion ORDER BY campo;",
            "💡 Especifica campos en lugar de * para mejor rendimiento: SELECT id, name FROM tabla;",
            "💡 Usa WHERE para filtrar resultados: SELECT * FROM tabla WHERE campo = 'valor';",
            "ℹ️ Para COUNT, SUM, AVG usa funciones de agregación (se manejan automáticamente)",
            "ℹ️ Para GROUP BY usa consultas de agrupación (se detectan automáticamente)"
        ];
    },
    
    /**
     * ✅ NUEVO: Obtiene consejos específicos según la consulta
     */
    getQuerySpecificTips(query) {
        const tips = [];
        const upperQuery = query.toUpperCase();
        
        if (!upperQuery.includes('LIMIT')) {
            tips.push("💡 Considera agregar LIMIT para evitar muchos resultados");
        }
        
        if (upperQuery.includes('SELECT *')) {
            tips.push("💡 Considera especificar campos específicos en lugar de *");
        }
        
        if (upperQuery.includes('WHERE') && !upperQuery.includes('ORDER BY')) {
            tips.push("💡 Considera agregar ORDER BY para ordenar los resultados filtrados");
        }
        
        if (!upperQuery.includes('WHERE') && !upperQuery.includes('LIMIT')) {
            tips.push("⚠️ Sin WHERE ni LIMIT puede devolver muchos resultados");
        }
        
        return tips;
    },
    
    /**
     * ✅ NUEVO: Valida si una consulta es apropiada para el parser simple
     */
    validateSimpleQuery(query) {
        const issues = [];
        const warnings = [];
        
        // Verificar que no tenga características avanzadas
        if (this.shouldUseAdvancedParser(query)) {
            issues.push("Esta consulta tiene características avanzadas y debe usar el parser especializado");
        }
        
        // Verificar sintaxis básica
        try {
            this.validateSyntax(query);
        } catch (error) {
            issues.push(error.message);
        }
        
        // Verificar mejores prácticas
        const upperQuery = query.toUpperCase();
        if (!upperQuery.includes('LIMIT') && !upperQuery.includes('WHERE')) {
            warnings.push("Consulta sin WHERE ni LIMIT puede devolver muchos resultados");
        }
        
        if (upperQuery.includes('SELECT *')) {
            warnings.push("SELECT * puede ser ineficiente - considera especificar campos");
        }
        
        return {
            isValid: issues.length === 0,
            issues: issues,
            warnings: warnings,
            tips: this.getQuerySpecificTips(query)
        };
    },
    
    /**
     * ✅ NUEVO: Optimiza consultas simples
     */
    optimizeSimpleQuery(query, analysis) {
        let optimized = query;
        
        // Agregar LIMIT si no tiene y puede devolver muchos resultados
        if (!analysis.hasLimit && !analysis.hasWhere) {
            console.log('⚡ Agregando LIMIT de seguridad a consulta sin filtros');
            optimized += ' LIMIT 1000';
        }
        
        // Sugerir optimizaciones
        const suggestions = [];
        
        if (analysis.fields.includes('*')) {
            suggestions.push("Considera especificar campos específicos en lugar de *");
        }
        
        if (analysis.hasWhere && !analysis.hasOrderBy) {
            suggestions.push("Considera agregar ORDER BY para resultados consistentes");
        }
        
        return {
            optimized: optimized,
            suggestions: suggestions
        };
    }
};
// src/translatorJS/select.js - Parser SELECT avanzado CORREGIDO
// Maneja consultas SELECT complejas con funciones de agregación, COUNT, GROUP BY

import { translatorAPI } from './api.js';

export const selectParser = {
    // Referencia al coordinador principal
    main: null,
    
    /**
     * Inicializa el parser SELECT avanzado
     * @param {Object} mainCoordinator - Referencia al coordinador principal
     */
    init(mainCoordinator) {
        this.main = mainCoordinator;
        console.log('🔍 Parser SELECT avanzado inicializado');
    },
    
    /**
     * Valida permisos para SELECT avanzado
     * @param {Object} permissions - Permisos del usuario
     * @param {string} query - Consulta SQL
     * @throws {Error} Si no tiene permisos
     */
    validatePermissions(permissions, query) {
        if (!permissions.select) {
            throw new Error('❌ No tienes permisos para realizar consultas SELECT');
        }
        console.log('✅ Permisos validados para SELECT avanzado');
    },
    
    /**
     * ✅ CORREGIDO: Ejecuta consulta SELECT avanzada con manejo específico de agregaciones
     */
    async execute(query, database, token) {
        try {
            console.log('🔍 Ejecutando SELECT avanzado...');
            
            // 1. Análisis profundo de la consulta
            const analysis = this.deepAnalyze(query);
            console.log('📊 Análisis profundo:', analysis);
            
            // 2. ✅ NUEVO: Detectar específicamente COUNT(*) y agregaciones
            if (analysis.features.hasAggregation) {
                console.log('🔢 Consulta de agregación detectada');
                return await this.executeAggregationQuery(query, database, token, analysis);
            }
            
            // 3. Optimizar consulta
            const optimizedQuery = this.optimizeAdvancedQuery(query, analysis);
            
            // 4. Ejecutar consulta estándar
            const result = await translatorAPI.executeSelect(optimizedQuery, database, token);
            
            // 5. Procesar resultado
            return this.processAdvancedResult(result, analysis);
            
        } catch (error) {
            console.error('❌ Error en SELECT avanzado:', error);
            throw error;
        }
    },
    
    /**
     * ✅ NUEVO: Ejecuta consultas de agregación (COUNT, SUM, etc.)
     */
    async executeAggregationQuery(query, database, token, analysis) {
        try {
            console.log('🔢 Ejecutando consulta de agregación específica...');
            
            // Ejecutar en backend
            const result = await translatorAPI.executeSelect(query, database, token);
            
            // Procesar resultado específico para agregaciones
            return this.processAggregationResult(result, analysis);
            
        } catch (error) {
            console.error('❌ Error en consulta de agregación:', error);
            throw error;
        }
    },
    
    /**
     * ✅ CORREGIDO: Análisis profundo mejorado para detectar agregaciones
     */
    deepAnalyze(query) {
        const upperQuery = query.toUpperCase();
        const analysis = {
            type: 'SELECT_ADVANCED',
            complexity: 'simple',
            features: {
                hasJoin: false,
                hasSubquery: false,
                hasAggregation: false,
                hasGroupBy: false,
                hasHaving: false,
                hasOrderBy: false,
                hasWindow: false,
                hasUnion: false,
                hasDistinct: false
            },
            tables: [],
            aggregations: [],
            joinTypes: [],
            orderBy: [],
            performance: {
                estimatedCost: 'low',
                recommendedOptimizations: []
            },
            mongodb: {
                requiresPipeline: false,
                estimatedStages: 1
            }
        };
        
        try {
            // ✅ CRÍTICO: Detectar funciones de agregación específicamente
            analysis.features.hasAggregation = this.detectAggregationFunctions(query);
            analysis.aggregations = this.extractDetailedAggregations(query);
            
            // Detectar otras características
            analysis.features.hasJoin = /\s+JOIN\s+/i.test(query);
            analysis.features.hasSubquery = /\(\s*SELECT\s+/i.test(query);
            analysis.features.hasGroupBy = /\bGROUP\s+BY\b/i.test(query);
            analysis.features.hasHaving = /\bHAVING\b/i.test(query);
            analysis.features.hasOrderBy = /\bORDER\s+BY\b/i.test(query);
            analysis.features.hasWindow = /\bOVER\s*\(/i.test(query);
            analysis.features.hasUnion = /\bUNION\b/i.test(query);
            analysis.features.hasDistinct = /\bSELECT\s+DISTINCT\b/i.test(query);
            
            // Extraer tablas
            analysis.tables = this.extractAllTables(query);
            
            // ✅ NUEVO: Extraer ORDER BY detallado
            if (analysis.features.hasOrderBy) {
                analysis.orderBy = this.parseOrderByClause(this.extractOrderByClause(query));
            }
            
            // Determinar complejidad
            analysis.complexity = this.calculateComplexity(analysis.features);
            
            // Planificar estrategia MongoDB
            analysis.mongodb = this.planMongoDBStrategy(analysis);
            
            console.log('📊 Agregaciones detectadas:', analysis.aggregations);
            
        } catch (error) {
            console.warn('⚠️ Error en análisis profundo:', error);
        }
        
        return analysis;
    },
    
    /**
     * ✅ NUEVO: Detecta funciones de agregación con mayor precisión
     */
    detectAggregationFunctions(query) {
        const aggregationPatterns = [
            /\bCOUNT\s*\(\s*\*\s*\)/i,           // COUNT(*)
            /\bCOUNT\s*\(\s*\w+\s*\)/i,         // COUNT(campo)
            /\bSUM\s*\(\s*\w+\s*\)/i,           // SUM(campo)
            /\bAVG\s*\(\s*\w+\s*\)/i,           // AVG(campo)
            /\bMAX\s*\(\s*\w+\s*\)/i,           // MAX(campo)
            /\bMIN\s*\(\s*\w+\s*\)/i,           // MIN(campo)
            /\bGROUP_CONCAT\s*\(/i              // GROUP_CONCAT
        ];
        
        return aggregationPatterns.some(pattern => pattern.test(query));
    },
    
    /**
     * ✅ NUEVO: Extrae agregaciones con detalles completos
     */
    extractDetailedAggregations(query) {
        const aggregations = [];
        
        // Patrones específicos para cada función
        const patterns = {
            COUNT: /\b(COUNT)\s*\(\s*(\*|\w+)\s*\)(?:\s+AS\s+(\w+))?/gi,
            SUM: /\b(SUM)\s*\(\s*(\w+)\s*\)(?:\s+AS\s+(\w+))?/gi,
            AVG: /\b(AVG)\s*\(\s*(\w+)\s*\)(?:\s+AS\s+(\w+))?/gi,
            MAX: /\b(MAX)\s*\(\s*(\w+)\s*\)(?:\s+AS\s+(\w+))?/gi,
            MIN: /\b(MIN)\s*\(\s*(\w+)\s*\)(?:\s+AS\s+(\w+))?/gi,
            GROUP_CONCAT: /\b(GROUP_CONCAT)\s*\(\s*(\w+)\s*\)(?:\s+AS\s+(\w+))?/gi
        };
        
        Object.entries(patterns).forEach(([funcName, pattern]) => {
            let match;
            while ((match = pattern.exec(query)) !== null) {
                const field = match[2]; // El campo o *
                const alias = match[3] || `${funcName.toLowerCase()}_${field === '*' ? 'all' : field}`;
                
                aggregations.push({
                    function: funcName,
                    field: field,
                    alias: alias,
                    expression: match[0],
                    isCountAll: funcName === 'COUNT' && field === '*'
                });
                
                console.log(`🔢 Agregación detectada: ${funcName}(${field}) AS ${alias}`);
            }
        });
        
        return aggregations;
    },
    
    /**
     * ✅ NUEVO: Procesa resultados específicos de agregación
     */
    processAggregationResult(result, analysis) {
        console.log('🔢 Procesando resultado de agregación...');
        
        const processed = {
            success: true,
            type: 'SELECT_AGGREGATION',
            result: result,
            analysis: analysis,
            summary: null,
            metadata: {
                isAggregation: true,
                aggregationType: this.getAggregationType(analysis),
                aggregations: analysis.aggregations,
                hasGroupBy: analysis.features.hasGroupBy,
                hasOrderBy: analysis.features.hasOrderBy,
                performance: analysis.performance
            }
        };
        
        // Extraer datos del resultado
        let data = result;
        if (result.results) data = result.results;
        if (result.data) data = result.data;
        
        // ✅ CRÍTICO: Manejar resultados de agregación específicamente
        if (analysis.aggregations.length > 0) {
            processed.aggregationResults = this.formatAggregationResults(data, analysis.aggregations);
            processed.data = processed.aggregationResults;
        } else {
            processed.data = data;
        }
        
        // Generar resumen específico para agregaciones
        processed.summary = this.generateAggregationSummary(processed.aggregationResults || data, analysis);
        
        console.log('📊 Resultado de agregación procesado:', processed.summary);
        return processed;
    },
    
    /**
     * ✅ NUEVO: Formatea resultados de agregación para mejor presentación
     */
    formatAggregationResults(data, aggregations) {
        if (!Array.isArray(data)) {
            data = [data];
        }
        
        // Si tenemos agregaciones específicas, formatear los resultados
        return data.map(row => {
            const formatted = { ...row };
            
            // Agregar metadatos sobre las agregaciones
            formatted._aggregation_info = {
                functions_used: aggregations.map(a => a.function),
                aliases: aggregations.map(a => a.alias),
                is_summary: true
            };
            
            return formatted;
        });
    },
    
    /**
     * ✅ NUEVO: Genera resumen específico para agregaciones
     */
    generateAggregationSummary(data, analysis) {
        const aggregations = analysis.aggregations;
        
        if (aggregations.length === 1) {
            const agg = aggregations[0];
            
            if (agg.function === 'COUNT' && agg.isCountAll) {
                const count = Array.isArray(data) && data[0] ? data[0][agg.alias] || 0 : 0;
                return `🔢 Total de registros: ${count}`;
            }
            
            return `🔢 ${agg.function}(${agg.field}): resultado calculado`;
        }
        
        if (aggregations.length > 1) {
            const functions = aggregations.map(a => a.function).join(', ');
            return `🔢 Múltiples agregaciones: ${functions}`;
        }
        
        if (analysis.features.hasGroupBy) {
            const count = Array.isArray(data) ? data.length : 1;
            return `📊 Consulta agrupada: ${count} grupo(s) de resultados`;
        }
        
        return '📊 Consulta de agregación ejecutada';
    },
    
    /**
     * ✅ NUEVO: Determina el tipo de agregación principal
     */
    getAggregationType(analysis) {
        if (analysis.features.hasGroupBy) return 'GROUP_BY';
        if (analysis.aggregations.some(a => a.function === 'COUNT')) return 'COUNT';
        if (analysis.aggregations.some(a => a.function === 'SUM')) return 'SUM';
        if (analysis.aggregations.some(a => a.function === 'AVG')) return 'AVERAGE';
        return 'GENERAL';
    },
    
    /**
     * Extrae ORDER BY clause
     */
    extractOrderByClause(query) {
        try {
            const orderByMatch = query.match(/ORDER\s+BY\s+(.+?)(?:\s+LIMIT|\s+OFFSET|\s*;|\s*$)/i);
            return orderByMatch ? orderByMatch[1].trim() : null;
        } catch (error) {
            return null;
        }
    },
    
    /**
     * Parsea ORDER BY clause
     */
    parseOrderByClause(orderByClause) {
        if (!orderByClause) return [];
        
        try {
            const fields = orderByClause.split(',').map(f => f.trim());
            
            return fields.map(field => {
                const parts = field.split(/\s+/);
                const fieldName = parts[0];
                const direction = parts.length > 1 && parts[1].toUpperCase() === 'DESC' ? 'DESC' : 'ASC';
                
                return {
                    field: fieldName,
                    direction: direction,
                    mongoDirection: direction === 'DESC' ? -1 : 1,
                    isFunction: /\w+\s*\(/.test(fieldName)
                };
            });
        } catch (error) {
            return [];
        }
    },
    
    /**
     * Extrae todas las tablas
     */
    extractAllTables(query) {
        const tables = new Set();
        
        try {
            // Tabla principal después de FROM
            const fromMatch = query.match(/FROM\s+(\w+)/i);
            if (fromMatch) tables.add(fromMatch[1]);
            
            // Tablas en JOINs
            const joinMatches = query.matchAll(/JOIN\s+(\w+)/gi);
            for (const match of joinMatches) {
                tables.add(match[1]);
            }
        } catch (error) {
            console.warn('⚠️ Error extrayendo tablas:', error);
        }
        
        return Array.from(tables);
    },
    
    /**
     * Calcula complejidad
     */
    calculateComplexity(features) {
        let score = 0;
        
        if (features.hasJoin) score += 2;
        if (features.hasSubquery) score += 3;
        if (features.hasAggregation) score += 1;
        if (features.hasGroupBy) score += 2;
        if (features.hasHaving) score += 2;
        if (features.hasOrderBy) score += 1;
        if (features.hasDistinct) score += 1;
        if (features.hasWindow) score += 4;
        if (features.hasUnion) score += 2;
        
        if (score === 0) return 'simple';
        if (score <= 3) return 'moderate';
        if (score <= 6) return 'complex';
        return 'very_complex';
    },
    
    /**
     * Planifica estrategia MongoDB
     */
    planMongoDBStrategy(analysis) {
        const strategy = {
            requiresPipeline: false,
            estimatedStages: 1,
            complexity: 'simple'
        };
        
        // Agregaciones requieren pipeline
        if (analysis.features.hasAggregation || 
            analysis.features.hasGroupBy ||
            analysis.features.hasOrderBy ||
            analysis.features.hasDistinct) {
            strategy.requiresPipeline = true;
        }
        
        // Estimar etapas
        let stages = 1;
        if (analysis.features.hasAggregation) stages += 1;
        if (analysis.features.hasGroupBy) stages += 1;
        if (analysis.features.hasOrderBy) stages += 1;
        if (analysis.features.hasDistinct) stages += 1;
        
        strategy.estimatedStages = stages;
        
        if (stages <= 2) strategy.complexity = 'simple';
        else if (stages <= 4) strategy.complexity = 'moderate';
        else strategy.complexity = 'complex';
        
        return strategy;
    },
    
    /**
     * Optimiza consultas avanzadas
     */
    optimizeAdvancedQuery(query, analysis) {
        let optimized = query;
        
        // Agregar LIMIT si es compleja y no tiene
        if (analysis.complexity === 'very_complex' && !/\bLIMIT\b/i.test(query)) {
            console.log('⚡ Agregando LIMIT de seguridad a consulta muy compleja');
            optimized += ' LIMIT 500';
        }
        
        return optimized;
    },
    
    /**
     * Procesa resultados avanzados estándar
     */
    processAdvancedResult(result, analysis) {
        const processed = {
            success: true,
            type: 'SELECT_ADVANCED',
            result: result,
            analysis: analysis,
            summary: null,
            metadata: {
                complexity: analysis.complexity,
                tablesInvolved: analysis.tables.length,
                hasAggregations: analysis.aggregations.length > 0,
                hasOrderBy: analysis.features.hasOrderBy,
                orderByFields: analysis.orderBy,
                performance: analysis.performance
            }
        };
        
        // Determinar datos
        let data = result;
        if (result.results) data = result.results;
        if (result.data) data = result.data;
        
        const count = Array.isArray(data) ? data.length : (data ? 1 : 0);
        
        // Generar resumen
        let summary = `🔍 Consulta ${analysis.complexity} ejecutada: ${count} resultado(s)`;
        
        if (analysis.tables.length > 1) {
            summary += ` (${analysis.tables.length} tablas)`;
        }
        
        if (analysis.aggregations.length > 0) {
            summary += ` con ${analysis.aggregations.length} agregación(es)`;
        }
        
        // Información de ORDER BY
        if (analysis.features.hasOrderBy && analysis.orderBy.length > 0) {
            const orderInfo = analysis.orderBy.map(o => `${o.field} ${o.direction}`).join(', ');
            summary += ` ordenado por: ${orderInfo}`;
        }
        
        processed.summary = summary;
        processed.count = count;
        processed.data = data;
        
        console.log('📊 Resultado SELECT avanzado procesado:', processed.summary);
        return processed;
    },
    
    /**
     * ✅ ACTUALIZADO: Ejemplos con agregaciones y COUNT
     */
    getExamples(permissions, currentTable = 'projects') {
        if (!permissions.select) {
            return ['-- No tienes permisos SELECT'];
        }
        
        return [
            // ✅ NUEVO: Ejemplos específicos de COUNT
            `SELECT COUNT(*) as total_usuarios FROM test_usuarios;`,
            `SELECT COUNT(*) as total_registros FROM ${currentTable};`,
            `SELECT COUNT(id) as registros_con_id FROM ${currentTable};`,
            
            // Ejemplos con GROUP BY y agregaciones
            `SELECT status, COUNT(*) as total FROM ${currentTable} GROUP BY status ORDER BY total DESC;`,
            `SELECT cuisine_type, COUNT(*) as restaurantes, AVG(rating) as rating_promedio FROM restaurants GROUP BY cuisine_type ORDER BY restaurantes DESC;`,
            `SELECT DATE(created_at) as fecha, COUNT(*) as registros_por_dia FROM ${currentTable} GROUP BY DATE(created_at) ORDER BY fecha DESC;`,
            
            // Ejemplos con ORDER BY
            `SELECT * FROM ${currentTable} ORDER BY name ASC LIMIT 10;`,
            `SELECT * FROM ${currentTable} ORDER BY created_date DESC;`,
            `SELECT name, status FROM ${currentTable} ORDER BY status, name;`,
            
            // Ejemplos complejos
            `SELECT MAX(rating) as mejor_rating, MIN(rating) as peor_rating, AVG(rating) as promedio FROM restaurants;`,
            `SELECT status, COUNT(*) as total, AVG(priority) as prioridad_promedio FROM ${currentTable} GROUP BY status HAVING COUNT(*) > 1 ORDER BY total DESC;`
        ];
    }
};
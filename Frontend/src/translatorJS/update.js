// src/translatorJS/update.js - Parser UPDATE (< 100 líneas)
// Maneja consultas UPDATE y modificaciones de datos

import { translatorAPI } from './api.js';

export const updateParser = {
    // Referencia al coordinador principal
    main: null,
    
    /**
     * Inicializa el parser UPDATE
     * @param {Object} mainCoordinator - Referencia al coordinador principal
     */
    init(mainCoordinator) {
        this.main = mainCoordinator;
        console.log('✏️ Parser UPDATE inicializado');
    },
    
    /**
     * Valida permisos para operaciones UPDATE
     * @param {Object} permissions - Permisos del usuario
     * @param {string} query - Consulta SQL
     * @throws {Error} Si no tiene permisos
     */
    validatePermissions(permissions, query) {
        if (!permissions.update) {
            throw new Error('❌ No tienes permisos para realizar operaciones UPDATE');
        }
        
        // Validación de seguridad: UPDATE sin WHERE
        const upperQuery = query.trim().toUpperCase();
        if (!upperQuery.includes('WHERE')) {
            throw new Error('⚠️ UPDATE sin WHERE modificará TODOS los registros. Use WHERE para especificar condiciones.');
        }
        
        console.log('✅ Permisos validados para operación UPDATE');
    },
    
    /**
     * Ejecuta una consulta UPDATE
     * @param {string} query - Consulta SQL
     * @param {string} database - Base de datos
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Resultado de la operación
     */
    async execute(query, database, token) {
        try {
            console.log('✏️ Ejecutando operación UPDATE...');
            
            // 1. Validar sintaxis básica
            this.validateSyntax(query);
            
            // 2. Analizar consulta
            const analysis = this.analyzeQuery(query);
            console.log('📋 Análisis de consulta UPDATE:', analysis);
            
            // 3. Validaciones de seguridad adicionales
            this.performSecurityChecks(analysis);
            
            // 4. Generar previsualización si es posible
            const previewQuery = this.generatePreviewQuery(query);
            console.log('👁️ Consulta de previsualización:', previewQuery);
            
            // 5. Ejecutar en backend
            const result = await translatorAPI.executeUpdate(query, database, token);
            
            // 6. Procesar resultado
            return this.processResult(result, analysis);
            
        } catch (error) {
            console.error('❌ Error en operación UPDATE:', error);
            throw error;
        }
    },
    
    /**
     * Valida la sintaxis básica de UPDATE
     * @param {string} query - Consulta SQL
     * @throws {Error} Si la sintaxis es inválida
     */
    validateSyntax(query) {
        const upperQuery = query.trim().toUpperCase();
        
        if (!upperQuery.startsWith('UPDATE')) {
            throw new Error('La consulta debe comenzar con UPDATE');
        }
        
        if (!upperQuery.includes('SET')) {
            throw new Error('Sintaxis incorrecta: UPDATE debe incluir SET');
        }
        
        if (!upperQuery.includes('WHERE')) {
            console.warn('⚠️ UPDATE sin WHERE detectado');
        }
        
        // Verificar estructura básica UPDATE tabla SET campo = valor WHERE condicion
        const basicPattern = /UPDATE\s+\w+\s+SET\s+.+/i;
        if (!basicPattern.test(query)) {
            throw new Error('Sintaxis incorrecta: Estructura UPDATE inválida');
        }
        
        console.log('✅ Sintaxis UPDATE validada');
    },
    
    /**
     * Analiza la estructura de la consulta UPDATE
     * @param {string} query - Consulta SQL
     * @returns {Object} - Análisis detallado
     */
    analyzeQuery(query) {
        const upperQuery = query.trim().toUpperCase();
        const analysis = {
            type: 'UPDATE',
            table: null,
            fields: [],
            hasWhere: false,
            conditions: [],
            estimatedImpact: 'unknown',
            isDangerous: false,
            warning: null,
            setClause: null,
            whereClause: null
        };
        
        try {
            // Extraer tabla
            const tableMatch = query.match(/UPDATE\s+(\w+)/i);
            if (tableMatch) {
                analysis.table = tableMatch[1];
            }
            
            // Extraer cláusula SET
            const setMatch = query.match(/SET\s+(.*?)(?:\s+WHERE|$)/i);
            if (setMatch) {
                analysis.setClause = setMatch[1].trim();
                
                // Extraer campos que se van a actualizar
                const fieldUpdates = analysis.setClause.split(',');
                analysis.fields = fieldUpdates.map(update => {
                    const fieldMatch = update.trim().match(/(\w+)\s*=/);
                    return fieldMatch ? fieldMatch[1] : 'unknown';
                });
            }
            
            // Extraer cláusula WHERE
            analysis.hasWhere = upperQuery.includes('WHERE');
            if (analysis.hasWhere) {
                const whereMatch = query.match(/WHERE\s+(.+?)(?:\s+ORDER|\s+LIMIT|$)/i);
                if (whereMatch) {
                    analysis.whereClause = whereMatch[1].trim();
                    analysis.conditions = this.parseWhereConditions(analysis.whereClause);
                }
                analysis.estimatedImpact = 'filtered_records';
            } else {
                analysis.isDangerous = true;
                analysis.warning = 'UPDATE sin WHERE modificará TODOS los registros';
                analysis.estimatedImpact = 'all_records';
            }
            
            // Evaluar nivel de peligro
            if (analysis.conditions.length === 0 && analysis.hasWhere) {
                analysis.isDangerous = true;
                analysis.warning = 'Condiciones WHERE muy amplias';
            }
            
        } catch (error) {
            console.warn('⚠️ Error analizando UPDATE:', error);
        }
        
        return analysis;
    },
    
    /**
     * Parsea condiciones WHERE
     * @param {string} whereClause - Cláusula WHERE
     * @returns {Array} - Array de condiciones
     */
    parseWhereConditions(whereClause) {
        try {
            return whereClause
                .split(/\s+AND\s+|\s+OR\s+/i)
                .map(condition => condition.trim())
                .filter(condition => condition.length > 0);
        } catch (error) {
            return [whereClause];
        }
    },
    
    /**
     * Realiza verificaciones de seguridad adicionales
     * @param {Object} analysis - Análisis de la consulta
     * @throws {Error} Si detecta operaciones peligrosas
     */
    performSecurityChecks(analysis) {
        // Verificar operaciones muy peligrosas
        if (analysis.isDangerous && analysis.estimatedImpact === 'all_records') {
            throw new Error('🚨 Operación peligrosa: UPDATE sin WHERE modificará TODOS los registros');
        }
        
        // Advertir sobre actualizaciones masivas
        if (analysis.conditions.length === 1 && 
            !analysis.conditions[0].includes('=') && 
            !analysis.conditions[0].includes('id')) {
            console.warn('⚠️ Actualización potencialmente masiva detectada');
        }
        
        // Verificar campos críticos
        const criticalFields = ['id', '_id', 'email', 'password', 'role'];
        const updatingCriticalFields = analysis.fields.some(field => 
            criticalFields.includes(field.toLowerCase())
        );
        
        if (updatingCriticalFields) {
            console.warn('⚠️ Actualizando campos críticos:', analysis.fields.filter(f => 
                criticalFields.includes(f.toLowerCase())
            ));
        }
    },
    
    /**
     * Genera consulta SELECT para previsualizar qué se va a actualizar
     * @param {string} updateQuery - Consulta UPDATE
     * @returns {string} - Consulta SELECT de previsualización
     */
    generatePreviewQuery(updateQuery) {
        try {
            // Convertir UPDATE tabla SET campos WHERE condiciones
            // a SELECT * FROM tabla WHERE condiciones
            
            const tableMatch = updateQuery.match(/UPDATE\s+(\w+)/i);
            const whereMatch = updateQuery.match(/WHERE\s+(.+?)(?:\s+ORDER|\s+LIMIT|$)/i);
            
            if (tableMatch) {
                const table = tableMatch[1];
                const whereClause = whereMatch ? ` WHERE ${whereMatch[1]}` : '';
                return `SELECT * FROM ${table}${whereClause} LIMIT 100;`;
            }
            
            return 'No se puede generar previsualización';
        } catch (error) {
            return 'Error generando previsualización';
        }
    },
    
    /**
     * Procesa el resultado de la operación UPDATE
     * @param {Object} result - Resultado del backend
     * @param {Object} analysis - Análisis de la consulta
     * @returns {Object} - Resultado procesado
     */
    processResult(result, analysis) {
        const processed = {
            success: true,
            type: 'UPDATE',
            table: analysis.table,
            result: result,
            summary: null,
            fieldsUpdated: analysis.fields,
            impact: analysis.estimatedImpact
        };
        
        // Determinar cantidad de registros modificados
        const modifiedCount = result.modifiedCount || 
                            result.modified_count || 
                            result.matchedCount || 
                            result.matched_count || 
                            0;
        
        const matchedCount = result.matchedCount || 
                           result.matched_count || 
                           modifiedCount;
        
        processed.modifiedCount = modifiedCount;
        processed.matchedCount = matchedCount;
        
        // Generar resumen
        if (modifiedCount === 0) {
            if (matchedCount === 0) {
                processed.summary = `ℹ️ No se encontraron registros que coincidan con las condiciones en ${analysis.table}`;
            } else {
                processed.summary = `ℹ️ Se encontraron ${matchedCount} registro(s) en ${analysis.table}, pero no se realizaron cambios (valores idénticos)`;
            }
        } else {
            processed.summary = `✏️ Actualizados ${modifiedCount} registro(s) en ${analysis.table}`;
            
            if (analysis.fields.length > 0) {
                processed.summary += ` (campos: ${analysis.fields.join(', ')})`;
            }
        }
        
        // Agregar advertencias si es necesario
        if (analysis.isDangerous) {
            processed.summary += ' ⚠️ (Operación de alto impacto)';
        }
        
        console.log('📋 Resultado UPDATE procesado:', processed.summary);
        return processed;
    },
    
    /**
     * Genera ejemplos seguros de UPDATE según permisos
     * @param {Object} permissions - Permisos del usuario
     * @param {string} currentTable - Tabla actualmente seleccionada
     * @returns {Array} - Lista de ejemplos seguros
     */
    getExamples(permissions, currentTable = 'projects') {
        if (!permissions.update) {
            return ['-- No tienes permisos UPDATE'];
        }
        
        return [
            `UPDATE ${currentTable} SET status = 'Completed' WHERE id = 'PRJ001';`,
            `UPDATE ${currentTable} SET status = 'In Progress', priority = 'High' WHERE status = 'Planning';`,
            `UPDATE restaurants SET rating = 4.5 WHERE name = 'Nuevo Restaurante';`,
            `UPDATE ${currentTable} SET end_date = '2025-06-30' WHERE status = 'Planning' AND start_date > '2025-01-01';`,
            `UPDATE restaurants SET cuisine_type = 'Mediterranean' WHERE cuisine_type = 'Italian' AND rating > 4;`,
            `UPDATE ${currentTable} SET description = 'Proyecto actualizado' WHERE id = 'PRJ002';`
        ];
    },
    
    /**
     * Obtiene consejos de seguridad para UPDATE
     * @returns {Array} - Lista de consejos
     */
    getSecurityTips() {
        return [
            "⚠️ SIEMPRE usa WHERE en UPDATE para evitar modificar todos los registros",
            "💡 Prueba primero con SELECT para ver qué registros se van a actualizar",
            "🎯 Usa condiciones específicas: UPDATE tabla SET campo = 'valor' WHERE id = 'específico'",
            "💾 Considera hacer backup antes de UPDATE masivos",
            "🔒 Ten cuidado al actualizar campos críticos como email, password o role",
            "📊 Verifica el resultado: cuántos registros fueron modificados vs encontrados"
        ];
    },
    
    /**
     * Convierte UPDATE a SELECT para previsualización
     * @param {string} updateQuery - Consulta UPDATE
     * @returns {string} - Consulta SELECT equivalente para previsualización
     */
    convertToPreview(updateQuery) {
        return this.generatePreviewQuery(updateQuery);
    },
    
    /**
     * Valida campos a actualizar
     * @param {Array} fields - Campos a actualizar
     * @returns {Object} - Resultado de la validación
     */
    validateFields(fields) {
        const validation = {
            safe: [],
            warning: [],
            dangerous: []
        };
        
        const criticalFields = ['id', '_id', 'email', 'password', 'role', 'permissions'];
        const warningFields = ['created_at', 'updated_at', 'created_date', 'modified_date'];
        
        fields.forEach(field => {
            const fieldLower = field.toLowerCase();
            
            if (criticalFields.includes(fieldLower)) {
                validation.dangerous.push(field);
            } else if (warningFields.includes(fieldLower)) {
                validation.warning.push(field);
            } else {
                validation.safe.push(field);
            }
        });
        
        return validation;
    }
};
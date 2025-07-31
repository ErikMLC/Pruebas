// src/translatorJS/delete.js - Parser DELETE (< 80 líneas)
// Maneja consultas DELETE FROM y DROP TABLE

import { translatorAPI } from './api.js';

export const deleteParser = {
    // Referencia al coordinador principal
    main: null,
    
    /**
     * Inicializa el parser DELETE
     * @param {Object} mainCoordinator - Referencia al coordinador principal
     */
    init(mainCoordinator) {
        this.main = mainCoordinator;
        console.log('🗑️ Parser DELETE inicializado');
    },
    
    /**
     * Valida permisos para operaciones DELETE
     * @param {Object} permissions - Permisos del usuario
     * @param {string} query - Consulta SQL
     * @throws {Error} Si no tiene permisos
     */
    validatePermissions(permissions, query) {
        const upperQuery = query.trim().toUpperCase();
        
        if (upperQuery.startsWith('DELETE')) {
            if (!permissions.delete) {
                throw new Error('❌ No tienes permisos para realizar operaciones DELETE');
            }
        } else if (upperQuery.includes('DROP TABLE') || upperQuery.includes('DROP COLLECTION')) {
            if (!permissions.drop_table) {
                throw new Error('❌ No tienes permisos para eliminar tablas/colecciones');
            }
        }
        
        // Validación de seguridad: DELETE sin WHERE
        if (upperQuery.startsWith('DELETE') && !upperQuery.includes('WHERE')) {
            throw new Error('⚠️ DELETE sin WHERE eliminará TODOS los registros. Use WHERE para especificar condiciones.');
        }
        
        console.log('✅ Permisos validados para operación DELETE');
    },
    
    /**
     * Ejecuta una consulta DELETE
     * @param {string} query - Consulta SQL
     * @param {string} database - Base de datos
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Resultado de la operación
     */
    async execute(query, database, token) {
        try {
            console.log('🗑️ Ejecutando operación DELETE...');
            
            // 1. Validar sintaxis básica
            this.validateSyntax(query);
            
            // 2. Analizar consulta
            const analysis = this.analyzeQuery(query);
            console.log('📋 Análisis de consulta DELETE:', analysis);
            
            // 3. Confirmación adicional para operaciones peligrosas
            if (analysis.isDangerous) {
                console.warn('⚠️ Operación peligrosa detectada:', analysis.warning);
            }
            
            // 4. Ejecutar en backend
            const result = await translatorAPI.executeDelete(query, database, token);
            
            // 5. Procesar resultado
            return this.processResult(result, analysis);
            
        } catch (error) {
            console.error('❌ Error en operación DELETE:', error);
            throw error;
        }
    },
    
    /**
     * Valida la sintaxis básica de la consulta DELETE
     * @param {string} query - Consulta SQL
     * @throws {Error} Si la sintaxis es inválida
     */
    validateSyntax(query) {
        const upperQuery = query.trim().toUpperCase();
        
        if (upperQuery.startsWith('DELETE')) {
            // Validar DELETE básico
            if (!upperQuery.includes('FROM')) {
                throw new Error('Sintaxis incorrecta: DELETE debe incluir FROM');
            }
            
            // Advertencia para DELETE sin WHERE
            if (!upperQuery.includes('WHERE')) {
                console.warn('⚠️ DELETE sin WHERE eliminará todos los registros');
            }
            
        } else if (upperQuery.startsWith('DROP')) {
            // Validar DROP básico
            if (!upperQuery.includes('TABLE') && !upperQuery.includes('COLLECTION')) {
                throw new Error('Sintaxis incorrecta: DROP debe especificar TABLE o COLLECTION');
            }
        }
        
        console.log('✅ Sintaxis básica validada');
    },
    
    /**
     * Analiza la estructura de la consulta DELETE
     * @param {string} query - Consulta SQL
     * @returns {Object} - Análisis de la consulta
     */
    analyzeQuery(query) {
        const upperQuery = query.trim().toUpperCase();
        const analysis = {
            type: null,
            table: null,
            hasWhere: false,
            conditions: [],
            isDangerous: false,
            warning: null,
            estimatedImpact: 'unknown'
        };
        
        if (upperQuery.startsWith('DELETE')) {
            analysis.type = 'DELETE';
            
            // Extraer nombre de tabla
            const tableMatch = query.match(/DELETE\s+FROM\s+(\w+)/i);
            if (tableMatch) {
                analysis.table = tableMatch[1];
            }
            
            // Verificar cláusula WHERE
            analysis.hasWhere = upperQuery.includes('WHERE');
            if (!analysis.hasWhere) {
                analysis.isDangerous = true;
                analysis.warning = 'DELETE sin WHERE eliminará TODOS los registros';
                analysis.estimatedImpact = 'all_records';
            } else {
                // Extraer condiciones WHERE (básico)
                const whereMatch = query.match(/WHERE\s+(.+?)(?:ORDER|LIMIT|$)/i);
                if (whereMatch) {
                    analysis.conditions = whereMatch[1].trim().split(/\s+AND\s+|\s+OR\s+/i);
                }
                analysis.estimatedImpact = 'filtered_records';
            }
            
        } else if (upperQuery.startsWith('DROP')) {
            analysis.type = 'DROP';
            
            // Extraer nombre de tabla
            const tableMatch = query.match(/DROP\s+(?:TABLE|COLLECTION)\s+(\w+)/i);
            if (tableMatch) {
                analysis.table = tableMatch[1];
            }
            
            analysis.isDangerous = true;
            analysis.warning = 'DROP eliminará completamente la tabla/colección';
            analysis.estimatedImpact = 'entire_table';
        }
        
        return analysis;
    },
    
    /**
     * Procesa el resultado de la operación DELETE
     * @param {Object} result - Resultado del backend
     * @param {Object} analysis - Análisis de la consulta
     * @returns {Object} - Resultado procesado
     */
    processResult(result, analysis) {
        const processed = {
            success: true,
            type: analysis.type,
            table: analysis.table,
            result: result,
            summary: null,
            impact: analysis.estimatedImpact
        };
        
        if (analysis.type === 'DELETE') {
            // Procesar resultado de DELETE
            const deletedCount = result.deletedCount || result.deleted_count || 0;
            processed.deletedCount = deletedCount;
            
            if (deletedCount === 0) {
                processed.summary = `ℹ️ No se eliminaron registros de ${analysis.table} (no se encontraron coincidencias)`;
            } else {
                processed.summary = `🗑️ Eliminados ${deletedCount} registro(s) de ${analysis.table}`;
            }
            
        } else if (analysis.type === 'DROP') {
            // Procesar resultado de DROP
            processed.summary = `🗑️ Tabla/Colección '${analysis.table}' eliminada completamente`;
        }
        
        console.log('📋 Resultado DELETE procesado:', processed.summary);
        return processed;
    },
    
    /**
     * Genera ejemplos seguros de consultas DELETE según permisos
     * @param {Object} permissions - Permisos del usuario
     * @param {string} currentTable - Tabla actualmente seleccionada
     * @returns {Array} - Lista de ejemplos seguros
     */
    getExamples(permissions, currentTable = 'projects') {
        const examples = [];
        
        if (permissions.delete) {
            examples.push(
                `DELETE FROM ${currentTable} WHERE status = 'Cancelled';`,
                `DELETE FROM ${currentTable} WHERE id = 'PRJ999';`,
                `DELETE FROM restaurants WHERE rating < 2;`,
                `DELETE FROM ${currentTable} WHERE created_date < '2020-01-01';`
            );
        }
        
        if (permissions.drop_table) {
            examples.push(
                `DROP TABLE tabla_temporal;`,
                `DROP COLLECTION coleccion_test;`
            );
        }
        
        return examples;
    },
    
    /**
     * Obtiene consejos de seguridad para DELETE
     * @returns {Array} - Lista de consejos
     */
    getSecurityTips() {
        return [
            "⚠️ SIEMPRE usa WHERE en DELETE para evitar eliminar todos los registros",
            "💡 Prueba primero con SELECT para ver qué registros se eliminarán",
            "🔒 DROP TABLE elimina completamente la tabla - ¡ten cuidado!",
            "💾 Considera hacer backup antes de operaciones DELETE masivas",
            "🎯 Usa condiciones específicas: DELETE FROM tabla WHERE id = 'específico'"
        ];
    },
    
    /**
     * Convierte DELETE a SELECT para previsualización
     * @param {string} deleteQuery - Consulta DELETE
     * @returns {string} - Consulta SELECT equivalente
     */
    convertToPreview(deleteQuery) {
        try {
            const upperQuery = deleteQuery.trim().toUpperCase();
            if (upperQuery.startsWith('DELETE FROM')) {
                // Convertir DELETE FROM tabla WHERE... a SELECT * FROM tabla WHERE...
                return deleteQuery.replace(/DELETE\s+FROM/i, 'SELECT * FROM');
            }
            return deleteQuery;
        } catch (error) {
            return deleteQuery;
        }
    }
};
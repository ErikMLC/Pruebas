// src/translatorJS/create.js - Parser INSERT/CREATE (< 80 líneas)
// Maneja consultas INSERT INTO y CREATE TABLE

import { translatorAPI } from './api.js';

export const createParser = {
    // Referencia al coordinador principal
    main: null,
    
    /**
     * Inicializa el parser CREATE
     * @param {Object} mainCoordinator - Referencia al coordinador principal
     */
    init(mainCoordinator) {
        this.main = mainCoordinator;
        console.log('➕ Parser CREATE inicializado');
    },
    
    /**
     * Valida permisos para operaciones CREATE/INSERT
     * @param {Object} permissions - Permisos del usuario
     * @param {string} query - Consulta SQL
     * @throws {Error} Si no tiene permisos
     */
    validatePermissions(permissions, query) {
        const upperQuery = query.trim().toUpperCase();
        
        if (upperQuery.startsWith('INSERT')) {
            if (!permissions.insert) {
                throw new Error('❌ No tienes permisos para realizar operaciones INSERT');
            }
        } else if (upperQuery.includes('CREATE TABLE') || upperQuery.includes('CREATE COLLECTION')) {
            if (!permissions.create_table) {
                throw new Error('❌ No tienes permisos para crear tablas/colecciones');
            }
        }
        
        console.log('✅ Permisos validados para operación CREATE/INSERT');
    },
    
    /**
     * Ejecuta una consulta INSERT/CREATE
     * @param {string} query - Consulta SQL
     * @param {string} database - Base de datos
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Resultado de la operación
     */
    async execute(query, database, token) {
        try {
            console.log('➕ Ejecutando operación CREATE/INSERT...');
            
            // 1. Validar sintaxis básica
            this.validateSyntax(query);
            
            // 2. Analizar consulta
            const analysis = this.analyzeQuery(query);
            console.log('📋 Análisis de consulta:', analysis);
            
            // 3. Ejecutar en backend
            const result = await translatorAPI.executeInsert(query, database, token);
            
            // 4. Procesar resultado
            return this.processResult(result, analysis);
            
        } catch (error) {
            console.error('❌ Error en operación CREATE/INSERT:', error);
            throw error;
        }
    },
    
    /**
     * Valida la sintaxis básica de la consulta
     * @param {string} query - Consulta SQL
     * @throws {Error} Si la sintaxis es inválida
     */
    validateSyntax(query) {
        const upperQuery = query.trim().toUpperCase();
        
        if (upperQuery.startsWith('INSERT')) {
            // Validar INSERT básico
            if (!upperQuery.includes('INTO')) {
                throw new Error('Sintaxis incorrecta: INSERT debe incluir INTO');
            }
            if (!upperQuery.includes('VALUES') && !upperQuery.includes('SELECT')) {
                throw new Error('Sintaxis incorrecta: INSERT debe incluir VALUES o SELECT');
            }
        } else if (upperQuery.startsWith('CREATE')) {
            // Validar CREATE básico
            if (!upperQuery.includes('TABLE') && !upperQuery.includes('COLLECTION')) {
                throw new Error('Sintaxis incorrecta: CREATE debe especificar TABLE o COLLECTION');
            }
        }
        
        console.log('✅ Sintaxis básica validada');
    },
    
    /**
     * Analiza la estructura de la consulta
     * @param {string} query - Consulta SQL
     * @returns {Object} - Análisis de la consulta
     */
    analyzeQuery(query) {
        const upperQuery = query.trim().toUpperCase();
        const analysis = {
            type: null,
            table: null,
            fields: [],
            values: [],
            estimatedDocs: 0
        };
        
        if (upperQuery.startsWith('INSERT')) {
            analysis.type = 'INSERT';
            
            // Extraer nombre de tabla
            const tableMatch = query.match(/INSERT\s+INTO\s+(\w+)/i);
            if (tableMatch) {
                analysis.table = tableMatch[1];
            }
            
            // Extraer campos
            const fieldsMatch = query.match(/\(([^)]+)\)\s+VALUES/i);
            if (fieldsMatch) {
                analysis.fields = fieldsMatch[1].split(',').map(f => f.trim());
            }
            
            // Contar valores (estimar documentos a insertar)
            const valuesMatches = query.match(/VALUES\s*\([^)]+\)/gi);
            analysis.estimatedDocs = valuesMatches ? valuesMatches.length : 1;
            
        } else if (upperQuery.startsWith('CREATE')) {
            analysis.type = 'CREATE';

            if (upperQuery.includes('CREATE TABLE') && upperQuery.includes('(')) {
                analysis.type = 'CREATE_TABLE';
                analysis.hasColumns = true;
                
                // Extraer columnas básicas
                const columnsMatch = query.match(/CREATE\s+TABLE\s+\w+\s*\((.*)\)/i);
                if (columnsMatch) {
                    const columnsStr = columnsMatch[1];
                    analysis.estimatedColumns = columnsStr.split(',').length;
                }
            }
        }
        
        return analysis;
    },
    
    /**
     * Procesa el resultado de la operación
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
            summary: null
        };
        
        if (analysis.type === 'INSERT') {
            // Procesar resultado de INSERT
            const insertedCount = result.insertedCount || result.inserted_count || analysis.estimatedDocs;
            processed.summary = `✅ Insertados ${insertedCount} documento(s) en ${analysis.table}`;
            
            if (result.insertedIds || result.inserted_ids) {
                processed.insertedIds = result.insertedIds || result.inserted_ids;
            }
            
        } else if (analysis.type === 'CREATE') {
            // Procesar resultado de CREATE
            processed.summary = `✅ Tabla/Colección '${analysis.table}' creada exitosamente`;
        }
        
        console.log('📋 Resultado procesado:', processed.summary);
        return processed;
    },
    
    /**
     * Genera ejemplos de consultas CREATE/INSERT según permisos
     * @param {Object} permissions - Permisos del usuario
     * @param {string} currentTable - Tabla actualmente seleccionada
     * @returns {Array} - Lista de ejemplos
     */
    getExamples(permissions, currentTable = 'projects') {
        const examples = [];
        
        if (permissions.insert) {
            examples.push(
                `INSERT INTO ${currentTable} (name, status) VALUES ('Nuevo Proyecto', 'Planning');`,
                `INSERT INTO ${currentTable} (name, description, status) VALUES ('API Development', 'Nueva API REST', 'In Progress');`,
                `INSERT INTO restaurants (name, cuisine_type, rating) VALUES ('Nuevo Restaurante', 'Italiana', 4.5);`
            );
        }
        
        if (permissions.create_table) {
            examples.push(
                `CREATE TABLE nueva_tabla (id INT, name VARCHAR(50), created_at TIMESTAMP);`,
                `CREATE COLLECTION nueva_coleccion;`
            );
        }
        
        return examples;
    },


    /**
     * ✅ NUEVO: Manejo específico para CREATE TABLE
     */
    async executeCreateTable(query, database, token, analysis) {
        console.log('🏗️ Ejecutando CREATE TABLE con esquema...');
        const result = await translatorAPI.executeInsert(query, database, token);
        return this.processCreateTableResult(result, analysis);
    },

    /**
     * ✅ NUEVO: Procesa resultado CREATE TABLE
     */
    processCreateTableResult(result, analysis) {
        const processed = {
            success: true,
            type: 'CREATE_TABLE',
            table: analysis.table,
            result: result,
            summary: null,
            schema_info: result.schema_info || null,
            indexes_created: result.indexes_created || [],
            has_validator: result.has_validator || false
        };
        
        // Generar resumen específico para CREATE TABLE
        let summary = `✅ Tabla '${analysis.table}' creada exitosamente`;
        
        if (result.schema_info && result.schema_info.total_columns) {
            summary += ` con ${result.schema_info.total_columns} columnas`;
        }
        
        if (result.indexes_created && result.indexes_created.length > 0) {
            summary += ` y ${result.indexes_created.length} índice(s)`;
        }
        
        if (result.has_validator) {
            summary += ` (con validación de esquema)`;
        }
        
        processed.summary = summary;
        return processed;
    },

    /**
     * Obtiene consejos para el usuario sobre CREATE/INSERT
     * @returns {Array} - Lista de consejos
     */
    getTips() {
        return [
            "💡 INSERT INTO tabla (campo1, campo2) VALUES (valor1, valor2);",
            "💡 Puedes insertar múltiples registros: VALUES (val1, val2), (val3, val4);",
            "💡 Asegúrate de que los tipos de datos coincidan con la estructura",
            "💡 CREATE TABLE crea nuevas estructuras en la base de datos"
        ];
    }
};
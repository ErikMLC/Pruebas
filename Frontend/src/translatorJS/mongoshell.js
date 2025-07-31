// src/translatorJS/mongoshell.js - Generador MongoDB Shell CORREGIDO
// Genera consultas MongoDB shell equivalentes con soporte completo para agregaciones

import { translatorAPI } from './api.js';

export const mongoShell = {
    // Referencia al coordinador principal
    main: null,
    
    /**
     * Inicializa el generador MongoDB Shell
     */
    init(mainCoordinator) {
        this.main = mainCoordinator;
        console.log('🐚 Generador MongoDB Shell inicializado');
    },
    
    /**
     * Genera consulta MongoDB shell desde SQL
     */
    async generate(sqlQuery, database, token) {
        try {
            console.log('🐚 Generando MongoDB shell query...');
            
            // 1. Intentar obtener del backend primero
            const backendShell = await this.getFromBackend(sqlQuery, database, token);
            if (backendShell && this.isValidShellQuery(backendShell)) {
                return this.formatShellQuery(backendShell);
            }
            
            // 2. Fallback: generar localmente con análisis completo
            console.log('📝 Generando shell query localmente...');
            return this.generateLocalAdvanced(sqlQuery);
            
        } catch (error) {
            console.warn('⚠️ Error generando shell query:', error.message);
            return this.generateLocalAdvanced(sqlQuery);
        }
    },
    
    /**
     * Obtiene shell query desde el backend
     */
    async getFromBackend(sqlQuery, database, token) {
        try {
            const shellQuery = await translatorAPI.generateShellQuery(sqlQuery, database, token);
            return shellQuery;
        } catch (error) {
            console.warn('⚠️ Backend shell generation failed:', error.message);
            return null;
        }
    },
    
    /**
     * Valida si una shell query es válida
     */
    isValidShellQuery(shellQuery) {
        return shellQuery && 
               !shellQuery.includes('Error') && 
               !shellQuery.includes('error') &&
               shellQuery.trim() !== '' &&
               shellQuery.includes('db.');
    },
    
    /**
     * ✅ NUEVO: Genera shell query localmente con análisis avanzado
     */
    generateLocalAdvanced(sqlQuery) {
        try {
            const analysis = this.analyzeSQL(sqlQuery);
            console.log('📊 Análisis SQL para shell:', analysis);
            
            if (analysis.type === 'SELECT') {
                return this.generateSelectShellAdvanced(sqlQuery, analysis);
            } else if (analysis.type === 'INSERT') {
                return this.generateInsertShell(sqlQuery);
            } else if (analysis.type === 'UPDATE') {
                return this.generateUpdateShell(sqlQuery);
            } else if (analysis.type === 'DELETE') {
                return this.generateDeleteShell(sqlQuery);
            } else if (analysis.type === 'CREATE') {
                return this.generateCreateShell(sqlQuery);
            } else if (analysis.type === 'DROP') {
                return this.generateDropShell(sqlQuery);
            }
            
            return `// Consulta SQL no reconocida:\n// ${sqlQuery}`;
            
        } catch (error) {
            return `// Error generando shell query: ${error.message}\n// SQL: ${sqlQuery}`;
        }
    },
    
    /**
     * ✅ NUEVO: Analiza consulta SQL para detectar características
     */
    analyzeSQL(sqlQuery) {
        const upperQuery = sqlQuery.toUpperCase();
        const analysis = {
            type: this.detectQueryType(sqlQuery),
            table: this.extractTableName(sqlQuery),
            hasAggregation: false,
            hasGroupBy: false,
            hasOrderBy: false,
            hasWhere: false,
            hasLimit: false,
            aggregations: [],
            orderBy: null,
            limit: null
        };
        
        // Detectar características específicas
        analysis.hasAggregation = this.detectAggregationFunctions(sqlQuery);
        analysis.hasGroupBy = upperQuery.includes('GROUP BY');
        analysis.hasOrderBy = upperQuery.includes('ORDER BY');
        analysis.hasWhere = upperQuery.includes('WHERE');
        analysis.hasLimit = upperQuery.includes('LIMIT');
        
        // Extraer detalles
        if (analysis.hasAggregation) {
            analysis.aggregations = this.extractAggregations(sqlQuery);
        }
        
        if (analysis.hasOrderBy) {
            analysis.orderBy = this.extractOrderBy(sqlQuery);
        }
        
        if (analysis.hasLimit) {
            analysis.limit = this.extractLimit(sqlQuery);
        }
        
        return analysis;
    },
    
    /**
     * ✅ NUEVO: Detecta funciones de agregación
     */
    detectAggregationFunctions(query) {
        const aggregationPatterns = [
            /\bCOUNT\s*\(\s*\*\s*\)/i,
            /\bCOUNT\s*\(\s*\w+\s*\)/i,
            /\bSUM\s*\(\s*\w+\s*\)/i,
            /\bAVG\s*\(\s*\w+\s*\)/i,
            /\bMAX\s*\(\s*\w+\s*\)/i,
            /\bMIN\s*\(\s*\w+\s*\)/i
        ];
        
        return aggregationPatterns.some(pattern => pattern.test(query));
    },
    
    /**
     * ✅ NUEVO: Extrae agregaciones detalladas
     */
    extractAggregations(query) {
        const aggregations = [];
        
        const patterns = {
            COUNT: /\b(COUNT)\s*\(\s*(\*|\w+)\s*\)(?:\s+AS\s+(\w+))?/gi,
            SUM: /\b(SUM)\s*\(\s*(\w+)\s*\)(?:\s+AS\s+(\w+))?/gi,
            AVG: /\b(AVG)\s*\(\s*(\w+)\s*\)(?:\s+AS\s+(\w+))?/gi,
            MAX: /\b(MAX)\s*\(\s*(\w+)\s*\)(?:\s+AS\s+(\w+))?/gi,
            MIN: /\b(MIN)\s*\(\s*(\w+)\s*\)(?:\s+AS\s+(\w+))?/gi
        };
        
        Object.entries(patterns).forEach(([funcName, pattern]) => {
            let match;
            while ((match = pattern.exec(query)) !== null) {
                aggregations.push({
                    function: funcName,
                    field: match[2],
                    alias: match[3] || `${funcName.toLowerCase()}_${match[2] === '*' ? 'all' : match[2]}`,
                    isCountAll: funcName === 'COUNT' && match[2] === '*'
                });
            }
        });
        
        return aggregations;
    },
    
    /**
     * ✅ CORREGIDO: Genera shell para SELECT con soporte completo de agregaciones
     */
    generateSelectShellAdvanced(query, analysis) {
        const table = analysis.table;
        
        // Si tiene agregaciones, usar pipeline de agregación
        if (analysis.hasAggregation || analysis.hasGroupBy) {
            return this.generateAggregationPipeline(query, analysis);
        }
        
        // Si es SELECT simple
        return this.generateSimpleSelectShell(query, analysis);
    },
    
    /**
     * ✅ NUEVO: Genera pipeline de agregación para MongoDB
     */
    generateAggregationPipeline(query, analysis) {
        const table = analysis.table;
        const pipeline = [];
        
        // 1. $match para WHERE clause
        const whereConditions = this.extractWhereConditions(query);
        if (whereConditions && whereConditions !== '{}') {
            pipeline.push(`  { $match: ${whereConditions} }`);
        }
        
        // 2. $group para agregaciones
        if (analysis.hasAggregation) {
            const groupStage = this.buildGroupStage(analysis);
            pipeline.push(`  ${groupStage}`);
        }
        
        // 3. $project para limpiar _id y mostrar campos
        if (analysis.hasAggregation) {
            const projectStage = this.buildProjectStage(analysis);
            pipeline.push(`  ${projectStage}`);
        }
        
        // 4. $sort para ORDER BY
        if (analysis.hasOrderBy && analysis.orderBy) {
            const sortStage = this.buildSortStage(analysis.orderBy);
            pipeline.push(`  ${sortStage}`);
        }
        
        // 5. $limit para LIMIT
        if (analysis.hasLimit && analysis.limit) {
            pipeline.push(`  { $limit: ${analysis.limit} }`);
        }
        
        // Construir query completa
        const pipelineStr = pipeline.join(',\n');
        
        const header = `// MongoDB Shell equivalente para agregación
// SQL: ${query}
// Usando pipeline de agregación

`;
        
        return header + `db.${table}.aggregate([
${pipelineStr}
]);`;
    },
    
    /**
     * ✅ NUEVO: Construye etapa $group
     */
    buildGroupStage(analysis) {
        const groupFields = {};
        
        // Determinar _id del grupo
        if (analysis.hasGroupBy) {
            // TODO: Extraer campos GROUP BY
            groupFields._id = '"$group_field"';
        } else {
            // Sin GROUP BY, agrupar todo
            groupFields._id = 'null';
        }
        
        // Agregar funciones de agregación
        analysis.aggregations.forEach(agg => {
            if (agg.function === 'COUNT') {
                if (agg.isCountAll) {
                    groupFields[agg.alias] = '{ $sum: 1 }';
                } else {
                    groupFields[agg.alias] = `{ $sum: { $cond: [{ $ne: ["$${agg.field}", null] }, 1, 0] } }`;
                }
            } else if (agg.function === 'SUM') {
                groupFields[agg.alias] = `{ $sum: "$${agg.field}" }`;
            } else if (agg.function === 'AVG') {
                groupFields[agg.alias] = `{ $avg: "$${agg.field}" }`;
            } else if (agg.function === 'MAX') {
                groupFields[agg.alias] = `{ $max: "$${agg.field}" }`;
            } else if (agg.function === 'MIN') {
                groupFields[agg.alias] = `{ $min: "$${agg.field}" }`;
            }
        });
        
        // Convertir a string
        const fieldsStr = Object.entries(groupFields)
            .map(([key, value]) => `    ${key}: ${value}`)
            .join(',\n');
        
        return `{ $group: {
${fieldsStr}
  } }`;
    },
    
    /**
     * ✅ NUEVO: Construye etapa $project
     */
    buildProjectStage(analysis) {
        const projectFields = { _id: 0 };
        
        // Incluir campos de agregación
        analysis.aggregations.forEach(agg => {
            projectFields[agg.alias] = 1;
        });
        
        const fieldsStr = Object.entries(projectFields)
            .map(([key, value]) => `    ${key}: ${value}`)
            .join(',\n');
        
        return `{ $project: {
${fieldsStr}
  } }`;
    },
    
    /**
     * ✅ NUEVO: Construye etapa $sort
     */
    buildSortStage(orderBy) {
        if (typeof orderBy === 'string') {
            return `{ $sort: { "${orderBy}": 1 } }`;
        }
        
        if (Array.isArray(orderBy)) {
            const sortFields = orderBy.map(field => {
                if (typeof field === 'object') {
                    const direction = field.direction === 'DESC' ? -1 : 1;
                    return `"${field.field}": ${direction}`;
                }
                return `"${field}": 1`;
            }).join(', ');
            
            return `{ $sort: { ${sortFields} } }`;
        }
        
        return `{ $sort: { "${orderBy}": 1 } }`;
    },
    
    /**
     * Genera SELECT simple
     */
    generateSimpleSelectShell(query, analysis) {
        const table = analysis.table;
        const conditions = this.extractWhereConditions(query);
        const limit = analysis.limit;
        
        let shell = `db.${table}.find(`;
        
        if (conditions && conditions !== '{}') {
            shell += `${conditions}`;
        } else {
            shell += `{}`;
        }
        
        shell += ')';
        
        if (analysis.hasOrderBy && analysis.orderBy) {
            const sortObj = this.convertOrderByToSort(analysis.orderBy);
            shell += `.sort(${sortObj})`;
        }
        
        if (limit) {
            shell += `.limit(${limit})`;
        }
        
        shell += ';';
        
        return this.addComments(shell, 'SELECT', query);
    },
    
    /**
     * Convierte ORDER BY a objeto sort
     */
    convertOrderByToSort(orderBy) {
        if (typeof orderBy === 'string') {
            return `{ "${orderBy}": 1 }`;
        }
        
        if (Array.isArray(orderBy)) {
            const sortFields = orderBy.map(field => {
                if (typeof field === 'object') {
                    const direction = field.direction === 'DESC' ? -1 : 1;
                    return `"${field.field}": ${direction}`;
                }
                return `"${field}": 1`;
            }).join(', ');
            
            return `{ ${sortFields} }`;
        }
        
        return `{ "${orderBy}": 1 }`;
    },
    
    /**
     * Detecta tipo de consulta
     */
    detectQueryType(query) {
        const upperQuery = query.trim().toUpperCase();
        
        if (upperQuery.startsWith('SELECT')) return 'SELECT';
        if (upperQuery.startsWith('INSERT')) return 'INSERT';
        if (upperQuery.startsWith('UPDATE')) return 'UPDATE';
        if (upperQuery.startsWith('DELETE')) return 'DELETE';
        if (upperQuery.startsWith('CREATE')) return 'CREATE';
        if (upperQuery.startsWith('DROP')) return 'DROP';
        
        return 'UNKNOWN';
    },
    
    /**
     * Extrae nombre de tabla
     */
    extractTableName(query) {
        try {
            const fromMatch = query.match(/FROM\s+(\w+)/i);
            if (fromMatch) return fromMatch[1];
            
            const intoMatch = query.match(/INTO\s+(\w+)/i);
            if (intoMatch) return intoMatch[1];
            
            const updateMatch = query.match(/UPDATE\s+(\w+)/i);
            if (updateMatch) return updateMatch[1];
            
            const tableMatch = query.match(/TABLE\s+(\w+)/i);
            if (tableMatch) return tableMatch[1];
            
            return 'collection';
        } catch (error) {
            return 'collection';
        }
    },
    
    /**
     * Extrae ORDER BY
     */
    extractOrderBy(query) {
        try {
            const orderByMatch = query.match(/ORDER\s+BY\s+(.+?)(?:\s+LIMIT|\s*;|\s*$)/i);
            if (!orderByMatch) return null;
            
            const orderClause = orderByMatch[1].trim();
            const fields = orderClause.split(',').map(field => {
                const parts = field.trim().split(/\s+/);
                return {
                    field: parts[0],
                    direction: parts.length > 1 && parts[1].toUpperCase() === 'DESC' ? 'DESC' : 'ASC'
                };
            });
            
            return fields;
        } catch (error) {
            return null;
        }
    },
    
    /**
     * Extrae LIMIT
     */
    extractLimit(query) {
        try {
            const limitMatch = query.match(/LIMIT\s+(\d+)/i);
            return limitMatch ? parseInt(limitMatch[1]) : null;
        } catch (error) {
            return null;
        }
    },
    
    /**
     * Extrae condiciones WHERE
     */
    extractWhereConditions(query) {
        try {
            const whereMatch = query.match(/WHERE\s+(.+?)(?:\s+GROUP|\s+ORDER|\s+LIMIT|\s*;|\s*$)/i);
            if (!whereMatch) return '{}';
            
            let conditions = whereMatch[1].trim();
            
            // Conversiones básicas SQL a MongoDB
            conditions = conditions
                .replace(/=/g, ':')
                .replace(/AND/gi, ',')
                .replace(/'/g, '"');
            
            // Agregar llaves si no las tiene
            if (!conditions.startsWith('{')) {
                conditions = `{ ${conditions} }`;
            }
            
            return conditions;
        } catch (error) {
            return '{}';
        }
    },
    
    /**
     * Genera shell para INSERT
     */
    generateInsertShell(query) {
        const table = this.extractTableName(query);
        
        const shell = `db.${table}.insertOne({
  // Documento basado en: ${query}
  // Ajustar campos según estructura real
});`;
        
        return this.addComments(shell, 'INSERT', query);
    },
    
    /**
     * Genera shell para UPDATE
     */
    generateUpdateShell(query) {
        const table = this.extractTableName(query);
        const conditions = this.extractWhereConditions(query);
        
        const shell = `db.${table}.updateMany(
  ${conditions},
  {
    $set: {
      // Campos a actualizar según SET clause
    }
  }
);`;
        
        return this.addComments(shell, 'UPDATE', query);
    },
    
    /**
     * Genera shell para DELETE
     */
    generateDeleteShell(query) {
        const table = this.extractTableName(query);
        const conditions = this.extractWhereConditions(query);
        
        let shell = `db.${table}.deleteMany(${conditions});`;
        
        if (conditions === '{}') {
            shell = `// ⚠️ PELIGRO: Elimina TODOS los documentos\n${shell}`;
        }
        
        return this.addComments(shell, 'DELETE', query);
    },
    
    /**
     * Genera shell para CREATE
     */
    generateCreateShell(query) {
        const table = this.extractTableName(query);
        
        const shell = `// En MongoDB, las colecciones se crean automáticamente
db.${table}.insertOne({
  // Primer documento de ejemplo
});`;
        
        return this.addComments(shell, 'CREATE', query);
    },
    
    /**
     * Genera shell para DROP
     */
    generateDropShell(query) {
        const table = this.extractTableName(query);
        
        const shell = `// ⚠️ PELIGRO: Elimina toda la colección
db.${table}.drop();`;
        
        return this.addComments(shell, 'DROP', query);
    },
    
    /**
     * Añade comentarios a shell query
     */
    addComments(shell, type, originalQuery) {
        const header = `// MongoDB Shell equivalente para ${type}
// SQL: ${originalQuery}
// Generado automáticamente

`;
        return header + shell;
    },
    
    /**
     * Formatea shell query del backend
     */
    formatShellQuery(shellQuery) {
        try {
            // Si no tiene comentarios, añadir formato básico
            if (!shellQuery.includes('//') && !shellQuery.includes('/*')) {
                return `// MongoDB Shell Query
// Generado por el backend

${shellQuery}`;
            }
            
            return shellQuery;
        } catch (error) {
            return shellQuery;
        }
    },
    
    /**
     * Copia shell query al portapapeles
     */
    async copyToClipboard(shellQuery) {
        try {
            await navigator.clipboard.writeText(shellQuery);
            return true;
        } catch (error) {
            console.error('Error copiando shell query:', error);
            return false;
        }
    }
};
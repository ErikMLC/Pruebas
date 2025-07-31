// src/translatorJS/api.js - Endpoints específicos del traductor (< 70 líneas)
// Maneja comunicación con backend para traducción SQL

export const translatorAPI = {
    baseURL: 'http://localhost:5000',
    
    /**
     * Realiza una petición HTTP genérica para el traductor
     * @param {string} endpoint - Endpoint de la API
     * @param {Object} options - Opciones de fetch
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Respuesta de la API
     */
    async makeRequest(endpoint, options = {}, token) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
                ...options.headers
            },
            ...options
        };
        
        const response = await fetch(`${this.baseURL}${endpoint}`, config);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}: ${data.message || 'Error del servidor'}`);
        }
        
        return data;
    },
    
    /**
     * Obtiene las bases de datos disponibles
     * @param {string} token - Token de autenticación
     * @returns {Promise<Array>} - Lista de bases de datos
     */
    async getDatabases(token) {
        console.log('🔍 [API] Obteniendo bases de datos...');
        const response = await this.makeRequest('/databases', { method: 'GET' }, token);
        return response.databases || [];
    },
    
   // ✅ REEMPLAZAR el método connectDatabase() en translatorJS/api.js

    /**
     * Conecta a una base de datos específica
     * @param {string} databaseName - Nombre de la base de datos
     * @param {string} token - Token de autenticación
     * @returns {Promise<Array>} - Lista de colecciones
     */
    async connectDatabase(databaseName, token) {
        try {
            console.log(`🔌 [API] Conectando a: ${databaseName}`);
            
            // ✅ DEBUG: Mostrar detalles de la petición
            const requestBody = { database: databaseName };
            console.log('📤 [API] Request body:', requestBody);
            console.log('📤 [API] Token (primeros 20 chars):', token ? token.substring(0, 20) + '...' : 'NO TOKEN');
            
            const response = await this.makeRequest('/connect', {
                method: 'POST',
                body: JSON.stringify(requestBody)
            }, token);
            
            // ✅ DEBUG: Mostrar respuesta completa
            console.log('📥 [API] Response completa:', response);
            console.log('📥 [API] Tipo de response:', typeof response);
            console.log('📥 [API] Keys de response:', Object.keys(response || {}));
            
            // ✅ DEBUG: Extraer colecciones con logging
            let collections = [];
            
            if (response && response.collections) {
                collections = response.collections;
                console.log('✅ [API] Colecciones en response.collections:', collections);
            } else if (response && response.data && response.data.collections) {
                collections = response.data.collections;
                console.log('✅ [API] Colecciones en response.data.collections:', collections);
            } else if (Array.isArray(response)) {
                collections = response;
                console.log('✅ [API] Response es array directo:', collections);
            } else if (response && response.result && Array.isArray(response.result)) {
                collections = response.result;
                console.log('✅ [API] Colecciones en response.result:', collections);
            } else {
                console.warn('⚠️ [API] Estructura de response no reconocida');
                console.log('📋 [API] Response completa para análisis:', JSON.stringify(response, null, 2));
                
                // Buscar arrays en cualquier parte de la respuesta
                const searchForArrays = (obj, path = '') => {
                    if (Array.isArray(obj)) {
                        console.log(`🔍 [API] Array encontrado en ${path}:`, obj);
                        return obj;
                    }
                    if (typeof obj === 'object' && obj !== null) {
                        for (const [key, value] of Object.entries(obj)) {
                            if (Array.isArray(value)) {
                                console.log(`🔍 [API] Array en ${path}.${key}:`, value);
                                return value;
                            }
                            if (typeof value === 'object') {
                                const found = searchForArrays(value, `${path}.${key}`);
                                if (found) return found;
                            }
                        }
                    }
                    return null;
                };
                
                const foundArray = searchForArrays(response);
                if (foundArray) {
                    collections = foundArray;
                    console.log('✅ [API] Array encontrado por búsqueda profunda:', collections);
                }
            }
            
            // ✅ Validar que collections sea un array
            if (!Array.isArray(collections)) {
                console.warn('⚠️ [API] collections no es un array, convirtiendo:', typeof collections, collections);
                collections = [];
            }
            
            // ✅ Filtrar elementos válidos
            const originalLength = collections.length;
            collections = collections.filter(item => 
                typeof item === 'string' && item.trim() !== ''
            );
            
            if (collections.length !== originalLength) {
                console.log(`🧹 [API] Filtradas ${originalLength - collections.length} colecciones inválidas`);
            }
            
            console.log(`✅ [API] Resultado final: ${collections.length} colecciones válidas:`, collections);
            
            return { collections: collections };
            
        } catch (error) {
            console.error('❌ [API] Error en connectDatabase:', error);
            console.error('❌ [API] Error details:', {
                message: error.message,
                stack: error.stack,
                response: error.response
            });
            throw error;
        }
    },
    
    /**
     * Ejecuta una consulta SELECT
     * @param {string} sqlQuery - Consulta SQL SELECT
     * @param {string} database - Base de datos
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Resultados de la consulta
     */
    async executeSelect(sqlQuery, database, token) {
        console.log(`📊 [API] Ejecutando SELECT: ${sqlQuery}`);
        return await this.translateAndExecute(sqlQuery, database, token);
    },
    
    /**
     * Ejecuta una consulta INSERT/CREATE
     * @param {string} sqlQuery - Consulta SQL INSERT
     * @param {string} database - Base de datos
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Resultado de la inserción
     */
    async executeInsert(sqlQuery, database, token) {
        console.log(`➕ [API] Ejecutando INSERT: ${sqlQuery}`);
        return await this.translateAndExecute(sqlQuery, database, token);
    },
    
    /**
     * Ejecuta una consulta UPDATE
     * @param {string} sqlQuery - Consulta SQL UPDATE
     * @param {string} database - Base de datos
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Resultado de la actualización
     */
    async executeUpdate(sqlQuery, database, token) {
        console.log(`✏️ [API] Ejecutando UPDATE: ${sqlQuery}`);
        return await this.translateAndExecute(sqlQuery, database, token);
    },
    
    /**
     * Ejecuta una consulta DELETE
     * @param {string} sqlQuery - Consulta SQL DELETE
     * @param {string} database - Base de datos
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Resultado de la eliminación
     */
    async executeDelete(sqlQuery, database, token) {
        console.log(`🗑️ [API] Ejecutando DELETE: ${sqlQuery}`);
        return await this.translateAndExecute(sqlQuery, database, token);
    },
    
    /**
     * Traduce y ejecuta cualquier consulta SQL
     * @param {string} sqlQuery - Consulta SQL
     * @param {string} database - Base de datos
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Resultados de la consulta
     */
    async translateAndExecute(sqlQuery, database, token) {
        const body = { query: sqlQuery };
        if (database) body.database = database;
        
        return await this.makeRequest('/translate', {
            method: 'POST',
            body: JSON.stringify(body)
        }, token);
    },
    
    /**
     * Genera la consulta MongoDB shell equivalente
     * @param {string} sqlQuery - Consulta SQL
     * @param {string} database - Base de datos
     * @param {string} token - Token de autenticación
     * @returns {Promise<string>} - Consulta MongoDB shell
     */
    async generateShellQuery(sqlQuery, database, token) {
        console.log(`🐚 [API] Generando shell: ${sqlQuery}`);
        const body = { query: sqlQuery };
        if (database) body.database = database;
        
        try {
            const response = await this.makeRequest('/generate-shell-query', {
                method: 'POST',
                body: JSON.stringify(body)
            }, token);
            return response.shell_query || response.query || 'Shell query no disponible';
        } catch (error) {
            console.warn('⚠️ [API] Error generando shell query:', error.message);
            return `// Error generando shell query: ${error.message}`;
        }
    },
    
    /**
     * Valida la sintaxis de una consulta SQL
     * @param {string} sqlQuery - Consulta SQL
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Resultado de la validación
     */
    async validateQuery(sqlQuery, token) {
        console.log(`✅ [API] Validando query: ${sqlQuery}`);
        try {
            const response = await this.makeRequest('/validate-query', {
                method: 'POST',
                body: JSON.stringify({ query: sqlQuery })
            }, token);
            return { valid: true, ...response };
        } catch (error) {
            return { valid: false, error: error.message };
        }
    },
    
    /**
     * Verifica el estado de la conexión MongoDB
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Estado de la conexión
     */
    async testConnection(token) {
        console.log('🔗 [API] Verificando conexión...');
        return await this.makeRequest('/test-connection', { method: 'GET' }, token);
    }
};
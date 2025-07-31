// api.js - Endpoints específicos del dashboard (< 70 líneas)
// Compatible con tu backend Flask

export const dashboardAPI = {
    baseURL: 'http://localhost:5000',
    
    /**
     * Realiza una petición HTTP genérica
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
            throw new Error(data.error || `HTTP ${response.status}`);
        }
        
        return data;
    },
    
    /**
     * Obtiene las bases de datos disponibles
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Lista de bases de datos
     */
    async getDatabases(token) {
        console.log('🔍 Obteniendo bases de datos...');
        return await this.makeRequest('/databases', { method: 'GET' }, token);
    },
    
    /**
     * Conecta a una base de datos específica
     * @param {string} databaseName - Nombre de la base de datos
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Respuesta con colecciones
     */
    async connectDatabase(databaseName, token) {
        console.log(`🔌 Conectando a: ${databaseName}`);
        return await this.makeRequest('/connect', {
            method: 'POST',
            body: JSON.stringify({ database: databaseName })
        }, token);
    },
    
    /**
     * Obtiene las colecciones de una base de datos
     * @param {string} databaseName - Nombre de la base de datos
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Lista de colecciones
     */
    async getCollections(databaseName, token) {
        console.log(`📂 Obteniendo colecciones de: ${databaseName}`);
        return await this.makeRequest(`/database/${databaseName}/collections`, { method: 'GET' }, token);
    },
    
    /**
     * Traduce y ejecuta una consulta SQL
     * @param {string} sqlQuery - Consulta SQL
     * @param {string} database - Base de datos (opcional)
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Resultados de la consulta
     */
    async translateAndExecute(sqlQuery, database, token) {
        console.log(`🔄 Ejecutando: ${sqlQuery}`);
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
     * @param {string} database - Base de datos (opcional)
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Consulta MongoDB shell
     */
    async generateShellQuery(sqlQuery, database, token) {
        console.log(`🐚 Generando query shell: ${sqlQuery}`);
        const body = { query: sqlQuery };
        if (database) body.database = database;
        
        return await this.makeRequest('/generate-shell-query', {
            method: 'POST',
            body: JSON.stringify(body)
        }, token);
    },
    
    /**
     * Obtiene el perfil del usuario actual
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Datos del perfil
     */
    async getUserProfile(token) {
        console.log('👤 Obteniendo perfil...');
        return await this.makeRequest('/api/auth/profile', { method: 'GET' }, token);
    },
    
    /**
     * Verifica el estado de la conexión MongoDB
     * @param {string} token - Token de autenticación
     * @returns {Promise<Object>} - Estado de la conexión
     */
    async testConnection(token) {
        console.log('🔗 Verificando conexión...');
        return await this.makeRequest('/test-connection', { method: 'GET' }, token);
    }
};
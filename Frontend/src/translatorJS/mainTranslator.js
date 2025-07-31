import { createParser } from './create.js';
import { deleteParser } from './delete.js';
import { readParser } from './read.js';
import { updateParser } from './update.js';
import { selectParser } from './select.js';
import { mongoShell } from './mongoshell.js';
import { translatorAPI } from './api.js';

export const mainTranslator = {
    // Módulos del traductor completos
    parsers: {
        create: createParser,
        delete: deleteParser,
        read: readParser,
        update: updateParser,
        select: selectParser,
        shell: mongoShell,
        api: translatorAPI
    },
    
    // Referencias externas del dashboard
    ui: null,
    storage: null,
    
    // Estado actual del traductor
    state: {
        currentDatabase: null,
        userPermissions: {},
        queryHistory: [],
        lastResults: null,
        isConnected: false,
        availableDatabases: [],
        currentCollections: []
    },
    
    
    /**
     * ✅ ACTUALIZADO: Método init con detector ORDER BY
     */
    async init(ui, storage) {
        try {
            console.log('🔄 Inicializando traductor modular...');
            
            this.ui = ui;
            this.storage = storage;
            
            // 1. Cargar permisos del usuario
            this.loadUserPermissions();
            
            // 2. Inicializar parsers
            this.initializeParsers();
            
            // 3. Cargar bases de datos disponibles
            await this.loadDatabases();
            
            // 4. Cargar historial de consultas
            this.loadQueryHistory();
            
            // 5. Configurar eventos de la interfaz
            this.bindEvents();
            
            // 6. ✅ NUEVO: Configurar detector ORDER BY
            this.setupOrderByDetector();
            
            // 7. Hacer el traductor globalmente accesible
            window.mainTranslator = this;
            
            // 8. Inicializar UI del traductor
            this.initializeUI();
            
            console.log('✅ Traductor modular inicializado correctamente');
            
        } catch (error) {
            console.error('❌ Error inicializando traductor:', error);
            this.ui?.showToast('Error inicializando traductor: ' + error.message, 'error');
            throw error;
        }
    },


    
    /**
     * Carga permisos del usuario desde storage
     */
    loadUserPermissions() {
        try {
            const userData = this.storage?.getUserData();
            let permissions = {};
            
            if (userData && userData.permissions) {
                permissions = userData.permissions;
            } else {
                // Intentar desde localStorage/sessionStorage como fallback
                const storedData = localStorage.getItem('user_data') || sessionStorage.getItem('user_data');
                if (storedData) {
                    const parsed = JSON.parse(storedData);
                    permissions = parsed.permissions || {};
                }
            }
            
            // Permisos por defecto si no se encuentran
            this.state.userPermissions = {
                select: true,
                insert: false,
                update: false,
                delete: false,
                create_table: false,
                drop_table: false,
                ...permissions
            };
            
            console.log('👮 Permisos de usuario cargados:', this.state.userPermissions);
            
        } catch (error) {
            console.error('❌ Error cargando permisos:', error);
            this.state.userPermissions = { select: true };
        }
    },
    
    /**
     * Inicializa todos los parsers del traductor
     */
    initializeParsers() {
        Object.entries(this.parsers).forEach(([name, parser]) => {
            if (parser.init && typeof parser.init === 'function') {
                parser.init(this);
                console.log(`✅ Parser ${name} inicializado`);
            }
        });
    },
    
    /**
     * Carga las bases de datos disponibles desde el backend
     */
    async loadDatabases() {
        try {
            const token = this.storage?.getToken();
            if (!token) {
                throw new Error('No hay token de autenticación');
            }
            
            console.log('🔍 Cargando bases de datos...');
            const databases = await this.parsers.api.getDatabases(token);
            this.state.availableDatabases = databases;
            this.updateDatabaseSelect(databases);
            
        } catch (error) {
            console.error('❌ Error cargando bases de datos:', error);
            this.ui?.showToast('Error cargando bases de datos: ' + error.message, 'error');
        }
    },
    
    /**
     * Actualiza el selector de bases de datos en la interfaz
     * @param {Array} databases - Lista de bases de datos
     */
    updateDatabaseSelect(databases) {
        const select = document.getElementById('database-select');
        if (!select) return;
        
        // Limpiar opciones existentes excepto la primera
        select.innerHTML = '<option value="">-- Seleccionar --</option>';
        
        // Agregar bases de datos
        databases.forEach(db => {
            const option = document.createElement('option');
            option.value = db;
            option.textContent = db;
            select.appendChild(option);
        });
        
        console.log(`📋 ${databases.length} bases de datos cargadas en selector`);
    },
    
    /**
     * Configura todos los eventos de la interfaz del traductor
     */
    bindEvents() {
        // Selector de base de datos
        const dbSelect = document.getElementById('database-select');
        dbSelect?.addEventListener('change', (e) => {
            const connectBtn = document.getElementById('connect-btn');
            if (connectBtn) {
                connectBtn.disabled = !e.target.value;
            }
        });
        
        // Botón conectar a base de datos
        const connectBtn = document.getElementById('connect-btn');
        connectBtn?.addEventListener('click', () => {
            this.connectToDatabase();
        });
        
        // Editor SQL - actualizar botón traducir
        const sqlEditor = document.getElementById('sql-editor');
        sqlEditor?.addEventListener('input', () => {
            this.updateTranslateButton();
        });
        
        // Botón traducir y ejecutar
        const translateBtn = document.getElementById('translate-btn');
        translateBtn?.addEventListener('click', () => {
            this.executeQuery();
        });
        
        // Botones de utilidad
        const clearBtn = document.getElementById('clear-btn');
        clearBtn?.addEventListener('click', () => {
            this.clearEditor();
        });
        
        const exampleBtn = document.getElementById('example-btn');
        exampleBtn?.addEventListener('click', () => {
            this.insertExample();
        });
        
        // Pestañas de resultados
        const resultTabs = document.querySelectorAll('.result-tab-btn');
        resultTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchResultTab(e.target.dataset.resultTab);
            });
        });
        
        // Botones de exportación
        const exportJsonBtn = document.getElementById('export-json-btn');
        exportJsonBtn?.addEventListener('click', () => {
            this.exportResults('json');
        });
        
        const exportCsvBtn = document.getElementById('export-csv-btn');
        exportCsvBtn?.addEventListener('click', () => {
            this.exportResults('csv');
        });
        
        // Botón copiar MongoDB shell
        const copyMongoBtn = document.getElementById('copy-mongodb-btn');
        copyMongoBtn?.addEventListener('click', () => {
            this.copyMongoQuery();
        });
        
        console.log('📡 Eventos de interfaz configurados');
    },
    
    /**
     * Inicializa la interfaz del traductor
     */
    initializeUI() {
        // Actualizar estado inicial de botones
        this.updateTranslateButton();
        
        // Mostrar permisos del usuario
        this.displayUserPermissions();
        
        // Configurar estado inicial de la interfaz
        this.switchResultTab('json');
    },
    
    /**
     * Muestra los permisos del usuario en la interfaz (opcional)
     */
    displayUserPermissions() {
        // Aquí podrías mostrar indicadores visuales de los permisos
        // Por ejemplo, deshabilitar botones según permisos
        const permissions = this.state.userPermissions;
        
        // Solo mostrar ejemplos según permisos disponibles
        console.log('🔐 Permisos disponibles para ejemplos:', permissions);
    },
    
    /**
     * Conecta a la base de datos seleccionada
     */
    async connectToDatabase() {
        try {
            const selectedDB = document.getElementById('database-select')?.value;
            if (!selectedDB) {
                this.ui?.showToast('Selecciona una base de datos', 'warning');
                return;
            }
            
            console.log(`🔌 Conectando a base de datos: ${selectedDB}`);
            const token = this.storage?.getToken();
            
            // Mostrar loading
            this.showLoading(true);
            
            // Ejecutar conexión
            const response = await this.parsers.api.connectDatabase(selectedDB, token);
            const collections = response.collections || [];
            
            // Actualizar estado
            this.state.currentDatabase = selectedDB;
            this.state.isConnected = true;
            this.state.currentCollections = collections;
            
            // Actualizar interfaz
            this.updateCollectionsList(collections);
            this.updateTranslateButton();
            
            this.ui?.showToast(`✅ Conectado a ${selectedDB}`, 'success');
            
        } catch (error) {
            console.error('❌ Error conectando a base de datos:', error);
            this.ui?.showToast('Error conectando: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    },
    
    /**
     * Actualiza la lista de colecciones en la interfaz
     * @param {Array} collections - Lista de colecciones
     */
    updateCollectionsList(collections) {
        const list = document.getElementById('collections-list');
        if (!list) return;
        
        if (!collections || collections.length === 0) {
            list.innerHTML = '<li class="no-collections">No hay colecciones</li>';
            return;
        }
        
        list.innerHTML = '';
        collections.forEach(collection => {
            const li = document.createElement('li');
            li.className = 'collection-item';
            li.innerHTML = `<i class="fas fa-table"></i> ${collection}`;
            li.style.cursor = 'pointer';
            li.title = `Click para insertar "${collection}" en el editor`;
            
            // Event listener para insertar nombre en editor
            li.addEventListener('click', () => {
                this.insertCollectionName(collection);
            });
            
            list.appendChild(li);
        });
        
        console.log(`📁 ${collections.length} colecciones cargadas`);
    },
    
    /**
     * Ejecuta la consulta SQL ingresada por el usuario
     */
    async executeQuery() {
        try {
            const query = document.getElementById('sql-editor')?.value?.trim();
            if (!query) {
                this.ui?.showToast('Escribe una consulta SQL', 'warning');
                return;
            }
            
            if (!this.state.isConnected) {
                this.ui?.showToast('Conecta a una base de datos primero', 'warning');
                return;
            }
            
            console.log('🚀 Ejecutando consulta:', query);
            
            // Mostrar loading
            this.showLoading(true);
            
            // 1. Detectar tipo de consulta
            const queryType = this.detectQueryType(query);
            const parser = this.parsers[queryType];
            
            if (!parser) {
                throw new Error(`Tipo de consulta no soportado: ${queryType}`);
            }
            
            // 2. Validar permisos
            parser.validatePermissions(this.state.userPermissions, query);
            
            // 3. Ejecutar consulta
            const token = this.storage?.getToken();
            const result = await parser.execute(query, this.state.currentDatabase, token);
            
            // 4. Generar MongoDB shell query
            const shellQuery = await this.parsers.shell.generate(query, this.state.currentDatabase, token);
            
            // 5. Mostrar resultados
            this.displayResults(result);
            this.displayMongoShell(shellQuery);
            
            // 6. Agregar al historial
            this.addToHistory(query, result);
            
            // 7. Mostrar mensaje de éxito
            this.ui?.showToast('✅ Consulta ejecutada exitosamente', 'success');
            
        } catch (error) {
            console.error('❌ Error ejecutando consulta:', error);
            this.ui?.showToast(error.message, 'error');
            this.displayError(error.message);
        } finally {
            this.showLoading(false);
        }
    },
    
    /**
     * ✅ CORREGIDO: Detecta el tipo de consulta SQL con funciones agregadas
     * @param {string} query - Consulta SQL
     * @returns {string} - Tipo de parser a usar
     */
    detectQueryType(query) {
        const upperQuery = query.trim().toUpperCase();
        
        if (upperQuery.startsWith('SELECT')) {
            // ✅ CORREGIDO: Verificar si es SELECT simple o avanzado
            const hasAdvancedFeatures = 
                upperQuery.includes('JOIN') || 
                upperQuery.includes('GROUP BY') || 
                upperQuery.includes('HAVING') || 
                upperQuery.includes('UNION') ||
                upperQuery.includes('ORDER BY') ||
                upperQuery.includes('DISTINCT') ||
                // ✅ CRÍTICO: Detectar funciones de agregación
                /\b(COUNT|SUM|AVG|MAX|MIN|GROUP_CONCAT)\s*\(/i.test(upperQuery);
            
            if (hasAdvancedFeatures) {
                console.log('🔍 SELECT avanzado detectado (incluye funciones agregadas, ORDER BY, etc.)');
                return 'select'; // SELECT avanzado
            }
            
            console.log('📊 SELECT simple detectado');
            return 'read'; // SELECT simple
        }
        
        if (upperQuery.startsWith('INSERT') || upperQuery.startsWith('CREATE')) {
            return 'create';
        }
        if (upperQuery.startsWith('UPDATE')) {
            return 'update';
        }
        if (upperQuery.startsWith('DELETE') || upperQuery.startsWith('DROP')) {
            return 'delete';
        }
        
        // Por defecto, usar read
        console.log('📊 Tipo no detectado, usando READ por defecto');
        return 'read';
    },

    /**
     * ✅ NUEVO: Analiza consultas SELECT para determinar complejidad
     */
    analyzeSelectQuery(query) {
        const upperQuery = query.toUpperCase();
        
        // ✅ CRÍTICO: Detectar funciones de agregación específicamente
        const hasAggregation = this.detectAggregationFunctions(query);
        
        // Detectar otras características avanzadas
        const features = {
            hasAggregation: hasAggregation,
            hasGroupBy: upperQuery.includes('GROUP BY'),
            hasHaving: upperQuery.includes('HAVING'),
            hasJoin: upperQuery.includes('JOIN'),
            hasUnion: upperQuery.includes('UNION'),
            hasDistinct: upperQuery.includes('SELECT DISTINCT'),
            hasSubquery: /\(\s*SELECT\s+/i.test(query),
            hasWindow: upperQuery.includes('OVER ('),
            hasOrderBy: upperQuery.includes('ORDER BY'),
            hasComplexWhere: this.hasComplexWhereClause(query)
        };
        
        // ✅ CRITERIO DE DECISIÓN: Usar parser avanzado si tiene cualquier característica compleja
        const shouldUseAdvanced = Object.values(features).some(feature => feature === true);
        
        console.log('🔍 Características detectadas:', features);
        console.log(`📊 Decisión: ${shouldUseAdvanced ? 'SELECT avanzado' : 'READ simple'}`);
        
        return {
            shouldUseAdvanced: shouldUseAdvanced,
            features: features,
            complexity: this.calculateQueryComplexity(features)
        };
    },


    /**
     * ✅ NUEVO: Detecta funciones de agregación con alta precisión
     */
    detectAggregationFunctions(query) {
        const aggregationPatterns = [
            /\bCOUNT\s*\(\s*\*\s*\)/i,           // COUNT(*)
            /\bCOUNT\s*\(\s*\w+\s*\)/i,         // COUNT(campo)
            /\bCOUNT\s*\(\s*DISTINCT\s+\w+\s*\)/i, // COUNT(DISTINCT campo)
            /\bSUM\s*\(\s*\w+\s*\)/i,           // SUM(campo)
            /\bAVG\s*\(\s*\w+\s*\)/i,           // AVG(campo)
            /\bMAX\s*\(\s*\w+\s*\)/i,           // MAX(campo)
            /\bMIN\s*\(\s*\w+\s*\)/i,           // MIN(campo)
            /\bGROUP_CONCAT\s*\(/i              // GROUP_CONCAT
        ];
        
        const hasAggregation = aggregationPatterns.some(pattern => pattern.test(query));
        
        if (hasAggregation) {
            console.log('🔢 Funciones de agregación detectadas en la consulta');
            // Mostrar qué funciones específicas se detectaron
            aggregationPatterns.forEach((pattern, index) => {
                if (pattern.test(query)) {
                    const functionNames = ['COUNT(*)', 'COUNT(field)', 'COUNT(DISTINCT)', 'SUM', 'AVG', 'MAX', 'MIN', 'GROUP_CONCAT'];
                    console.log(`✅ Detectado: ${functionNames[index]}`);
                }
            });
        }
        
        return hasAggregation;
    },


    /**
     * ✅ NUEVO: Detecta cláusulas WHERE complejas
     */
    hasComplexWhereClause(query) {
        const whereMatch = query.match(/WHERE\s+(.+?)(?:\s+GROUP|\s+ORDER|\s+LIMIT|\s*;|\s*$)/i);
        if (!whereMatch) return false;
        
        const whereClause = whereMatch[1];
        
        const complexityIndicators = [
            /\bIN\s*\(/i,           // IN clause
            /\bBETWEEN\b/i,         // BETWEEN
            /\bLIKE\b/i,            // LIKE
            /\bIS\s+NULL\b/i,       // IS NULL
            /\bIS\s+NOT\s+NULL\b/i, // IS NOT NULL
            /\bEXISTS\b/i,          // EXISTS
            /\(\s*SELECT\s+/i       // Subqueries en WHERE
        ];
        
        return complexityIndicators.some(pattern => pattern.test(whereClause));
    },

    /**
     * ✅ NUEVO: Calcula nivel de complejidad de la consulta
     */
    calculateQueryComplexity(features) {
        let score = 0;
        
        if (features.hasAggregation) score += 2;
        if (features.hasGroupBy) score += 2;
        if (features.hasJoin) score += 3;
        if (features.hasSubquery) score += 3;
        if (features.hasHaving) score += 2;
        if (features.hasUnion) score += 3;
        if (features.hasWindow) score += 4;
        if (features.hasDistinct) score += 1;
        if (features.hasOrderBy) score += 1;
        if (features.hasComplexWhere) score += 1;
        
        if (score === 0) return 'simple';
        if (score <= 3) return 'moderate';
        if (score <= 6) return 'complex';
        return 'very_complex';
    },
    

    /**
     * ✅ NUEVO: Extrae datos del resultado manejando diferentes formatos
     */
    extractResultData(result) {
        // Manejar diferentes estructuras de respuesta
        if (result.data) return result.data;
        if (result.results) return result.results;
        if (result.aggregationResults) return result.aggregationResults;
        if (result.result) {
            if (result.result.data) return result.result.data;
            if (result.result.results) return result.result.results;
            return result.result;
        }
        
        return result;
    },

    /**
     * ✅ NUEVO: Genera texto del contador con información específica
     */
    generateResultCountText(result, data, count) {
        let countText = `${count} resultado${count !== 1 ? 's' : ''}`;
        
        // ✅ Información específica para agregaciones
        if (result.type === 'SELECT_AGGREGATION') {
            countText = '🔢 Resultado de agregación';
            
            if (result.analysis && result.analysis.aggregations) {
                const functions = result.analysis.aggregations.map(a => a.function).join(', ');
                countText += ` (${functions})`;
            }
        }
        
        // Información de ORDER BY
        if (result.metadata && result.metadata.hasOrderBy && result.metadata.orderByFields) {
            const orderInfo = result.metadata.orderByFields
                .map(o => `${o.field} ${o.direction}`)
                .join(', ');
            countText += ` - ordenado por: ${orderInfo}`;
        }
        
        // Información de agrupación
        if (result.metadata && result.metadata.hasGroupBy) {
            countText += ' - datos agrupados';
        }
        
        return countText;
    },

    /**
     * Muestra/oculta el overlay de loading
     * @param {boolean} show - True para mostrar loading
     */
    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.toggle('hidden', !show);
        }
    },
    

    /**
     * ✅ ACTUALIZADO: Muestra los resultados con información de ORDER BY
     * @param {Object} result - Resultado de la consulta
     */
    displayResults(result) {
        const container = document.getElementById('results-container');
        const countElement = document.querySelector('.result-count');
        const exportButtons = document.querySelectorAll('.btn-export');
        
        if (!container) return;
        
        // Limpiar resultados anteriores
        container.innerHTML = '';
        
        try {
            // Extraer datos del resultado
            let data = result.data || result.result || result;
            if (result.results) data = result.results;
            
            const count = Array.isArray(data) ? data.length : (data ? 1 : 0);
            
            // ✅ ACTUALIZADO: Contador con información de ORDER BY
            let countText = `${count} resultado${count !== 1 ? 's' : ''}`;
            
            if (result.metadata && result.metadata.hasOrderBy && result.metadata.orderByFields) {
                const orderInfo = result.metadata.orderByFields
                    .map(o => `${o.field} ${o.direction}`)
                    .join(', ');
                countText += ` (ordenado por: ${orderInfo})`;

                if (result.type === 'CREATE_TABLE') {
                    countText = '🏗️ Tabla creada exitosamente';
                    
                    if (result.schema_info && result.schema_info.total_columns) {
                        countText += ` (${result.schema_info.total_columns} columnas)`;
                    }
                    
                    if (result.has_validator) {
                        countText += ' - con validación de esquema';
                    }
                }

            }
            
            if (countElement) {
                countElement.textContent = countText;
            }
            
            // Habilitar botones de exportación
            exportButtons.forEach(btn => btn.disabled = count === 0);
            
            if (count === 0) {
                container.innerHTML = `
                    <div class="no-results">
                        <i class="fas fa-search"></i>
                        <p>No se encontraron resultados</p>
                    </div>
                `;
                return;
            }
            
            // ✅ NUEVO: Mostrar información de ordenamiento si existe
            if (result.metadata && result.metadata.hasOrderBy) {
                const orderInfo = document.createElement('div');
                orderInfo.className = 'order-info';
                orderInfo.innerHTML = `
                    <i class="fas fa-sort"></i>
                    <span>Resultados ordenados por: ${result.metadata.orderByFields.map(o => `${o.field} ${o.direction}`).join(', ')}</span>
                `;
                container.appendChild(orderInfo);

                if (result.type === 'CREATE_TABLE' && result.schema_info) {
                    const schemaInfo = document.createElement('div');
                    schemaInfo.className = 'schema-info';
                    schemaInfo.innerHTML = `
                        <i class="fas fa-table"></i>
                        <span>Esquema: ${result.schema_info.total_columns} columnas, ${result.indexes_created?.length || 0} índices</span>
                        ${result.has_validator ? '<span class="validator-badge">✓ Con validación</span>' : ''}
                    `;
                    container.appendChild(schemaInfo);
                }

            }
            
            // Mostrar resultados en tabla
            this.renderResultsTable(data);
            
            // Guardar resultados para exportación
            this.state.lastResults = data;
            
        } catch (error) {
            console.error('❌ Error mostrando resultados:', error);
            this.displayError('Error mostrando resultados: ' + error.message);
        }
    },
    

    /**
     * Renderiza los resultados en formato de tabla
     * @param {Array|Object} data - Datos a mostrar
     */
    renderResultsTable(data) {
        const container = document.getElementById('results-container');
        
        if (!Array.isArray(data)) {
            data = [data];
        }
        
        if (data.length === 0) return;
        
        // Obtener todas las claves de los objetos
        const allKeys = new Set();
        data.forEach(item => {
            if (typeof item === 'object' && item !== null) {
                Object.keys(item).forEach(key => allKeys.add(key));
            }
        });
        
        const keys = Array.from(allKeys);
        
        // Crear tabla
        const table = document.createElement('table');
        table.className = 'results-table';
        
        // Crear encabezado
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        keys.forEach(key => {
            const th = document.createElement('th');
            th.textContent = key;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Crear cuerpo
        const tbody = document.createElement('tbody');
        data.forEach(item => {
            const row = document.createElement('tr');
            keys.forEach(key => {
                const td = document.createElement('td');
                const value = item[key];
                
                if (value === null || value === undefined) {
                    td.textContent = 'null';
                    td.className = 'null-value';
                } else if (typeof value === 'object') {
                    td.textContent = JSON.stringify(value);
                    td.className = 'object-value';
                } else {
                    td.textContent = String(value);
                }
                
                row.appendChild(td);
            });
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        
        container.appendChild(table);
    },
    
    /**
     * Muestra la consulta MongoDB shell
     * @param {string} shellQuery - Consulta MongoDB shell
     */
    displayMongoShell(shellQuery) {
        const mongoQueryElement = document.getElementById('mongodb-query');
        if (mongoQueryElement) {
            mongoQueryElement.textContent = shellQuery;
        }
    },
    
    /**
     * Muestra un error en la interfaz
     * @param {string} error - Mensaje de error
     */
    displayError(error) {
        const container = document.getElementById('results-container');
        if (container) {
            container.innerHTML = `
                <div class="error-results">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error: ${error}</p>
                </div>
            `;
        }
        
        // Limpiar MongoDB shell
        this.displayMongoShell('// Error en la consulta');
    },
    
    /**
     * Cambia entre pestañas de resultados
     * @param {string} tabId - ID de la pestaña ('json' o 'mongodb')
     */
    switchResultTab(tabId) {
        // Remover clases activas
        document.querySelectorAll('.result-tab-btn').forEach(btn => 
            btn.classList.remove('active')
        );
        document.querySelectorAll('.result-content').forEach(content => 
            content.classList.remove('active')
        );
        
        // Activar pestaña seleccionada
        const activeButton = document.querySelector(`[data-result-tab="${tabId}"]`);
        const activeContent = document.getElementById(`${tabId}-results`);
        
        if (activeButton && activeContent) {
            activeButton.classList.add('active');
            activeContent.classList.add('active');
        }
    },
    
    /**
     * Exporta los resultados en el formato especificado
     * @param {string} format - Formato de exportación ('json' o 'csv')
     */
    exportResults(format) {
        if (!this.state.lastResults) {
            this.ui?.showToast('No hay resultados para exportar', 'warning');
            return;
        }
        
        try {
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[:.]/g, '-');
            const filename = `resultados_${timestamp}`;
            
            if (format === 'json') {
                this.downloadJSON(this.state.lastResults, `${filename}.json`);
            } else if (format === 'csv') {
                this.downloadCSV(this.state.lastResults, `${filename}.csv`);
            }
            
            this.ui?.showToast(`✅ Resultados exportados en ${format.toUpperCase()}`, 'success');
            
        } catch (error) {
            console.error('❌ Error exportando:', error);
            this.ui?.showToast('Error exportando resultados', 'error');
        }
    },
    
    /**
     * Copia la consulta MongoDB al portapapeles
     */
    async copyMongoQuery() {
        const mongoQuery = document.getElementById('mongodb-query')?.textContent;
        if (!mongoQuery) {
            this.ui?.showToast('No hay consulta MongoDB para copiar', 'warning');
            return;
        }
        
        try {
            await navigator.clipboard.writeText(mongoQuery);
            this.ui?.showToast('✅ Consulta MongoDB copiada al portapapeles', 'success');
        } catch (error) {
            console.error('❌ Error copiando:', error);
            this.ui?.showToast('Error copiando consulta', 'error');
        }
    },
    
    /**
     * Descarga datos como JSON
     * @param {Object} data - Datos a descargar
     * @param {string} filename - Nombre del archivo
     */
    downloadJSON(data, filename) {
        const jsonString = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        this.downloadBlob(blob, filename);
    },
    
    /**
     * Descarga datos como CSV
     * @param {Array} data - Datos a descargar
     * @param {string} filename - Nombre del archivo
     */
    downloadCSV(data, filename) {
        if (!Array.isArray(data)) data = [data];
        if (data.length === 0) return;
        
        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(h => `"${row[h] || ''}"`).join(','))
        ].join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        this.downloadBlob(blob, filename);
    },
    
    /**
     * Descarga un blob como archivo
     * @param {Blob} blob - Blob a descargar
     * @param {string} filename - Nombre del archivo
     */
    downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    },
    

    /**
     * ✅ ACTUALIZADO: Agrega consulta al historial con detección ORDER BY
     * @param {string} query - Consulta SQL
     * @param {Object} result - Resultado de la consulta
     */
    addToHistory(query, result) {
        try {
            const hasOrderBy = /\bORDER\s+BY\b/i.test(query);
            
            const historyItem = {
                id: Date.now(),
                query: query,
                database: this.state.currentDatabase,
                timestamp: new Date().toISOString(),
                success: !result.error,
                type: this.detectQueryType(query),
                hasOrderBy: hasOrderBy,          // ✅ NUEVO
                features: {                      // ✅ NUEVO
                    orderBy: hasOrderBy,
                    distinct: /\bSELECT\s+DISTINCT\b/i.test(query),
                    groupBy: /\bGROUP\s+BY\b/i.test(query),
                    having: /\bHAVING\b/i.test(query),
                    join: /\bJOIN\b/i.test(query)
                }
            };
            
            this.state.queryHistory.unshift(historyItem);
            
            // Limitar historial a 50 elementos
            if (this.state.queryHistory.length > 50) {
                this.state.queryHistory = this.state.queryHistory.slice(0, 50);
            }
            
            // Guardar en localStorage
            localStorage.setItem('queryHistory', JSON.stringify(this.state.queryHistory));
            
            // Actualizar UI del historial
            this.updateHistoryUI();
            
        } catch (error) {
            console.error('❌ Error guardando historial:', error);
        }
    },
    

    /**
     * Carga el historial de consultas
     */
    loadQueryHistory() {
        try {
            const stored = localStorage.getItem('queryHistory');
            if (stored) {
                this.state.queryHistory = JSON.parse(stored);
                this.updateHistoryUI();
            }
        } catch (error) {
            console.error('❌ Error cargando historial:', error);
            this.state.queryHistory = [];
        }
    },
    

    /**
     * ✅ ACTUALIZADO: Actualiza UI del historial con indicadores ORDER BY
     */
    updateHistoryUI() {
        const historyList = document.getElementById('query-history');
        if (!historyList) return;

        if (this.state.queryHistory.length === 0) {
            historyList.innerHTML = '<li class="no-history">Sin consultas recientes</li>';
            return;
        }

        historyList.innerHTML = '';

        // Mostrar últimas 10 consultas
        this.state.queryHistory.slice(0, 10).forEach(item => {
            const li = document.createElement('li');
            li.className = 'history-item';
            
            // ✅ NUEVO: Agregar clase especial para ORDER BY
            if (item.hasOrderBy) {
                li.classList.add('has-order-by');
            }
            
            // ✅ NUEVO: Crear badges para características
            let badges = '';
            if (item.features) {
                if (item.features.orderBy) badges += '<span class="feature-badge order-by">📊</span>';
                if (item.features.distinct) badges += '<span class="feature-badge distinct">🔍</span>';
                if (item.features.groupBy) badges += '<span class="feature-badge group">📊</span>';
                if (item.features.join) badges += '<span class="feature-badge join">🔗</span>';
            }
            
            li.innerHTML = `
                <div class="history-query" title="${item.query}">
                    <i class="fas fa-${this.getQueryIcon(item.type)}"></i>
                    ${item.query.length > 30 ? item.query.substring(0, 30) + '...' : item.query}
                    ${badges}
                </div>
                <div class="history-time">${new Date(item.timestamp).toLocaleTimeString()}</div>
            `;

            li.style.cursor = 'pointer';
            li.addEventListener('click', () => {
                this.loadHistoryQuery(item.query);
            });

            historyList.appendChild(li);
        });
    },

    
    /**
     * Obtiene el icono para un tipo de consulta
     * @param {string} type - Tipo de consulta
     * @returns {string} - Clase del icono
     */
    getQueryIcon(type) {
        const icons = {
            'read': 'search',
            'select': 'table',
            'create': 'plus',
            'update': 'edit',
            'delete': 'trash'
        };
        return icons[type] || 'code';
    },
    
    /**
     * Carga una consulta del historial en el editor
     * @param {string} query - Consulta a cargar
     */
    loadHistoryQuery(query) {
        const editor = document.getElementById('sql-editor');
        if (editor) {
            editor.value = query;
            this.updateTranslateButton();
            this.ui?.showToast('Consulta cargada del historial', 'success');
        }
    },
    

    /**
     * ✅ ACTUALIZADO: Funciones auxiliares de interfaz con detección ORDER BY
     */
    updateTranslateButton() {
        const btn = document.getElementById('translate-btn');
        const sqlEditor = document.getElementById('sql-editor');
        if (!btn || !sqlEditor) return;
        
        const hasQuery = sqlEditor.value?.trim().length > 0;
        const query = sqlEditor.value?.trim() || '';
        
        btn.disabled = !hasQuery || !this.state.isConnected;
        
        // ✅ NUEVO: Detectar ORDER BY y actualizar botón dinámicamente
        if (hasQuery && this.state.isConnected) {
            const hasOrderBy = /\bORDER\s+BY\b/i.test(query);
            
            let buttonText = '<i class="fas fa-play"></i> ';
            
            if (hasOrderBy) {
                buttonText += 'Traducir ORDER BY';
                btn.classList.add('has-order-by');
            } else {
                buttonText += 'Traducir y Ejecutar';
                btn.classList.remove('has-order-by');
            }
            
            btn.innerHTML = buttonText;
        } else {
            btn.innerHTML = '<i class="fas fa-play"></i> Traducir y Ejecutar';
            btn.classList.remove('has-order-by');
        }
    },

    
    clearEditor() {
        const editor = document.getElementById('sql-editor');
        if (editor) {
            editor.value = '';
            this.updateTranslateButton();
            this.ui?.showToast('Editor limpiado', 'success');
        }
    },
    
    insertExample() {
        const examples = this.getExampleQueries();
        if (examples.length === 0) {
            this.ui?.showToast('No hay ejemplos disponibles para tus permisos', 'info');
            return;
        }
        
        const randomExample = examples[Math.floor(Math.random() * examples.length)];
        const editor = document.getElementById('sql-editor');
        if (editor) {
            editor.value = randomExample;
            this.updateTranslateButton();
            this.ui?.showToast('Ejemplo insertado', 'success');
        }
    },
    
    getExampleQueries() {
        const examples = [];
        
        // Obtener ejemplos de todos los parsers disponibles
        Object.entries(this.parsers).forEach(([name, parser]) => {
            if (parser.getExamples && typeof parser.getExamples === 'function') {
                try {
                    const currentTable = this.state.currentCollections[0] || 'projects';
                    const parserExamples = parser.getExamples(this.state.userPermissions, currentTable);
                    examples.push(...parserExamples);
                } catch (error) {
                    console.warn(`⚠️ Error obteniendo ejemplos de ${name}:`, error);
                }
            }
        });
        
        return examples;
    },


    /**
     * ✅ NUEVO: Configura detector de ORDER BY en tiempo real
     */
    setupOrderByDetector() {
        const sqlEditor = document.getElementById('sql-editor');
        if (!sqlEditor) return;

        // Crear indicador ORDER BY
        const indicator = document.createElement('div');
        indicator.className = 'order-by-indicator';
        indicator.innerHTML = '<i class="fas fa-sort"></i> ORDER BY';
        
        // Envolver editor si no está envuelto
        if (!sqlEditor.parentElement.classList.contains('sql-editor-wrapper')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'sql-editor-wrapper';
            sqlEditor.parentElement.insertBefore(wrapper, sqlEditor);
            wrapper.appendChild(sqlEditor);
            wrapper.appendChild(indicator);
        }

        // Detector en tiempo real
        sqlEditor.addEventListener('input', (e) => {
            this.detectOrderByFeatures(e.target.value, indicator);
        });
    },


    /**
     * ✅ NUEVO: Detecta características ORDER BY en tiempo real
     * @param {string} query - Consulta SQL actual
     * @param {HTMLElement} indicator - Elemento indicador
     */
    detectOrderByFeatures(query, indicator) {
        const upperQuery = query.toUpperCase();
        const features = {
            hasOrderBy: /\bORDER\s+BY\b/.test(upperQuery),
            hasMultipleFields: false,
            hasDesc: /\bDESC\b/.test(upperQuery),
            hasAsc: /\bASC\b/.test(upperQuery),
            hasAggregate: /\b(COUNT|SUM|AVG|MAX|MIN)\s*\(/i.test(upperQuery), // ✅ NUEVO
            fields: []
        };

        // Extraer campos ORDER BY
        if (features.hasOrderBy) {
            const orderByMatch = query.match(/ORDER\s+BY\s+(.+?)(?:\s+LIMIT|\s*;|\s*$)/i);
            if (orderByMatch) {
                const orderClause = orderByMatch[1].trim();
                features.fields = orderClause.split(',').map(f => f.trim());
                features.hasMultipleFields = features.fields.length > 1;
            }
        }

        // Actualizar indicador
        if (features.hasOrderBy || features.hasAggregate) {  // ✅ CORREGIDO
            indicator.classList.add('active');
            
            let tooltipText = '';
            if (features.hasAggregate) tooltipText += 'Función agregada detectada. ';
            if (features.hasOrderBy) tooltipText += `ORDER BY detectado: ${features.fields.length} campo(s)`;
            if (features.hasDesc) tooltipText += ' (DESC)';
            if (features.hasAsc) tooltipText += ' (ASC)';
            
            indicator.title = tooltipText;
            
            // Animar editor
            const sqlEditor = document.getElementById('sql-editor');
            sqlEditor.classList.add('order-by-detected');
            setTimeout(() => sqlEditor.classList.remove('order-by-detected'), 2000);
            
        } else {
            indicator.classList.remove('active');
        }

        // Actualizar botón traducir con información específica
        this.updateTranslateButtonWithFeatures(features);
    },


    /**
     * ✅ NUEVO: Actualiza botón traducir con información de características
     * @param {Object} features - Características detectadas
     */
    updateTranslateButtonWithFeatures(features) {
        const btn = document.getElementById('translate-btn');
        if (!btn) return;

        const hasQuery = document.getElementById('sql-editor')?.value?.trim().length > 0;
        btn.disabled = !hasQuery || !this.state.isConnected;

        // Actualizar texto del botón según características
        if (hasQuery && this.state.isConnected) {
            let buttonText = '<i class="fas fa-play"></i> ';
            
            if (features.hasOrderBy) {
                buttonText += 'Traducir ORDER BY';
                btn.classList.add('has-order-by');
            } else {
                buttonText += 'Traducir y Ejecutar';
                btn.classList.remove('has-order-by');
            }
            
            btn.innerHTML = buttonText;
        }
    },


    /**
     * ✅ NUEVO: Obtiene ejemplos específicos con ORDER BY
     * @returns {Array} - Ejemplos organizados por tipo
     */
    getExampleQueries() {
        const examples = [];
        const currentTable = this.state.currentCollections[0] || 'projects';
        
        // ✅ NUEVO: Ejemplos específicos para ORDER BY
        if (this.state.userPermissions.select) {
            // Ejemplos básicos
            examples.push(
                `SELECT * FROM ${currentTable} LIMIT 5;`,
                `SELECT * FROM ${currentTable} WHERE status = 'In Progress';`
            );
            
            // ✅ EJEMPLOS ORDER BY
            examples.push(
                `SELECT * FROM ${currentTable} ORDER BY name ASC LIMIT 10;`,
                `SELECT * FROM ${currentTable} ORDER BY created_date DESC;`,
                `SELECT name, status FROM ${currentTable} ORDER BY status, name;`,
                `SELECT * FROM ${currentTable} WHERE status = 'Active' ORDER BY priority DESC;`
            );
            
            // Ejemplos con agregaciones y ORDER BY
            examples.push(
                `SELECT status, COUNT(*) as total FROM ${currentTable} GROUP BY status ORDER BY total DESC;`,
                `SELECT cuisine_type, AVG(rating) FROM restaurants GROUP BY cuisine_type ORDER BY AVG(rating) DESC;`
            );
        }
        
        // Obtener ejemplos de todos los parsers disponibles
        Object.entries(this.parsers).forEach(([name, parser]) => {
            if (parser.getExamples && typeof parser.getExamples === 'function') {
                try {
                    const parserExamples = parser.getExamples(this.state.userPermissions, currentTable);
                    examples.push(...parserExamples);
                } catch (error) {
                    console.warn(`⚠️ Error obteniendo ejemplos de ${name}:`, error);
                }
            }
        });
        
        // Remover duplicados y filtrar vacíos
        return [...new Set(examples)].filter(example => example && example.trim() !== '');
    },

    
    insertCollectionName(name) {
        const editor = document.getElementById('sql-editor');
        if (!editor) return;
        
        const start = editor.selectionStart;
        const end = editor.selectionEnd;
        const text = editor.value;
        
        editor.value = text.substring(0, start) + name + text.substring(end);
        editor.focus();
        editor.setSelectionRange(start + name.length, start + name.length);
        this.updateTranslateButton();
        
        this.ui?.showToast(`Tabla "${name}" insertada`, 'success');
    }
};
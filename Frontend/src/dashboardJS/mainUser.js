// mainUser.js - Coordinador principal del dashboard (< 100 líneas)
// Orquesta la inicialización y comunicación entre todos los módulos

export const mainUserCoordinator = {
    // Referencias a módulos
    modules: {
        auth: null,
        ui: null,
        storage: null,
        authCheck: null,
        headerManager: null,
        tabsManager: null,
        translatorModule: null,
        profileModule: null
    },
    
    // Estado del dashboard
    state: {
        isInitialized: false,
        currentUser: null,
        activeModules: []
    },
    
    /**
     * Inicializa todo el dashboard de forma coordinada
     * @param {Object} dependencies - Módulos externos (auth, ui, storage)
     */
    async init(dependencies) {
        try {
            console.log('🚀 Iniciando coordinador principal del dashboard...');
            
            // 1. Guardar dependencias externas
            this.setDependencies(dependencies);
            
            // 2. Verificar autenticación PRIMERO
            const isAuthenticated = await this.verifyAuthentication();
            if (!isAuthenticated) {
                this.redirectToLogin();
                return false;
            }
            
            // 3. Cargar información del usuario
            await this.loadUserInfo();
            
            // 4. Inicializar módulos del dashboard
            await this.initializeDashboardModules();
            
            // 5. Configurar eventos globales
            this.setupGlobalEvents();
            
            this.state.isInitialized = true;
            console.log('✅ Dashboard inicializado correctamente');
            
            return true;
            
        } catch (error) {
            console.error('❌ Error crítico inicializando dashboard:', error);
            this.handleInitializationError(error);
            return false;
        }
    },
    
    /**
     * Establece las dependencias de módulos externos
     * @param {Object} deps - Dependencias {auth, ui, storage, authCheck, etc.}
     */
    setDependencies(deps) {
        Object.assign(this.modules, deps);
        console.log('📦 Dependencias establecidas:', Object.keys(deps));
    },
    
    /**
     * Verifica la autenticación del usuario
     * @returns {Promise<boolean>} - True si está autenticado
     */
    async verifyAuthentication() {
        console.log('🔐 Verificando autenticación...');
        
        if (!this.modules.authCheck || !this.modules.auth || !this.modules.storage) {
            console.error('❌ Módulos de autenticación no disponibles');
            return false;
        }
        
        return await this.modules.authCheck.verify(this.modules.auth, this.modules.storage);
    },
    
    /**
     * Carga la información del usuario actual
     */
    async loadUserInfo() {
        try {
            console.log('👤 Cargando información del usuario...');
            
            // Obtener usuario del token o storage
            this.state.currentUser = this.modules.authCheck.getUserFromToken(this.modules.storage);
            
            if (!this.state.currentUser) {
                throw new Error('No se pudo obtener información del usuario');
            }
            
            console.log('✅ Usuario cargado:', this.state.currentUser.username);
            
        } catch (error) {
            console.error('❌ Error cargando usuario:', error);
            throw error;
        }
    },
    
    /**
     * Inicializa todos los módulos del dashboard
     */
    async initializeDashboardModules() {
        console.log('🔧 Inicializando módulos del dashboard...');
        
        try {
            // Header y navegación
            if (this.modules.headerManager) {
                this.modules.headerManager.init(this.modules.ui, this.modules.storage, this.modules.auth);
                this.registerModule('header');
            }
            
            // Sistema de pestañas
            if (this.modules.tabsManager) {
                this.modules.tabsManager.init();
                this.registerModule('tabs');
            }
            
            // Módulo traductor
            if (this.modules.translatorModule) {
                this.modules.translatorModule.init(this.modules.ui);
                this.registerModule('translator');
            }
            
            // Módulo perfil
            if (this.modules.profileModule) {
                this.modules.profileModule.init(this.modules.storage, this.modules.ui);
                this.registerModule('profile');
            }
            
            console.log('✅ Módulos inicializados:', this.state.activeModules);
            
        } catch (error) {
            console.error('❌ Error inicializando módulos:', error);
            throw error;
        }
    },
    
    /**
     * Registra un módulo como activo
     * @param {string} moduleName - Nombre del módulo
     */
    registerModule(moduleName) {
        if (!this.state.activeModules.includes(moduleName)) {
            this.state.activeModules.push(moduleName);
        }
    },
    
    /**
     * Configura eventos globales del dashboard
     */
    setupGlobalEvents() {
        // Evento de cambio de pestaña
        document.addEventListener('tabChanged', (e) => {
            this.handleTabChange(e.detail);
        });
        
        // Evento de error global
        window.addEventListener('error', (e) => {
            this.handleGlobalError(e);
        });
        
        // Evento antes de cerrar ventana
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
        
        console.log('📡 Eventos globales configurados');
    },
    
    /**
     * Maneja cambios de pestaña
     * @param {Object} detail - Detalles del cambio de pestaña
     */
    handleTabChange(detail) {
        console.log(`🗂️ Cambio de pestaña: ${detail.previousTab} → ${detail.tabId}`);
        
        // Notificar módulos específicos si es necesario
        if (detail.tabId === 'profile' && this.modules.profileModule) {
            this.modules.profileModule.refresh?.();
        }
    },
    
    /**
     * Maneja errores globales
     * @param {Error} error - Error capturado
     */
    handleGlobalError(error) {
        console.error('❌ Error global capturado:', error);
        
        if (this.modules.ui?.showToast) {
            this.modules.ui.showToast('Ha ocurrido un error inesperado', 'error');
        }
    },
    
    /**
     * Maneja errores de inicialización
     * @param {Error} error - Error de inicialización
     */
    handleInitializationError(error) {
        if (this.modules.ui?.showToast) {
            this.modules.ui.showToast('Error iniciando dashboard', 'error');
        }
        
        // Redirigir al login después de un delay
        setTimeout(() => {
            this.redirectToLogin();
        }, 3000);
    },
    
    /**
     * Redirige al login
     */
    redirectToLogin() {
        console.log('🔄 Redirigiendo al login...');
        window.location.href = 'index.html';
    },
    
    /**
     * Limpia recursos antes de cerrar
     */
    cleanup() {
        console.log('🧹 Limpiando recursos del dashboard...');
        
        // Limpiar timers o listeners específicos si es necesario
        this.state.activeModules.forEach(moduleName => {
            const module = this.modules[`${moduleName}Manager`] || this.modules[`${moduleName}Module`];
            if (module?.cleanup) {
                module.cleanup();
            }
        });
    },
    
    /**
     * Obtiene el estado actual del dashboard
     * @returns {Object} - Estado actual
     */
    getState() {
        return { ...this.state };
    },
    
    /**
     * Obtiene información del usuario actual
     * @returns {Object|null} - Datos del usuario
     */
    getCurrentUser() {
        return this.state.currentUser;
    }
};
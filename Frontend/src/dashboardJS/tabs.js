// src/dashboardJS/tabs.js - Sistema de pestañas INTELIGENTE
// Compatible con dashboard.html y admin-dashboard.html

export const tabsManager = {
    currentTab: null,
    availableTabs: [],
    
    /**
     * Inicializa el sistema de pestañas
     */
    init() {
        console.log('🗂️ Inicializando pestañas...');
        
        // ✅ CORREGIDO: Detectar pestañas disponibles dinámicamente
        this.detectAvailableTabs();
        
        this.bindEvents();
        
        // ✅ CORREGIDO: Mostrar primera pestaña disponible
        if (this.availableTabs.length > 0) {
            this.showTab(this.availableTabs[0]);
        }
        
        console.log('✅ Pestañas inicializadas');
    },
    
    /**
     * ✅ NUEVO: Detecta qué pestañas están disponibles en la página actual
     */
    detectAvailableTabs() {
        const tabButtons = document.querySelectorAll('.tab-btn[data-tab]');
        this.availableTabs = [];
        
        tabButtons.forEach(button => {
            const tabId = button.getAttribute('data-tab');
            const tabContent = document.getElementById(`${tabId}-tab`);
            
            if (tabContent) {
                this.availableTabs.push(tabId);
            }
        });
        
        console.log('📋 Pestañas disponibles:', this.availableTabs);
    },
    
    /**
     * Vincula eventos de las pestañas
     */
    bindEvents() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const tabId = e.currentTarget.getAttribute('data-tab');
                this.showTab(tabId);
            });
        });
    },
    
    /**
     * Muestra una pestaña específica
     * @param {string} tabId - ID de la pestaña
     */
    showTab(tabId) {
        console.log(`🗂️ Cambiando a: ${tabId}`);
        
        // ✅ CORREGIDO: Verificar que la pestaña existe antes de cambiar
        if (!this.availableTabs.includes(tabId)) {
            console.warn(`⚠️ Pestaña '${tabId}' no disponible. Pestañas válidas:`, this.availableTabs);
            return false;
        }
        
        // Remover clases activas
        document.querySelectorAll('.tab-btn').forEach(btn => 
            btn.classList.remove('active')
        );
        document.querySelectorAll('.tab-content').forEach(content => 
            content.classList.remove('active')
        );
        
        // Activar pestaña y contenido
        const activeButton = document.querySelector(`[data-tab="${tabId}"]`);
        const activeContent = document.getElementById(`${tabId}-tab`);
        
        if (activeButton && activeContent) {
            activeButton.classList.add('active');
            activeContent.classList.add('active');
            
            // Actualizar estado y disparar evento
            const previousTab = this.currentTab;
            this.currentTab = tabId;
            
            this.dispatchTabChangeEvent(tabId, previousTab);
            
            console.log(`✅ Pestaña '${tabId}' activada`);
            return true;
        } else {
            console.error(`❌ Elementos de pestaña '${tabId}' no encontrados`);
            return false;
        }
    },
    
    /**
     * Dispara evento personalizado de cambio de pestaña
     * @param {string} tabId - Pestaña actual
     * @param {string} previousTab - Pestaña anterior
     */
    dispatchTabChangeEvent(tabId, previousTab) {
        const event = new CustomEvent('tabChanged', {
            detail: { tabId, previousTab, availableTabs: this.availableTabs }
        });
        document.dispatchEvent(event);
    },
    
    /**
     * Obtiene la pestaña actualmente activa
     * @returns {string} - ID de la pestaña activa
     */
    getCurrentTab() {
        return this.currentTab;
    },
    
    /**
     * Verifica si una pestaña está activa
     * @param {string} tabId - ID de la pestaña
     * @returns {boolean} - True si está activa
     */
    isTabActive(tabId) {
        return this.currentTab === tabId;
    },
    
    /**
     * ✅ NUEVO: Obtiene lista de pestañas disponibles
     * @returns {Array} - Array de IDs de pestañas disponibles
     */
    getAvailableTabs() {
        return [...this.availableTabs];
    },
    
    /**
     * ✅ NUEVO: Verifica si una pestaña específica existe
     * @param {string} tabId - ID de la pestaña
     * @returns {boolean} - True si existe
     */
    tabExists(tabId) {
        return this.availableTabs.includes(tabId);
    },
    
    /**
     * ✅ NUEVO: Cambia a pestaña con fallback
     * @param {string} preferredTab - Pestaña preferida
     * @param {string} fallbackTab - Pestaña fallback
     */
    showTabWithFallback(preferredTab, fallbackTab = null) {
        if (this.tabExists(preferredTab)) {
            return this.showTab(preferredTab);
        } else if (fallbackTab && this.tabExists(fallbackTab)) {
            console.log(`⚠️ Pestaña '${preferredTab}' no existe, usando fallback '${fallbackTab}'`);
            return this.showTab(fallbackTab);
        } else if (this.availableTabs.length > 0) {
            console.log(`⚠️ Usando primera pestaña disponible: '${this.availableTabs[0]}'`);
            return this.showTab(this.availableTabs[0]);
        } else {
            console.error('❌ No hay pestañas disponibles');
            return false;
        }
    }
};
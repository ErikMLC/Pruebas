// tabs.js - Sistema de pestañas del dashboard (< 60 líneas)
// Maneja navegación entre Traductor SQL y Perfil

export const tabsManager = {
    currentTab: 'translator',
    
    /**
     * Inicializa el sistema de pestañas
     */
    init() {
        console.log('🗂️ Inicializando pestañas...');
        
        this.bindEvents();
        this.showTab('translator'); // Pestaña por defecto
        
        console.log('✅ Pestañas inicializadas');
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
     * @param {string} tabId - ID de la pestaña ('translator' o 'profile')
     */
    showTab(tabId) {
        console.log(`🗂️ Cambiando a: ${tabId}`);
        
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
        } else {
            console.error(`❌ Pestaña no encontrada: ${tabId}`);
        }
    },
    
    /**
     * Dispara evento personalizado de cambio de pestaña
     * @param {string} tabId - Pestaña actual
     * @param {string} previousTab - Pestaña anterior
     */
    dispatchTabChangeEvent(tabId, previousTab) {
        const event = new CustomEvent('tabChanged', {
            detail: { tabId, previousTab }
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
    }
};
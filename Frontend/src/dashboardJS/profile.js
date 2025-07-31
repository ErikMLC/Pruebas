// profile.js - Módulo perfil de usuario (< 80 líneas)
// Maneja la pestaña de perfil del dashboard

import { dashboardAPI } from './api.js';

export const profileModule = {
    storage: null,
    ui: null,
    userData: null,
    
    /**
     * Inicializa el módulo de perfil
     * @param {Object} storage - Tu módulo storage.js
     * @param {Object} ui - Tu módulo ui.js
     */
    init(storage, ui) {
        console.log('👤 Inicializando módulo perfil...');
        
        this.storage = storage;
        this.ui = ui;
        
        this.loadUserData();
        this.bindEvents();
        
        console.log('✅ Módulo perfil inicializado');
    },
    
    /**
     * Carga los datos del usuario en la interfaz
     */
    async loadUserData() {
        try {
            // Obtener datos del storage o del backend
            this.userData = this.storage.getUserData();
            
            if (!this.userData) {
                // Si no hay datos en storage, obtenerlos del backend
                const token = this.storage.getToken();
                const response = await dashboardAPI.getUserProfile(token);
                this.userData = response.user;
            }
            
            this.displayUserInfo();
            this.displayPermissions();
            this.displayStats();
            
        } catch (error) {
            console.error('❌ Error cargando perfil:', error);
            this.ui.showToast('Error cargando perfil de usuario', 'error');
        }
    },
    
    /**
     * Muestra la información del usuario
     */
    displayUserInfo() {
        if (!this.userData) return;
        
        document.getElementById('profile-username').textContent = this.userData.username || 'N/A';
        document.getElementById('profile-email').textContent = this.userData.email || 'N/A';
        
        const roleElement = document.getElementById('profile-role');
        roleElement.textContent = this.userData.role || 'user';
        roleElement.className = `role-badge ${this.userData.role}`;
        
        const createdDate = this.userData.created_at ? 
            new Date(this.userData.created_at).toLocaleDateString('es-ES') : 'N/A';
        document.getElementById('profile-created').textContent = createdDate;
    },
    
    /**
     * Muestra los permisos del usuario
     */
    displayPermissions() {
        const permissions = this.userData?.permissions || {};
        
        // Lista de permisos a mostrar
        const permissionIds = ['select', 'insert', 'update', 'delete', 'create_table', 'drop_table'];
        
        permissionIds.forEach(permission => {
            const element = document.getElementById(`perm-${permission}`);
            if (element) {
                const hasPermission = permissions[permission] === true;
                element.textContent = hasPermission ? '✅' : '❌';
                element.className = `permission-status ${hasPermission ? 'granted' : 'denied'}`;
            }
        });
    },
    
    /**
     * Muestra las estadísticas del usuario
     */
    displayStats() {
        // Estadísticas básicas desde localStorage o datos por defecto
        const stats = this.getStoredStats();
        
        document.getElementById('queries-count').textContent = stats.queriesCount;
        document.getElementById('databases-used').textContent = stats.databasesUsed;
        document.getElementById('last-login').textContent = stats.lastLogin;
        document.getElementById('session-time').textContent = stats.sessionTime;
    },
    
    /**
     * Obtiene estadísticas almacenadas
     * @returns {Object} - Estadísticas del usuario
     */
    getStoredStats() {
        try {
            const queryHistory = JSON.parse(localStorage.getItem('queryHistory') || '[]');
            const uniqueDatabases = [...new Set(queryHistory.map(q => q.database).filter(Boolean))];
            
            return {
                queriesCount: queryHistory.length,
                databasesUsed: uniqueDatabases.length,
                lastLogin: this.formatLastLogin(),
                sessionTime: this.calculateSessionTime()
            };
        } catch (error) {
            return { queriesCount: 0, databasesUsed: 0, lastLogin: '--', sessionTime: '00:00' };
        }
    },
    
    /**
     * Formatea la última fecha de login
     * @returns {string} - Fecha formateada
     */
    formatLastLogin() {
        try {
            const lastLogin = localStorage.getItem('lastLoginTime');
            if (lastLogin) {
                return new Date(lastLogin).toLocaleDateString('es-ES');
            }
            return 'Hoy';
        } catch (error) {
            return '--';
        }
    },
    
    /**
     * Calcula el tiempo de sesión actual
     * @returns {string} - Tiempo en formato HH:MM
     */
    calculateSessionTime() {
        try {
            const loginTime = localStorage.getItem('lastLoginTime');
            if (loginTime) {
                const sessionMinutes = Math.floor((Date.now() - new Date(loginTime)) / (1000 * 60));
                const hours = Math.floor(sessionMinutes / 60);
                const minutes = sessionMinutes % 60;
                return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
            }
            return '00:00';
        } catch (error) {
            return '00:00';
        }
    },
    
    /**
     * Vincula eventos del módulo
     */
    bindEvents() {
        // Evento para refrescar perfil cuando se cambia a esta pestaña
        document.addEventListener('tabChanged', (e) => {
            if (e.detail.tabId === 'profile') {
                this.refresh();
            }
        });
    },
    
    /**
     * Refresca los datos del perfil
     */
    refresh() {
        console.log('🔄 Refrescando perfil...');
        this.displayStats(); // Recargar estadísticas dinámicas
    }
};
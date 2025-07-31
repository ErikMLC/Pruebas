// header.js - Gestión del header y logout del dashboard (< 80 líneas)
// Compatible con tus módulos auth.js, ui.js, storage.js

export const headerManager = {
    ui: null,
    storage: null,
    auth: null,
    
    /**
     * Inicializa el header del dashboard
     * @param {Object} ui - Tu módulo ui.js
     * @param {Object} storage - Tu módulo storage.js  
     * @param {Object} auth - Tu módulo auth.js
     */
    init(ui, storage, auth) {
        console.log('🎯 Inicializando header...');
        
        this.ui = ui;
        this.storage = storage;
        this.auth = auth;
        
        this.loadUserInfo();
        this.bindEvents();
        
        console.log('✅ Header inicializado');
    },
    
    /**
     * Carga la información del usuario en el header
     */
    loadUserInfo() {
        try {
            // Obtener datos del usuario (compatible con tu storage)
            const userData = this.storage.getUserData();
            const username = userData?.username || this.getUserFromToken()?.username || 'Usuario';
            
            this.updateUsername(username);
            console.log('✅ Usuario cargado:', username);
            
        } catch (error) {
            console.error('❌ Error cargando usuario:', error);
            this.updateUsername('Usuario');
        }
    },
    
    /**
     * Vincula eventos del header
     */
    bindEvents() {
        const logoutBtn = document.getElementById('logout-btn');
        const usernameEl = document.getElementById('username');
        
        // Evento logout
        logoutBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleLogout();
        });
        
        // Tooltip en hover del username
        usernameEl?.addEventListener('mouseenter', () => {
            const userData = this.storage.getUserData();
            const role = userData?.role || 'user';
            this.ui.showToast(`Rol: ${role}`, 'info', 2000);
        });
    },
    
    /**
     * Actualiza el nombre de usuario en el header
     * @param {string} username - Nombre del usuario
     */
    updateUsername(username) {
        const usernameEl = document.getElementById('username');
        if (usernameEl) {
            usernameEl.textContent = username;
            usernameEl.title = `Sesión activa: ${username}`;
        }
    },
    
    /**
     * Maneja el proceso de logout
     */
    async handleLogout() {
        try {
            console.log('🚪 Iniciando logout...');
            
            // Confirmar logout
            if (!confirm('¿Estás seguro de que quieres cerrar tu sesión?')) {
                return;
            }
            
            // Mostrar loading en botón
            this.setLogoutLoading(true);
            
            // Usar tu método de logout existente
            await this.auth.logout(this.storage.getToken());
            
            console.log('✅ Logout completado');
            
        } catch (error) {
            console.error('❌ Error en logout:', error);
            this.ui.showToast('Error cerrando sesión', 'error');
            
            // Logout forzado usando tu método
            this.auth.forceLogout();
        } finally {
            this.setLogoutLoading(false);
        }
    },
    
    /**
     * Obtiene usuario del token JWT
     * @returns {Object|null} - Datos del usuario
     */
    getUserFromToken() {
        try {
            const token = this.storage.getToken();
            if (!token) return null;
            
            const payload = JSON.parse(atob(token.split('.')[1]));
            return {
                username: payload.username,
                email: payload.email,
                role: payload.role
            };
        } catch (error) {
            return null;
        }
    },
    
    /**
     * Controla el estado de loading del botón logout
     * @param {boolean} show - True para mostrar loading
     */
    setLogoutLoading(show) {
        const logoutBtn = document.getElementById('logout-btn');
        if (!logoutBtn) return;
        
        const icon = logoutBtn.querySelector('i');
        
        logoutBtn.disabled = show;
        
        if (show) {
            icon.className = 'fas fa-spinner fa-spin';
        } else {
            icon.className = 'fas fa-sign-out-alt';
        }
    }
};
// src/adminJS/adminMain.js - Coordinador principal del panel admin
// Enfocado solo en lo esencial para funcionar

export const adminMain = {
    // Referencias a módulos base
    ui: null,
    storage: null,
    auth: null,
    
    // Estado del admin
    state: {
        users: [],
        stats: {},
        isLoaded: false
    },
    
    /**
     * Inicializa el coordinador principal admin
     */
    async init(ui, storage, auth) {
        console.log('🛡️ Inicializando AdminMain...');
        
        this.ui = ui;
        this.storage = storage;
        this.auth = auth;
        
        try {
            // 1. Cargar información del admin
            this.loadAdminInfo();
            
            // 2. Configurar eventos básicos
            this.bindEvents();
            
            // 3. Cargar datos iniciales
            await this.loadInitialData();
            
            console.log('✅ AdminMain inicializado correctamente');
            
        } catch (error) {
            console.error('❌ Error inicializando AdminMain:', error);
            throw error;
        }
    },
    
    /**
     * Carga información del administrador
     */
    loadAdminInfo() {
        try {
            const userData = this.storage.getUserData();
            const adminName = userData?.username || 'Admin';
            
            // Actualizar header con nombre del admin
            const adminUsernameEl = document.getElementById('admin-username');
            if (adminUsernameEl) {
                adminUsernameEl.textContent = adminName;
            }
            
            console.log('👤 Admin cargado:', adminName);
            
        } catch (error) {
            console.error('❌ Error cargando info admin:', error);
        }
    },
    
    /**
     * Configura eventos principales
     */
    bindEvents() {
        // Botón logout admin
        const logoutBtn = document.getElementById('admin-logout-btn');
        logoutBtn?.addEventListener('click', () => this.handleLogout());
        
        // Botón refresh activity
        const refreshBtn = document.getElementById('refresh-activity');
        refreshBtn?.addEventListener('click', () => this.refreshDashboard());
        
        // Botón refresh usuarios
        const refreshUsersBtn = document.getElementById('refresh-users');
        refreshUsersBtn?.addEventListener('click', () => this.refreshUsers());
        
        console.log('📡 Eventos admin configurados');
    },
    
    /**
     * Carga datos iniciales del dashboard
     */
    async loadInitialData() {
        try {
            console.log('📊 Cargando datos iniciales...');
            
            // Cargar usuarios desde la API
            await this.loadUsers();
            
            // Calcular estadísticas
            this.calculateStats();
            
            // Actualizar dashboard
            this.updateDashboard();
            
            this.state.isLoaded = true;
            
        } catch (error) {
            console.error('❌ Error cargando datos iniciales:', error);
            this.ui.showToast('Error cargando datos del sistema', 'error');
        }
    },
    
    /**
     * Carga usuarios desde la API
     */
    async loadUsers() {
        try {
            const token = this.storage.getToken();
            const response = await fetch('http://localhost:5000/api/admin/users', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.state.users = data.users || [];
            
            console.log(`👥 ${this.state.users.length} usuarios cargados`);
            
        } catch (error) {
            console.error('❌ Error cargando usuarios:', error);
            // Usar datos mock para desarrollo
            this.state.users = this.getMockUsers();
        }
    },
    
    /**
     * Datos mock para desarrollo
     */
    getMockUsers() {
        return [
            {
                _id: '1',
                username: 'erik.chalacama',
                email: 'erikchalacama74@gmail.com',
                role: 'admin',
                is_active: true,
                permissions: {
                    select: true,
                    insert: true,
                    update: true,
                    delete: true,
                    create_table: true,
                    drop_table: true
                },
                created_at: '2025-06-09T13:28:36.021+00:00'
            },
            {
                _id: '2',
                username: 'maria.garcia',
                email: 'maria@example.com',
                role: 'user',
                is_active: true,
                permissions: {
                    select: true,
                    insert: true,
                    update: false,
                    delete: false,
                    create_table: false,
                    drop_table: false
                },
                created_at: '2025-06-08T10:15:20.000+00:00'
            },
            {
                _id: '3',
                username: 'juan.perez',
                email: 'juan@example.com',
                role: 'viewer',
                is_active: false,
                permissions: {
                    select: true,
                    insert: false,
                    update: false,
                    delete: false,
                    create_table: false,
                    drop_table: false
                },
                created_at: '2025-06-07T08:30:45.000+00:00'
            }
        ];
    },
    
    /**
     * Calcula estadísticas del sistema
     */
    calculateStats() {
        const users = this.state.users;
        
        this.state.stats = {
            totalUsers: users.length,
            activeUsers: users.filter(u => u.is_active).length,
            adminUsers: users.filter(u => u.role === 'admin').length,
            permissions: {
                select: users.filter(u => u.permissions?.select).length,
                insert: users.filter(u => u.permissions?.insert).length,
                update: users.filter(u => u.permissions?.update).length,
                delete: users.filter(u => u.permissions?.delete).length,
                create_table: users.filter(u => u.permissions?.create_table).length,
                drop_table: users.filter(u => u.permissions?.drop_table).length
            }
        };
        
        console.log('📊 Estadísticas calculadas:', this.state.stats);
    },
    

    /**
     * ✅ CORREGIR: Actualiza el dashboard con las estadísticas
     */
    updateDashboard() {
        const stats = this.state.stats;
        
        // Actualizar header stats
        this.updateElement('total-users-header', stats.totalUsers);
        this.updateElement('active-users-header', stats.activeUsers);
        
        // Actualizar dashboard stats
        this.updateElement('total-users-dashboard', stats.totalUsers);
        this.updateElement('active-users-dashboard', stats.activeUsers);
        this.updateElement('admin-users-dashboard', stats.adminUsers);
        
        // ✅ CORREGIDO: Actualizar porcentajes de permisos con nombres correctos
        const permissionMappings = {
            'select': 'select',
            'insert': 'insert', 
            'update': 'update',
            'delete': 'delete',
            'create_table': 'create',     // ✅ MAPEAR: create_table -> create
            'drop_table': 'drop'          // ✅ MAPEAR: drop_table -> drop
        };
        
        Object.entries(stats.permissions).forEach(([perm, count]) => {
            const percentage = stats.totalUsers > 0 ? Math.round((count / stats.totalUsers) * 100) : 0;
            
            // ✅ USAR MAPEO CORRECTO
            const htmlId = permissionMappings[perm] || perm;
            
            // Actualizar contadores
            this.updateElement(`${htmlId}-users-count`, count);
            this.updateElement(`${htmlId}-percentage-text`, `${percentage}% del total`);
            
            // Actualizar barras de progreso
            const bar = document.getElementById(`${htmlId}-percentage-bar`);
            if (bar) {
                bar.style.width = `${percentage}%`;
            }
            
            console.log(`📊 ${perm} -> ${htmlId}: ${count} usuarios (${percentage}%)`);
        });
        
        console.log('📊 Dashboard actualizado correctamente');
    },

    
    /**
     * Actualiza texto de un elemento
     */
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    },
    
    /**
     * Refresca datos del dashboard
     */
    async refreshDashboard() {
        try {
            this.ui.showToast('Actualizando datos...', 'info');
            
            await this.loadInitialData();
            
            this.ui.showToast('Datos actualizados correctamente', 'success');
            
        } catch (error) {
            console.error('❌ Error refrescando dashboard:', error);
            this.ui.showToast('Error actualizando datos', 'error');
        }
    },
    
    /**
     * Refresca lista de usuarios
     */
    async refreshUsers() {
        try {
            this.ui.showToast('Actualizando usuarios...', 'info');
            
            await this.loadUsers();
            this.calculateStats();
            this.updateDashboard();
            
            // Notificar a permissionsManager si existe
            if (window.permissionsManager && window.permissionsManager.refreshTable) {
                window.permissionsManager.refreshTable();
            }
            
            this.ui.showToast('Usuarios actualizados', 'success');
            
        } catch (error) {
            console.error('❌ Error refrescando usuarios:', error);
            this.ui.showToast('Error actualizando usuarios', 'error');
        }
    },
    
    /**
     * Maneja logout del admin
     */
    async handleLogout() {
        try {
            console.log('🚪 Admin cerrando sesión...');
            
            // Usar método de logout existente
            await this.auth.logout(this.storage.getToken());
            
        } catch (error) {
            console.error('❌ Error en logout admin:', error);
            // Logout forzado si hay error
            this.auth.forceLogout();
        }
    },
    
    /**
     * Obtiene usuarios cargados
     */
    getUsers() {
        return this.state.users;
    },
    
    /**
     * Obtiene estadísticas
     */
    getStats() {
        return this.state.stats;
    },
    
    /**
     * Verifica si está cargado
     */
    isLoaded() {
        return this.state.isLoaded;
    }
};
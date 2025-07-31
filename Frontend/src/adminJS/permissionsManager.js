// src/adminJS/permissionsManager.js - Gestión completa de permisos con eliminación
// Maneja tabla de permisos, toggles, búsqueda, eliminación de usuarios

export const permissionsManager = {
    ui: null,
    storage: null,
    
    // Estado simple
    state: {
        users: [],
        filteredUsers: [],
        isLoading: false
    },
    
    // Lista de permisos disponibles
    permissions: ['select', 'insert', 'update', 'delete', 'create_table', 'drop_table'],
    
    /**
     * Inicializa el gestor de permisos
     */
    async init(ui, storage, auth) {
        console.log('🔐 Inicializando gestor de permisos...');
        
        this.ui = ui;
        this.storage = storage;
        
        // Configurar eventos y cargar usuarios
        this.bindEvents();
        await this.loadUsers();
        this.renderTable();
        
        // Hacer accesible globalmente
        window.permissionsManager = this;
        
        console.log('✅ Gestor de permisos listo');
    },
    
    /**
     * Configura eventos básicos
     */
    bindEvents() {
        // Búsqueda
        const searchInput = document.getElementById('user-search');
        searchInput?.addEventListener('input', (e) => {
            this.filterUsers(e.target.value);
        });
        
        // Refresh
        const refreshBtn = document.getElementById('refresh-users');
        refreshBtn?.addEventListener('click', () => this.refreshUsers());
    },
    
    /**
     * Carga usuarios desde adminMain o API
     */
    async loadUsers() {
        try {
            // Intentar desde adminMain
            if (window.adminMain?.getUsers) {
                this.state.users = window.adminMain.getUsers();
            } else {
                // Cargar desde API
                await this.loadFromAPI();
            }
            
            // Aplicar filtros
            this.state.filteredUsers = [...this.state.users];
            
            console.log(`👥 ${this.state.users.length} usuarios cargados`);
            
        } catch (error) {
            console.error('❌ Error cargando usuarios:', error);
            this.ui?.showToast('Error cargando usuarios', 'error');
        }
    },
    
    /**
     * Carga usuarios desde API
     */
    async loadFromAPI() {
        const token = this.storage.getToken();
        const response = await fetch('http://localhost:5000/api/admin/users', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            this.state.users = data.users || [];
        } else {
            throw new Error('Error cargando desde API');
        }
    },
    
    /**
     * Renderiza la tabla de permisos
     */
    renderTable() {
        const tbody = document.getElementById('permissions-table-body');
        if (!tbody) return;
        
        if (this.state.filteredUsers.length === 0) {
            tbody.innerHTML = `
                <tr><td colspan="10">
                    <div class="table-loading">
                        <i class="fas fa-users"></i>
                        <span>No hay usuarios</span>
                    </div>
                </td></tr>
            `;
            return;
        }
        
        tbody.innerHTML = this.state.filteredUsers.map(user => this.createUserRow(user)).join('');
    },
    

    /**
     * ✅ CORREGIR: Crear toggles de permisos SIN deshabilitar admin
     */
    createUserRow(user) {
        const avatar = user.username.substring(0, 2).toUpperCase();
        const status = user.is_active ? 'active' : 'inactive';
        const statusIcon = user.is_active ? 'fa-check-circle' : 'fa-times-circle';
        
        // ✅ CORREGIDO: No deshabilitar permisos de admin, solo hacer que no se puedan cambiar
        const permissionToggles = this.permissions.map(perm => {
            const checked = user.permissions?.[perm] ? 'checked' : '';
            // ✅ SOLO deshabilitar la INTERACCIÓN, no el visual
            const disabled = user.role === 'admin' ? 'disabled title="Los administradores tienen todos los permisos"' : '';
            
            return `
                <td class="permission-col">
                    <label class="permission-toggle ${perm} ${user.role === 'admin' ? 'admin-permission' : ''}">
                        <input type="checkbox" ${checked} ${disabled}
                            data-user-id="${user._id}" 
                            data-permission="${perm}"
                            onchange="permissionsManager.togglePermission(this)">
                        <span class="toggle-slider"></span>
                    </label>
                </td>
            `;
        }).join('');
        
        return `
            <tr data-user-id="${user._id}">
                <td class="user-col">
                    <div class="user-info-cell">
                        <div class="user-avatar">${avatar}</div>
                        <div class="user-details">
                            <h4>${user.username}</h4>
                            <span class="user-role">${user.role}</span>
                        </div>
                    </div>
                </td>
                <td class="email-col">${user.email}</td>
                <td class="status-col">
                    <span class="user-status ${status}">
                        <i class="fas ${statusIcon}"></i>
                        ${user.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                </td>
                ${permissionToggles}
                ${this.createActionsCell(user)}
            </tr>
        `;
    },

    
    /**
     * ✅ ACTUALIZADO: Crear celda de acciones CON botón eliminar
     */
    createActionsCell(user) {
        const isCurrentUser = this.isCurrentUser(user);
        const isAdmin = user.role === 'admin';
        const canDelete = !isCurrentUser && !isAdmin;
        
        return `
            <td class="actions-col">
                <div class="action-buttons">
                    
                    ${canDelete ? `
                        <button 
                            class="btn-action delete" 
                            title="Eliminar usuario permanentemente"
                            onclick="permissionsManager.deleteUser('${user._id}')"
                            style="
                                background: #fef2f2;
                                color: #dc2626;
                                border: 1px solid #fecaca;
                            "
                        >
                            <i class="fas fa-trash"></i>
                        </button>
                    ` : ''}
                    
                    ${isCurrentUser ? `
                        <span style="
                            font-size: 0.75rem;
                            color: #6b7280;
                            font-style: italic;
                        ">Tú</span>
                    ` : ''}
                    
                    ${isAdmin && !isCurrentUser ? `
                        <span style="
                            font-size: 0.75rem;
                            color: #dc2626;
                            font-weight: 500;
                        ">Admin</span>
                    ` : ''}
                </div>
            </td>
        `;
    },
    
    /**
     * Maneja toggle de permisos - FUNCIÓN PRINCIPAL
     */
    async togglePermission(checkbox) {
        const userId = checkbox.dataset.userId;
        const permission = checkbox.dataset.permission;
        const isGranted = checkbox.checked;
        
        try {
            console.log(`🔐 ${permission} -> ${isGranted} para usuario ${userId}`);
            
            // Actualizar en backend
            await this.updatePermission(userId, permission, isGranted);
            
            // Actualizar estado local
            const user = this.state.users.find(u => u._id === userId);
            if (user) {
                if (!user.permissions) user.permissions = {};
                user.permissions[permission] = isGranted;
            }
            
            // Feedback
            this.showSuccess(checkbox);
            this.ui?.showToast(`✅ Permiso ${permission} ${isGranted ? 'activado' : 'desactivado'}`, 'success');
            
        } catch (error) {
            console.error('❌ Error:', error);
            
            // Revertir checkbox
            checkbox.checked = !isGranted;
            this.ui?.showToast('Error actualizando permiso', 'error');
        }
    },
    
    /**
     * Actualiza permiso en backend
     */
    async updatePermission(userId, permission, granted) {
        const token = this.storage.getToken();
        
        const response = await fetch(`http://localhost:5000/api/admin/users/${userId}/permissions`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ permission, granted })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        return response.json();
    },
    
    /**
     * ✅ NUEVO: Elimina un usuario de la base de datos
     */
    async deleteUser(userId) {
        try {
            const user = this.state.users.find(u => u._id === userId);
            if (!user) {
                this.ui?.showToast('Usuario no encontrado', 'error');
                return;
            }
            
            // Verificar que no sea el usuario actual
            if (this.isCurrentUser(user)) {
                this.ui?.showToast('❌ No puedes eliminarte a ti mismo', 'error');
                return;
            }
            
            // Verificar que no sea otro admin
            if (user.role === 'admin') {
                this.ui?.showToast('❌ No se pueden eliminar otros administradores', 'error');
                return;
            }
            
            // ✅ CONFIRMACIÓN DOBLE con confirm()
            const confirmMessage = `⚠️ ¿ELIMINAR USUARIO "${user.username}"?\n\n` +
                                  `Email: ${user.email}\n` +
                                  `Role: ${user.role}\n\n` +
                                  `⚠️ ESTA ACCIÓN NO SE PUEDE DESHACER ⚠️\n\n` +
                                  `El usuario será eliminado PERMANENTEMENTE de la base de datos.\n\n` +
                                  `¿Estás completamente seguro?`;
            
            if (!confirm(confirmMessage)) {
                console.log('🚫 Eliminación cancelada por el usuario');
                return;
            }
            
            // Segunda confirmación para estar seguros
            const finalConfirm = confirm(`ÚLTIMA CONFIRMACIÓN:\n\n¿Eliminar definitivamente a "${user.username}"?\n\nEscribe "SI" para continuar`);
            if (!finalConfirm) {
                console.log('🚫 Eliminación cancelada en segunda confirmación');
                return;
            }
            
            console.log(`🗑️ ELIMINANDO usuario: ${userId} (${user.username})`);
            
            // Mostrar toast de proceso
            this.ui?.showToast('🗑️ Eliminando usuario...', 'info');
            
            // Eliminar en backend
            await this.deleteUserFromBackend(userId);
            
            // Eliminar del estado local
            this.state.users = this.state.users.filter(u => u._id !== userId);
            this.state.filteredUsers = this.state.filteredUsers.filter(u => u._id !== userId);
            
            // Re-renderizar tabla
            this.renderTable();
            
            // Actualizar estadísticas en adminMain
            if (window.adminMain?.refreshUsers) {
                window.adminMain.refreshUsers();
            }
            
            this.ui?.showToast(`✅ Usuario "${user.username}" eliminado exitosamente`, 'success');
            
        } catch (error) {
            console.error('❌ Error eliminando usuario:', error);
            this.ui?.showToast('Error eliminando usuario: ' + error.message, 'error');
        }
    },
    
    /**
     * ✅ NUEVO: Elimina usuario del backend
     */
    async deleteUserFromBackend(userId) {
        const token = this.storage.getToken();
        
        const response = await fetch(`http://localhost:5000/api/admin/users/${userId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        return response.json();
    },
    
    /**
     * ✅ MEJORADO: Verifica si es el usuario actual
     */
    isCurrentUser(user) {
        const currentUserData = this.storage.getUserData();
        if (!currentUserData) return false;
        
        return currentUserData.id === user._id || 
               currentUserData._id === user._id ||
               currentUserData.username === user.username;
    },
    
    /**
     * Feedback visual de éxito
     */
    showSuccess(checkbox) {
        const toggle = checkbox.closest('.permission-toggle');
        toggle.style.boxShadow = '0 0 10px #10b981';
        setTimeout(() => {
            toggle.style.boxShadow = '';
        }, 1000);
    },
    
    /**
     * Filtra usuarios por búsqueda
     */
    filterUsers(searchTerm) {
        if (!searchTerm.trim()) {
            this.state.filteredUsers = [...this.state.users];
        } else {
            const term = searchTerm.toLowerCase();
            this.state.filteredUsers = this.state.users.filter(user => 
                user.username.toLowerCase().includes(term) ||
                user.email.toLowerCase().includes(term) ||
                user.role.toLowerCase().includes(term)
            );
        }
        
        this.renderTable();
        console.log(`🔍 Filtro "${searchTerm}": ${this.state.filteredUsers.length} resultados`);
    },
    
    /**
     * Refresca usuarios
     */
    async refreshUsers() {
        this.state.isLoading = true;
        await this.loadUsers();
        this.renderTable();
        this.state.isLoading = false;
        this.ui?.showToast('✅ Usuarios actualizados', 'success');
    },
    
    /**
     * Método público para refresh externo
     */
    refreshTable() {
        this.refreshUsers();
    }
};
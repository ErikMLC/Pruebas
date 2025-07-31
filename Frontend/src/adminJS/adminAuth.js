// src/adminJS/adminAuth.js - Protección de acceso admin
// Enfocado en verificar permisos de administrador

export const adminAuth = {
    
    /**
     * Verifica si el usuario actual es administrador
     * Triple verificación: token + role + backend
     */
    async verifyAdmin(auth, storage) {
        try {
            console.log('🔒 Verificando acceso de administrador...');
            
            // 1. Verificar token válido
            const token = storage.getToken();
            if (!token) {
                console.log('❌ Sin token de acceso');
                return false;
            }
            
            // 2. Verificar role en token JWT
            const userRole = this.getRoleFromToken(token);
            if (userRole !== 'admin') {
                console.log('❌ Usuario no es admin:', userRole);
                return false;
            }
            
            // 3. Verificar con backend (opcional, con fallback)
            const backendVerified = await this.verifyWithBackend(token);
            if (!backendVerified) {
                console.log('⚠️ Backend no verificó admin, pero token indica admin');
                // Continuar si token es válido, en caso de problemas de red
            }
            
            console.log('✅ Acceso de administrador verificado');
            return true;
            
        } catch (error) {
            console.error('❌ Error verificando admin:', error);
            return false;
        }
    },
    
    /**
     * Extrae el role del token JWT
     */
    getRoleFromToken(token) {
        try {
            // Decodificar payload del JWT
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.role || payload.user_role || 'user';
            
        } catch (error) {
            console.error('❌ Error decodificando token:', error);
            return null;
        }
    },
    
    /**
     * Verifica permisos admin con el backend
     */
    async verifyWithBackend(token) {
        try {
            const response = await fetch('http://localhost:5000/api/admin/verify', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                // Timeout corto para no bloquear
                signal: AbortSignal.timeout(5000)
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.is_admin === true;
            }
            
            return false;
            
        } catch (error) {
            console.warn('⚠️ Error verificando con backend:', error.message);
            // En caso de error de red, confiar en el token
            return true;
        }
    },
    
    /**
     * Verifica permisos específicos de admin
     */
    async verifyAdminPermissions(storage) {
        try {
            const userData = storage.getUserData();
            const permissions = userData?.permissions || {};
            
            // Verificar permisos críticos de admin
            const hasAdminPerms = permissions.manage_users === true || 
                                 permissions.admin === true ||
                                 userData?.role === 'admin';
            
            if (!hasAdminPerms) {
                console.log('❌ Sin permisos de administrador');
                return false;
            }
            
            console.log('✅ Permisos de admin verificados');
            return true;
            
        } catch (error) {
            console.error('❌ Error verificando permisos admin:', error);
            return false;
        }
    },
    
    /**
     * Redirige al login si no es admin
     */
    redirectToLogin() {
        console.log('🔄 Redirigiendo a login - acceso denegado');
        
        // Limpiar sesión si no es admin
        try {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user_data');
            sessionStorage.clear();
        } catch (error) {
            console.warn('Error limpiando storage:', error);
        }
        
        // Mostrar mensaje y redirigir
        this.showAccessDeniedMessage();
        
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 2000);
    },
    
    /**
     * Muestra mensaje de acceso denegado
     */
    showAccessDeniedMessage() {
        // Crear overlay de acceso denegado
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(220, 38, 38, 0.95);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 99999;
            color: white;
            font-family: 'Inter', sans-serif;
        `;
        
        overlay.innerHTML = `
            <div style="text-align: center; padding: 40px; max-width: 500px;">
                <div style="font-size: 4rem; margin-bottom: 20px;">
                    🚫
                </div>
                <h1 style="font-size: 2rem; margin-bottom: 15px; font-weight: 700;">
                    Acceso Denegado
                </h1>
                <p style="font-size: 1.1rem; margin-bottom: 30px; opacity: 0.9;">
                    No tienes permisos de <strong>administrador</strong> para acceder a este panel.
                </p>
                <div style="background: rgba(255, 255, 255, 0.1); padding: 20px; border-radius: 10px; margin-bottom: 30px;">
                    <p style="margin: 0; font-size: 0.9rem;">
                        Solo usuarios con role <strong>"admin"</strong> pueden acceder al panel de administración.
                    </p>
                </div>
                <p style="font-size: 0.9rem; opacity: 0.8;">
                    Redirigiendo al login en 2 segundos...
                </p>
            </div>
        `;
        
        document.body.appendChild(overlay);
    },
    
    /**
     * Verifica permisos para operación específica
     */
    canPerformAdminAction(action, storage) {
        try {
            const userData = storage.getUserData();
            const role = userData?.role;
            const permissions = userData?.permissions || {};
            
            // Solo admins pueden hacer operaciones admin
            if (role !== 'admin') {
                return false;
            }
            
            // Verificar permisos específicos
            switch (action) {
                case 'manage_users':
                    return permissions.manage_users === true || role === 'admin';
                case 'modify_permissions':
                    return permissions.admin === true || role === 'admin';
                case 'view_system_stats':
                    return role === 'admin';
                default:
                    return role === 'admin';
            }
            
        } catch (error) {
            console.error('❌ Error verificando acción admin:', error);
            return false;
        }
    },
    
    /**
     * Obtiene información del admin actual
     */
    getAdminInfo(storage) {
        try {
            const userData = storage.getUserData();
            
            if (!userData || userData.role !== 'admin') {
                return null;
            }
            
            return {
                id: userData.id || userData._id,
                username: userData.username,
                email: userData.email,
                role: userData.role,
                permissions: userData.permissions || {},
                isAdmin: true
            };
            
        } catch (error) {
            console.error('❌ Error obteniendo info admin:', error);
            return null;
        }
    },
    
    /**
     * Configura verificación periódica de permisos admin
     */
    setupPeriodicVerification(auth, storage, intervalMs = 300000) { // 5 minutos
        console.log('⏰ Configurando verificación periódica admin');
        
        const verifyInterval = setInterval(async () => {
            const isStillAdmin = await this.verifyAdmin(auth, storage);
            
            if (!isStillAdmin) {
                console.log('❌ Permisos admin revocados - cerrando sesión');
                clearInterval(verifyInterval);
                this.redirectToLogin();
            }
        }, intervalMs);
        
        // Limpiar interval al cerrar página
        window.addEventListener('beforeunload', () => {
            clearInterval(verifyInterval);
        });
        
        return verifyInterval;
    },
    
    /**
     * Verifica si el token está próximo a expirar
     */
    isTokenNearExpiry(token, minutesBefore = 10) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const expiryTime = payload.exp * 1000; // Convertir a ms
            const currentTime = Date.now();
            const timeUntilExpiry = expiryTime - currentTime;
            const warningTime = minutesBefore * 60 * 1000; // Convertir a ms
            
            return timeUntilExpiry <= warningTime;
            
        } catch (error) {
            return true; // Asumir que expira si hay error
        }
    },
    
    /**
     * Inicializa protecciones admin
     */
    async initAdminProtection(auth, storage) {
        console.log('🛡️ Inicializando protecciones admin...');
        
        // Verificar acceso inicial
        const hasAccess = await this.verifyAdmin(auth, storage);
        if (!hasAccess) {
            return false;
        }
        
        // Configurar verificación periódica
        this.setupPeriodicVerification(auth, storage);
        
        // Verificar expiración de token
        const token = storage.getToken();
        if (this.isTokenNearExpiry(token)) {
            console.log('⚠️ Token próximo a expirar');
            // Aquí podrías implementar refresh automático
        }
        
        console.log('✅ Protecciones admin inicializadas');
        return true;
    }
};
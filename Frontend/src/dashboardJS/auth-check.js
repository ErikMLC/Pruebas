// auth-check.js - Con BYPASS TEMPORAL para solucionar el problema
// ✅ CORREGIDO - Compatible con storage.js existente

export const authCheck = {
    /**
     * Verifica si el usuario está autenticado
     * @param {Object} auth - Módulo de autenticación existente
     * @param {Object} storage - Módulo de storage existente
     * @returns {Promise<boolean>} - True si está autenticado
     */
    async verify(auth, storage) {
        try {
            console.log('🔒 Verificando autenticación en dashboard...');
            
            // 1. Verificar token en storage
            const token = storage.getToken();
            if (!token) {
                console.log('❌ No hay token guardado');
                return false;
            }
            
            console.log('🔑 Token encontrado, verificando validez...');
            
            // 2. Verificar si el token es válido (no expirado)
            if (this.isTokenExpired(token)) {
                console.log('❌ Token expirado, limpiando...');
                storage.clearAll();
                return false;
            }
            
            console.log('⏰ Token no expirado');
            
            // ✅ BYPASS TEMPORAL: Verificar directamente con backend sin usar auth.validateToken
            console.log('🔄 BYPASS: Validando directamente con backend...');
            
            try {
                // Hacer petición directa al backend
                const response = await fetch('http://localhost:5000/api/auth/profile', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                console.log('📡 Respuesta backend status:', response.status);
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('✅ BYPASS: Backend confirmó token válido:', data);
                    
                    // ✅ CRÍTICO: Establecer estado autenticado en auth
                    if (auth.isAuthenticated !== undefined) {
                        auth.isAuthenticated = true;
                        auth.token = token;
                        console.log('🔧 Estado de autenticación establecido en auth');
                    }
                    
                    return true;
                } else if (response.status === 401 || response.status === 403) {
                    console.log('❌ BYPASS: Token rechazado por backend (401/403)');
                    storage.clearAll();
                    return false;
                } else {
                    console.log('⚠️ BYPASS: Error de servidor, manteniendo sesión');
                    return true;
                }
                
            } catch (networkError) {
                console.error('❌ BYPASS: Error de red:', networkError);
                
                // Si es error de red, mantener sesión
                if (networkError.message?.includes('fetch') || 
                    networkError.message?.includes('Failed to fetch')) {
                    console.log('🌐 BYPASS: Error de red, manteniendo sesión');
                    return true;
                }
                
                throw networkError;
            }
            
        } catch (error) {
            console.error('❌ Error crítico verificando autenticación:', error);
            
            // Solo limpiar en errores críticos, no de red
            if (!error.message?.includes('fetch') && !error.message?.includes('Failed to fetch')) {
                storage.clearAll();
            }
            
            return false;
        }
    },
    
    /**
     * Verifica si un token JWT está expirado
     * @param {string} token - Token JWT
     * @returns {boolean} - True si está expirado
     */
    isTokenExpired(token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            const currentTime = Math.floor(Date.now() / 1000);
            const isExpired = payload.exp < currentTime;
            
            console.log('🕐 Verificación de expiración:', {
                tokenExp: payload.exp,
                currentTime: currentTime,
                isExpired: isExpired,
                timeRemaining: isExpired ? 0 : payload.exp - currentTime
            });
            
            return isExpired;
        } catch (error) {
            console.error('❌ Error decodificando token:', error);
            return true;
        }
    },
    
    /**
     * Obtiene información del usuario desde el token
     * @param {Object} storage - Módulo de storage
     * @returns {Object|null} - Datos del usuario o null
     */
    getUserFromToken(storage) {
        try {
            const token = storage.getToken();
            if (!token) {
                console.log('❌ No hay token para extraer usuario');
                return null;
            }
            
            const payload = JSON.parse(atob(token.split('.')[1]));
            
            const userInfo = {
                id: payload.sub || payload.user_id || payload.identity,
                username: payload.username,
                email: payload.email,
                role: payload.role || 'user',
                permissions: payload.permissions || {}
            };
            
            console.log('👤 Usuario extraído del token:', {
                username: userInfo.username,
                email: userInfo.email,
                role: userInfo.role,
                hasPermissions: !!userInfo.permissions
            });
            
            return userInfo;
        } catch (error) {
            console.error('❌ Error extrayendo usuario del token:', error);
            return null;
        }
    },
    
    /**
     * ✅ NUEVO: Método para verificar datos completos del usuario
     * @param {Object} storage - Módulo de storage
     * @returns {Object|null} - Datos completos del usuario
     */
    getCompleteUserData(storage) {
        try {
            // Primero intentar obtener del storage
            let userData = storage.getUserData();
            
            // Si no hay datos en storage, extraer del token
            if (!userData) {
                console.log('📦 No hay datos en storage, extrayendo del token...');
                userData = this.getUserFromToken(storage);
            }
            
            console.log('📋 Datos completos del usuario:', userData);
            return userData;
            
        } catch (error) {
            console.error('❌ Error obteniendo datos completos:', error);
            return null;
        }
    }
};
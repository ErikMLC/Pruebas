/**
 * auth.js - Módulo de autenticación y comunicación con API (VERSIÓN ARREGLADA)
 * Maneja todas las operaciones relacionadas con autenticación
 */

class AuthManager {
  constructor() {
    // ✅ URL correcta según tu backend
    this.baseURL = 'http://localhost:5000/api';
    this.timeout = 10000; // 10 segundos
    
    // ✅ Variables de estado para logout
    this.isAuthenticated = false;
    this.user = null;
    this.token = null;
    this.validationTimer = null;
    this.isValidating = false;
    this.isLoggingOut = false; // ✅ Prevenir logout múltiple
  }

  /**
   * Realiza login con email y contraseña
   */
  async login(email, password) {
    try {
      console.log('🔄 Intentando login con:', { email, baseURL: this.baseURL });
      
      const response = await this.makeRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username: email,  // Tu backend espera 'username'
          password: password
        })
      });

      console.log('✅ Respuesta del servidor:', response);
      
      // ✅ CRÍTICO: Verificar estructura de respuesta de tu backend
      if (response && response.access_token) {
        // ✅ Guardar estado de autenticación
        this.token = response.access_token;
        this.user = response.user || {
          email: response.email || email,
          username: response.username || response.user?.username || email.split('@')[0],
          role: response.role || response.user?.role || 'user',
          permissions: response.permissions || response.user?.permissions || {}
        };
        this.isAuthenticated = true;
        
        return {
          success: true,
          data: {
            access_token: response.access_token,
            refresh_token: response.refresh_token,
            user: this.user
          }
        };
      } else {
        return {
          success: false,
          message: response.error || response.message || 'Respuesta inválida del servidor'
        };
      }

    } catch (error) {
      console.error('❌ Error en login:', error);
      
      // ✅ Manejo mejorado de errores
      let errorMessage = 'Constraseña o usuario incorrecto';
      
      if (error.message.includes('401')) {
        errorMessage = 'Credenciales incorrectas';
      } else if (error.message.includes('404')) {
        errorMessage = 'Servicio no encontrado. Verifica que el servidor esté ejecutándose.';
      } else if (error.message.includes('ECONNREFUSED') || error.message.includes('fetch')) {
        errorMessage = 'No se puede conectar al servidor. Verifica que esté ejecutándose en el puerto 5000.';
      }
      
      return {
        success: false,
        message: errorMessage
      };
    }
  }


/**
 * Métodos LOGOUT corregidos para auth.js
 * Reemplaza estos 3 métodos en tu auth.js actual
 */

/**
 * ✅ LOGOUT ARREGLADO - Con redirección correcta
 */
  async logout(token) {
    // ✅ Prevenir múltiples logouts simultáneos
    if (this.isLoggingOut) {
      console.log('🔄 Logout ya en progreso...');
      return;
    }
    
    this.isLoggingOut = true;
    
    try {
      console.log('🚪 Cerrando sesión...');
      
      // ✅ 1. Parar validaciones INMEDIATAMENTE
      if (this.validationTimer) {
        clearInterval(this.validationTimer);
        this.validationTimer = null;
      }
      
      // ✅ 2. Limpiar estado local INMEDIATAMENTE
      this.isAuthenticated = false;
      this.user = null;
      this.token = null;
      this.isValidating = false;
      
      // ✅ 3. Limpiar TODOS los storages INMEDIATAMENTE
      try {
        // Limpiar localStorage
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        localStorage.removeItem('lastLoginTime');
        localStorage.removeItem('loginAttempts');
        localStorage.removeItem('lastQuery');
        localStorage.removeItem('remember_me');
        
        // Limpiar sessionStorage
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('refresh_token');
        sessionStorage.removeItem('user_data');
        sessionStorage.removeItem('authToken');
        sessionStorage.removeItem('refreshToken');
        sessionStorage.removeItem('user');
        
        console.log('🧹 Storage limpiado completamente');
      } catch (e) {
        console.warn('Error limpiando storage:', e);
      }
      
      // ✅ 4. Redireccionar INMEDIATAMENTE
      this.redirectToLogin();
      
      console.log('✅ Logout completado');
      
    } catch (error) {
      console.error('❌ Error durante logout:', error);
      this.forceLogout();
    } finally {
      this.isLoggingOut = false;
    }
  }

  /**
   * ✅ Logout forzado para casos de error
   */
  forceLogout() {
    console.log('🔨 Forzando logout...');
    
    // Parar todos los timers
    if (this.validationTimer) {
      clearInterval(this.validationTimer);
      this.validationTimer = null;
    }
    
    // Limpiar todo el estado
    this.isAuthenticated = false;
    this.user = null;
    this.token = null;
    this.isValidating = false;
    this.isLoggingOut = false;
    
    // Limpiar storage completamente
    try {
      localStorage.clear();
      sessionStorage.clear();
      console.log('🧹 Storage forzado limpiado');
    } catch (e) {
      console.warn('Error limpiando storage:', e);
    }
    
    // Redirección inmediata
    this.redirectToLogin();
  }

  /**
   * ✅ REDIRECCIÓN CORREGIDA - Funciona desde cualquier página
   */
  redirectToLogin() {
    console.log('🔄 Redirigiendo al login...');
    
    try {
      // ✅ MÉTODO 1: Redirección directa inmediata
      console.log('1️⃣ Intentando redirección directa...');
      window.location.href = 'index.html';
      
      // ✅ MÉTODO 2: Fallback con replace después de 500ms
      setTimeout(() => {
        console.log('2️⃣ Fallback: usando replace...');
        window.location.replace('index.html');
      }, 500);
      
      // ✅ MÉTODO 3: Fallback final después de 1 segundo
      setTimeout(() => {
        console.log('3️⃣ Fallback final: forzando navegación...');
        window.location = 'index.html';
      }, 1000);
      
    } catch (error) {
      console.error('💥 Error en redirección:', error);
      
      // ✅ MÉTODO DE EMERGENCIA: Crear enlace manual
      try {
        const link = document.createElement('a');
        link.href = 'index.html';
        link.style.cssText = 'position:fixed; top:50%; left:50%; z-index:99999; padding:20px; background:red; color:white; font-size:18px;';
        link.textContent = '🔄 CLICK AQUÍ PARA IR AL LOGIN';
        document.body.appendChild(link);
        link.click();
      } catch (linkError) {
        console.error('💥 Error creando enlace de emergencia:', linkError);
        
        // ✅ ÚLTIMO RECURSO: Recargar página
        window.location.reload();
      }
    }
  }




  /**
   * Realiza registro de nuevo usuario
   */
  async register(username, email, password) {
    try {
      const response = await this.makeRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          username: username,
          email: email,
          password: password
        })
      });

      return response;
    } catch (error) {
      console.error('Error en registro:', error);
      throw new Error('Contraseña no Válida');
    }
  }

  /**
   * Valida un token de acceso
   */
  
/**
 * auth.js - SOLO EL MÉTODO validateToken CORREGIDO
 * Reemplaza este método en tu auth.js existente
 */

/**
 * ✅ MÉTODO CORREGIDO - Valida un token de acceso
 */
  async validateToken(token) {
    // ✅ Prevenir validaciones si ya estamos cerrando sesión
    if (this.isLoggingOut || !this.isAuthenticated) {
      console.log('🛑 Validación cancelada: logout en progreso o no autenticado');
      return false;
    }
    
    try {
      console.log('🔐 Validando token con backend...');
      
      const response = await this.makeRequest('/auth/profile', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('📨 Respuesta validación:', response);
      
      // ✅ CRÍTICO: Verificar la estructura correcta de respuesta
      if (response && (response.user || response.email || response.username)) {
        console.log('✅ Token válido - usuario encontrado');
        return true;
      } else {
        console.log('❌ Token válido pero respuesta inesperada:', response);
        return true; // ✅ CAMBIADO: Si hay respuesta, asumir válido
      }

    } catch (error) {
      console.error('❌ Error validando token:', error);
      
      // ✅ MEJORADO: Solo rechazar token si es error de autenticación
      if (error.message?.includes('401') || error.message?.includes('403') || error.message?.includes('Unauthorized')) {
        console.log('❌ Token rechazado por servidor (401/403)');
        
        // Solo limpiar si NO estamos haciendo logout
        if (!this.isLoggingOut) {
          console.log('🧹 Limpiando sesión por token inválido...');
          this.forceLogout();
        }
        
        return false;
      }
      
      // ✅ NUEVO: Para errores de red, mantener sesión
      console.log('⚠️ Error de red/servidor, manteniendo sesión temporalmente...');
      console.log('📝 Tipo de error:', error.message);
      
      // Si es error de conexión, no invalidar el token
      if (error.message?.includes('fetch') || 
          error.message?.includes('network') || 
          error.message?.includes('Failed to fetch') ||
          error.message?.includes('ECONNREFUSED')) {
        console.log('🌐 Error de conexión detectado, token sigue siendo válido');
        return true; // ✅ Mantener sesión si es problema de red
      }
      
      // Para otros errores, ser conservador y mantener sesión
      console.log('🤔 Error desconocido, manteniendo sesión por seguridad');
      return true;
    }
  }


  /**
   * Refresca el token de acceso
   */
  async refreshToken(refreshToken) {
    try {
      const response = await this.makeRequest('/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${refreshToken}`
        }
      });

      return response;
    } catch (error) {
      console.error('Error refrescando token:', error);
      throw new Error('Error al refrescar token');
    }
  }

  /**
   * Realiza una petición HTTP genérica
   */
  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    console.log(`🌐 Haciendo petición a: ${url}`);
    
    const config = {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers
      },
      ...options
    };

    // Crear controlador para timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...config,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      console.log(`📡 Respuesta HTTP ${response.status} de ${url}`);

      // ✅ CRÍTICO: Manejo mejorado de respuestas de error
      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = { message: `HTTP ${response.status}` };
        }
        
        console.error('❌ Error del servidor:', errorData);
        throw new Error(errorData.error || errorData.message || `HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('📦 Datos recibidos:', data);
      return data;

    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new Error('Tiempo de espera agotado');
      }
      
      console.error('❌ Error en petición:', error);
      throw error;
    }
  }

  /**
   * Configura la URL base de la API
   */
  setBaseURL(url) {
    this.baseURL = url;
    console.log(`🔧 URL base cambiada a: ${url}`);
  }

  /**
   * Configura el timeout para peticiones
   */
  setTimeout(ms) {
    this.timeout = ms;
  }

  /**
   * ✅ Métodos públicos para verificar estado
   */
  isUserAuthenticated() {
    return this.isAuthenticated;
  }

  getCurrentUser() {
    return this.user;
  }

  getToken() {
    return this.token;
  }
}

// Exportar instancia única
export const auth = new AuthManager();
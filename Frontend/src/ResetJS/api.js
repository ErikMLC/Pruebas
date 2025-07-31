/**
 * api.js - API específica para reset de contraseña
 * Maneja endpoints de forgot/verify/reset y comunicación con backend
 */

class ResetAPI {
  constructor() {
    this.baseURL = 'http://localhost:5000/api';
    this.timeout = 15000; // 15 segundos
  }

  /**
   * Solicita código de recuperación por email
   */
  async forgotPassword(email) {
    try {
      const response = await this.makeRequest('/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ email })
      });

      return {
        success: true,
        message: response.message || 'Código enviado a tu email',
        data: response
      };

    } catch (error) {
      return {
        success: false,
        message: error.message || 'Error enviando código de recuperación'
      };
    }
  }

  /**
   * Verifica el código de recuperación
   */
  async verifyCode(email, code) {
    try {
      const response = await this.makeRequest('/auth/verify-reset-code', {
        method: 'POST',
        body: JSON.stringify({
          email,
          code
        })
      });

      return {
        success: true,
        message: response.message || 'Código verificado correctamente',
        data: response
      };

    } catch (error) {
      return {
        success: false,
        message: error.message || 'Código inválido o expirado'
      };
    }
  }

  /**
   * Resetea la contraseña con la nueva
   */
  async resetPassword(email, newPassword) {
    try {
      const response = await this.makeRequest('/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify({
          email,
          new_password: newPassword
        })
      });

      return {
        success: true,
        message: response.message || 'Contraseña actualizada exitosamente',
        data: response
      };

    } catch (error) {
      return {
        success: false,
        message: error.message || 'Error actualizando contraseña'
      };
    }
  }

  /**
   * Reenvía el código de verificación
   */
  async resendCode(email) {
    try {
      const response = await this.makeRequest('/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ 
          email,
          resend: true 
        })
      });

      return {
        success: true,
        message: response.message || 'Código reenviado a tu email',
        data: response
      };

    } catch (error) {
      return {
        success: false,
        message: error.message || 'Error reenviando código'
      };
    }
  }

  /**
   * Valida si un email existe en el sistema
   */
  async checkEmailExists(email) {
    try {
      const response = await this.makeRequest('/auth/check-email', {
        method: 'POST',
        body: JSON.stringify({ email })
      });

      return {
        exists: response.exists || false,
        message: response.message
      };

    } catch (error) {
      // En caso de error, asumir que no existe
      return {
        exists: false,
        message: 'Error verificando email'
      };
    }
  }

  /**
   * Obtiene información del rate limiting
   */
  async getRateLimitInfo(email) {
    try {
      const response = await this.makeRequest(`/auth/rate-limit/${email}`, {
        method: 'GET'
      });

      return {
        success: true,
        data: {
          attempts: response.attempts || 0,
          maxAttempts: response.maxAttempts || 3,
          resetTime: response.resetTime || null,
          canAttempt: response.canAttempt || true
        }
      };

    } catch (error) {
      return {
        success: false,
        message: error.message || 'Error obteniendo información de límites'
      };
    }
  }

  /**
   * Realiza una petición HTTP genérica
   */
  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
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

      // Verificar si la respuesta es exitosa
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        // Manejar errores específicos de reset
        if (response.status === 400) {
          throw new Error(errorData.message || 'Datos inválidos');
        } else if (response.status === 404) {
          throw new Error(errorData.message || 'Email no encontrado');
        } else if (response.status === 429) {
          throw new Error(errorData.message || 'Demasiados intentos. Intenta más tarde');
        } else if (response.status === 410) {
          throw new Error(errorData.message || 'Código expirado');
        } else {
          throw new Error(errorData.message || `Error HTTP ${response.status}`);
        }
      }

      const data = await response.json();
      return data;

    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new Error('Tiempo de espera agotado. Verifica tu conexión.');
      }
      
      throw error;
    }
  }

  /**
   * Configura la URL base de la API
   */
  setBaseURL(url) {
    this.baseURL = url;
  }

  /**
   * Configura el timeout para peticiones
   */
  setTimeout(ms) {
    this.timeout = ms;
  }

  /**
   * Obtiene configuración actual de la API
   */
  getConfig() {
    return {
      baseURL: this.baseURL,
      timeout: this.timeout
    };
  }

  /**
   * Valida conectividad con el servidor
   */
  async checkHealth() {
    try {
      const response = await this.makeRequest('/health', {
        method: 'GET'
      });

      return {
        success: true,
        message: 'Servidor disponible',
        data: response
      };

    } catch (error) {
      return {
        success: false,
        message: 'Servidor no disponible'
      };
    }
  }

  /**
   * Cancela todas las peticiones pendientes
   */
  cancelAllRequests() {
    // Implementación para cancelar peticiones en curso
    // En un caso real, mantendríamos un array de controllers
    console.log('Cancelando todas las peticiones...');
  }
}

// Exportar instancia única
export const api = new ResetAPI();
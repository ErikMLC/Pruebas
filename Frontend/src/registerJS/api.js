/**
 * api.js - API específica para registro
 * Maneja registro, validación de usuarios existentes y tokens
 */

class RegisterAPI {
  constructor() {
    this.baseURL = 'http://localhost:5000/api';
    this.timeout = 15000; // 15 segundos para registro
  }

  /**
   * Registra un nuevo usuario
   */
  async register(userData) {
    try {
      const response = await this.makeRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          username: userData.username,
          email: userData.email,
          password: userData.password
        })
      });

      return {
        success: true,
        data: response,
        message: response.message || 'Usuario registrado exitosamente'
      };

    } catch (error) {
      return {
        success: false,
        message: error.message || 'Error al registrar usuario'
      };
    }
  }

  /**
   * Verifica si un email ya existe
   */
  async checkEmailExists(email) {
    try {
      const response = await this.makeRequest('/auth/check-email', {
        method: 'POST',
        body: JSON.stringify({ email })
      });

      return response.exists || false;
    } catch (error) {
      console.warn('Error verificando email:', error);
      return false;
    }
  }

  /**
   * Verifica si un username ya existe
   */
  async checkUsernameExists(username) {
    try {
      const response = await this.makeRequest('/auth/check-username', {
        method: 'POST',
        body: JSON.stringify({ username })
      });

      return response.exists || false;
    } catch (error) {
      console.warn('Error verificando username:', error);
      return false;
    }
  }

  /**
   * Valida un token existente (para verificar sesión activa)
   */
  async validateToken(token) {
    try {
      const response = await this.makeRequest('/auth/validate', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      return response.success || false;
    } catch (error) {
      return false;
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
        
        // Manejar errores específicos de registro
        if (response.status === 400) {
          throw new Error(errorData.error || 'Datos de registro inválidos');
        } else if (response.status === 409) {
          throw new Error(errorData.error || 'El usuario ya existe');
        } else if (response.status === 422) {
          throw new Error(errorData.error || 'Email o username ya registrado');
        } else {
          throw new Error(errorData.error || `Error HTTP ${response.status}`);
        }
      }

      const data = await response.json();
      return data;

    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new Error('Tiempo de espera agotado. Intenta nuevamente.');
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
}

// Exportar instancia única
export const api = new RegisterAPI();
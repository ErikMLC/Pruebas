/**
 * storage.js - Módulo de gestión de almacenamiento
 * Maneja localStorage, sessionStorage y datos del usuario
 */

class StorageManager {
  constructor() {
    this.keys = {
      ACCESS_TOKEN: 'access_token',
      REFRESH_TOKEN: 'refresh_token',
      USER_DATA: 'user_data',
      PREFERENCES: 'user_preferences',
      REMEMBER_ME: 'remember_me'
    };
  }

  /**
   * Guarda los tokens de autenticación
   */
  saveTokens(accessToken, refreshToken, persistent = false) {
    const storage = persistent ? localStorage : sessionStorage;
    
    // Guardar tokens
    storage.setItem(this.keys.ACCESS_TOKEN, accessToken);
    if (refreshToken) {
      storage.setItem(this.keys.REFRESH_TOKEN, refreshToken);
    }

    // Guardar preferencia de recordar
    if (persistent) {
      localStorage.setItem(this.keys.REMEMBER_ME, 'true');
    }

    // Limpiar del otro storage
    const otherStorage = persistent ? sessionStorage : localStorage;
    this.clearTokensFromStorage(otherStorage);
  }

  /**
   * Obtiene el token de acceso
   */
  getToken() {
    return localStorage.getItem(this.keys.ACCESS_TOKEN) ||
           sessionStorage.getItem(this.keys.ACCESS_TOKEN);
  }

  /**
   * Obtiene el token de refresco
   */
  getRefreshToken() {
    return localStorage.getItem(this.keys.REFRESH_TOKEN) ||
           sessionStorage.getItem(this.keys.REFRESH_TOKEN);
  }

  /**
   * Guarda los datos del usuario
   */
  saveUserData(userData, persistent = false) {
    const storage = persistent ? localStorage : sessionStorage;
    
    try {
      storage.setItem(this.keys.USER_DATA, JSON.stringify(userData));
      
      // Limpiar del otro storage
      const otherStorage = persistent ? sessionStorage : localStorage;
      otherStorage.removeItem(this.keys.USER_DATA);
    } catch (error) {
      console.error('Error guardando datos de usuario:', error);
    }
  }

  /**
   * Obtiene los datos del usuario
   */
  getUserData() {
    const data = localStorage.getItem(this.keys.USER_DATA) ||
                 sessionStorage.getItem(this.keys.USER_DATA);
    
    if (!data) return null;

    try {
      return JSON.parse(data);
    } catch (error) {
      console.error('Error parseando datos de usuario:', error);
      return null;
    }
  }

  /**
   * Guarda las preferencias del usuario
   */
  savePreferences(preferences) {
    try {
      localStorage.setItem(this.keys.PREFERENCES, JSON.stringify(preferences));
    } catch (error) {
      console.error('Error guardando preferencias:', error);
    }
  }

  /**
   * Obtiene las preferencias del usuario
   */
  getPreferences() {
    const data = localStorage.getItem(this.keys.PREFERENCES);
    
    if (!data) return {};

    try {
      return JSON.parse(data);
    } catch (error) {
      console.error('Error parseando preferencias:', error);
      return {};
    }
  }

  /**
   * Verifica si el usuario eligió "recordarme"
   */
  isRememberMeActive() {
    return localStorage.getItem(this.keys.REMEMBER_ME) === 'true';
  }

  /**
   * Verifica si hay una sesión activa
   */
  hasActiveSession() {
    return !!this.getToken();
  }

  /**
   * Actualiza el token de acceso
   */
  updateAccessToken(newToken) {
    const storage = this.isRememberMeActive() ? localStorage : sessionStorage;
    storage.setItem(this.keys.ACCESS_TOKEN, newToken);
  }

  /**
   * Limpia todos los datos almacenados
   */
  clearAll() {
    // Limpiar de ambos storages
    this.clearTokensFromStorage(localStorage);
    this.clearTokensFromStorage(sessionStorage);
    
    // Limpiar datos de usuario
    localStorage.removeItem(this.keys.USER_DATA);
    sessionStorage.removeItem(this.keys.USER_DATA);
    
    // Limpiar remember me
    localStorage.removeItem(this.keys.REMEMBER_ME);
  }

  /**
   * Limpia solo los tokens (mantiene preferencias)
   */
  clearTokens() {
    this.clearTokensFromStorage(localStorage);
    this.clearTokensFromStorage(sessionStorage);
    localStorage.removeItem(this.keys.REMEMBER_ME);
  }

  /**
   * Limpia tokens de un storage específico
   */
  clearTokensFromStorage(storage) {
    storage.removeItem(this.keys.ACCESS_TOKEN);
    storage.removeItem(this.keys.REFRESH_TOKEN);
  }

  /**
   * Obtiene información del almacenamiento para debug
   */
  getStorageInfo() {
    return {
      hasAccessToken: !!this.getToken(),
      hasRefreshToken: !!this.getRefreshToken(),
      hasUserData: !!this.getUserData(),
      isRememberMe: this.isRememberMeActive(),
      storageUsed: this.isRememberMeActive() ? 'localStorage' : 'sessionStorage'
    };
  }
}

// Exportar instancia única
export const storage = new StorageManager();
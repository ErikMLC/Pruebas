/**
 * main.js - REDIRECCIÓN INMEDIATA (sin setTimeout que está fallando)
 */

import { auth } from './auth.js';
import { ui } from './ui.js';
import { storage } from './storage.js';
import { validation } from './validation.js';

class LoginApp {
  constructor() {
    this.form = null;
    this.isLoading = false;
    this.init();
  }

  init() {
    console.log('🚀 Iniciando aplicación de login...');
    this.checkExistingSession();
    this.setupDOM();
    this.setupEvents();
    console.log('✅ Login inicializado correctamente');
  }

  async checkExistingSession() {
    const token = storage.getToken();
    if (token) {
      const isValid = await auth.validateToken(token);
      if (isValid) {
        ui.showToast('Sesión válida, redirigiendo...', 'success');
        // REDIRECCIÓN INMEDIATA - SIN TIMEOUT
        this.executeRedirect();
        return;
      } else {
        storage.clearAll();
      }
    }
  }

  setupDOM() {
    this.form = document.getElementById('loginForm');
    this.emailInput = document.getElementById('email');
    this.passwordInput = document.getElementById('password');
    this.rememberCheckbox = document.getElementById('rememberMe');
    this.loginButton = document.getElementById('loginButton');
    this.passwordToggle = document.getElementById('passwordToggle');
  }

  setupEvents() {
    if (!this.form) return;

    this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    
    if (this.passwordToggle) {
      this.passwordToggle.addEventListener('click', () => this.togglePassword());
    }
    
    if (this.emailInput) {
      this.emailInput.addEventListener('blur', () => this.validateEmail());
      this.emailInput.addEventListener('input', () => ui.clearFieldError('email'));
    }
    
    if (this.passwordInput) {
      this.passwordInput.addEventListener('input', () => ui.clearFieldError('password'));
    }
    
    [this.emailInput, this.passwordInput].forEach(input => {
      if (input) {
        input.addEventListener('input', () => ui.hideGlobalError());
      }
    });
  }

  async handleSubmit(event) {
    event.preventDefault();
    
    if (this.isLoading) return;
    
    const formData = this.getFormData();
    ui.clearAllErrors();
    
    const validationResult = validation.validateLoginData(formData.email, formData.password);
    
    if (!validationResult.isValid) {
      Object.keys(validationResult.errors).forEach(field => {
        ui.showFieldError(field, validationResult.errors[field]);
      });
      return;
    }
    
    await this.performLogin(formData);
  }

  getFormData() {
    return {
      email: this.emailInput?.value.trim() || '',
      password: this.passwordInput?.value || '',
      rememberMe: this.rememberCheckbox?.checked || false
    };
  }

  async performLogin(data) {
    this.setLoadingState(true);
    ui.hideGlobalError();
    
    try {
      console.log('🔐 Ejecutando login...');
      const result = await auth.login(data.email, data.password);
      
      if (result.success) {
        console.log('✅ Login exitoso, guardando datos...');
        
        // Guardar datos
        await this.saveAuthData(result.data, data.rememberMe);
        
        // Verificar guardado
        const savedToken = storage.getToken();
        console.log('💾 Token guardado:', !!savedToken);
        
        // Mostrar éxito
        ui.showToast('¡Login exitoso! Redirigiendo...', 'success');
        
        console.log('🚀 EJECUTANDO REDIRECCIÓN INMEDIATA...');
        
        // ✅ REDIRECCIÓN INMEDIATA - SIN TIMEOUT
        this.executeRedirect();
        
      } else {
        console.error('❌ Login falló:', result.message);
        ui.showGlobalError(result.message || 'Error al iniciar sesión');
      }
      
    } catch (error) {
      console.error('💥 Error en login:', error);
      ui.showGlobalError('Error de conexión. Verifica tu internet.');
    } finally {
      this.setLoadingState(false);
    }
  }

  async saveAuthData(loginData, remember) {
    try {
      // Guardar usando storage.js
      storage.saveTokens(loginData.access_token, loginData.refresh_token, remember);
      storage.saveUserData(loginData.user, remember);
      
      // También guardar directamente para compatibilidad
      const targetStorage = remember ? localStorage : sessionStorage;
      targetStorage.setItem('access_token', loginData.access_token);
      targetStorage.setItem('refresh_token', loginData.refresh_token);
      targetStorage.setItem('user_data', JSON.stringify(loginData.user));
      
      console.log('✅ Datos guardados correctamente');
      
    } catch (error) {
      console.error('💥 Error guardando datos:', error);
      throw error;
    }
  }

  /**
   * 🚀 REDIRECCIÓN INMEDIATA Y MÚLTIPLE
   */
  executeRedirect() {
    console.log('🚀 === EJECUTANDO REDIRECCIÓN INMEDIATA ===');
    
    // Verificar token antes de redireccionar
    const token = storage.getToken();
    if (!token) {
      console.error('❌ CRÍTICO: No hay token para redireccionar');
      ui.showToast('Error: Sesión no guardada', 'error');
      return;
    }
    
    console.log('✅ Token verificado, procediendo con redirección...');
    
    try {
      // 🎯 MÉTODO 1: Redirección directa inmediata
      console.log('1️⃣ Intentando redirección directa...');
      window.location.href = 'dashboard.html';
      
      // 🎯 MÉTODO 2: Fallback inmediato con replace
      console.log('2️⃣ Ejecutando fallback con replace...');
      window.location.replace('dashboard.html');
      
      // 🎯 MÉTODO 3: Fallback con assign
      console.log('3️⃣ Ejecutando fallback con assign...');
      window.location.assign('dashboard.html');
      
      // 🎯 MÉTODO 4: Último fallback
      console.log('4️⃣ Último fallback...');
      window.location = 'dashboard.html';
      
    } catch (error) {
      console.error('💥 ERROR EN TODOS LOS MÉTODOS DE REDIRECCIÓN:', error);
      
      // 🆘 MÉTODO DE EMERGENCIA: Crear enlace manual
      this.createManualRedirectLink();
    }
  }

  /**
   * 🆘 Método de emergencia si la redirección falla
   */
  createManualRedirectLink() {
    console.log('🆘 Creando enlace manual de emergencia...');
    
    // Crear overlay con enlace manual
    const overlay = document.createElement('div');
    overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.9);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 999999;
      color: white;
      font-family: Arial, sans-serif;
    `;
    
    const userData = storage.getUserData();
    
    overlay.innerHTML = `
      <div style="text-align: center; padding: 40px; background: #1a1a1a; border-radius: 15px; max-width: 500px;">
        <h2 style="color: #4CAF50; margin-bottom: 20px;">
          🎉 ¡Login Exitoso!
        </h2>
        <p style="margin-bottom: 15px;">
          <strong>Usuario:</strong> ${userData?.username || 'Cargado'}
        </p>
        <p style="margin-bottom: 30px;">
          Tu sesión se guardó correctamente.
        </p>
        
        <div style="margin: 30px 0;">
          <h3 style="color: #ff9800; margin-bottom: 15px;">
            ⚠️ Redirección automática falló
          </h3>
          <p style="margin-bottom: 20px;">
            Haz clic en el botón para acceder al dashboard:
          </p>
        </div>
        
        <button 
          onclick="window.location.href='dashboard.html'" 
          style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 18px;
            border-radius: 8px;
            cursor: pointer;
            margin: 10px;
            width: 200px;
            display: block;
            margin: 10px auto;
          "
          onmouseover="this.style.opacity='0.9'"
          onmouseout="this.style.opacity='1'"
        >
          🚀 Ir al Dashboard
        </button>
        
        <div style="margin-top: 30px; font-size: 14px; color: #666;">
          <p>Si el botón no funciona, verifica que dashboard.html existe en tu proyecto.</p>
        </div>
      </div>
    `;
    
    document.body.appendChild(overlay);
    
    // También mostrar toast con instrucciones
    ui.showToast('Redirección manual creada. Haz clic en el botón.', 'info', 10000);
  }

  // Resto de métodos sin cambios...
  togglePassword() {
    if (!this.passwordInput || !this.passwordToggle) return;
    const isPassword = this.passwordInput.type === 'password';
    this.passwordInput.type = isPassword ? 'text' : 'password';
    const icon = this.passwordToggle.querySelector('i');
    if (icon) {
      icon.className = isPassword ? 'fas fa-eye-slash' : 'fas fa-eye';
    }
  }

  validateEmail() {
    if (!this.emailInput) return true;
    const email = this.emailInput.value.trim();
    if (email && !validation.validateEmail(email)) {
      ui.showFieldError('email', 'Formato de email inválido');
      return false;
    }
    ui.clearFieldError('email');
    return true;
  }

  setLoadingState(loading) {
    this.isLoading = loading;
    if (!this.loginButton) return;
    
    if (loading) {
      this.loginButton.classList.add('loading');
      this.loginButton.disabled = true;
      const buttonText = this.loginButton.querySelector('.button-text');
      const buttonLoader = this.loginButton.querySelector('.button-loader');
      if (buttonText) buttonText.style.display = 'none';
      if (buttonLoader) buttonLoader.style.display = 'flex';
    } else {
      this.loginButton.classList.remove('loading');
      this.loginButton.disabled = false;
      const buttonText = this.loginButton.querySelector('.button-text');
      const buttonLoader = this.loginButton.querySelector('.button-loader');
      if (buttonText) buttonText.style.display = 'inline';
      if (buttonLoader) buttonLoader.style.display = 'none';
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  console.log('🌟 DOM READY - INICIANDO LOGIN CON REDIRECCIÓN INMEDIATA');
  new LoginApp();
});
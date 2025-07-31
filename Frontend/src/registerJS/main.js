/**
 * main.js - Coordinador principal del registro
 * Inicializa módulos y maneja el flujo completo del formulario
 */

import { form } from './form.js';
import { password } from './password.js';
import { modal } from './modal.js';
import { api } from './api.js';

class RegisterApp {
  constructor() {
    this.isSubmitting = false;
    this.init();
  }

  /**
   * Inicializa la aplicación de registro
   */
  init() {
    console.log('🚀 Iniciando registro...');
    
    // Verificar si ya hay sesión activa
    this.checkExistingSession();
    
    // Inicializar módulos
    this.initModules();
    
    // Configurar eventos principales
    this.setupMainEvents();
    
    console.log('✅ Registro inicializado');
  }

  /**
   * Verifica sesión activa y redirige si es necesario
   */
  async checkExistingSession() {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    
    if (token) {
      try {
        const isValid = await api.validateToken(token);
        if (isValid) {
          form.showToast('Ya tienes una sesión activa', 'info');
          setTimeout(() => window.location.href = '/dashboard.html', 1500);
        }
      } catch (error) {
        // Token inválido, continuar con registro
        localStorage.removeItem('access_token');
        sessionStorage.removeItem('access_token');
      }
    }
  }

  /**
   * Inicializa todos los módulos
   */
  initModules() {
    form.init();
    password.init();
    modal.init();
  }

  /**
   * Configura eventos principales del formulario
   */
  setupMainEvents() {
    const registerForm = document.getElementById('registerForm');
    if (!registerForm) return;

    registerForm.addEventListener('submit', (e) => this.handleSubmit(e));
  }

  /**
   * Maneja el envío del formulario principal
   */
  async handleSubmit(event) {
    event.preventDefault();
    
    if (this.isSubmitting) return;

    // Obtener y validar datos
    const formData = this.getFormData();
    if (!this.validateAllFields(formData)) {
      return;
    }

    // Enviar registro
    await this.submitRegistration(formData);
  }

  /**
   * Obtiene todos los datos del formulario
   */
  getFormData() {
    return {
      fullName: document.getElementById('fullName').value.trim(),
      email: document.getElementById('email').value.trim(),
      password: document.getElementById('password').value,
      confirmPassword: document.getElementById('confirmPassword').value,
      acceptTerms: document.getElementById('acceptTerms').checked
    };
  }

  /**
   * Valida todos los campos del formulario
   */
  validateAllFields(data) {
    let isValid = true;

    // Validar campos individuales
    if (!form.validateField('fullName', data.fullName)) isValid = false;
    if (!form.validateField('email', data.email)) isValid = false;
    if (!password.validatePassword(data.password)) isValid = false;
    if (!password.validateConfirmation(data.password, data.confirmPassword)) isValid = false;

    // Validar términos
    if (!data.acceptTerms) {
      form.showGlobalError('Debes aceptar los términos y condiciones');
      isValid = false;
    }

    return isValid;
  }

  /**
   * Envía el registro al servidor
   */
  async submitRegistration(data) {
    this.setSubmittingState(true);
    form.hideGlobalError();

    try {
      const result = await api.register({
        username: data.fullName,
        email: data.email,
        password: data.password
      });

      if (result.success) {
        this.handleRegistrationSuccess();
      } else {
        form.showGlobalError(result.message || 'Error al crear la cuenta');
      }

    } catch (error) {
      console.error('Error en registro:', error);
      form.showGlobalError(error.message || 'Error de conexión');
    } finally {
      this.setSubmittingState(false);
    }
  }

  /**
   * Maneja el registro exitoso
   */
  handleRegistrationSuccess() {
    form.showGlobalSuccess('¡Cuenta creada exitosamente!');
    form.resetForm();
    password.resetPasswordMeter();
    
    form.showToast('Redirigiendo al login...', 'success');
    setTimeout(() => {
      window.location.href = '../../index.html';
    }, 2000);
  }

  /**
   * Controla el estado de envío del formulario
   */
  setSubmittingState(submitting) {
    this.isSubmitting = submitting;
    const button = document.getElementById('registerButton');
    
    if (!button) return;

    if (submitting) {
      button.classList.add('loading');
      button.disabled = true;
    } else {
      button.classList.remove('loading');
      button.disabled = false;
    }
  }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
  new RegisterApp();
});
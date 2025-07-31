/**
 * main.js - Coordinador principal del reset de contraseña
 * Maneja el flujo general y coordina todos los módulos
 */

import { steps } from './steps.js';
import { code } from './code.js';
import { password } from './password.js';
import { api } from './api.js';

class ResetApp {
  constructor() {
    this.currentStep = 1;
    this.userEmail = '';
    this.isProcessing = false;
    this.init();
  }

  /**
   * Inicializa la aplicación de reset
   */
  init() {
    console.log('🔄 Iniciando sistema de reset...');
    
    // Inicializar módulos
    this.initModules();
    
    // Configurar eventos principales
    this.setupMainEvents();
    
    // Mostrar paso inicial
    steps.showStep(1);
    
    console.log('✅ Reset inicializado correctamente');
  }

  /**
   * Inicializa todos los módulos
   */
  initModules() {
    steps.init();
    code.init();
    password.init();
  }

  /**
   * Configura eventos principales del reset
   */
  setupMainEvents() {
    // Evento para seleccionar método de recuperación
    this.setupRecoveryMethodSelection();
    
    // Evento para enviar código
    this.setupSendCodeButton();
    
    // Evento para verificar código
    this.setupVerifyCodeButton();
    
    // Evento para formulario de nueva contraseña
    this.setupPasswordForm();
    
    // Evento para ir al login
    this.setupGoToLoginButton();
  }

  /**
   * Configura selección de método de recuperación
   */
  setupRecoveryMethodSelection() {
    const recoveryOptions = document.querySelectorAll('.recovery-option:not(.disabled)');
    
    recoveryOptions.forEach(option => {
      option.addEventListener('click', () => {
        this.selectRecoveryMethod(option.dataset.method);
      });
    });
  }

  /**
   * Maneja selección de método de recuperación
   */
  selectRecoveryMethod(method) {
    if (method === 'email') {
      // Quitar selección previa
      document.querySelectorAll('.recovery-option').forEach(opt => {
        opt.classList.remove('selected');
      });
      
      // Seleccionar opción actual
      const selectedOption = document.querySelector(`[data-method="${method}"]`);
      selectedOption.classList.add('selected');
      
      // Mostrar sección de email
      const emailSection = document.getElementById('emailSection');
      emailSection.style.display = 'block';
      
      // Enfocar campo de email
      const emailInput = document.getElementById('recoveryEmail');
      emailInput.focus();
    }
  }

  /**
   * Configura botón de enviar código
   */
  setupSendCodeButton() {
    const sendButton = document.getElementById('sendCodeButton');
    if (sendButton) {
      sendButton.addEventListener('click', () => this.handleSendCode());
    }
  }

  /**
   * Maneja envío de código
   */
  async handleSendCode() {
    if (this.isProcessing) return;

    const emailInput = document.getElementById('recoveryEmail');
    const email = emailInput.value.trim();

    if (!this.validateEmail(email)) {
      this.showEmailError('Ingresa un email válido');
      return;
    }

    this.userEmail = email;
    this.setButtonLoading('sendCodeButton', true);

    try {
      const result = await api.forgotPassword(email);
      
      if (result.success) {
        // Mostrar email en paso 2
        document.getElementById('emailDisplay').textContent = email;
        
        // Avanzar al paso 2
        steps.goToStep(2);
        
        // Iniciar código
        code.startVerification();
        
        this.showToast('Código enviado a tu email', 'success');
      } else {
        this.showEmailError(result.message);
      }
    } catch (error) {
      this.showEmailError('Error de conexión. Intenta nuevamente.');
    } finally {
      this.setButtonLoading('sendCodeButton', false);
    }
  }

  /**
   * Configura botón de verificar código
   */
  setupVerifyCodeButton() {
    const verifyButton = document.getElementById('verifyCodeButton');
    if (verifyButton) {
      verifyButton.addEventListener('click', () => this.handleVerifyCode());
    }
  }

  /**
   * Maneja verificación de código
   */
  async handleVerifyCode() {
    if (this.isProcessing) return;

    const enteredCode = code.getCode();
    
    if (!enteredCode || enteredCode.length !== 6) {
      code.showError('Ingresa el código completo');
      return;
    }

    this.setButtonLoading('verifyCodeButton', true);

    try {
      const result = await api.verifyCode(this.userEmail, enteredCode);
      
      if (result.success) {
        steps.goToStep(3);
        password.focus();
        this.showToast('Código verificado correctamente', 'success');
      } else {
        code.showError(result.message);
        code.clearCode();
      }
    } catch (error) {
      code.showError('Error de conexión. Intenta nuevamente.');
    } finally {
      this.setButtonLoading('verifyCodeButton', false);
    }
  }

  /**
   * Configura formulario de nueva contraseña
   */
  setupPasswordForm() {
    const passwordForm = document.getElementById('newPasswordForm');
    if (passwordForm) {
      passwordForm.addEventListener('submit', (e) => this.handlePasswordSubmit(e));
    }
  }

  /**
   * Maneja envío de nueva contraseña
   */
  async handlePasswordSubmit(event) {
    event.preventDefault();
    
    if (this.isProcessing) return;

    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmNewPassword').value;

    if (!password.validatePasswords(newPassword, confirmPassword)) {
      return;
    }

    this.setButtonLoading('resetPasswordButton', true);

    try {
      const result = await api.resetPassword(this.userEmail, newPassword);
      
      if (result.success) {
        steps.goToStep(4);
        this.startAutoRedirect();
        this.showToast('¡Contraseña actualizada exitosamente!', 'success');
      } else {
        password.showError(result.message);
      }
    } catch (error) {
      password.showError('Error de conexión. Intenta nuevamente.');
    } finally {
      this.setButtonLoading('resetPasswordButton', false);
    }
  }

  /**
   * Configura botón para ir al login
   */
  setupGoToLoginButton() {
    const goToLoginButton = document.getElementById('goToLoginButton');
    if (goToLoginButton) {
      goToLoginButton.addEventListener('click', () => {
        window.location.href = '../../index.html';
      });
    }
  }

  /**
   * Inicia redirect automático
   */
  startAutoRedirect() {
    let countdown = 5;
    const countdownElement = document.getElementById('redirectCountdown');
    
    const timer = setInterval(() => {
      countdown--;
      if (countdownElement) {
        countdownElement.textContent = countdown;
      }
      
      if (countdown <= 0) {
        clearInterval(timer);
        window.location.href = '../../index.html';
      }
    }, 1000);
  }

  /**
   * Valida email
   */
  validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * Muestra error en campo de email
   */
  showEmailError(message) {
    const errorElement = document.getElementById('recoveryEmailError');
    const emailInput = document.getElementById('recoveryEmail');
    
    if (errorElement) {
      errorElement.textContent = message;
      errorElement.classList.add('show');
    }
    
    if (emailInput) {
      emailInput.classList.add('error');
    }
  }

  /**
   * Controla estado de carga de botones
   */
  setButtonLoading(buttonId, loading) {
    const button = document.getElementById(buttonId);
    if (!button) return;

    this.isProcessing = loading;

    if (loading) {
      button.classList.add('loading');
      button.disabled = true;
    } else {
      button.classList.remove('loading');
      button.disabled = false;
    }
  }

  /**
   * Muestra toast de notificación
   */
  showToast(message, type = 'info') {
    steps.showToast(message, type);
  }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
  new ResetApp();
});
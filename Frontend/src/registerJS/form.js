/**
 * form.js - Manejo específico del formulario de registro
 * Validaciones, errores UI, toasts y estado de campos
 */

class RegisterFormManager {
  constructor() {
    this.toastContainer = null;
  }

  /**
   * Inicializa el manejo del formulario
   */
  init() {
    this.createToastContainer();
    this.setupFieldValidation();
  }

  /**
   * Configura validación en tiempo real de campos
   */
  setupFieldValidation() {
    const fields = ['fullName', 'email'];
    
    fields.forEach(fieldId => {
      const field = document.getElementById(fieldId);
      if (field) {
        field.addEventListener('blur', () => this.validateFieldOnBlur(fieldId));
        field.addEventListener('input', () => this.clearFieldError(fieldId));
      }
    });
  }

  /**
   * Valida un campo específico
   */
  validateField(fieldId, value) {
    switch (fieldId) {
      case 'fullName':
        return this.validateFullName(value);
      case 'email':
        return this.validateEmail(value);
      default:
        return true;
    }
  }

  /**
   * Valida nombre completo
   */
  validateFullName(name) {
    if (!name || name.length < 2) {
      this.showFieldError('fullName', 'El nombre debe tener al menos 2 caracteres');
      return false;
    }
    
    if (name.length > 50) {
      this.showFieldError('fullName', 'El nombre no puede exceder 50 caracteres');
      return false;
    }

    this.clearFieldError('fullName');
    return true;
  }

  /**
   * Valida email
   */
  validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (!email) {
      this.showFieldError('email', 'El email es requerido');
      return false;
    }
    
    if (!emailRegex.test(email)) {
      this.showFieldError('email', 'Formato de email inválido');
      return false;
    }

    this.clearFieldError('email');
    return true;
  }

  /**
   * Valida campo cuando pierde el foco
   */
  validateFieldOnBlur(fieldId) {
    const field = document.getElementById(fieldId);
    if (field && field.value.trim()) {
      this.validateField(fieldId, field.value.trim());
    }
  }

  /**
   * Muestra error en un campo específico
   */
  showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorElement = document.getElementById(`${fieldId}Error`);

    if (field) {
      field.classList.add('error');
      field.classList.remove('success');
    }

    if (errorElement) {
      errorElement.textContent = message;
      errorElement.classList.add('show');
    }
  }

  /**
   * Limpia error de un campo
   */
  clearFieldError(fieldId) {
    const field = document.getElementById(fieldId);
    const errorElement = document.getElementById(`${fieldId}Error`);

    if (field) {
      field.classList.remove('error');
    }

    if (errorElement) {
      errorElement.textContent = '';
      errorElement.classList.remove('show');
    }
  }

  /**
   * Muestra mensaje de error global
   */
  showGlobalError(message) {
    const errorElement = document.getElementById('globalError');
    const messageElement = document.getElementById('globalErrorMessage');

    if (errorElement && messageElement) {
      messageElement.textContent = message;
      errorElement.classList.add('show');
    }
  }

  /**
   * Oculta mensaje de error global
   */
  hideGlobalError() {
    const errorElement = document.getElementById('globalError');
    if (errorElement) {
      errorElement.classList.remove('show');
    }
  }

  /**
   * Muestra mensaje de éxito global
   */
  showGlobalSuccess(message) {
    const successElement = document.getElementById('globalSuccess');
    const messageElement = document.getElementById('globalSuccessMessage');

    this.hideGlobalError();

    if (successElement && messageElement) {
      messageElement.textContent = message;
      successElement.classList.add('show');
    }
  }

  /**
   * Crea contenedor de toasts
   */
  createToastContainer() {
    if (!this.toastContainer) {
      this.toastContainer = document.createElement('div');
      this.toastContainer.className = 'toast-container';
      this.toastContainer.id = 'toastContainer';
      document.body.appendChild(this.toastContainer);
    }
  }

  /**
   * Muestra un toast de notificación
   */
  showToast(message, type = 'success', duration = 4000) {
    const toast = this.createToast(message, type);
    this.toastContainer.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 100);

    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => {
        if (toast.parentNode) {
          this.toastContainer.removeChild(toast);
        }
      }, 300);
    }, duration);
  }

  /**
   * Crea elemento toast
   */
  createToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
      success: 'fas fa-check-circle',
      error: 'fas fa-times-circle',
      info: 'fas fa-info-circle',
      warning: 'fas fa-exclamation-triangle'
    };

    toast.innerHTML = `
      <i class="${icons[type] || icons.info}"></i>
      <span>${message}</span>
    `;

    return toast;
  }

  /**
   * Resetea el formulario completo
   */
  resetForm() {
    const form = document.getElementById('registerForm');
    if (form) {
      form.reset();
      this.clearAllErrors();
    }
  }

  /**
   * Limpia todos los errores del formulario
   */
  clearAllErrors() {
    const errorElements = document.querySelectorAll('.error-message.show');
    errorElements.forEach(element => {
      element.classList.remove('show');
      element.textContent = '';
    });

    const errorFields = document.querySelectorAll('input.error');
    errorFields.forEach(field => {
      field.classList.remove('error');
    });

    this.hideGlobalError();
  }
}

// Exportar instancia única
export const form = new RegisterFormManager();
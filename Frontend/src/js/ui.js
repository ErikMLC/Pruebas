/**
 * ui.js - Módulo de gestión de interfaz de usuario
 * Maneja toasts, errores, estados visuales y elementos UI
 */

class UIManager {
  constructor() {
    this.toastContainer = this.getOrCreateToastContainer();
  }

  /**
   * Muestra un toast de notificación
   */
  showToast(message, type = 'success', duration = 5000) {
    const toast = this.createToast(message, type);
    this.toastContainer.appendChild(toast);

    // Mostrar toast con animación
    setTimeout(() => toast.classList.add('show'), 100);

    // Ocultar y remover toast
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => {
        if (toast.parentNode) {
          this.toastContainer.removeChild(toast);
        }
      }, 300);
    }, duration);

    return toast;
  }

  /**
   * Crea un elemento toast
   */
  createToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
      success: 'fas fa-check-circle',
      error: 'fas fa-times-circle',
      warning: 'fas fa-exclamation-triangle',
      info: 'fas fa-info-circle'
    };

    toast.innerHTML = `
      <i class="${icons[type] || icons.info}"></i>
      <span>${message}</span>
    `;

    return toast;
  }

  /**
   * Obtiene o crea el contenedor de toasts
   */
  getOrCreateToastContainer() {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  /**
   * Muestra un error en un campo específico
   */
  showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorElement = document.getElementById(`${fieldId}Error`);

    if (field) {
      field.classList.add('error');
    }

    if (errorElement) {
      errorElement.textContent = message;
      errorElement.classList.add('show');
    }
  }

  /**
   * Limpia el error de un campo específico
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
   * Muestra un mensaje de error global
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
   * Oculta el mensaje de error global
   */
  hideGlobalError() {
    const errorElement = document.getElementById('globalError');
    if (errorElement) {
      errorElement.classList.remove('show');
    }
  }

  /**
   * Limpia todos los errores de formulario
   */
  clearAllErrors() {
    // Limpiar errores de campos
    const errorElements = document.querySelectorAll('.error-message.show');
    errorElements.forEach(element => {
      element.classList.remove('show');
      element.textContent = '';
    });

    // Limpiar clases de error en campos
    const errorFields = document.querySelectorAll('.form-group input.error');
    errorFields.forEach(field => {
      field.classList.remove('error');
    });

    // Ocultar error global
    this.hideGlobalError();
  }

  /**
   * Habilita o deshabilita un elemento
   */
  toggleElement(elementId, enable = true) {
    const element = document.getElementById(elementId);
    if (element) {
      element.disabled = !enable;
      
      if (enable) {
        element.classList.remove('disabled');
      } else {
        element.classList.add('disabled');
      }
    }
  }

  /**
   * Muestra u oculta un elemento
   */
  toggleVisibility(elementId, show = true) {
    const element = document.getElementById(elementId);
    if (element) {
      element.style.display = show ? 'block' : 'none';
    }
  }

  /**
   * Añade una clase CSS a un elemento
   */
  addClass(elementId, className) {
    const element = document.getElementById(elementId);
    if (element) {
      element.classList.add(className);
    }
  }

  /**
   * Remueve una clase CSS de un elemento
   */
  removeClass(elementId, className) {
    const element = document.getElementById(elementId);
    if (element) {
      element.classList.remove(className);
    }
  }
}

// Exportar instancia única
export const ui = new UIManager();
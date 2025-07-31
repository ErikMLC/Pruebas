/**
 * steps.js - Manejo de transiciones entre pasos del reset
 * Controla navegación, progreso visual y animaciones
 */

class StepsManager {
  constructor() {
    this.currentStep = 1;
    this.totalSteps = 4;
    this.toastContainer = null;
  }

  /**
   * Inicializa el manejo de pasos
   */
  init() {
    this.createToastContainer();
    this.updateProgressIndicator();
  }

  /**
   * Muestra un paso específico
   */
  showStep(stepNumber) {
    if (stepNumber < 1 || stepNumber > this.totalSteps) return;

    // Ocultar todos los pasos
    this.hideAllSteps();

    // Mostrar paso actual
    const stepElement = document.getElementById(`step${stepNumber}`);
    if (stepElement) {
      stepElement.classList.add('active');
      this.currentStep = stepNumber;
      this.updateProgressIndicator();
    }
  }

  /**
   * Avanza al siguiente paso
   */
  goToStep(stepNumber) {
    if (stepNumber <= this.currentStep) return;

    // Marcar pasos anteriores como completados
    for (let i = 1; i < stepNumber; i++) {
      this.markStepCompleted(i);
    }

    // Mostrar nuevo paso
    this.showStep(stepNumber);

    // Animación de transición
    this.animateStepTransition(stepNumber);
  }

  /**
   * Oculta todos los pasos
   */
  hideAllSteps() {
    for (let i = 1; i <= this.totalSteps; i++) {
      const step = document.getElementById(`step${i}`);
      if (step) {
        step.classList.remove('active');
      }
    }
  }

  /**
   * Actualiza el indicador de progreso
   */
  updateProgressIndicator() {
    for (let i = 1; i <= this.totalSteps; i++) {
      const progressStep = document.querySelector(`[data-step="${i}"]`);
      if (!progressStep) continue;

      // Limpiar clases previas
      progressStep.classList.remove('active', 'completed');

      if (i < this.currentStep) {
        // Pasos completados
        progressStep.classList.add('completed');
      } else if (i === this.currentStep) {
        // Paso actual
        progressStep.classList.add('active');
      }
      // Los pasos futuros quedan sin clase (inactive)
    }

    // Actualizar líneas de progreso
    this.updateProgressLines();
  }

  /**
   * Actualiza las líneas de conexión del progreso
   */
  updateProgressLines() {
    const progressLines = document.querySelectorAll('.progress-line');
    
    progressLines.forEach((line, index) => {
      const stepNumber = index + 1; // Las líneas están entre pasos
      
      if (stepNumber < this.currentStep) {
        line.classList.add('completed');
      } else {
        line.classList.remove('completed');
      }
    });
  }

  /**
   * Marca un paso como completado
   */
  markStepCompleted(stepNumber) {
    const progressStep = document.querySelector(`[data-step="${stepNumber}"]`);
    if (progressStep) {
      progressStep.classList.remove('active');
      progressStep.classList.add('completed');
    }
  }

  /**
   * Anima la transición entre pasos
   */
  animateStepTransition(toStep) {
    const stepElement = document.getElementById(`step${toStep}`);
    if (!stepElement) return;

    // Remover animación previa si existe
    stepElement.classList.remove('fade-in');

    // Forzar reflow para reiniciar animación
    stepElement.offsetHeight;

    // Agregar animación
    stepElement.classList.add('fade-in');
  }

  /**
   * Retrocede al paso anterior
   */
  goToPreviousStep() {
    if (this.currentStep > 1) {
      this.showStep(this.currentStep - 1);
    }
  }

  /**
   * Verifica si se puede avanzar al siguiente paso
   */
  canAdvanceToStep(stepNumber) {
    // Validaciones específicas por paso
    switch (stepNumber) {
      case 2:
        // Debe haber seleccionado método y email válido
        return this.validateStep1();
      case 3:
        // Debe haber verificado código
        return this.validateStep2();
      case 4:
        // Debe haber ingresado nueva contraseña
        return this.validateStep3();
      default:
        return true;
    }
  }

  /**
   * Valida paso 1: selección de método y email
   */
  validateStep1() {
    const selectedMethod = document.querySelector('.recovery-option.selected');
    const emailInput = document.getElementById('recoveryEmail');
    
    return selectedMethod && emailInput && emailInput.value.trim();
  }

  /**
   * Valida paso 2: código ingresado
   */
  validateStep2() {
    const codeInputs = document.querySelectorAll('.code-digit');
    return Array.from(codeInputs).every(input => input.value.trim());
  }

  /**
   * Valida paso 3: nueva contraseña
   */
  validateStep3() {
    const newPassword = document.getElementById('newPassword');
    const confirmPassword = document.getElementById('confirmNewPassword');
    
    return newPassword && confirmPassword && 
           newPassword.value && confirmPassword.value &&
           newPassword.value === confirmPassword.value;
  }

  /**
   * Obtiene el número del paso actual
   */
  getCurrentStep() {
    return this.currentStep;
  }

  /**
   * Reinicia el flujo al paso 1
   */
  resetToStep1() {
    this.currentStep = 1;
    this.showStep(1);
    this.clearAllData();
  }

  /**
   * Limpia todos los datos ingresados
   */
  clearAllData() {
    // Limpiar selección de método
    document.querySelectorAll('.recovery-option').forEach(option => {
      option.classList.remove('selected');
    });

    // Ocultar sección de email
    const emailSection = document.getElementById('emailSection');
    if (emailSection) {
      emailSection.style.display = 'none';
    }

    // Limpiar campos
    const emailInput = document.getElementById('recoveryEmail');
    if (emailInput) {
      emailInput.value = '';
      emailInput.classList.remove('error');
    }

    // Limpiar código
    document.querySelectorAll('.code-digit').forEach(input => {
      input.value = '';
      input.classList.remove('filled', 'error');
    });

    // Limpiar contraseñas
    const passwordInputs = ['newPassword', 'confirmNewPassword'];
    passwordInputs.forEach(id => {
      const input = document.getElementById(id);
      if (input) {
        input.value = '';
        input.classList.remove('error', 'success');
      }
    });
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
  showToast(message, type = 'info', duration = 4000) {
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
}

// Exportar instancia única
export const steps = new StepsManager();
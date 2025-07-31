/**
 * code.js - Manejo del input de código de 6 dígitos
 * Controla navegación automática, validación y reenvío
 */

class CodeManager {
  constructor() {
    this.codeInputs = [];
    this.resendTimer = null;
    this.resendCountdown = 60;
    this.maxResendAttempts = 3;
    this.currentResendAttempts = 0;
  }

  /**
   * Inicializa el manejo del código
   */
  init() {
    this.setupCodeInputs();
    this.setupResendButton();
  }

  /**
   * Configura los inputs de código
   */
  setupCodeInputs() {
    this.codeInputs = document.querySelectorAll('.code-digit');
    
    this.codeInputs.forEach((input, index) => {
      this.setupSingleInput(input, index);
    });
  }

  /**
   * Configura un input individual
   */
  setupSingleInput(input, index) {
    // Evento de entrada
    input.addEventListener('input', (e) => this.handleInput(e, index));
    
    // Evento de tecla presionada
    input.addEventListener('keydown', (e) => this.handleKeydown(e, index));
    
    // Evento de pegado
    input.addEventListener('paste', (e) => this.handlePaste(e));
    
    // Evento de foco
    input.addEventListener('focus', () => input.select());
  }

  /**
   * Maneja entrada de dígito
   */
  handleInput(event, index) {
    const input = event.target;
    let value = input.value;

    // Solo permitir números
    value = value.replace(/[^0-9]/g, '');
    
    // Limitar a 1 dígito
    if (value.length > 1) {
      value = value.slice(0, 1);
    }

    input.value = value;

    // Actualizar estado visual
    if (value) {
      input.classList.add('filled');
      input.classList.remove('error');
      
      // Avanzar al siguiente input
      this.focusNextInput(index);
    } else {
      input.classList.remove('filled');
    }

    // Verificar si el código está completo
    this.checkCodeComplete();
  }

  /**
   * Maneja teclas especiales
   */
  handleKeydown(event, index) {
    const input = event.target;

    // Backspace
    if (event.key === 'Backspace') {
      if (!input.value && index > 0) {
        // Si el input está vacío, ir al anterior
        this.focusPreviousInput(index);
      } else {
        // Limpiar input actual
        input.value = '';
        input.classList.remove('filled', 'error');
      }
    }
    
    // Arrow keys
    else if (event.key === 'ArrowLeft' && index > 0) {
      this.focusPreviousInput(index);
    }
    else if (event.key === 'ArrowRight' && index < this.codeInputs.length - 1) {
      this.focusNextInput(index);
    }
    
    // Enter para verificar código
    else if (event.key === 'Enter') {
      const verifyButton = document.getElementById('verifyCodeButton');
      if (verifyButton && !verifyButton.disabled) {
        verifyButton.click();
      }
    }
  }

  /**
   * Maneja pegado de código completo
   */
  handlePaste(event) {
    event.preventDefault();
    
    const pastedText = (event.clipboardData || window.clipboardData).getData('text');
    const cleanCode = pastedText.replace(/[^0-9]/g, '').slice(0, 6);
    
    if (cleanCode.length >= 6) {
      // Llenar todos los inputs
      this.fillCode(cleanCode);
    }
  }

  /**
   * Llena el código completo
   */
  fillCode(code) {
    for (let i = 0; i < 6 && i < code.length; i++) {
      if (this.codeInputs[i]) {
        this.codeInputs[i].value = code[i];
        this.codeInputs[i].classList.add('filled');
        this.codeInputs[i].classList.remove('error');
      }
    }
    
    // Enfocar último input o el siguiente vacío
    const lastFilledIndex = Math.min(code.length - 1, 5);
    if (this.codeInputs[lastFilledIndex]) {
      this.codeInputs[lastFilledIndex].focus();
    }
    
    this.checkCodeComplete();
  }

  /**
   * Enfoca el siguiente input
   */
  focusNextInput(currentIndex) {
    if (currentIndex < this.codeInputs.length - 1) {
      this.codeInputs[currentIndex + 1].focus();
    }
  }

  /**
   * Enfoca el input anterior
   */
  focusPreviousInput(currentIndex) {
    if (currentIndex > 0) {
      this.codeInputs[currentIndex - 1].focus();
    }
  }

  /**
   * Verifica si el código está completo
   */
  checkCodeComplete() {
    const code = this.getCode();
    const verifyButton = document.getElementById('verifyCodeButton');
    
    if (verifyButton) {
      verifyButton.disabled = code.length !== 6;
    }
  }

  /**
   * Obtiene el código completo
   */
  getCode() {
    return Array.from(this.codeInputs)
      .map(input => input.value)
      .join('');
  }

  /**
   * Limpia todos los inputs de código
   */
  clearCode() {
    this.codeInputs.forEach(input => {
      input.value = '';
      input.classList.remove('filled', 'error');
    });
    
    // Enfocar primer input
    if (this.codeInputs[0]) {
      this.codeInputs[0].focus();
    }
    
    this.checkCodeComplete();
  }

  /**
   * Muestra error en los inputs de código
   */
  showError(message) {
    this.codeInputs.forEach(input => {
      input.classList.add('error');
    });
    
    // Mostrar mensaje si hay elemento para ello
    const errorElement = document.getElementById('codeError');
    if (errorElement) {
      errorElement.textContent = message;
      errorElement.style.display = 'block';
    }
    
    // Animar error
    this.animateError();
  }

  /**
   * Anima error de código
   */
  animateError() {
    const container = document.querySelector('.code-input-container');
    if (container) {
      container.classList.add('shake');
      setTimeout(() => {
        container.classList.remove('shake');
      }, 500);
    }
  }

  /**
   * Configura botón de reenvío
   */
  setupResendButton() {
    const resendButton = document.getElementById('resendCodeButton');
    if (resendButton) {
      resendButton.addEventListener('click', () => this.handleResendCode());
    }
  }

  /**
   * Inicia verificación (cuando se muestra el paso 2)
   */
  startVerification() {
    // Limpiar código anterior
    this.clearCode();
    
    // Enfocar primer input
    if (this.codeInputs[0]) {
      setTimeout(() => this.codeInputs[0].focus(), 300);
    }
    
    // Iniciar timer de reenvío
    this.startResendTimer();
  }

  /**
   * Inicia timer de reenvío
   */
  startResendTimer() {
    const resendButton = document.getElementById('resendCodeButton');
    const countdownElement = document.getElementById('countdown');
    const timerElement = document.getElementById('countdownTimer');
    
    if (!resendButton || !countdownElement || !timerElement) return;

    // Deshabilitar botón
    resendButton.disabled = true;
    resendButton.style.display = 'none';
    timerElement.style.display = 'block';
    
    this.resendCountdown = 60;
    
    this.resendTimer = setInterval(() => {
      this.resendCountdown--;
      countdownElement.textContent = this.resendCountdown;
      
      if (this.resendCountdown <= 0) {
        this.stopResendTimer();
      }
    }, 1000);
  }

  /**
   * Detiene timer de reenvío
   */
  stopResendTimer() {
    if (this.resendTimer) {
      clearInterval(this.resendTimer);
      this.resendTimer = null;
    }
    
    const resendButton = document.getElementById('resendCodeButton');
    const timerElement = document.getElementById('countdownTimer');
    
    if (resendButton && timerElement) {
      resendButton.disabled = false;
      resendButton.style.display = 'inline-flex';
      timerElement.style.display = 'none';
    }
  }

  /**
   * Maneja reenvío de código
   */
  async handleResendCode() {
    if (this.currentResendAttempts >= this.maxResendAttempts) {
      this.showError('Demasiados intentos de reenvío. Intenta más tarde.');
      return;
    }
    
    this.currentResendAttempts++;
    
    // Aquí se llamaría a la API para reenviar
    // Por ahora solo simulamos el reenvío
    this.startResendTimer();
    
    // Limpiar código actual
    this.clearCode();
    
    // Mostrar feedback
    const toast = document.createElement('div');
    toast.className = 'toast success show';
    toast.innerHTML = `
      <i class="fas fa-check-circle"></i>
      <span>Código reenviado a tu email</span>
    `;
    
    const container = document.getElementById('toastContainer');
    if (container) {
      container.appendChild(toast);
      setTimeout(() => {
        if (toast.parentNode) {
          container.removeChild(toast);
        }
      }, 3000);
    }
  }
}

// Exportar instancia única
export const code = new CodeManager();
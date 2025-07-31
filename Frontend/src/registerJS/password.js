/**
 * password.js - Medidor de fortaleza y confirmación de contraseña
 * Maneja validación, medidor visual y toggle de visibilidad
 */

class PasswordManager {
  constructor() {
    this.passwordField = null;
    this.confirmField = null;
    this.strengthMeter = null;
    this.strengthText = null;
  }

  /**
   * Inicializa el manejo de contraseñas
   */
  init() {
    this.setupElements();
    this.setupEvents();
  }

  /**
   * Configura elementos del DOM
   */
  setupElements() {
    this.passwordField = document.getElementById('password');
    this.confirmField = document.getElementById('confirmPassword');
    this.strengthMeter = document.getElementById('strengthFill');
    this.strengthText = document.getElementById('strengthText');
  }

  /**
   * Configura eventos de contraseña
   */
  setupEvents() {
    // Eventos de entrada de contraseña
    if (this.passwordField) {
      this.passwordField.addEventListener('input', () => this.handlePasswordInput());
    }

    if (this.confirmField) {
      this.confirmField.addEventListener('input', () => this.handleConfirmInput());
    }

    // Toggles de visibilidad
    this.setupPasswordToggles();
  }

  /**
   * Configura botones de toggle de contraseña
   */
  setupPasswordToggles() {
    const passwordToggle = document.getElementById('passwordToggle');
    const confirmToggle = document.getElementById('confirmPasswordToggle');

    if (passwordToggle) {
      passwordToggle.addEventListener('click', () => this.toggleVisibility('password'));
    }

    if (confirmToggle) {
      confirmToggle.addEventListener('click', () => this.toggleVisibility('confirmPassword'));
    }
  }

  /**
   * Maneja entrada en campo de contraseña
   */
  handlePasswordInput() {
    const password = this.passwordField.value;
    
    // Actualizar medidor de fortaleza
    this.updateStrengthMeter(password);
    
    // Limpiar error de contraseña
    this.clearPasswordError();
    
    // Revalidar confirmación si ya tiene contenido
    if (this.confirmField && this.confirmField.value) {
      this.validateConfirmation(password, this.confirmField.value);
    }
  }

  /**
   * Maneja entrada en campo de confirmación
   */
  handleConfirmInput() {
    const password = this.passwordField.value;
    const confirm = this.confirmField.value;
    
    this.validateConfirmation(password, confirm);
  }

  /**
   * Actualiza el medidor de fortaleza visual
   */
  updateStrengthMeter(password) {
    if (!this.strengthMeter || !this.strengthText) return;

    const strength = this.calculateStrength(password);
    
    // Limpiar clases previas
    this.strengthMeter.className = 'strength-fill';
    this.strengthText.className = 'strength-text';

    if (!password) {
      this.strengthText.textContent = 'Ingresa una contraseña';
      return;
    }

    // Aplicar clase y texto según fortaleza
    this.strengthMeter.classList.add(strength.level);
    this.strengthText.classList.add(strength.level);
    this.strengthText.textContent = strength.text;
  }

  /**
   * Calcula la fortaleza de la contraseña
   */
  calculateStrength(password) {
    if (!password) return { level: 'weak', text: 'Ingresa una contraseña', score: 0 };

    let score = 0;

    // Criterios de fortaleza
    if (password.length >= 6) score++;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[a-z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;

    // Determinar nivel
    if (score < 3) {
      return { level: 'weak', text: 'Contraseña débil', score };
    } else if (score < 5) {
      return { level: 'medium', text: 'Contraseña media', score };
    } else {
      return { level: 'strong', text: 'Contraseña fuerte', score };
    }
  }

  /**
   * Valida la contraseña principal
   */
  validatePassword(password) {
    if (!password) {
      this.showPasswordError('La contraseña es requerida');
      return false;
    }

    if (password.length < 6) {
      this.showPasswordError('La contraseña debe tener al menos 6 caracteres');
      return false;
    }

    const strength = this.calculateStrength(password);
    if (strength.score < 2) {
      this.showPasswordError('La contraseña es muy débil');
      return false;
    }

    this.clearPasswordError();
    return true;
  }

  /**
   * Valida la confirmación de contraseña
   */
  validateConfirmation(password, confirmPassword) {
    if (!confirmPassword) {
      this.showConfirmError('Confirma tu contraseña');
      return false;
    }

    if (password !== confirmPassword) {
      this.showConfirmError('Las contraseñas no coinciden');
      return false;
    }

    this.clearConfirmError();
    return true;
  }

  /**
   * Alterna la visibilidad de las contraseñas
   */
  toggleVisibility(fieldType) {
    const field = fieldType === 'password' ? this.passwordField : this.confirmField;
    const toggleId = fieldType === 'password' ? 'passwordToggle' : 'confirmPasswordToggle';
    const toggle = document.getElementById(toggleId);

    if (!field || !toggle) return;

    const isPassword = field.type === 'password';
    field.type = isPassword ? 'text' : 'password';

    const icon = toggle.querySelector('i');
    if (icon) {
      icon.className = isPassword ? 'fas fa-eye-slash' : 'fas fa-eye';
    }
  }

  /**
   * Muestra error en campo de contraseña
   */
  showPasswordError(message) {
    const errorElement = document.getElementById('passwordError');
    const field = this.passwordField;

    if (field) field.classList.add('error');
    if (errorElement) {
      errorElement.textContent = message;
      errorElement.classList.add('show');
    }
  }

  /**
   * Limpia error de contraseña
   */
  clearPasswordError() {
    const errorElement = document.getElementById('passwordError');
    const field = this.passwordField;

    if (field) field.classList.remove('error');
    if (errorElement) {
      errorElement.textContent = '';
      errorElement.classList.remove('show');
    }
  }

  /**
   * Muestra error en confirmación
   */
  showConfirmError(message) {
    const errorElement = document.getElementById('confirmPasswordError');
    const field = this.confirmField;

    if (field) field.classList.add('error');
    if (errorElement) {
      errorElement.textContent = message;
      errorElement.classList.add('show');
    }
  }

  /**
   * Limpia error de confirmación
   */
  clearConfirmError() {
    const errorElement = document.getElementById('confirmPasswordError');
    const field = this.confirmField;

    if (field) field.classList.remove('error');
    if (errorElement) {
      errorElement.textContent = '';
      errorElement.classList.remove('show');
    }
  }

  /**
   * Resetea el medidor de contraseña
   */
  resetPasswordMeter() {
    if (this.strengthMeter) {
      this.strengthMeter.className = 'strength-fill';
    }
    if (this.strengthText) {
      this.strengthText.className = 'strength-text';
      this.strengthText.textContent = 'Ingresa una contraseña';
    }
  }
}

// Exportar instancia única
export const password = new PasswordManager();
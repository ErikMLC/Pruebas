/**
 * password.js - Medidor de fortaleza y validación de nueva contraseña
 * Maneja validación, medidor visual y confirmación de contraseña
 */

class ResetPasswordManager {
  constructor() {
    this.newPasswordField = null;
    this.confirmPasswordField = null;
    this.strengthMeter = null;
    this.strengthText = null;
    this.currentStrength = 0;
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
    this.newPasswordField = document.getElementById('newPassword');
    this.confirmPasswordField = document.getElementById('confirmNewPassword');
    this.strengthMeter = document.getElementById('strengthFill');
    this.strengthText = document.getElementById('strengthText');
  }

  /**
   * Configura eventos de contraseña
   */
  setupEvents() {
    // Eventos de entrada de contraseña
    if (this.newPasswordField) {
      this.newPasswordField.addEventListener('input', () => this.handlePasswordInput());
    }

    if (this.confirmPasswordField) {
      this.confirmPasswordField.addEventListener('input', () => this.handleConfirmInput());
    }

    // Toggles de visibilidad
    this.setupPasswordToggles();
  }

  /**
   * Configura botones de toggle de contraseña
   */
  setupPasswordToggles() {
    const newPasswordToggle = document.getElementById('newPasswordToggle');
    const confirmToggle = document.getElementById('confirmPasswordToggle');

    if (newPasswordToggle) {
      newPasswordToggle.addEventListener('click', () => this.toggleVisibility('newPassword'));
    }

    if (confirmToggle) {
      confirmToggle.addEventListener('click', () => this.toggleVisibility('confirmNewPassword'));
    }
  }

  /**
   * Maneja entrada en campo de nueva contraseña
   */
  handlePasswordInput() {
    const password = this.newPasswordField.value;
    
    // Actualizar medidor de fortaleza
    this.updateStrengthMeter(password);
    
    // Limpiar error de contraseña
    this.clearPasswordError();
    
    // Revalidar confirmación si ya tiene contenido
    if (this.confirmPasswordField && this.confirmPasswordField.value) {
      this.validateConfirmation();
    }
  }

  /**
   * Maneja entrada en campo de confirmación
   */
  handleConfirmInput() {
    this.validateConfirmation();
  }

  /**
   * Actualiza el medidor de fortaleza visual
   */
  updateStrengthMeter(password) {
    if (!this.strengthMeter || !this.strengthText) return;

    const strength = this.calculateStrength(password);
    this.currentStrength = strength.score;
    
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
    const checks = {
      length: password.length >= 8,
      minLength: password.length >= 6,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[^A-Za-z0-9]/.test(password)
    };

    // Puntuación detallada
    if (checks.minLength) score++;
    if (checks.length) score++;
    if (checks.uppercase) score++;
    if (checks.lowercase) score++;
    if (checks.number) score++;
    if (checks.special) score++;

    // Determinar nivel y mensaje
    if (score < 3) {
      return { 
        level: 'weak', 
        text: 'Contraseña muy débil',
        score,
        requirements: this.getMissingRequirements(checks)
      };
    } else if (score < 5) {
      return { 
        level: 'medium', 
        text: 'Contraseña moderada',
        score,
        requirements: this.getMissingRequirements(checks)
      };
    } else {
      return { 
        level: 'strong', 
        text: 'Contraseña fuerte',
        score,
        requirements: []
      };
    }
  }

  /**
   * Obtiene requisitos faltantes
   */
  getMissingRequirements(checks) {
    const missing = [];
    
    if (!checks.minLength) missing.push('Al menos 6 caracteres');
    if (!checks.uppercase) missing.push('Una mayúscula');
    if (!checks.lowercase) missing.push('Una minúscula');
    if (!checks.number) missing.push('Un número');
    
    return missing;
  }

  /**
   * Valida la nueva contraseña
   */
  validateNewPassword(password) {
    if (!password) {
      this.showPasswordError('La nueva contraseña es requerida');
      return false;
    }

    if (password.length < 6) {
      this.showPasswordError('La contraseña debe tener al menos 6 caracteres');
      return false;
    }

    const strength = this.calculateStrength(password);
    if (strength.score < 2) {
      this.showPasswordError('La contraseña es muy débil. ' + strength.requirements[0]);
      return false;
    }

    this.clearPasswordError();
    this.markFieldSuccess('newPassword');
    return true;
  }

  /**
   * Valida la confirmación de contraseña
   */
  validateConfirmation() {
    const newPassword = this.newPasswordField.value;
    const confirmPassword = this.confirmPasswordField.value;

    if (!confirmPassword) {
      this.showConfirmError('Confirma tu nueva contraseña');
      return false;
    }

    if (newPassword !== confirmPassword) {
      this.showConfirmError('Las contraseñas no coinciden');
      return false;
    }

    this.clearConfirmError();
    this.markFieldSuccess('confirmNewPassword');
    return true;
  }

  /**
   * Valida ambas contraseñas
   */
  validatePasswords(newPassword, confirmPassword) {
    const isNewPasswordValid = this.validateNewPassword(newPassword);
    const isConfirmValid = this.validateConfirmation();
    
    return isNewPasswordValid && isConfirmValid;
  }

  /**
   * Alterna la visibilidad de las contraseñas
   */
  toggleVisibility(fieldId) {
    const field = document.getElementById(fieldId);
    const toggleId = fieldId === 'newPassword' ? 'newPasswordToggle' : 'confirmPasswordToggle';
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
   * Muestra error en campo de nueva contraseña
   */
  showPasswordError(message) {
    const errorElement = document.getElementById('newPasswordError');
    const field = this.newPasswordField;

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
   * Limpia error de nueva contraseña
   */
  clearPasswordError() {
    const errorElement = document.getElementById('newPasswordError');
    const field = this.newPasswordField;

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
    const errorElement = document.getElementById('confirmNewPasswordError');
    const field = this.confirmPasswordField;

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
   * Limpia error de confirmación
   */
  clearConfirmError() {
    const errorElement = document.getElementById('confirmNewPasswordError');
    const field = this.confirmPasswordField;

    if (field) field.classList.remove('error');
    if (errorElement) {
      errorElement.textContent = '';
      errorElement.classList.remove('show');
    }
  }

  /**
   * Marca un campo como exitoso
   */
  markFieldSuccess(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) {
      field.classList.remove('error');
      field.classList.add('success');
    }
  }

  /**
   * Muestra error general
   */
  showError(message) {
    const errorElement = document.getElementById('globalError');
    const messageElement = document.getElementById('globalErrorMessage');

    if (errorElement && messageElement) {
      messageElement.textContent = message;
      errorElement.classList.add('show');
    }
  }

  /**
   * Enfoca el primer campo de contraseña
   */
  focus() {
    if (this.newPasswordField) {
      setTimeout(() => this.newPasswordField.focus(), 300);
    }
  }

  /**
   * Resetea todos los campos y el medidor
   */
  reset() {
    if (this.newPasswordField) {
      this.newPasswordField.value = '';
      this.newPasswordField.classList.remove('error', 'success');
    }
    
    if (this.confirmPasswordField) {
      this.confirmPasswordField.value = '';
      this.confirmPasswordField.classList.remove('error', 'success');
    }
    
    this.clearPasswordError();
    this.clearConfirmError();
    this.updateStrengthMeter('');
  }

  /**
   * Obtiene la fortaleza actual
   */
  getCurrentStrength() {
    return this.currentStrength;
  }
}

// Exportar instancia única
export const password = new ResetPasswordManager();
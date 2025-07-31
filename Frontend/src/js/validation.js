/**
 * validation.js - Módulo de validaciones
 * Contiene todas las reglas de validación para formularios
 */

class ValidationManager {
  constructor() {
    this.rules = {
      EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
      PASSWORD_MIN_LENGTH: 6,
      NAME_MIN_LENGTH: 2
    };
  }

  /**
   * Valida un email
   */
  validateEmail(email) {
    if (!email || typeof email !== 'string') {
      return false;
    }

    const cleanEmail = email.trim();
    
    // Verificar longitud mínima
    if (cleanEmail.length < 5) {
      return false;
    }

    // Verificar formato con regex
    return this.rules.EMAIL_REGEX.test(cleanEmail);
  }

  /**
   * Valida una contraseña básica
   */
  validatePassword(password) {
    if (!password || typeof password !== 'string') {
      return false;
    }

    // Para login, solo verificamos que no esté vacía
    return password.length > 0;
  }

  /**
   * Valida una contraseña con reglas estrictas (para registro)
   */
  validateStrongPassword(password) {
    if (!password || typeof password !== 'string') {
      return {
        isValid: false,
        errors: ['La contraseña es requerida']
      };
    }

    const errors = [];

    // Longitud mínima
    if (password.length < this.rules.PASSWORD_MIN_LENGTH) {
      errors.push(`Debe tener al menos ${this.rules.PASSWORD_MIN_LENGTH} caracteres`);
    }

    // Al menos una mayúscula
    if (!/[A-Z]/.test(password)) {
      errors.push('Debe contener al menos una mayúscula');
    }

    // Al menos una minúscula
    if (!/[a-z]/.test(password)) {
      errors.push('Debe contener al menos una minúscula');
    }

    // Al menos un número
    if (!/\d/.test(password)) {
      errors.push('Debe contener al menos un número');
    }

    return {
      isValid: errors.length === 0,
      errors: errors
    };
  }

  /**
   * Valida que las contraseñas coincidan
   */
  validatePasswordMatch(password, confirmPassword) {
    return password === confirmPassword;
  }

  /**
   * Valida un nombre
   */
  validateName(name) {
    if (!name || typeof name !== 'string') {
      return false;
    }

    const cleanName = name.trim();
    return cleanName.length >= this.rules.NAME_MIN_LENGTH;
  }

  /**
   * Valida que un campo no esté vacío
   */
  validateRequired(value) {
    if (value === null || value === undefined) {
      return false;
    }

    if (typeof value === 'string') {
      return value.trim().length > 0;
    }

    return !!value;
  }

  /**
   * Sanitiza un string removiendo caracteres peligrosos
   */
  sanitizeString(str) {
    if (typeof str !== 'string') {
      return '';
    }

    return str
      .trim()
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/[<>]/g, '');
  }

  /**
   * Valida datos de login
   */
  validateLoginData(email, password) {
    const errors = {};

    // Validar email
    if (!this.validateRequired(email)) {
      errors.email = 'El email es requerido';
    } else if (!this.validateEmail(email)) {
      errors.email = 'Formato de email inválido';
    }

    // Validar contraseña
    if (!this.validateRequired(password)) {
      errors.password = 'La contraseña es requerida';
    } else if (!this.validatePassword(password)) {
      errors.password = 'La contraseña no puede estar vacía';
    }

    return {
      isValid: Object.keys(errors).length === 0,
      errors: errors
    };
  }

  /**
   * Valida datos de registro
   */
  validateRegistrationData(userData) {
    const errors = {};

    // Validar nombre
    if (!this.validateRequired(userData.name)) {
      errors.name = 'El nombre es requerido';
    } else if (!this.validateName(userData.name)) {
      errors.name = `El nombre debe tener al menos ${this.rules.NAME_MIN_LENGTH} caracteres`;
    }

    // Validar email
    if (!this.validateRequired(userData.email)) {
      errors.email = 'El email es requerido';
    } else if (!this.validateEmail(userData.email)) {
      errors.email = 'Formato de email inválido';
    }

    // Validar contraseña
    const passwordValidation = this.validateStrongPassword(userData.password);
    if (!passwordValidation.isValid) {
      errors.password = passwordValidation.errors[0];
    }

    // Validar confirmación de contraseña
    if (!this.validatePasswordMatch(userData.password, userData.confirmPassword)) {
      errors.confirmPassword = 'Las contraseñas no coinciden';
    }

    return {
      isValid: Object.keys(errors).length === 0,
      errors: errors
    };
  }

  /**
   * Valida longitud de texto
   */
  validateLength(text, minLength, maxLength = null) {
    if (!text || typeof text !== 'string') {
      return false;
    }

    const length = text.trim().length;
    
    if (length < minLength) {
      return false;
    }

    if (maxLength && length > maxLength) {
      return false;
    }

    return true;
  }
}

// Exportar instancia única
export const validation = new ValidationManager();
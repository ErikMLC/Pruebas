/**
 * modal.js - Modal de términos y condiciones
 * Maneja apertura, cierre y aceptación del modal
 */

class ModalManager {
  constructor() {
    this.modal = null;
    this.acceptTermsCheckbox = null;
  }

  /**
   * Inicializa el manejo del modal
   */
  init() {
    this.setupElements();
    this.setupEvents();
  }

  /**
   * Configura elementos del DOM
   */
  setupElements() {
    this.modal = document.getElementById('termsModal');
    this.acceptTermsCheckbox = document.getElementById('acceptTerms');
  }

  /**
   * Configura eventos del modal
   */
  setupEvents() {
    this.setupModalTriggers();
    this.setupModalControls();
    this.setupModalClose();
  }

  /**
   * Configura enlaces que abren el modal
   */
  setupModalTriggers() {
    const termsLinks = document.querySelectorAll('.terms-link');
    const privacyLinks = document.querySelectorAll('.privacy-link');

    // Enlaces de términos
    termsLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        this.openModal();
      });
    });

    // Enlaces de privacidad (mismo modal por ahora)
    privacyLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        this.openModal();
      });
    });
  }

  /**
   * Configura controles internos del modal
   */
  setupModalControls() {
    // Botón de cerrar (X)
    const closeButton = document.getElementById('closeTermsModal');
    if (closeButton) {
      closeButton.addEventListener('click', () => this.closeModal());
    }

    // Botón de aceptar
    const acceptButton = document.getElementById('acceptTermsModal');
    if (acceptButton) {
      acceptButton.addEventListener('click', () => this.acceptTerms());
    }
  }

  /**
   * Configura cierre del modal con clics externos
   */
  setupModalClose() {
    if (this.modal) {
      this.modal.addEventListener('click', (e) => {
        // Cerrar solo si se hace clic en el overlay (no en el contenido)
        if (e.target === this.modal) {
          this.closeModal();
        }
      });
    }

    // Cerrar con tecla Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isModalOpen()) {
        this.closeModal();
      }
    });
  }

  /**
   * Abre el modal de términos
   */
  openModal() {
    if (!this.modal) return;

    this.modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    
    // Enfocar el modal para accesibilidad
    this.modal.focus();
    
    // Animación de entrada
    setTimeout(() => {
      this.modal.classList.add('show');
    }, 10);
  }

  /**
   * Cierra el modal de términos
   */
  closeModal() {
    if (!this.modal) return;

    this.modal.classList.remove('show');
    
    setTimeout(() => {
      this.modal.style.display = 'none';
      document.body.style.overflow = '';
    }, 200);
  }

  /**
   * Acepta términos y cierra modal
   */
  acceptTerms() {
    if (this.acceptTermsCheckbox) {
      this.acceptTermsCheckbox.checked = true;
      
      // Disparar evento de cambio para validaciones
      const changeEvent = new Event('change', { bubbles: true });
      this.acceptTermsCheckbox.dispatchEvent(changeEvent);
    }

    this.closeModal();
    
    // Mostrar feedback visual
    this.showAcceptanceFeedback();
  }

  /**
   * Muestra feedback visual de aceptación
   */
  showAcceptanceFeedback() {
    const checkboxLabel = this.acceptTermsCheckbox?.closest('.checkbox-label');
    if (checkboxLabel) {
      checkboxLabel.classList.add('accepted');
      
      // Remover clase después de animación
      setTimeout(() => {
        checkboxLabel.classList.remove('accepted');
      }, 1000);
    }
  }

  /**
   * Verifica si el modal está abierto
   */
  isModalOpen() {
    return this.modal && this.modal.style.display === 'flex';
  }

  /**
   * Valida si los términos han sido aceptados
   */
  areTermsAccepted() {
    return this.acceptTermsCheckbox ? this.acceptTermsCheckbox.checked : false;
  }

  /**
   * Fuerza la aceptación de términos (para uso externo)
   */
  forceAcceptTerms() {
    if (this.acceptTermsCheckbox) {
      this.acceptTermsCheckbox.checked = true;
    }
  }

  /**
   * Resalta el checkbox de términos si no está aceptado
   */
  highlightTermsCheckbox() {
    const checkboxLabel = this.acceptTermsCheckbox?.closest('.checkbox-label');
    if (checkboxLabel && !this.areTermsAccepted()) {
      checkboxLabel.classList.add('highlight');
      
      setTimeout(() => {
        checkboxLabel.classList.remove('highlight');
      }, 2000);
    }
  }

  /**
   * Actualiza el contenido del modal (para diferentes tipos)
   */
  updateModalContent(title, content) {
    const titleElement = this.modal?.querySelector('.modal-header h3');
    const bodyElement = this.modal?.querySelector('.modal-body');

    if (titleElement) titleElement.textContent = title;
    if (bodyElement) bodyElement.innerHTML = content;
  }
}

// Exportar instancia única
export const modal = new ModalManager();
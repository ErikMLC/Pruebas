// utils.js - Utilidades compartidas del dashboard (< 50 líneas)
// Funciones auxiliares reutilizables para todos los módulos

export const dashboardUtils = {
    /**
     * Formatea una fecha a formato legible en español
     * @param {string|Date} dateInput - Fecha a formatear
     * @returns {string} - Fecha formateada
     */
    formatDate(dateInput) {
        try {
            const date = new Date(dateInput);
            return date.toLocaleDateString('es-ES', {
                year: 'numeric',
                month: 'long', 
                day: 'numeric'
            });
        } catch (error) {
            return 'Fecha inválida';
        }
    },
    
    /**
     * Formatea tiempo de sesión en formato HH:MM
     * @param {number} minutes - Minutos de sesión
     * @returns {string} - Tiempo formateado
     */
    formatSessionTime(minutes) {
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
    },
    
    /**
     * Copia texto al portapapeles
     * @param {string} text - Texto a copiar
     * @returns {Promise<boolean>} - True si se copió exitosamente
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (error) {
            console.error('Error copiando:', error);
            return false;
        }
    },
    
    /**
     * Descarga datos como archivo JSON
     * @param {Object} data - Datos a descargar
     * @param {string} filename - Nombre del archivo
     */
    downloadJSON(data, filename = 'datos.json') {
        const jsonString = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        this.downloadBlob(blob, filename);
    },
    
    /**
     * Convierte array a CSV y lo descarga
     * @param {Array} data - Array de objetos
     * @param {string} filename - Nombre del archivo
     */
    downloadCSV(data, filename = 'datos.csv') {
        if (!Array.isArray(data) || data.length === 0) return;
        
        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(h => `"${row[h] || ''}"`).join(','))
        ].join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        this.downloadBlob(blob, filename);
    },
    
    /**
     * Descarga un blob como archivo
     * @param {Blob} blob - Blob a descargar  
     * @param {string} filename - Nombre del archivo
     */
    downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }
};
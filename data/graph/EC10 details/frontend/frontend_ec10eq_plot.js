/**
 * Frontend JavaScript pour formater et afficher les graphiques EC10eq
 * Utilise Plotly.js pour le rendu des graphiques
 * 
 * Usage:
 *   - Inclure Plotly.js dans votre HTML: <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
 *   - Inclure ce fichier: <script src="frontend_ec10eq_plot.js"></script>
 *   - Utiliser: EC10eqPlotter.renderPlot('container-id', '60-51-5')
 */

class EC10eqPlotter {
    /**
     * Configuration par défaut
     */
    static defaultConfig = {
        apiBaseUrl: '',  // URL de base de l'API (vide pour relative, ou 'http://localhost:8000')
        logScale: true,
        width: 1800,
        height: 900,
        responsive: true
    };

    /**
     * Récupère les données depuis l'API et affiche le graphique
     * 
     * @param {string} containerId - ID de l'élément HTML où afficher le graphique
     * @param {string} casNumber - Numéro CAS du produit chimique
     * @param {Object} options - Options de configuration
     * @param {string} options.colorBy - Mode de coloration: 'trophic_group', 'year', ou 'author'
     * @param {string} options.apiBaseUrl - URL de base de l'API
     * @returns {Promise<void>}
     */
    static async renderPlot(containerId, casNumber, options = {}) {
        const config = { ...this.defaultConfig, ...options };
        const apiUrl = `${config.apiBaseUrl}/ec10eq/plot/json?cas=${casNumber}&color_by=${config.colorBy || 'trophic_group'}`;
        
        try {
            // Afficher un indicateur de chargement
            this.showLoading(containerId);
            
            // Récupérer les données depuis l'API
            const response = await fetch(apiUrl);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const plotData = await response.json();
            
            // Vérifier que Plotly est disponible
            if (typeof Plotly === 'undefined') {
                throw new Error('Plotly.js is not loaded. Please include: <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>');
            }
            
            // Afficher le graphique
            await Plotly.newPlot(
                containerId,
                plotData.data,
                plotData.layout,
                {
                    responsive: config.responsive,
                    displayModeBar: true,
                    modeBarButtonsToRemove: ['lasso2d', 'select2d']
                }
            );
            
        } catch (error) {
            this.showError(containerId, error.message);
            console.error('Error rendering plot:', error);
        }
    }

    /**
     * Récupère les données brutes depuis l'API
     * 
     * @param {string} casNumber - Numéro CAS du produit chimique
     * @param {string} format - Format de sortie: 'detailed' ou 'simple'
     * @param {string} apiBaseUrl - URL de base de l'API
     * @returns {Promise<Object>} Données JSON
     */
    static async fetchData(casNumber, format = 'detailed', apiBaseUrl = '') {
        const url = `${apiBaseUrl}/ec10eq/data?cas=${casNumber}&format=${format}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }

    /**
     * Récupère les statistiques depuis l'API
     * 
     * @param {string} casNumber - Numéro CAS du produit chimique
     * @param {string} apiBaseUrl - URL de base de l'API
     * @returns {Promise<Object>} Statistiques JSON
     */
    static async fetchStats(casNumber, apiBaseUrl = '') {
        const url = `${apiBaseUrl}/ec10eq/stats?cas=${casNumber}`;
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }

    /**
     * Crée un graphique Plotly à partir de données JSON personnalisées
     * Utile si vous avez déjà les données et voulez créer le graphique manuellement
     * 
     * @param {string} containerId - ID de l'élément HTML où afficher le graphique
     * @param {Object} data - Données au format de l'API
     * @param {Object} options - Options de configuration
     * @returns {Promise<void>}
     */
    static async renderFromData(containerId, data, options = {}) {
        const config = { ...this.defaultConfig, ...options };
        
        try {
            // Convertir les données de l'API en format Plotly
            const plotData = this.convertDataToPlotly(data, config);
            
            // Vérifier que Plotly est disponible
            if (typeof Plotly === 'undefined') {
                throw new Error('Plotly.js is not loaded. Please include: <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>');
            }
            
            // Afficher le graphique
            await Plotly.newPlot(
                containerId,
                plotData.data,
                plotData.layout,
                {
                    responsive: config.responsive,
                    displayModeBar: true,
                    modeBarButtonsToRemove: ['lasso2d', 'select2d']
                }
            );
            
        } catch (error) {
            this.showError(containerId, error.message);
            console.error('Error rendering plot from data:', error);
        }
    }

    /**
     * Convertit les données de l'API en format Plotly
     * (Cette fonction peut être étendue pour personnaliser le rendu)
     * 
     * @param {Object} apiData - Données au format de l'API
     * @param {Object} config - Configuration
     * @returns {Object} Structure Plotly {data, layout}
     */
    static convertDataToPlotly(apiData, config = {}) {
        // Cette fonction devrait normalement utiliser la même logique que create_ec10eq_plot
        // Pour simplifier, on recommande d'utiliser directement l'endpoint /ec10eq/plot/json
        // qui retourne déjà le format Plotly
        throw new Error('convertDataToPlotly is not implemented. Use /ec10eq/plot/json endpoint instead.');
    }

    /**
     * Affiche un indicateur de chargement
     * 
     * @param {string} containerId - ID de l'élément HTML
     */
    static showLoading(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '<div style="text-align: center; padding: 50px;"><p>Chargement du graphique...</p></div>';
        }
    }

    /**
     * Affiche un message d'erreur
     * 
     * @param {string} containerId - ID de l'élément HTML
     * @param {string} message - Message d'erreur
     */
    static showError(containerId, message) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `<div style="text-align: center; padding: 50px; color: red;"><p>Erreur: ${message}</p></div>`;
        }
    }

    /**
     * Met à jour un graphique existant avec de nouvelles données
     * 
     * @param {string} containerId - ID de l'élément HTML
     * @param {string} casNumber - Numéro CAS du produit chimique
     * @param {Object} options - Options de configuration
     */
    static async updatePlot(containerId, casNumber, options = {}) {
        const config = { ...this.defaultConfig, ...options };
        const apiUrl = `${config.apiBaseUrl}/ec10eq/plot/json?cas=${casNumber}&color_by=${config.colorBy || 'trophic_group'}`;
        
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const plotData = await response.json();
            
            if (typeof Plotly === 'undefined') {
                throw new Error('Plotly.js is not loaded');
            }
            
            await Plotly.update(containerId, plotData.data, plotData.layout);
            
        } catch (error) {
            this.showError(containerId, error.message);
            console.error('Error updating plot:', error);
        }
    }
}

// Export pour utilisation en module (si supporté)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EC10eqPlotter;
}


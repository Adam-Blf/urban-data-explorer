/**
 * Module de Visualisation (Charts.js)
 * Auteur : Adam BELOUCIF (Refactored for Split-Screen)
 * Rôle : Rendu des graphiques radar pour la comparaison et indicateurs.
 */

let charts = {
    a: null,
    b: null
};

Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'Outfit', sans-serif";

function initCharts() {
    console.log("📊 Graphiques initialisés.");
}

/**
 * Met à jour le graphique radar d'un slot spécifique (A ou B).
 * @param {Object} data - Données de l'arrondissement.
 * @param {string} slot - 'a' ou 'b'.
 */
function updateRadarChart(data, slot) {
    const s = slot.toLowerCase();
    const canvasId = `radarChart${slot.toUpperCase()}`;
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    if (charts[s]) charts[s].destroy();

    const color = s === 'a' ? 'rgba(59, 130, 246, 0.5)' : 'rgba(239, 68, 68, 0.5)';
    const borderColor = s === 'a' ? '#3b82f6' : '#ef4444';

    charts[s] = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Qualité de Vie', 'Mobilité', 'Patrimoine', 'Dynamisme'],
            datasets: [{
                label: `Indicateurs - District ${slot.toUpperCase()}`,
                data: [
                    data.qualite_vie || 0, 
                    data.mobilite || 0, 
                    data.patrimoine || 0, 
                    data.tension || 0
                ],
                backgroundColor: color,
                borderColor: borderColor,
                pointBackgroundColor: borderColor,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: 'rgba(255,255,255,0.1)' },
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    pointLabels: { 
                        color: '#94a3b8', 
                        font: { size: 12, weight: '500' } 
                    },
                    ticks: { display: false, min: 0, max: 100, stepSize: 20 },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

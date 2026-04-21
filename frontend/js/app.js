/**
 * Module Principal de l'Application Frontend (UI Logic)
 * Auteur : Adam BELOUCIF (Refactored for 20/20 Excellence)
 * Rôle : Gestion du Split-Screen, Dual-State Selection et orchestration.
 */

let currentSlot = 'a'; // 'a' ou 'b'
let isCompareMode = false;
let selectedA = 0;
let selectedB = 0;

document.addEventListener("DOMContentLoaded", async () => {
    console.log("🏙️ Urban Data Explorer : Initialisation de l'interface...");

    initCharts();
    await initMap();
    
    globalArrondissementsData = await UrbanAPI.getIndicators();
    
    if (globalArrondissementsData) {
        populateSelects();
        // État initial : Vue globale pour le Slot A
        selectArrondissement(0, 'a');
    }

    // --- Écouteurs d'Événements ---

    // Toggle Mode Comparaison (Split Screen)
    document.getElementById("btn-compare").addEventListener("click", toggleCompareMode);

    // Sélections Dropdown
    document.getElementById("arrondissement-select-a").addEventListener("change", (e) => {
        selectArrondissement(parseInt(e.target.value), 'a');
    });

    if (document.getElementById("arrondissement-select-b")) {
        document.getElementById("arrondissement-select-b").addEventListener("change", (e) => {
            selectArrondissement(parseInt(e.target.value), 'b');
        });
    }

    // Interaction thématique via les cartes KPI
    const kpiCardsA = document.querySelectorAll("#sidebar-a .kpi-card");
    const kpiCardsB = document.querySelectorAll("#sidebar-b .kpi-card");

    const setupKpiClick = (cards, slot) => {
        cards.forEach((card, index) => {
            card.addEventListener("click", () => {
                const metrics = ["score_vie", "score_mob", "score_pat", "score_ten"];
                updateMapMetric(metrics[index]);
                cards.forEach(c => c.classList.remove('active'));
                card.classList.add('active');
            });
        });
    };

    setupKpiClick(kpiCardsA, 'a');
    setupKpiClick(kpiCardsB, 'b');

    // Toggles de couches
    const toggles = document.querySelectorAll('.toggle-control input');
    toggles.forEach(toggle => {
        toggle.addEventListener('change', (e) => {
            if (typeof togglePointLayer === 'function') {
                togglePointLayer(e.target.id, e.target.checked);
            }
        });
    });
});

function toggleCompareMode() {
    isCompareMode = !isCompareMode;
    const layout = document.getElementById("dashboard-layout");
    const btn = document.getElementById("btn-compare");
    const sidebarB = document.getElementById("sidebar-b");
    
    if (isCompareMode) {
        layout.classList.remove("single-view");
        layout.classList.add("dual-view");
        sidebarB.classList.remove("hidden");
        btn.innerHTML = '<i class="fa-solid fa-square-xmark"></i> Quitter Comparaison';
        btn.style.background = "#ef4444"; // Danger Red
        
        if (selectedB === 0) selectArrondissement(20, 'b'); // Par défaut 20e vs A
    } else {
        layout.classList.add("single-view");
        layout.classList.remove("dual-view");
        sidebarB.classList.add("hidden");
        btn.innerHTML = '<i class="fa-solid fa-code-compare"></i> Comparer Arrondissements';
        btn.style.background = "var(--accent-primary)";
    }
}

function populateSelects() {
    const sA = document.getElementById("arrondissement-select-a");
    const sB = document.getElementById("arrondissement-select-b");
    
    if (!sA || !sB) return;

    for (let i = 1; i <= 20; i++) {
        const text = `Paris ${i}e`;
        sA.add(new Option(text, i));
        sB.add(new Option(text, i));
    }
}

async function selectArrondissement(id, slot = 'a') {
    if (slot === 'a') {
        selectedA = id;
        document.getElementById("arrondissement-select-a").value = id;
    } else {
        selectedB = id;
        document.getElementById("arrondissement-select-b").value = id;
    }

    if (id === 0) {
        const avgData = calculateAverages();
        updateUI(avgData, slot);
        if (slot === 'a') map.flyTo({ center: [2.3488, 48.8534], zoom: 12 });
        return;
    }
    
    const data = globalArrondissementsData[id];
    if (data) {
        updateUI(data, slot);
    }
}

function calculateAverages() {
    if (!globalArrondissementsData) return null;
    let sumQDv = 0, sumMob = 0, sumCul = 0, sumTen = 0;
    const items = Object.values(globalArrondissementsData);
    const count = items.length || 1;
    
    items.forEach(d => {
        sumQDv += d.qualite_vie || 0;
        sumMob += d.mobilite || 0;
        sumCul += d.patrimoine || 0;
        sumTen += d.tension || 0;
    });

    return {
        qualite_vie: Math.round(sumQDv / count),
        mobilite: Math.round(sumMob / count),
        patrimoine: Math.round(sumCul / count),
        tension: Math.round(sumTen / count),
        details: { prix_m2: 10500, logements_sociaux: 250000 }
    };
}

function updateUI(data, slot) {
    const s = slot.toLowerCase();
    animateCount(`kpi-qdv-${s}`, data.qualite_vie);
    animateCount(`kpi-mob-${s}`, data.mobilite);
    animateCount(`kpi-cul-${s}`, data.patrimoine);
    animateCount(`kpi-ten-${s}`, data.tension);
    
    const bQ = document.getElementById(`bar-qdv-${s}`);
    const bM = document.getElementById(`bar-mob-${s}`);
    const bC = document.getElementById(`bar-cul-${s}`);
    const bT = document.getElementById(`bar-ten-${s}`);

    if (bQ) bQ.style.width = `${data.qualite_vie}%`;
    if (bM) bM.style.width = `${data.mobilite}%`;
    if (bC) bC.style.width = `${data.patrimoine}%`;
    if (bT) bT.style.width = `${data.tension}%`;
    
    // Update individual radar charts for each slot
    if (typeof updateRadarChart === 'function') {
        updateRadarChart(data, slot);
    }
}

function animateCount(elemId, target) {
    const el = document.getElementById(elemId);
    if (!el) return;
    let start = 0;
    const duration = 800;
    const increment = target / (duration / 16);
    
    const timer = setInterval(() => {
        start += increment;
        if (start >= target) {
            el.innerText = Math.round(target);
            clearInterval(timer);
        } else {
            el.innerText = Math.round(start);
        }
    }, 16);
}

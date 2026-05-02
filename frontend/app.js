/**
 * Urban Data Explorer · frontend ESM (no build).
 * MapLibre GL JS + Chart.js + fetch direct sur l'API FastAPI.
 */

// API base · priorité ·
//   1. ?api=https://...  dans l'URL (utile pour la démo Vercel)
//   2. <meta name=udeApiBase content=...>
//   3. fallback localhost
const API_BASE = (() => {
    const fromQs = new URLSearchParams(location.search).get("api");
    if (fromQs) return fromQs.replace(/\/$/, "");
    const metaTag = document.querySelector('meta[name="udeApiBase"]');
    return (metaTag?.getAttribute("content") || "http://localhost:8000").replace(/\/$/, "");
})();

// --------------------------------------------------------------------------
// Auth flow
// --------------------------------------------------------------------------

let token = null;
let arrondissementsData = null;
let kpiData = [];
let timelineData = [];
let timelineMonths = [];
let charts = { bar: null, line: null, compare: null };
let map = null;
let highlightedCode = null;

const els = {
    loginSection:    document.getElementById("login-section"),
    filtersSection:  document.getElementById("filters-section"),
    kpiSection:      document.getElementById("kpi-section"),
    compareSection:  document.getElementById("compare-section"),
    loginBtn:        document.getElementById("login-btn"),
    loginHint:       document.getElementById("login-hint"),
    username:        document.getElementById("username"),
    password:        document.getElementById("password"),
    indicatorSelect: document.getElementById("indicator-select"),
    timeRange:       document.getElementById("time-range"),
    timeLabel:       document.getElementById("time-label"),
    kpiTitle:        document.getElementById("kpi-title"),
    kpiGrid:         document.getElementById("kpi-grid"),
    chartBar:        document.getElementById("chart-bar"),
    chartLine:       document.getElementById("chart-line"),
    chartCompare:    document.getElementById("chart-compare"),
    compareA:        document.getElementById("compare-a"),
    compareB:        document.getElementById("compare-b"),
    compareBtn:      document.getElementById("compare-btn"),
    compareTitle:    document.getElementById("compare-title"),
};

els.loginBtn.addEventListener("click", login);
els.indicatorSelect.addEventListener("change", () => paintChoropleth());
els.timeRange.addEventListener("input", onTimeChanged);
els.compareBtn.addEventListener("click", runCompare);
document.querySelectorAll('.layers input[type="checkbox"]').forEach(cb => {
    cb.addEventListener("change", () => togglePoiLayer(cb.dataset.cat, cb.checked));
});

// Submit on Enter from password field
els.password.addEventListener("keydown", (e) => { if (e.key === "Enter") login(); });

// Keyboard shortcut · "?" for help, "/" to focus indicator select
document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
    if (e.key === "?") { showShortcutsHelp(); }
    if (e.key === "/") { e.preventDefault(); els.indicatorSelect.focus(); }
});

function showShortcutsHelp() {
    const existing = document.getElementById("shortcuts-modal");
    if (existing) { existing.remove(); return; }
    const modal = document.createElement("div");
    modal.id = "shortcuts-modal";
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.innerHTML = `
        <div class="shortcuts-card">
            <h3>Raccourcis clavier</h3>
            <dl>
                <dt><kbd>?</kbd></dt><dd>Afficher / cacher cette aide</dd>
                <dt><kbd>/</kbd></dt><dd>Sélecteur d'indicateur</dd>
                <dt><kbd>Tab</kbd></dt><dd>Naviguer entre les contrôles</dd>
                <dt><kbd>Esc</kbd></dt><dd>Fermer cette aide</dd>
            </dl>
            <button type="button" id="shortcuts-close">Fermer</button>
        </div>
    `;
    document.body.appendChild(modal);
    document.getElementById("shortcuts-close").addEventListener("click", () => modal.remove());
    document.addEventListener("keydown", function escClose(e) {
        if (e.key === "Escape") { modal.remove(); document.removeEventListener("keydown", escClose); }
    });
}

// Scroll-reveal sections in the sidebar
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add("is-visible"); });
}, { threshold: 0.15 });
document.querySelectorAll("aside section").forEach((s) => {
    s.classList.add("reveal");
    revealObserver.observe(s);
});

async function login() {
    els.loginHint.textContent = "";
    try {
        const r = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                username: els.username.value,
                password: els.password.value,
            }),
        });
        if (!r.ok) throw new Error(`login ${r.status}`);
        const data = await r.json();
        token = data.access_token;
        els.loginSection.classList.add("hidden");
        els.filtersSection.classList.remove("hidden");
        els.kpiSection.classList.remove("hidden");
        await bootstrapMap();
    } catch (e) {
        els.loginHint.textContent = "Identifiants refusés (" + e.message + ").";
    }
}

function authHeaders() { return { Authorization: `Bearer ${token}` }; }

async function api(path) {
    const r = await fetch(`${API_BASE}${path}`, { headers: authHeaders() });
    if (!r.ok) throw new Error(`${path} → ${r.status}`);
    return r.json();
}

// --------------------------------------------------------------------------
// Map bootstrap
// --------------------------------------------------------------------------

async function bootstrapMap() {
    arrondissementsData = await api("/geo/arrondissements.geojson");

    const kpiPage = await api("/datamarts/arrondissements?page_size=50&order_by=code_arrondissement");
    kpiData = kpiPage.items;
    populateCompareSelects();

    const tlPage = await api("/datamarts/timeline?page_size=500&year_from=2019&year_to=2024");
    timelineData = tlPage.items;
    timelineMonths = [...new Set(timelineData.map(p => p.year_month))].sort();
    els.timeRange.max = Math.max(0, timelineMonths.length - 1);
    els.timeRange.value = timelineMonths.length - 1;
    els.timeLabel.textContent = timelineMonths.at(-1) ?? "—";

    map = new maplibregl.Map({
        container: "map",
        style: {
            version: 8,
            sources: {
                "carto-dark": {
                    type: "raster",
                    tiles: ["https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"],
                    tileSize: 256,
                    attribution: "© OpenStreetMap · © CARTO",
                },
            },
            layers: [{ id: "carto-dark", type: "raster", source: "carto-dark" }],
        },
        center: [2.349, 48.853],
        zoom: 11.5,
        pitch: 28,
    });

    map.on("load", () => {
        map.addSource("arr", { type: "geojson", data: arrondissementsData });
        map.addLayer({
            id: "arr-fill",
            type: "fill",
            source: "arr",
            paint: { "fill-color": "#FFD166", "fill-opacity": 0.6 },
        });
        map.addLayer({
            id: "arr-line",
            type: "line",
            source: "arr",
            paint: { "line-color": "#0b1020", "line-width": 1.4 },
        });
        map.addLayer({
            id: "arr-highlight",
            type: "line",
            source: "arr",
            paint: { "line-color": "#06D6A0", "line-width": 3 },
            filter: ["==", "code_arrondissement", ""],
        });

        paintChoropleth();
        attachInteractions();
    });
}

function populateCompareSelects() {
    [els.compareA, els.compareB].forEach((sel, i) => {
        sel.innerHTML = kpiData
            .map(k => `<option value="${k.code_arrondissement}">${k.label}</option>`)
            .join("");
        sel.value = kpiData[i === 0 ? 0 : 4]?.code_arrondissement ?? "";
    });
}

// --------------------------------------------------------------------------
// Choropleth (paint)
// --------------------------------------------------------------------------

function paintChoropleth() {
    if (!map || !arrondissementsData) return;
    const indicator = els.indicatorSelect.value;
    const values = arrondissementsData.features
        .map(f => f.properties[indicator])
        .filter(v => v !== null && v !== undefined && !isNaN(v));
    if (values.length === 0) return;

    const min = Math.min(...values);
    const max = Math.max(...values);
    map.setPaintProperty("arr-fill", "fill-color", [
        "interpolate", ["linear"], ["coalesce", ["get", indicator], min],
        min, "#073b4c",
        (min + max) / 2, "#FFD166",
        max, "#EF476F",
    ]);
}

// --------------------------------------------------------------------------
// Interactions · click + popup
// --------------------------------------------------------------------------

function attachInteractions() {
    map.on("mousemove", "arr-fill", () => map.getCanvas().style.cursor = "pointer");
    map.on("mouseleave", "arr-fill", () => map.getCanvas().style.cursor = "");

    map.on("click", "arr-fill", (e) => {
        const props = e.features[0].properties;
        const code = props.code_arrondissement;
        highlightedCode = code;
        map.setFilter("arr-highlight", ["==", "code_arrondissement", code]);
        new maplibregl.Popup({ closeButton: false })
            .setLngLat(e.lngLat)
            .setHTML(popupHtml(props))
            .addTo(map);
        renderKpiPanel(code);
    });
}

function popupHtml(p) {
    return `
        <h3>${p.label ?? p.code_arrondissement}</h3>
        <table>
            <tr><td>Prix m²</td><td>${fmt(p.prix_m2)} €</td></tr>
            <tr><td>Accessibilité</td><td>${fmt(p.idx_accessibilite, 2)}</td></tr>
            <tr><td>Tension</td><td>${fmt(p.idx_tension, 2)}</td></tr>
            <tr><td>Effort social</td><td>${fmt(p.idx_effort_social, 2)}</td></tr>
            <tr><td>Attractivité</td><td>${fmt(p.idx_attractivite, 2)}</td></tr>
        </table>
    `;
}

function fmt(v, digits = 0) {
    if (v === null || v === undefined || isNaN(v)) return "—";
    return Number(v).toLocaleString("fr-FR", { maximumFractionDigits: digits });
}

// --------------------------------------------------------------------------
// KPI panel + charts (Chart.js)
// --------------------------------------------------------------------------

function renderKpiPanel(code) {
    const k = kpiData.find(x => x.code_arrondissement === code);
    if (!k) return;
    els.kpiTitle.textContent = `${k.label} · ${k.code_arrondissement}`;
    els.kpiGrid.innerHTML = [
        ["Population",         fmt(k.population)],
        ["Parc logements",     fmt(k.parc_logements)],
        ["Revenu médian",      `${fmt(k.revenu_median)} €`],
        ["Prix m² médian",     `${fmt(k.prix_m2)} €`],
        ["Trans. / an",        fmt(k.transactions_an)],
        ["Log. sociaux fin.",  fmt(k.log_sociaux_finances)],
        ["Indice attract.",    fmt(k.idx_attractivite, 2)],
        ["Indice access.",     fmt(k.idx_accessibilite, 2)],
    ].map(([l, v]) => `<div class="kpi"><div class="label">${l}</div><div class="value">${v}</div></div>`).join("");

    if (charts.bar) charts.bar.destroy();
    charts.bar = new Chart(els.chartBar, {
        type: "bar",
        data: {
            labels: ["transport", "service public", "commerce", "culture", "santé", "environnement"],
            datasets: [{
                label: `Équipements · ${k.label}`,
                data: [k.nb_transport, k.nb_service_public, k.nb_commerce, k.nb_culture, k.nb_sante, k.nb_environnement],
                backgroundColor: "#FFD166",
            }],
        },
        options: { plugins: { legend: { labels: { color: "#f4f6fb" } } },
                   scales: { x: { ticks: { color: "#aab2cc" } }, y: { ticks: { color: "#aab2cc" } } } },
    });

    const tlSeries = timelineData
        .filter(p => p.code_arrondissement === code)
        .sort((a, b) => a.year_month.localeCompare(b.year_month));
    if (charts.line) charts.line.destroy();
    charts.line = new Chart(els.chartLine, {
        type: "line",
        data: {
            labels: tlSeries.map(p => p.year_month),
            datasets: [{
                label: "Prix m² médian (€)",
                data: tlSeries.map(p => p.prix_m2_median),
                borderColor: "#06D6A0",
                backgroundColor: "rgba(6, 214, 160, 0.2)",
                tension: 0.25,
                fill: true,
            }],
        },
        options: { plugins: { legend: { labels: { color: "#f4f6fb" } } },
                   scales: { x: { ticks: { color: "#aab2cc" } }, y: { ticks: { color: "#aab2cc" } } } },
    });
}

// --------------------------------------------------------------------------
// Timeline animation (slider)
// --------------------------------------------------------------------------

function onTimeChanged() {
    if (!arrondissementsData) return;
    const idx = parseInt(els.timeRange.value, 10);
    const ym = timelineMonths[idx];
    els.timeLabel.textContent = ym ?? "—";

    const snapshot = {};
    timelineData
        .filter(p => p.year_month === ym)
        .forEach(p => snapshot[p.code_arrondissement] = p.prix_m2_median);

    arrondissementsData.features.forEach(f => {
        const c = f.properties.code_arrondissement;
        f.properties.prix_m2 = snapshot[c] ?? f.properties.prix_m2;
    });
    map.getSource("arr").setData(arrondissementsData);
    if (els.indicatorSelect.value === "prix_m2") paintChoropleth();
}

// --------------------------------------------------------------------------
// Comparison mode
// --------------------------------------------------------------------------

function runCompare() {
    const a = kpiData.find(x => x.code_arrondissement === els.compareA.value);
    const b = kpiData.find(x => x.code_arrondissement === els.compareB.value);
    if (!a || !b) return;
    els.compareSection.classList.remove("hidden");
    els.compareTitle.textContent = `${a.label} vs ${b.label}`;

    const dims = ["prix_m2", "idx_accessibilite", "idx_tension", "idx_effort_social", "idx_attractivite"];
    const norm = (raw) => dims.map(d => Math.abs(raw[d] ?? 0));

    if (charts.compare) charts.compare.destroy();
    charts.compare = new Chart(els.chartCompare, {
        type: "radar",
        data: {
            labels: ["Prix m²", "Accessibilité", "Tension", "Effort social", "Attractivité"],
            datasets: [
                { label: a.label, data: norm(a), borderColor: "#FFD166", backgroundColor: "rgba(255, 209, 102, 0.25)" },
                { label: b.label, data: norm(b), borderColor: "#EF476F", backgroundColor: "rgba(239, 71, 111, 0.25)" },
            ],
        },
        options: {
            plugins: { legend: { labels: { color: "#f4f6fb" } } },
            scales: { r: { angleLines: { color: "rgba(255,255,255,0.1)" },
                            grid: { color: "rgba(255,255,255,0.1)" },
                            pointLabels: { color: "#aab2cc" },
                            ticks: { color: "#aab2cc", backdropColor: "transparent" } } },
        },
    });
}

// --------------------------------------------------------------------------
// POI layer toggling
// --------------------------------------------------------------------------

const poiSourceId = (cat) => `poi-${cat}`;
const poiLayerId = (cat) => `poi-${cat}-circle`;

const POI_COLORS = {
    transport:      "#06D6A0",
    service_public: "#FFD166",
    commerce:       "#EF476F",
    culture:        "#118AB2",
    sante:          "#9B5DE5",
    environnement:  "#4ECB71",
};

async function togglePoiLayer(cat, on) {
    if (!map) return;
    if (!on) {
        if (map.getLayer(poiLayerId(cat))) map.removeLayer(poiLayerId(cat));
        if (map.getSource(poiSourceId(cat))) map.removeSource(poiSourceId(cat));
        return;
    }
    try {
        const data = await api(`/geo/poi.geojson?category=${cat}&limit=2000`);
        if (!map.getSource(poiSourceId(cat))) {
            map.addSource(poiSourceId(cat), { type: "geojson", data });
            map.addLayer({
                id: poiLayerId(cat),
                type: "circle",
                source: poiSourceId(cat),
                paint: {
                    "circle-radius": 4,
                    "circle-color": POI_COLORS[cat] ?? "#fff",
                    "circle-opacity": 0.85,
                    "circle-stroke-color": "#0b1020",
                    "circle-stroke-width": 0.6,
                },
            });
        }
    } catch (e) {
        console.error("POI layer fetch failed", e);
    }
}

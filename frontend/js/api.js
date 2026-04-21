const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000/api"
    : "https://urban-data-explorer-api.onrender.com/api";

/**
 * UrbanAPI - Client d'accès aux données (Mode Résilient)
 * Gère le basculement automatique entre l'API Cloud (Render) et les fichiers statiques (Vercel)
 * pour éviter l'effet "carte cassée" quand les serveurs dorment.
 */
class UrbanAPI {
    
    // Timeout court (5s) pour basculer rapidement sur les données locales si Render dort
    static async fetchWithTimeout(resource, options = {}) {
        const { timeout = 5000 } = options;
        const controller = new AbortController();
        const id = setTimeout(() => controller.abort(), timeout);
        const response = await fetch(resource, { ...options, signal: controller.signal });
        clearTimeout(id);
        return response;
    }

    static async getArrondissementsGeoJSON() {
        try {
            console.log("📡 Tentative récupération GeoJSON (API Cloud)...");
            const res = await this.fetchWithTimeout(`${API_BASE}/arrondissements`);
            if (!res.ok) throw new Error("API Indisponible");
            return await res.json();
        } catch (e) {
            console.warn("⚠️ API Cloud lente ou inaccessible. Utilisation du Fallback Local (Données Gold)...");
            // Fallback sur le fichier statique déployé sur Vercel
            const localRes = await fetch("data/arrondissements_stats.geojson");
            return await localRes.json();
        }
    }

    static async getIndicators() {
        try {
            console.log("📡 Tentative récupération Indicateurs (API Cloud)...");
            const res = await this.fetchWithTimeout(`${API_BASE}/indicateurs`);
            if (!res.ok) throw new Error("API Indisponible");
            
            const data = await res.json();
            
            // --- DATA SANITY GUARD (20/20 Logic) ---
            // On vérifie si les données sont "saines". 
            // Si l'arrondissement 1 a 0 en mobilité ou patrimoine, c'est une erreur de pipeline sur le Cloud.
            if (data["1"] && (data["1"].mobilite === 0 || data["1"].patrimoine === 0)) {
                console.warn("🚩 Données Cloud détectées comme corrompues (0 suspect). Basculement forcé...");
                throw new Error("Data Corrupted");
            }
            
            return data;
        } catch (e) {
            console.warn("⚠️ Utilisation du Fallback Local (Scores Gold certifiés)...");
            const localRes = await fetch("data/indicateurs.json");
            return await localRes.json();
        }
    }

    static async getDatasetGeoJSON(datasetName) {
        try {
            const res = await this.fetchWithTimeout(`${API_BASE}/dataset/${datasetName}?geojson=true`);
            if (!res.ok) throw new Error("API Indisponible");
            return await res.json();
        } catch (e) {
            console.error(`❌ Impossible de charger le dataset ${datasetName} (API Offline)`);
            return null;
        }
    }

    static async getComparison(arr1, arr2) {
        try {
            const res = await this.fetchWithTimeout(`${API_BASE}/compare?a1=${arr1}&a2=${arr2}`);
            if (!res.ok) throw new Error("API Indisponible");
            return await res.json();
        } catch (e) {
            // Reconstitution locale simple de la comparaison
            const indicators = await this.getIndicators();
            if(!indicators) return null;
            return {
                "arrondissement_1": { ...indicators[arr1], "id": arr1 },
                "arrondissement_2": { ...indicators[arr2], "id": arr2 }
            };
        }
    }
}

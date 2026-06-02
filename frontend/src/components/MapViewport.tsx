import React, { useEffect, useRef, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import mapboxgl from 'mapbox-gl';
import { AlertTriangle, Settings } from 'lucide-react';
import { api } from '../services/api';

type Theme = 'light' | 'dark';

/* ── Palette data-viz par thème (valeurs littérales pour Mapbox GL) ───── */

interface ThemeColors {
  seq: (number | string)[];      // paliers interpolate séquentiels bleu France
  fallback: string;
  sel: string;                   // arrondissement sélectionné (bleu France)
  comp: string;                  // arrondissement comparé (rouge Marianne)
  line: string;                  // contour par défaut
  buildings: string;            // extrusion 3D
}

const THEME_COLORS: Record<Theme, ThemeColors> = {
  light: {
    seq: [0, '#e3e3fd', 35, '#8585f6', 70, '#4d4dde', 100, '#000091'],
    fallback: 'rgba(0, 0, 145, 0.08)',
    sel: '#000091',
    comp: '#e1000f',
    line: '#6a6af4',
    buildings: '#8585f6',
  },
  dark: {
    seq: [0, '#272747', 35, '#5b5bd6', 70, '#8585f6', 100, '#b1b1f9'],
    fallback: 'rgba(133, 133, 246, 0.10)',
    sel: '#b1b1f9',
    comp: '#f95c5e',
    line: '#8585f6',
    buildings: '#5b5bd6',
  },
};

/* ── Style structurel par granularité (épaisseurs / opacités / libellé) ── */

const LEVEL_STYLES: Record<number, { lineWidth: number; fillOpacity: number; label: string }> = {
  0: { lineWidth: 2.5, fillOpacity: 0.1, label: 'Ville' },
  1: { lineWidth: 1.5, fillOpacity: 0.15, label: 'Arrondissement' },
  2: { lineWidth: 1.0, fillOpacity: 0.1, label: 'IRIS' },
  3: { lineWidth: 2.0, fillOpacity: 0.0, label: 'Rue' },
  4: { lineWidth: 0.5, fillOpacity: 0.2, label: 'Bâtiment' },
};

/* ── Extraction du code selon le niveau (handler de clic) ──────────────── */

function extractCode(level: number, properties: Record<string, unknown> | null | undefined): string | null {
  if (!properties) return null;
  switch (level) {
    case 0:
      return typeof properties.name === 'string' ? properties.name : null;
    case 1: {
      const code = properties.c_arinsee ?? properties.c_ar ?? properties.insee_com;
      return code != null ? String(code) : null;
    }
    case 2: {
      const iris = properties.code_iris ?? properties.c_iris ?? properties.iris;
      if (typeof iris === 'string') return iris.substring(0, 5);
      const arCode = properties.c_arinsee ?? properties.c_ar;
      return arCode != null ? String(arCode) : null;
    }
    case 3:
      return typeof properties.l_voie === 'string'
        ? properties.l_voie
        : typeof properties.name === 'string' ? properties.name : null;
    case 4:
      return typeof properties.n_sq_vo === 'string'
        ? properties.n_sq_vo
        : typeof properties.name === 'string' ? properties.name : null;
    default:
      return null;
  }
}

/* ── Expression de coloration choroplèthe ─────────────────────────────── */

const propertyForFamily = (activeFamily: string): string => {
  if (activeFamily === 'immobilier') return 'immobilier_idx';
  if (activeFamily === 'logement_social') return 'logement_social_idx';
  if (activeFamily === 'revenus') return 'revenu_idx';
  if (activeFamily === 'cadre_vie') return 'cadre_vie_idx';
  if (activeFamily === 'environnement') return 'environnement_idx';
  return 'score';
};

const getChoroplethColorExpression = (activeFamily: string, theme: Theme): any => {
  const c = THEME_COLORS[theme];
  return [
    'coalesce',
    ['interpolate', ['linear'], ['get', propertyForFamily(activeFamily)], ...c.seq],
    c.fallback,
  ];
};

/* ── Détails de légende ─────────────────────────────────────────────── */

const getLegendDetails = (activeFamily: string) => {
  switch (activeFamily) {
    case 'immobilier':
      return { title: 'Prix moyen au m²', minLabel: '8 k€', midLabel: '12 k€', maxLabel: '16 k€' };
    case 'logement_social':
      return { title: 'Taux de logement social', minLabel: '0 %', midLabel: '20 %', maxLabel: '40 %+' };
    case 'revenus':
      return { title: 'Revenu médian annuel', minLabel: '20 k€', midLabel: '34 k€', maxLabel: '48 k€+' };
    case 'cadre_vie':
      return { title: 'Indice cadre de vie', minLabel: '0', midLabel: '50', maxLabel: '100' };
    case 'environnement':
      return { title: 'Indice environnement', minLabel: '0', midLabel: '50', maxLabel: '100' };
    default:
      return { title: 'Score global parisien', minLabel: '0', midLabel: '50', maxLabel: '100' };
  }
};

/* ── Composant ─────────────────────────────────────────────────────────── */

interface MapViewportProps {
  mapMode: '2d' | '3d';
  mapboxToken: string;
  theme: Theme;
  setShowSettings: (show: boolean) => void;
  selectedDistrict: string | null;
  setSelectedDistrict: React.Dispatch<React.SetStateAction<string | null>>;
  comparedDistrict: string | null;
  setComparedDistrict: React.Dispatch<React.SetStateAction<string | null>>;
  granularity: number;
  setGranularity: (level: number) => void;
  activeFamily: string;
}

export const MapViewport: React.FC<MapViewportProps> = ({
  mapMode,
  mapboxToken,
  theme,
  setShowSettings,
  selectedDistrict,
  setSelectedDistrict,
  comparedDistrict,
  setComparedDistrict,
  granularity,
  setGranularity,
  activeFamily,
}) => {
  const mapContainer2D = useRef<HTMLDivElement>(null);
  const mapContainer3D = useRef<HTMLDivElement>(null);
  const map2DRef = useRef<maplibregl.Map | null>(null);
  const map3DRef = useRef<mapboxgl.Map | null>(null);
  const granularityRef = useRef(granularity);
  const loadingRef = useRef(false);

  const coords: Record<string, [number, number]> = {
    '75001': [2.3364, 48.8626], '75002': [2.3426, 48.8682], '75003': [2.3601, 48.8629],
    '75004': [2.3553, 48.8543], '75005': [2.3486, 48.8453], '75006': [2.3323, 48.8491],
    '75007': [2.3126, 48.8562], '75008': [2.3075, 48.8725], '75009': [2.3374, 48.8771],
    '75010': [2.3605, 48.8761], '75011': [2.3800, 48.8594], '75012': [2.4060, 48.8352],
    '75013': [2.3557, 48.8283], '75014': [2.3255, 48.8292], '75015': [2.2925, 48.8402],
    '75016': [2.2618, 48.8604], '75017': [2.3082, 48.8873], '75018': [2.3475, 48.8925],
    '75019': [2.3802, 48.8870], '75020': [2.4014, 48.8631],
  };

  useEffect(() => { granularityRef.current = granularity; }, [granularity]);

  const updateGranularityByZoom = useCallback((zoom: number) => {
    let level = 0;
    if (zoom >= 16) level = 4;
    else if (zoom >= 14) level = 3;
    else if (zoom >= 12) level = 2;
    else if (zoom >= 10) level = 1;
    else level = 0;

    if (level !== granularityRef.current) {
      granularityRef.current = level;
      setGranularity(level);
    }
  }, [setGranularity]);

  /* ── Sélection / comparaison ──────────────────────────────────────── */

  const handleMapClick = useCallback((properties: Record<string, unknown> | null | undefined) => {
    const code = extractCode(granularityRef.current, properties);
    if (!code) return;

    setSelectedDistrict((current) => {
      if (current === code) { setComparedDistrict(null); return null; }
      if (!current) return code;
      setComparedDistrict((comp) => (comp === code ? null : code));
      return current;
    });
  }, [setSelectedDistrict, setComparedDistrict]);

  /* ── Application des styles (2D) ──────────────────────────────────── */

  const applyStyles2D = useCallback((map: maplibregl.Map, level: number, active: string, sel: string | null, comp: string | null, th: Theme) => {
    const style = LEVEL_STYLES[level] || LEVEL_STYLES[1];
    const c = THEME_COLORS[th];
    const choro = getChoroplethColorExpression(active, th);
    try {
      if (map.getLayer('paris-base-fill')) {
        map.setPaintProperty('paris-base-fill', 'fill-color', choro);
        map.setPaintProperty('paris-base-fill', 'fill-opacity', level === 2 ? 0.15 : level === 0 ? 0.1 : 0.6);
      }
      if (map.getLayer('paris-districts-fill')) {
        if (level === 2 || level === 4) {
          map.setPaintProperty('paris-districts-fill', 'fill-color', choro);
          map.setPaintProperty('paris-districts-fill', 'fill-opacity', 0.65);
        } else if (level === 1) {
          map.setPaintProperty('paris-districts-fill', 'fill-color', 'rgba(0,0,0,0)');
          map.setPaintProperty('paris-districts-fill', 'fill-opacity', 0.0);
        } else {
          map.setPaintProperty('paris-districts-fill', 'fill-color', c.line);
          map.setPaintProperty('paris-districts-fill', 'fill-opacity', style.fillOpacity);
        }
      }
      if (map.getLayer('paris-districts-line')) {
        const codeExpr = ['coalesce', ['get', 'c_arinsee'], ['get', 'c_ar'], ['get', 'insee_com']];
        map.setPaintProperty('paris-districts-line', 'line-color', [
          'case',
          ['==', codeExpr, sel || ''], c.sel,
          ['==', codeExpr, comp || ''], c.comp,
          c.line,
        ]);
        map.setPaintProperty('paris-districts-line', 'line-width', [
          'case',
          ['in', codeExpr, ['literal', [sel || '', comp || '']]], 3.5,
          style.lineWidth,
        ]);
      }
    } catch (e) { console.warn('Style update failed', e); }
  }, []);

  const applyStyles3D = useCallback((map: mapboxgl.Map, level: number, active: string, sel: string | null, comp: string | null, th: Theme) => {
    const style = LEVEL_STYLES[level] || LEVEL_STYLES[1];
    const c = THEME_COLORS[th];
    const choro = getChoroplethColorExpression(active, th);
    try {
      if (map.getLayer('paris-base-fill-3d')) {
        map.setPaintProperty('paris-base-fill-3d', 'fill-color', choro as any);
        map.setPaintProperty('paris-base-fill-3d', 'fill-opacity', level === 2 ? 0.15 : level === 0 ? 0.1 : 0.6);
      }
      if (map.getLayer('paris-districts-fill-3d')) {
        if (level === 2 || level === 4) {
          map.setPaintProperty('paris-districts-fill-3d', 'fill-color', choro as any);
          map.setPaintProperty('paris-districts-fill-3d', 'fill-opacity', 0.65);
        } else if (level === 1) {
          map.setPaintProperty('paris-districts-fill-3d', 'fill-color', 'rgba(0,0,0,0)');
          map.setPaintProperty('paris-districts-fill-3d', 'fill-opacity', 0.0);
        } else {
          map.setPaintProperty('paris-districts-fill-3d', 'fill-color', c.line);
          map.setPaintProperty('paris-districts-fill-3d', 'fill-opacity', style.fillOpacity);
        }
      }
      if (map.getLayer('paris-districts-line-3d')) {
        const codeExpr = ['coalesce', ['get', 'c_arinsee'], ['get', 'c_ar'], ['get', 'insee_com']];
        map.setPaintProperty('paris-districts-line-3d', 'line-color', [
          'case',
          ['==', codeExpr, sel || ''], c.sel,
          ['==', codeExpr, comp || ''], c.comp,
          c.line,
        ] as any);
        map.setPaintProperty('paris-districts-line-3d', 'line-width', [
          'case',
          ['in', codeExpr, ['literal', [sel || '', comp || '']]], 3.5,
          style.lineWidth,
        ] as any);
      }
    } catch (e) { console.warn('Style update failed', e); }
  }, []);

  /* ── Carte 2D (MapLibre + fond IGN clair / Carto sombre) ──────────── */

  useEffect(() => {
    if (mapMode !== '2d' || !mapContainer2D.current) return;
    if (map2DRef.current) map2DRef.current.remove();

    const ignSource: maplibregl.RasterSourceSpecification = {
      type: 'raster',
      tiles: ['https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&TILEMATRIXSET=PM&FORMAT=image/png&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}'],
      tileSize: 256,
      attribution: '© IGN · Géoplateforme',
    };
    const cartoDark: maplibregl.RasterSourceSpecification = {
      type: 'raster',
      tiles: ['https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', 'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', 'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap, © CARTO',
    };

    const map = new maplibregl.Map({
      container: mapContainer2D.current,
      style: {
        version: 8,
        sources: { basemap: theme === 'dark' ? cartoDark : ignSource },
        layers: [{ id: 'basemap-layer', type: 'raster', source: 'basemap', minzoom: 0, maxzoom: 20 }],
      },
      center: [2.349014, 48.853316],
      zoom: 11.5,
      pitch: 0,
    });

    map2DRef.current = map;
    map.on('zoomend', () => updateGranularityByZoom(map.getZoom()));

    map.on('load', async () => {
      try {
        const level = granularityRef.current;
        const style = LEVEL_STYLES[level] || LEVEL_STYLES[1];
        const c = THEME_COLORS[theme];

        const baseGeojson = await api.fetchGeoJsonByGranularity(1);
        map.addSource('paris-base', { type: 'geojson', data: baseGeojson });
        map.addLayer({
          id: 'paris-base-fill', type: 'fill', source: 'paris-base',
          paint: { 'fill-color': getChoroplethColorExpression(activeFamily, theme), 'fill-opacity': 0.6 },
        });

        const geojson = await api.fetchGeoJsonByGranularity(level);
        if (!geojson.features || geojson.features.length === 0) return;
        map.addSource('paris-bounds', { type: 'geojson', data: geojson });
        map.addLayer({
          id: 'paris-districts-fill', type: 'fill', source: 'paris-bounds',
          paint: { 'fill-color': c.line, 'fill-opacity': style.fillOpacity },
        });
        map.addLayer({
          id: 'paris-districts-line', type: 'line', source: 'paris-bounds',
          paint: { 'line-color': c.line, 'line-width': style.lineWidth },
        });

        applyStyles2D(map, level, activeFamily, selectedDistrict, comparedDistrict, theme);

        map.on('click', 'paris-districts-fill', (e) => {
          if (e.features && e.features[0]) handleMapClick(e.features[0].properties);
        });
        map.on('mouseenter', 'paris-districts-fill', () => { map.getCanvas().style.cursor = 'pointer'; });
        map.on('mouseleave', 'paris-districts-fill', () => { map.getCanvas().style.cursor = ''; });
      } catch (err) { console.error('GeoJSON load failed', err); }
    });

    return () => { if (map2DRef.current) { map2DRef.current.remove(); map2DRef.current = null; } };
  }, [mapMode, theme, handleMapClick]);

  /* ── Mises à jour 2D (granularité / thématique / sélection) ───────── */

  useEffect(() => {
    const map = map2DRef.current;
    if (!map || !map.getSource('paris-bounds') || loadingRef.current) return;

    loadingRef.current = true;
    api.fetchGeoJsonByGranularity(granularity)
      .then((data) => {
        const source = map.getSource('paris-bounds') as maplibregl.GeoJSONSource | undefined;
        source?.setData(data);
        applyStyles2D(map, granularity, activeFamily, selectedDistrict, comparedDistrict, theme);
      })
      .catch((err) => console.error('GeoJSON update failed', err))
      .finally(() => { loadingRef.current = false; });
  }, [granularity, activeFamily, selectedDistrict, comparedDistrict, theme, applyStyles2D]);

  /* ── Carte 3D (Mapbox) ────────────────────────────────────────────── */

  useEffect(() => {
    if (mapMode !== '3d' || !mapContainer3D.current || !mapboxToken) return;
    if (map3DRef.current) map3DRef.current.remove();

    mapboxgl.accessToken = mapboxToken;

    const map = new mapboxgl.Map({
      container: mapContainer3D.current,
      style: theme === 'dark' ? 'mapbox://styles/mapbox/dark-v11' : 'mapbox://styles/mapbox/light-v11',
      center: [2.349014, 48.853316],
      zoom: 12,
      pitch: 60,
      bearing: -20,
    });

    map3DRef.current = map;
    map.on('zoomend', () => updateGranularityByZoom(map.getZoom()));

    map.on('load', async () => {
      const c = THEME_COLORS[theme];
      const layers = map.getStyle().layers;
      const labelLayerId = layers?.find((layer: any) => layer.type === 'symbol' && layer.layout?.['text-field'])?.id;

      map.addLayer({
        id: '3d-buildings', source: 'composite', 'source-layer': 'building',
        filter: ['==', 'extrude', 'true'], type: 'fill-extrusion', minzoom: 14,
        paint: {
          'fill-extrusion-color': c.buildings,
          'fill-extrusion-height': ['interpolate', ['linear'], ['zoom'], 15, 0, 15.05, ['get', 'height']],
          'fill-extrusion-base': ['interpolate', ['linear'], ['zoom'], 15, 0, 15.05, ['get', 'min_height']],
          'fill-extrusion-opacity': 0.6,
        },
      }, labelLayerId);

      try {
        const level = granularityRef.current;
        const style = LEVEL_STYLES[level] || LEVEL_STYLES[1];

        const baseGeojson = await api.fetchGeoJsonByGranularity(1);
        map.addSource('paris-base-3d', { type: 'geojson', data: baseGeojson });
        map.addLayer({
          id: 'paris-base-fill-3d', type: 'fill', source: 'paris-base-3d',
          paint: { 'fill-color': getChoroplethColorExpression(activeFamily, theme) as any, 'fill-opacity': 0.6 },
        });

        const geojson = await api.fetchGeoJsonByGranularity(level);
        if (!geojson.features || geojson.features.length === 0) return;
        map.addSource('paris-bounds-3d', { type: 'geojson', data: geojson });
        map.addLayer({
          id: 'paris-districts-fill-3d', type: 'fill', source: 'paris-bounds-3d',
          paint: { 'fill-color': c.line, 'fill-opacity': style.fillOpacity },
        });
        map.addLayer({
          id: 'paris-districts-line-3d', type: 'line', source: 'paris-bounds-3d',
          paint: { 'line-color': c.line, 'line-width': style.lineWidth },
        });

        applyStyles3D(map, level, activeFamily, selectedDistrict, comparedDistrict, theme);

        map.on('click', 'paris-districts-fill-3d', (e) => {
          if (e.features && e.features[0]) handleMapClick(e.features[0].properties);
        });
      } catch (err) { console.error('GeoJSON load failed', err); }
    });

    return () => { if (map3DRef.current) { map3DRef.current.remove(); map3DRef.current = null; } };
  }, [mapMode, mapboxToken, theme, handleMapClick]);

  /* ── Mises à jour 3D ──────────────────────────────────────────────── */

  useEffect(() => {
    const map = map3DRef.current;
    if (!map || !map.getSource('paris-bounds-3d')) return;

    api.fetchGeoJsonByGranularity(granularity).then((data) => {
      const source = map.getSource('paris-bounds-3d') as mapboxgl.GeoJSONSource | undefined;
      source?.setData(data);
      applyStyles3D(map, granularity, activeFamily, selectedDistrict, comparedDistrict, theme);
    });
  }, [granularity, activeFamily, selectedDistrict, comparedDistrict, theme, applyStyles3D]);

  /* ── Vol vers le secteur sélectionné ──────────────────────────────── */

  useEffect(() => {
    if (selectedDistrict && coords[selectedDistrict]) {
      const center = coords[selectedDistrict];
      if (mapMode === '2d' && map2DRef.current) {
        map2DRef.current.flyTo({ center, zoom: 13, duration: 1500 });
      } else if (mapMode === '3d' && map3DRef.current) {
        map3DRef.current.flyTo({ center, zoom: 13.5, pitch: 50, duration: 1800 });
      }
    }
  }, [selectedDistrict, mapMode]);

  const currentStyle = LEVEL_STYLES[granularity] || LEVEL_STYLES[1];
  const legendInfo = getLegendDetails(activeFamily);
  const seqGradient = theme === 'dark'
    ? 'linear-gradient(to right, #272747, #5b5bd6, #8585f6, #b1b1f9)'
    : 'linear-gradient(to right, #e3e3fd, #8585f6, #4d4dde, #000091)';

  return (
    <>
      {mapMode === '2d' ? (
        <div ref={mapContainer2D} className="map-viewport" />
      ) : mapboxToken ? (
        <div ref={mapContainer3D} className="map-viewport" />
      ) : (
        <div className="map-viewport" style={{ background: 'var(--bg-alt)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '16px', zIndex: 1, padding: '24px' }}>
          <AlertTriangle size={40} style={{ color: 'var(--warning)' }} />
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-title)' }}>Jeton Mapbox requis pour la vue 3D</h2>
          <p style={{ color: 'var(--text-default)', maxWidth: '420px', textAlign: 'center', fontSize: '14px', lineHeight: 1.5 }}>
            Pour explorer Paris en 3D (hauteurs de bâtiments, relief), renseignez votre jeton d’accès Mapbox.
            La vue 2D s’appuie sur le fond de plan IGN et ne nécessite aucun jeton.
          </p>
          <button onClick={() => setShowSettings(true)} className="dsfr-btn dsfr-btn--primary" style={{ marginTop: '4px' }}>
            <Settings size={18} /> Configurer le jeton
          </button>
        </div>
      )}

      {/* Légende choroplèthe */}
      {granularity >= 1 && (
        <div
          className="dsfr-surface"
          style={{ position: 'absolute', bottom: '16px', left: '16px', zIndex: 12, padding: '12px 16px', width: '272px', display: 'flex', flexDirection: 'column', gap: '8px' }}
        >
          <span className="dsfr-eyebrow" style={{ color: 'var(--text-title)' }}>{legendInfo.title}</span>
          <div style={{ height: '10px', background: seqGradient, width: '100%' }} />
          <div className="tabular" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-mention)' }}>
            <span>{legendInfo.minLabel}</span>
            <span>{legendInfo.midLabel}</span>
            <span>{legendInfo.maxLabel}</span>
          </div>
        </div>
      )}

      {/* Indicateur de niveau */}
      <div
        className="dsfr-surface"
        style={{ position: 'absolute', bottom: '16px', left: '50%', transform: 'translateX(-50%)', zIndex: 12, display: 'flex', alignItems: 'center', gap: '8px', padding: '7px 16px' }}
      >
        <span className="dsfr-status-dot" style={{ background: 'var(--blue-france)' }} />
        <span className="tabular" style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-title)', letterSpacing: '0.02em' }}>
          Niveau {granularity} · {currentStyle.label}
        </span>
      </div>
    </>
  );
};

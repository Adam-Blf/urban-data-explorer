import React, { useEffect, useRef, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import mapboxgl from 'mapbox-gl';
import { AlertTriangle, Settings } from 'lucide-react';
import { api } from '../services/api';

/* ── Style configuration per granularity level ─────────────────────────── */

const LEVEL_STYLES: Record<number, {
  fillColor: string;
  lineColor: string;
  lineWidth: number;
  fillOpacity: number;
  label: string;
}> = {
  0: { fillColor: '#06b6d4', lineColor: '#0891b2', lineWidth: 2.5, fillOpacity: 0.10, label: 'Ville' },
  1: { fillColor: '#06b6d4', lineColor: '#0891b2', lineWidth: 1.5, fillOpacity: 0.15, label: 'Arrondissement' },
  2: { fillColor: '#3b82f6', lineColor: '#2563eb', lineWidth: 1.0, fillOpacity: 0.10, label: 'IRIS' },
  3: { fillColor: '#f59e0b', lineColor: '#d97706', lineWidth: 2.0, fillOpacity: 0.0,  label: 'Rue' },
  4: { fillColor: '#8b5cf6', lineColor: '#7c3aed', lineWidth: 0.5, fillOpacity: 0.20, label: 'Bâtiment' },
};

/* ── Property extraction per level (for click handler) ─────────────────── */

function extractCode(level: number, properties: Record<string, unknown> | null | undefined): string | null {
  if (!properties) return null;
  switch (level) {
    case 0:
      return typeof properties.name === 'string' ? properties.name : null;
    case 1: {
      // Open Data Paris arrondissements
      const code = properties.c_arinsee ?? properties.c_ar ?? properties.insee_com;
      return code != null ? String(code) : null;
    }
    case 2: {
      // IRIS — extract arrondissement code
      const iris = properties.code_iris ?? properties.c_iris ?? properties.iris;
      if (typeof iris === 'string') return iris.substring(0, 5);
      const arCode = properties.c_arinsee ?? properties.c_ar;
      return arCode != null ? String(arCode) : null;
    }
    case 3:
      return typeof properties.l_voie === 'string'
        ? properties.l_voie
        : typeof properties.name === 'string'
          ? properties.name
          : null;
    case 4:
      return typeof properties.n_sq_vo === 'string'
        ? properties.n_sq_vo
        : typeof properties.name === 'string'
          ? properties.name
          : null;
    default:
      return null;
  }
}

/* ── Component ─────────────────────────────────────────────────────────── */

interface MapViewportProps {
  mapMode: '2d' | '3d';
  mapboxToken: string;
  setShowSettings: (show: boolean) => void;
  selectedDistrict: string | null;
  setSelectedDistrict: (code: string) => void;
  granularity: number;
  setGranularity: (level: number) => void;
}

export const MapViewport: React.FC<MapViewportProps> = ({
  mapMode,
  mapboxToken,
  setShowSettings,
  selectedDistrict,
  setSelectedDistrict,
  granularity,
  setGranularity
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
    '75019': [2.3802, 48.8870], '75020': [2.4014, 48.8631]
  };

  useEffect(() => {
   granularityRef.current = granularity;
  }, [granularity]);

  const updateGranularityByZoom = useCallback((zoom: number) => {
   let level = 0;
   if (zoom >= 16) level = 4;      // Bâtiment
   else if (zoom >= 14) level = 3; // Rue
   else if (zoom >= 12) level = 2; // IRIS
   else if (zoom >= 10) level = 1; // Arrondissement
   else level = 0;                // Ville

   if (level !== granularityRef.current) {
     granularityRef.current = level;
     setGranularity(level);
   }
  }, [setGranularity]);

  /* ── Helper: apply level-specific paint properties ─────────────────── */

  const applyLevelStyle2D = useCallback((map: maplibregl.Map, level: number) => {
    const style = LEVEL_STYLES[level] || LEVEL_STYLES[1];
    try {
      if (map.getLayer('paris-districts-fill')) {
        map.setPaintProperty('paris-districts-fill', 'fill-color', style.fillColor);
        map.setPaintProperty('paris-districts-fill', 'fill-opacity', style.fillOpacity);
      }
      if (map.getLayer('paris-districts-line')) {
        map.setPaintProperty('paris-districts-line', 'line-color', style.lineColor);
        map.setPaintProperty('paris-districts-line', 'line-width', style.lineWidth);
      }
    } catch (e) {
      console.warn('Style update failed', e);
    }
  }, []);

  const applyLevelStyle3D = useCallback((map: mapboxgl.Map, level: number) => {
    const style = LEVEL_STYLES[level] || LEVEL_STYLES[1];
    try {
      if (map.getLayer('paris-districts-fill-3d')) {
        map.setPaintProperty('paris-districts-fill-3d', 'fill-color', style.fillColor);
        map.setPaintProperty('paris-districts-fill-3d', 'fill-opacity', style.fillOpacity);
      }
      if (map.getLayer('paris-districts-line-3d')) {
        map.setPaintProperty('paris-districts-line-3d', 'line-color', style.lineColor);
        map.setPaintProperty('paris-districts-line-3d', 'line-width', style.lineWidth);
      }
    } catch (e) {
      console.warn('Style update failed', e);
    }
  }, []);

  /* ── 2D Map ────────────────────────────────────────────────────────── */

  useEffect(() => {
    if (mapMode !== '2d' || !mapContainer2D.current) return;
    if (map2DRef.current) map2DRef.current.remove();

    const map = new maplibregl.Map({
      container: mapContainer2D.current,
      style: {
        version: 8,
        sources: {
          'carto-dark': {
            type: 'raster',
            tiles: ['https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', 'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', 'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '© OpenStreetMap, © CartoDB'
          }
        },
        layers: [{ id: 'carto-dark-layer', type: 'raster', source: 'carto-dark', minzoom: 0, maxzoom: 20 }]
      },
      center: [2.349014, 48.853316],
      zoom: 11.5,
      pitch: 0
    });

    map2DRef.current = map;

    map.on('zoomend', () => {
      updateGranularityByZoom(map.getZoom());
    });

    map.on('load', async () => {
      try {
        const level = granularityRef.current;
        const style = LEVEL_STYLES[level] || LEVEL_STYLES[1];
        const geojson = await api.fetchGeoJsonByGranularity(level);
        if (!geojson.features || geojson.features.length === 0) return;
        map.addSource('paris-bounds', { type: 'geojson', data: geojson });
        map.addLayer({
          id: 'paris-districts-fill',
          type: 'fill',
          source: 'paris-bounds',
          paint: { 'fill-color': style.fillColor, 'fill-opacity': style.fillOpacity, 'fill-outline-color': style.lineColor }
        });
        map.addLayer({
          id: 'paris-districts-line',
          type: 'line',
          source: 'paris-bounds',
          paint: { 'line-color': style.lineColor, 'line-width': style.lineWidth }
        });
        map.on('click', 'paris-districts-fill', (e) => {
          if (e.features && e.features[0]) {
            const properties = e.features[0].properties as Record<string, unknown> | null | undefined;
            const code = extractCode(granularityRef.current, properties);
            if (code) setSelectedDistrict(code);
          }
        });
      } catch (err) { console.error('GeoJSON load failed', err); }
    });

    return () => { if (map2DRef.current) { map2DRef.current.remove(); map2DRef.current = null; } };
  }, [mapMode]);

  /* ── Granularity change → reload data + update style (2D) ──────────── */

  useEffect(() => {
    const map = map2DRef.current;
    if (!map || !map.getSource('paris-bounds') || loadingRef.current) return;

    loadingRef.current = true;
    api.fetchGeoJsonByGranularity(granularity)
      .then(data => {
        const source = map.getSource('paris-bounds') as maplibregl.GeoJSONSource | undefined;
        source?.setData(data);
        applyLevelStyle2D(map, granularity);
      })
      .catch(err => console.error('GeoJSON update failed', err))
      .finally(() => { loadingRef.current = false; });
  }, [granularity, applyLevelStyle2D]);

  /* ── 3D Map ────────────────────────────────────────────────────────── */

  useEffect(() => {
    if (mapMode !== '3d' || !mapContainer3D.current || !mapboxToken) return;
    if (map3DRef.current) map3DRef.current.remove();

    mapboxgl.accessToken = mapboxToken;

    const map = new mapboxgl.Map({
      container: mapContainer3D.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [2.349014, 48.853316],
      zoom: 12,
      pitch: 60,
      bearing: -20
    });

    map3DRef.current = map;

    map.on('zoomend', () => {
      updateGranularityByZoom(map.getZoom());
    });

    map.on('load', async () => {
      const layers = map.getStyle().layers;
      const labelLayerId = layers?.find((layer: any) => layer.type === 'symbol' && layer.layout?.['text-field'])?.id;

      // Mapbox native building extrusion (always available for 3D)
      map.addLayer({
        id: '3d-buildings',
        source: 'composite',
        'source-layer': 'building',
        filter: ['==', 'extrude', 'true'],
        type: 'fill-extrusion',
        minzoom: 14,
        paint: {
          'fill-extrusion-color': '#06b6d4',
          'fill-extrusion-height': ['interpolate', ['linear'], ['zoom'], 15, 0, 15.05, ['get', 'height']],
          'fill-extrusion-base': ['interpolate', ['linear'], ['zoom'], 15, 0, 15.05, ['get', 'min_height']],
          'fill-extrusion-opacity': 0.6
        }
      }, labelLayerId);

      try {
        const level = granularityRef.current;
        const style = LEVEL_STYLES[level] || LEVEL_STYLES[1];
        const geojson = await api.fetchGeoJsonByGranularity(level);
        if (!geojson.features || geojson.features.length === 0) return;
        map.addSource('paris-bounds-3d', { type: 'geojson', data: geojson });
        map.addLayer({
          id: 'paris-districts-fill-3d',
          type: 'fill',
          source: 'paris-bounds-3d',
          paint: { 'fill-color': style.fillColor, 'fill-opacity': style.fillOpacity }
        });
        map.addLayer({
          id: 'paris-districts-line-3d',
          type: 'line',
          source: 'paris-bounds-3d',
          paint: { 'line-color': style.lineColor, 'line-width': style.lineWidth }
        });
        map.on('click', 'paris-districts-fill-3d', (e) => {
          if (e.features && e.features[0]) {
            const properties = e.features[0].properties as Record<string, unknown> | null | undefined;
            const code = extractCode(granularityRef.current, properties);
            if (code) setSelectedDistrict(code);
          }
        });
      } catch (err) { console.error('GeoJSON load failed', err); }
    });

    return () => { if (map3DRef.current) { map3DRef.current.remove(); map3DRef.current = null; } };
  }, [mapMode, mapboxToken]);

  /* ── Granularity change → reload data + update style (3D) ──────────── */

  useEffect(() => {
    const map = map3DRef.current;
    if (!map || !map.getSource('paris-bounds-3d')) return;

    api.fetchGeoJsonByGranularity(granularity).then(data => {
      const source = map.getSource('paris-bounds-3d') as mapboxgl.GeoJSONSource | undefined;
      source?.setData(data);
      applyLevelStyle3D(map, granularity);
    });
  }, [granularity, applyLevelStyle3D]);

  /* ── Fly to selected district ──────────────────────────────────────── */

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

  /* ── Level indicator overlay ───────────────────────────────────────── */

  const currentStyle = LEVEL_STYLES[granularity] || LEVEL_STYLES[1];

  return (
    <>
      {mapMode === '2d' ? (
        <div ref={mapContainer2D} className="map-viewport" />
      ) : mapboxToken ? (
        <div ref={mapContainer3D} className="map-viewport" />
      ) : (
        <div className="map-viewport flex items-center justify-center" style={{ background: '#0a0c10', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '16px', zIndex: 1 }}>
          <AlertTriangle size={48} className="text-warning pulse-element" style={{ color: 'var(--accent-purple)' }} />
          <h2 style={{ fontSize: '20px', fontWeight: 600 }}>Jeton Mapbox 3D Requis</h2>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '400px', textAlign: 'center', fontSize: '14px' }}>
            Pour explorer Paris en 3D avec hauteurs de bâtiments et relief, configurez votre clé Mapbox dans les paramètres.
          </p>
          <button onClick={() => setShowSettings(true)} className="btn-tab active" style={{ marginTop: '8px' }}>
            <Settings size={18} /> Configurer maintenant
          </button>
        </div>
      )}

      {/* Level indicator badge */}
      <div style={{
        position: 'absolute',
        bottom: '30px',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 15,
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        background: 'rgba(10, 12, 16, 0.85)',
        backdropFilter: 'blur(12px)',
        border: `1px solid ${currentStyle.lineColor}40`,
        borderRadius: '20px',
        padding: '6px 16px',
        transition: 'all 0.3s ease',
      }}>
        <div style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          background: currentStyle.lineColor,
          boxShadow: `0 0 8px ${currentStyle.lineColor}`,
        }} />
        <span style={{
          fontSize: '12px',
          fontWeight: 600,
          color: currentStyle.lineColor,
          letterSpacing: '0.03em',
        }}>
          Niveau {granularity} — {currentStyle.label}
        </span>
      </div>
    </>
  );
};

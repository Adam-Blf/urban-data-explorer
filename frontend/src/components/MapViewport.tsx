import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import mapboxgl from 'mapbox-gl';
import { AlertTriangle, Settings } from 'lucide-react';
import { api } from '../services/api';

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

  const updateGranularityByZoom = (zoom: number) => {
   let level = 0;
   if (zoom >= 16) level = 4;      // Immeuble
   else if (zoom >= 14) level = 3; // Rue
   else if (zoom >= 12) level = 2; // IRIS
   else if (zoom >= 10) level = 1; // Arrondissement
   else level = 0;                // Ville

   if (level !== granularityRef.current) {
     granularityRef.current = level;
     setGranularity(level);
   }
  };

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
        const geojson = await api.fetchGeoJsonByGranularity(granularityRef.current);
        if (!geojson.features || geojson.features.length === 0) return;
        map.addSource('paris-bounds', { type: 'geojson', data: geojson });
        map.addLayer({
          id: 'paris-districts-fill',
          type: 'fill',
          source: 'paris-bounds',
          paint: { 'fill-color': '#06b6d4', 'fill-opacity': 0.15, 'fill-outline-color': '#0891b2' }
        });
        map.addLayer({
          id: 'paris-districts-line',
          type: 'line',
          source: 'paris-bounds',
          paint: { 'line-color': '#06b6d4', 'line-width': 1.5 }
        });
        map.on('click', 'paris-districts-fill', (e) => {
          if (e.features && e.features[0]) {
            const properties = e.features[0].properties as Record<string, unknown> | null | undefined;
            const code = typeof properties?.insee_com === 'string'
              ? properties.insee_com
              : typeof properties?.code_iris === 'string'
                ? properties.code_iris.substring(0, 5)
                : null;
            if (code) setSelectedDistrict(code);
          }
        });
      } catch (err) { console.error('GeoJSON load failed', err); }
    });

    return () => { if (map2DRef.current) { map2DRef.current.remove(); map2DRef.current = null; } };
  }, [mapMode]);

  useEffect(() => {
    if (map2DRef.current && map2DRef.current.getSource('paris-bounds')) {
      api.fetchGeoJsonByGranularity(granularity).then(data => {
        const source = map2DRef.current?.getSource('paris-bounds') as maplibregl.GeoJSONSource | undefined;
        source?.setData(data);
      });
    }
  }, [granularity]);

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
        const geojson = await api.fetchGeoJsonByGranularity(granularityRef.current);
        if (!geojson.features || geojson.features.length === 0) return;
        map.addSource('paris-bounds-3d', { type: 'geojson', data: geojson });
        map.addLayer({
          id: 'paris-districts-fill-3d',
          type: 'fill',
          source: 'paris-bounds-3d',
          paint: { 'fill-color': '#8b5cf6', 'fill-opacity': 0.12 }
        });
        map.addLayer({
          id: 'paris-districts-line-3d',
          type: 'line',
          source: 'paris-bounds-3d',
          paint: { 'line-color': '#8b5cf6', 'line-width': 1.5 }
        });
        map.on('click', 'paris-districts-fill-3d', (e) => {
          if (e.features && e.features[0]) {
            const properties = e.features[0].properties as Record<string, unknown> | null | undefined;
            const code = typeof properties?.insee_com === 'string'
              ? properties.insee_com
              : typeof properties?.code_iris === 'string'
                ? properties.code_iris.substring(0, 5)
                : null;
            if (code) setSelectedDistrict(code);
          }
        });
      } catch (err) { console.error('GeoJSON load failed', err); }
    });

    return () => { if (map3DRef.current) { map3DRef.current.remove(); map3DRef.current = null; } };
  }, [mapMode, mapboxToken]);

  useEffect(() => {
    if (map3DRef.current && map3DRef.current.getSource('paris-bounds-3d')) {
      api.fetchGeoJsonByGranularity(granularity).then(data => {
        const source = map3DRef.current?.getSource('paris-bounds-3d') as mapboxgl.GeoJSONSource | undefined;
        source?.setData(data);
      });
    }
  }, [granularity]);

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
    </>
  );
};

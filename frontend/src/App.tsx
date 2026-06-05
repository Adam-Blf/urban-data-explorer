import React, { useEffect, useState } from 'react';
import { api } from './services/api';
import { District, Overview, TimelinePoint, EventLog } from './types';
import { Header } from './components/Header';
import { ControlPanel } from './components/ControlPanel';
import { DataPanel } from './components/DataPanel';
import { MapViewport } from './components/MapViewport';
import { SettingsDrawer } from './components/SettingsDrawer';

type Theme = 'light' | 'dark';

export default function App() {
  // Config & Modes
  const [mapMode, setMapMode] = useState<'2d' | '3d'>('2d');
  const [mapboxToken, setMapboxToken] = useState<string>(() => {
    return localStorage.getItem('ude_mapbox_token') || '';
  });
  const [showSettings, setShowSettings] = useState(false);

  // Thème DSFR (clair par défaut, codes officiels)
  const [theme, setTheme] = useState<Theme>(() => {
    return (localStorage.getItem('ude_theme') as Theme) || 'light';
  });
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ude_theme', theme);
  }, [theme]);

  // Granularities & Filters
  const [granularity, setGranularity] = useState<number>(1);
  const [activeFamily, setActiveFamily] = useState<string>('all');
  const [selectedDistrict, setSelectedDistrict] = useState<string | null>(null);
  const [comparedDistrict, setComparedDistrict] = useState<string | null>(null);

  // Panel visibility
  const [showControlPanel, setShowControlPanel] = useState<boolean>(true);
  const [showDataPanel, setShowDataPanel] = useState<boolean>(true);

  // API Data
  const [districts, setDistricts] = useState<District[]>([]);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [events, setEvents] = useState<EventLog[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  const fetchData = async () => {
    try {
      const connected = await api.checkHealth();
      setIsConnected(connected);

      const [d, o, t, e] = await Promise.all([
        api.fetchDashboard(),
        api.fetchOverview(),
        api.fetchTimeline(),
        api.fetchEvents()
      ]);

      setDistricts(d);
      setOverview(o);
      setTimeline(t);
      setEvents(e);
    } catch (err) {
      console.warn('API non disponible, utilisation des données locales de secours.', err);
      setIsConnected(false);

      // Fallback local mock data with 4 categories indices and raw values
      setOverview({
        source_count: 19,
        family_count: 8,
        district_count: 20,
        accessibility_index: 68,
        pressure_index: 42,
        attractiveness_index: 71,
        source_family_counts: {
          housing: 3, mobility: 4, education: 3, green_space: 2,
          culture: 2, health: 1, public_service: 2, pressure: 2
        },
        immobilier_idx: 65,
        logement_social_idx: 22,
        revenu_idx: 55,
        cadre_vie_idx: 68,
        environnement_idx: 72,
        prix_m2: 11200.0,
        logement_social_pct: 14.5,
        revenu_median: 32000.0,
      });

      const mockDistricts = Array.from({ length: 20 }, (_, i) => {
        const code = `750${(i + 1).toString().padStart(2, '0')}`;
        const prix = 8000 + (i * 400) % 8000;
        const pct = 3.0 + (i * 2.5) % 35;
        const count = Math.round(pct * 500);
        const income = 20000 + (i * 1500) % 28000;
        const vol = 150 + (i * 35) % 700;
        const base_acc = 55 + (i * 2) % 30;

        const immobilier_idx = Math.round(((prix - 8000) / 8000) * 100);
        const logement_social_idx = Math.round(pct * 2.5);
        const revenu_idx = Math.round(((income - 20000) / 28000) * 100);
        const cadre_vie_idx = Math.round(base_acc);
        const environnement_idx = Math.round(55 + (i * 4) % 35);
        const score = Math.round((immobilier_idx + logement_social_idx + revenu_idx + cadre_vie_idx + environnement_idx) / 5);

        return {
          code,
          name: `Arrondissement ${i + 1}`,
          label: `${i + 1}e`,
          family_counts: {
            housing: 5 + (i % 3), mobility: 6 + (i % 2), education: 4, green_space: 3,
            culture: 2, health: 2, public_service: 3, pressure: 4
          },
          accessibility_index: base_acc,
          pressure_index: 30 + (i * 3) % 40,
          attractiveness_index: 60 + (i * 2.5) % 35,
          score,
          immobilier_idx,
          logement_social_idx,
          revenu_idx,
          cadre_vie_idx,
          environnement_idx,
          prix_m2: prix,
          logements_sociaux_count: count,
          logement_social_pct: pct,
          revenu_median: income,
          sales_volume: vol
        };
      });
      setDistricts(mockDistricts);

      setTimeline(Array.from({ length: 12 }, (_, i) => ({
        month: `2025-${(i + 1).toString().padStart(2, '0')}`,
        label: `Mois ${i + 1}`,
        activity: 80 + i * 2,
        accessibility_index: 65 + Math.sin(i) * 3,
        pressure_index: 40 + Math.cos(i) * 2,
        attractiveness_index: 70 + Math.sin(i * 0.5) * 4,
        immobilier_idx: 65 + Math.sin(i * 0.4) * 2,
        logement_social_idx: 22 + Math.cos(i * 0.3) * 0.5,
        revenu_idx: 55 + Math.sin(i * 0.5) * 1.5,
        cadre_vie_idx: 65 + Math.sin(i) * 3,
        environnement_idx: 70 + Math.cos(i * 0.4) * 3
      })));
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  const saveToken = (token: string) => {
    setMapboxToken(token);
    localStorage.setItem('ude_mapbox_token', token);
    window.location.reload();
  };

  const maxActivity = timeline.length ? Math.max(...timeline.map(t => t.activity)) : 100;

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', background: 'var(--bg)' }}>
      <MapViewport
        mapMode={mapMode}
        mapboxToken={mapboxToken}
        theme={theme}
        setShowSettings={setShowSettings}
        selectedDistrict={selectedDistrict}
        setSelectedDistrict={setSelectedDistrict}
        comparedDistrict={comparedDistrict}
        setComparedDistrict={setComparedDistrict}
        granularity={granularity}
        setGranularity={setGranularity}
        activeFamily={activeFamily}
      />

      <Header
        isConnected={isConnected}
        mapMode={mapMode}
        setMapMode={setMapMode}
        theme={theme}
        setTheme={setTheme}
        showSettings={showSettings}
        setShowSettings={setShowSettings}
        showControlPanel={showControlPanel}
        setShowControlPanel={setShowControlPanel}
        showDataPanel={showDataPanel}
        setShowDataPanel={setShowDataPanel}
      />

      <SettingsDrawer
        showSettings={showSettings}
        setShowSettings={setShowSettings}
        mapboxToken={mapboxToken}
        saveToken={saveToken}
      />

      <ControlPanel
        granularity={granularity}
        setGranularity={setGranularity}
        activeFamily={activeFamily}
        setActiveFamily={setActiveFamily}
        style={{
          left: showControlPanel ? '16px' : '-420px',
          right: 'auto',
          transition: 'left 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
        }}
        onClose={() => setShowControlPanel(false)}
      />

      <DataPanel
        selectedDistrict={selectedDistrict}
        setSelectedDistrict={setSelectedDistrict}
        comparedDistrict={comparedDistrict}
        setComparedDistrict={setComparedDistrict}
        districts={districts}
        overview={overview}
        timeline={timeline}
        events={events}
        activeFamily={activeFamily}
        maxActivity={maxActivity}
        style={{
          right: showDataPanel ? '16px' : '-480px',
          transition: 'right 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
        }}
        onClose={() => setShowDataPanel(false)}
      />
    </div>
  );
}

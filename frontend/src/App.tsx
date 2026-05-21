import React, { useEffect, useState } from 'react';
import { api } from './services/api';
import { District, Overview, TimelinePoint, EventLog } from './types';
import { Header } from './components/Header';
import { ControlPanel } from './components/ControlPanel';
import { DataPanel } from './components/DataPanel';
import { MapViewport } from './components/MapViewport';
import { SettingsDrawer } from './components/SettingsDrawer';

export default function App() {
  // Config & Modes
  const [mapMode, setMapMode] = useState<'2d' | '3d'>('2d');
  const [mapboxToken, setMapboxToken] = useState<string>(() => {
    return localStorage.getItem('ude_mapbox_token') || '';
  });
  const [showSettings, setShowSettings] = useState(false);

  // Granularities & Filters
  const [granularity, setGranularity] = useState<number>(1);
  const [activeFamily, setActiveFamily] = useState<string>('all');
  const [selectedDistrict, setSelectedDistrict] = useState<string | null>(null);

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

      // Fallback local mock data (keeping the a-bit-of-life version from original)
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
        }
      });

      const mockDistricts = Array.from({ length: 20 }, (_, i) => {
        const code = `750${(i + 1).toString().padStart(2, '0')}`;
        return {
          code,
          name: `Arrondissement ${i + 1}`,
          label: `${i + 1}e`,
          family_counts: {
            housing: 5 + (i % 3), mobility: 6 + (i % 2), education: 4, green_space: 3,
            culture: 2, health: 2, public_service: 3, pressure: 4
          },
          accessibility_index: 55 + (i * 2) % 30,
          pressure_index: 30 + (i * 3) % 40,
          attractiveness_index: 60 + (i * 2.5) % 35,
          score: 62 + i % 15
        };
      });
      setDistricts(mockDistricts);

      setTimeline(Array.from({ length: 12 }, (_, i) => ({
        month: `2025-${(i + 1).toString().padStart(2, '0')}`,
        label: `Mois ${i + 1}`,
        activity: 80 + i * 2,
        accessibility_index: 65 + Math.sin(i) * 3,
        pressure_index: 40 + Math.cos(i) * 2,
        attractiveness_index: 70 + Math.sin(i * 0.5) * 4
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
    <div style={{ position: 'relative', width: '100vw', height: '100vh', background: '#07090e' }}>
      <MapViewport
        mapMode={mapMode}
        mapboxToken={mapboxToken}
        setShowSettings={setShowSettings}
        selectedDistrict={selectedDistrict}
        setSelectedDistrict={setSelectedDistrict}
        granularity={granularity}
        setGranularity={setGranularity}
      />

      <Header
        isConnected={isConnected}
        mapMode={mapMode}
        setMapMode={setMapMode}
        showSettings={showSettings}
        setShowSettings={setShowSettings}
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
      />

      <DataPanel
        selectedDistrict={selectedDistrict}
        districts={districts}
        overview={overview}
        timeline={timeline}
        events={events}
        activeFamily={activeFamily}
        maxActivity={maxActivity}
      />
    </div>
  );
}

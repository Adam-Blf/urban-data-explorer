import { District, Overview, TimelinePoint, EventLog, QualityEntry } from '../types';

// Base API resolue au build :
//  - dev      -> http://localhost:8000 (defaut en mode dev)
//  - Vercel   -> URL du service Render (variable VITE_API_BASE)
//  - exe local-> '' (meme origine : l'exe sert l'API + le front)
const API_BASE =
  import.meta.env.VITE_API_BASE ??
  (import.meta.env.DEV ? 'http://localhost:8000' : '');

export const api = {
  async checkHealth(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/health`);
      return res.ok;
    } catch {
      return false;
    }
  },

  async fetchDashboard(): Promise<District[]> {
    const res = await fetch(`${API_BASE}/datamarts/dashboard`);
    if (!res.ok) throw new Error('Failed to fetch dashboard');
    return res.json();
  },

  async fetchOverview(): Promise<Overview> {
    const res = await fetch(`${API_BASE}/datamarts/overview`);
    if (!res.ok) throw new Error('Failed to fetch overview');
    return res.json();
  },

  async fetchTimeline(): Promise<TimelinePoint[]> {
    const res = await fetch(`${API_BASE}/datamarts/timeline`);
    if (!res.ok) throw new Error('Failed to fetch timeline');
    return res.json();
  },

  async fetchEvents(): Promise<EventLog[]> {
    const res = await fetch(`${API_BASE}/events/recent`);
    if (!res.ok) throw new Error('Failed to fetch events');
    return res.json();
  },

  async fetchIrisGeoJson(): Promise<any> {
    const res = await fetch(`${API_BASE}/datamarts/iris/geojson`);
    if (!res.ok) throw new Error('Failed to fetch geojson');
    return res.json();
  },

  async fetchGeoJsonByGranularity(level: number): Promise<any> {
    const res = await fetch(`${API_BASE}/datamarts/geojson/${level}`);
    if (!res.ok) throw new Error(`Failed to fetch geojson level ${level}`);
    return res.json();
  },

  async fetchQuality(): Promise<QualityEntry[]> {
    const res = await fetch(`${API_BASE}/pipeline/quality`);
    if (!res.ok) throw new Error('Failed to fetch quality report');
    return res.json();
  },
};

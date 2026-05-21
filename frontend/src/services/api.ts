import { District, Overview, TimelinePoint, EventLog } from '../types';

const API_BASE = 'http://localhost:8000';

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
  }
};

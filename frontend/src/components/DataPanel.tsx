import React from 'react';
import { TrendingUp, Activity, RefreshCw } from 'lucide-react';
import { District, Overview, TimelinePoint, EventLog } from '../types';

interface DataPanelProps {
  selectedDistrict: string | null;
  districts: District[];
  overview: Overview | null;
  timeline: TimelinePoint[];
  events: EventLog[];
  activeFamily: string;
  maxActivity: number;
}

export const DataPanel: React.FC<DataPanelProps> = ({
  selectedDistrict,
  districts,
  overview,
  timeline,
  events,
  activeFamily,
  maxActivity
}) => {
  const selectedDistrictData = districts.find(d => d.code === selectedDistrict);

  return (
    <div className="glass-panel" style={{ position: 'absolute', top: '110px', right: '20px', bottom: '20px', width: '420px', zIndex: 10, padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px', overflowY: 'auto' }}>

      {/* Active Selection Details */}
      <div>
        <h2 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '4px' }}>
          {selectedDistrictData ? `${selectedDistrictData.label} - ${selectedDistrictData.name}` : 'Paris (Global)'}
        </h2>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <TrendingUp size={12} style={{ color: 'var(--accent-cyan)' }} />
          Statistiques consolidées par granularité active.
        </p>
      </div>

      {/* Indexes & Scores */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
        {[
          { label: 'Accessibilité', val: selectedDistrictData ? selectedDistrictData.accessibility_index : overview?.accessibility_index || 68, color: 'var(--accent-cyan)' },
          { label: 'Pression', val: selectedDistrictData ? selectedDistrictData.pressure_index : overview?.pressure_index || 42, color: 'var(--accent-pink)' },
          { label: 'Attractivité', val: selectedDistrictData ? selectedDistrictData.attractiveness_index : overview?.attractiveness_index || 71, color: 'var(--accent-purple)' }
        ].map((idx, i) => (
          <div
            key={i}
            className={`glass-panel ${activeFamily !== 'all' && activeFamily !== ['mobility', 'pressure', 'green_space'][i] ? 'grayed-out' : ''}`}
            style={{ padding: '14px', borderRadius: '12px', textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '6px' }}
          >
            <span style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>{idx.label}</span>
            <span style={{ fontSize: '24px', fontWeight: 800, color: idx.color }}>{idx.val}%</span>
          </div>
        ))}
      </div>

      {/* Graph representation (Custom SVG Timeline) */}
      <div className={`glass-panel ${activeFamily !== 'all' ? 'grayed-out' : ''}`} style={{ padding: '16px', borderRadius: '12px' }}>
        <h3 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <TrendingUp size={14} /> Chronologie d'Activité
        </h3>
        <div style={{ width: '100%', height: '120px', position: 'relative' }}>
          {timeline.length > 0 ? (
            <svg width="100%" height="100%" viewBox="0 0 340 100" preserveAspectRatio="none">
              <defs>
                <linearGradient id="glow-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--accent-cyan)" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="var(--accent-cyan)" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path
                d={`M 0 100 ${timeline.map((t, idx) => `L ${idx * 30.9} ${100 - (t.activity / maxActivity) * 70}`).join(' ')} L 340 100 Z`}
                fill="url(#glow-grad)"
              />
              <path
                d={timeline.map((t, idx) => `${idx === 0 ? 'M' : 'L'} ${idx * 30.9} ${100 - (t.activity / maxActivity) * 70}`).join(' ')}
                fill="none"
                stroke="var(--accent-cyan)"
                strokeWidth="2.5"
              />
              {timeline.map((t, idx) => (
                <circle
                  key={idx}
                  cx={idx * 30.9}
                  cy={100 - (t.activity / maxActivity) * 70}
                  r="3.5"
                  fill="var(--bg-main)"
                  stroke="var(--accent-cyan)"
                  strokeWidth="2"
                />
              ))}
            </svg>
          ) : (
            <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
              Chargement du graphique...
            </div>
          )}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: 'var(--text-muted)', marginTop: '8px' }}>
          <span>Juin 2025</span>
          <span>Mai 2026</span>
        </div>
      </div>

      {/* Real-time Streaming Logs Feed */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px', minHeight: '180px' }}>
        <h3 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Activity size={14} className="pulse-element" style={{ color: 'var(--accent-pink)' }} />
          Flux d'Événements Kafka & Cassandra
        </h3>
        <div className="glass-panel" style={{ flex: 1, padding: '14px', borderRadius: '12px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '200px' }}>
          {events.length > 0 ? (
            events.slice(0, 10).map((evt) => (
              <div key={evt.event_id} style={{ display: 'flex', flexDirection: 'column', gap: '2px', borderBottom: '1px solid rgba(255,255,255,0.04)', paddingBottom: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}>
                  <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{evt.event_type}</span>
                  <span style={{ color: 'var(--text-muted)' }}>
                    {new Date(evt.event_time).toLocaleTimeString()}
                  </span>
                </div>
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  {evt.payload.message || `Mise à jour sur le district ${evt.district_code}`}
                </span>
              </div>
            ))
          ) : (
            <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '11px', textAlign: 'center', flexDirection: 'column', gap: '8px', padding: '20px 0' }}>
              <RefreshCw size={24} className="pulse-element" />
              En attente d'événements Kafka de streaming temps réel...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

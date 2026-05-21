import React from 'react';
import { Building2, Settings } from 'lucide-react';

interface HeaderProps {
  isConnected: boolean;
  mapMode: '2d' | '3d';
  setMapMode: (mode: '2d' | '3d') => void;
  showSettings: boolean;
  setShowSettings: (show: boolean) => void;
}

export const Header: React.FC<HeaderProps> = ({
  isConnected,
  mapMode,
  setMapMode,
  showSettings,
  setShowSettings
}) => {
  return (
    <header className="glass-panel" style={{ position: 'absolute', top: '20px', left: '20px', right: '20px', height: '70px', zIndex: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px', pointerEvents: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-blue))', padding: '10px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 15px rgba(6, 182, 212, 0.4)' }}>
          <Building2 size={24} style={{ color: '#fff' }} />
        </div>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, letterSpacing: '0.5px' }}>URBAN DATA EXPLORER</h1>
          <p style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 500 }}>RECHERCHE & DÉVELOPPEMENT PARIS — BLOC 1</p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        <div className="flex items-center gap-2" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: isConnected ? 'var(--success)' : 'var(--warning)', boxShadow: isConnected ? '0 0 8px var(--success)' : '0 0 8px var(--warning)' }} />
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)' }}>
            {isConnected ? 'CONNEXION LIVE (POSTGRESQL/CASSANDRA)' : 'MODE LOCAL-FIRST (OFFLINE)'}
          </span>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setMapMode('2d')}
            className={`btn-tab ${mapMode === '2d' ? 'active' : ''}`}
          >
            2D MapLibre
          </button>
          <button
            onClick={() => setMapMode('3d')}
            className={`btn-tab ${mapMode === '3d' ? 'active' : ''}`}
          >
            3D Mapbox
          </button>
          <button onClick={() => setShowSettings(!showSettings)} className="btn-tab" style={{ padding: '8px' }}>
            <Settings size={18} />
          </button>
        </div>
      </div>
    </header>
  );
};

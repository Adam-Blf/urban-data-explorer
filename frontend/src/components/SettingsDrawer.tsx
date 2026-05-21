import React from 'react';
import { Settings } from 'lucide-react';

interface SettingsDrawerProps {
  showSettings: boolean;
  setShowSettings: (show: boolean) => void;
  mapboxToken: string;
  saveToken: (token: string) => void;
}

export const SettingsDrawer: React.FC<SettingsDrawerProps> = ({
  showSettings,
  setShowSettings,
  mapboxToken,
  saveToken
}) => {
  if (!showSettings) return null;

  return (
    <div className="glass-panel glass-panel-glow" style={{ position: 'absolute', top: '100px', right: '20px', width: '360px', padding: '20px', zIndex: 100, display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Settings size={18} /> Paramètres de la carte
        </h3>
        <button onClick={() => setShowSettings(false)} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>×</button>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Clé API Mapbox (Jeton d'accès public) :</label>
        <input
          type="text"
          placeholder="pk.eyJ1..."
          defaultValue={mapboxToken}
          onKeyDown={(e) => {
            if (e.key === 'Enter') saveToken((e.target as HTMLInputElement).value);
          }}
          style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-card)', borderRadius: '8px', padding: '10px', color: '#fff', fontSize: '12px' }}
        />
        <p style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Appuyez sur Entrée pour appliquer et recharger la carte.</p>
      </div>
    </div>
  );
};

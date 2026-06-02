import React from 'react';
import { Settings, X } from 'lucide-react';

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
  saveToken,
}) => {
  if (!showSettings) return null;

  return (
    <div
      className="dsfr-surface"
      style={{ position: 'absolute', top: '88px', right: '16px', width: '380px', padding: '20px', zIndex: 100, display: 'flex', flexDirection: 'column', gap: '16px' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-title)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Settings size={18} style={{ color: 'var(--blue-france)' }} /> Paramètres de la carte
        </h3>
        <button onClick={() => setShowSettings(false)} className="dsfr-btn dsfr-btn--tertiary" style={{ padding: '6px' }} aria-label="Fermer">
          <X size={16} />
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <label htmlFor="mapbox-token" style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-title)' }}>
          Jeton d’accès Mapbox (vue 3D)
        </label>
        <input
          id="mapbox-token"
          type="text"
          placeholder="pk.eyJ1…"
          defaultValue={mapboxToken}
          onKeyDown={(e) => {
            if (e.key === 'Enter') saveToken((e.target as HTMLInputElement).value);
          }}
          className="dsfr-input"
        />
        <p style={{ fontSize: '11px', color: 'var(--text-mention)', lineHeight: 1.5 }}>
          Appuyez sur <strong style={{ color: 'var(--text-title)' }}>Entrée</strong> pour appliquer et recharger la carte.
          La vue 2D s’appuie sur le fond de plan IGN et ne requiert aucun jeton.
        </p>
      </div>
    </div>
  );
};

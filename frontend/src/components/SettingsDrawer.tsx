import React, { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
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
  const inputRef = useRef<HTMLInputElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);
  const prevFocusRef = useRef<HTMLElement | null>(null);

  /* Focus management: focus input on open, restore trigger focus on close */
  useEffect(() => {
    if (showSettings) {
      prevFocusRef.current = document.activeElement as HTMLElement;
      const t = setTimeout(() => inputRef.current?.focus(), 50);
      return () => clearTimeout(t);
    } else {
      prevFocusRef.current?.focus();
    }
  }, [showSettings]);

  /* inert via DOM — keeps off-screen content fully inoperable */
  useEffect(() => {
    const el = drawerRef.current;
    if (!el) return;
    if (!showSettings) el.setAttribute('inert', '');
    else el.removeAttribute('inert');
  }, [showSettings]);

  const handleApply = () => {
    saveToken(inputRef.current?.value ?? '');
  };

  return (
    <motion.div
      ref={drawerRef}
      className="dsfr-surface"
      initial={false}
      animate={{
        opacity: showSettings ? 1 : 0,
        y: showSettings ? 0 : -8,
        pointerEvents: showSettings ? 'auto' : 'none',
      }}
      transition={{ type: 'tween', ease: [0.4, 0, 0.2, 1], duration: 0.2 }}
      style={{
        position: 'absolute',
        top: '88px',
        right: '16px',
        width: '380px',
        padding: '20px',
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
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
          Jeton d'accès Mapbox (vue 3D)
        </label>
        <input
          ref={inputRef}
          id="mapbox-token"
          type="text"
          placeholder="pk.eyJ1…"
          defaultValue={mapboxToken}
          onKeyDown={(e) => {
            if (e.key === 'Enter') saveToken((e.target as HTMLInputElement).value);
          }}
          className="dsfr-input"
        />
        <button
          onClick={handleApply}
          className="dsfr-btn dsfr-btn--primary"
          style={{ alignSelf: 'flex-start', marginTop: '4px' }}
        >
          Appliquer
        </button>
        <p style={{ fontSize: '11px', color: 'var(--text-mention)', lineHeight: 1.5 }}>
          Cliquez sur <strong style={{ color: 'var(--text-title)' }}>Appliquer</strong> ou appuyez sur <strong style={{ color: 'var(--text-title)' }}>Entrée</strong> pour sauvegarder.
          La vue 2D s'appuie sur le fond de plan IGN et ne requiert aucun jeton.
        </p>
      </div>
    </motion.div>
  );
};

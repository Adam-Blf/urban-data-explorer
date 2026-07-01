import React from 'react';
import { Settings, SlidersHorizontal, BarChart3, Sun, Moon, Map, Box, TableProperties, Database } from 'lucide-react';

interface HeaderProps {
  isConnected: boolean;
  mapMode: '2d' | '3d';
  setMapMode: (mode: '2d' | '3d') => void;
  theme: 'light' | 'dark';
  setTheme: (t: 'light' | 'dark') => void;
  showSettings: boolean;
  setShowSettings: (show: boolean) => void;
  showControlPanel: boolean;
  setShowControlPanel: (show: boolean) => void;
  showDataPanel: boolean;
  setShowDataPanel: (show: boolean) => void;
  showTable: boolean;
  setShowTable: (show: boolean) => void;
  showTableExplorer: boolean;
  setShowTableExplorer: (show: boolean) => void;
}

/* Bloc-marque EFREI : logo + titre application */
const EfreiBrand: React.FC<{ theme: 'light' | 'dark' }> = ({ theme }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
    <a
      href="https://efrei.fr"
      target="_blank"
      rel="noopener noreferrer"
      aria-label="EFREI Paris"
      style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}
    >
      <img
        src={theme === 'dark' ? '/Logo-Efrei-Blanc.png' : '/Logo-Efrei-CMJN.png'}
        alt="EFREI Paris"
        height={36}
        style={{ height: '36px', width: 'auto', display: 'block' }}
      />
    </a>
    <div style={{ width: '1px', height: '40px', background: 'var(--border)' }} aria-hidden="true" />
    <div>
      <h1
        style={{
          fontSize: '18px',
          fontWeight: 700,
          color: 'var(--text-title)',
          letterSpacing: '-0.02em',
          lineHeight: 1.1,
        }}
      >
        Urban Data Explorer
      </h1>
      <p style={{ fontSize: '12px', color: 'var(--text-mention)', fontWeight: 400, marginTop: '2px' }}>
        Observatoire socio-urbain · Paris
      </p>
    </div>
  </div>
);

export const Header: React.FC<HeaderProps> = ({
  isConnected,
  mapMode,
  setMapMode,
  theme,
  setTheme,
  showSettings,
  setShowSettings,
  showControlPanel,
  setShowControlPanel,
  showDataPanel,
  setShowDataPanel,
  showTable,
  setShowTable,
  showTableExplorer,
  setShowTableExplorer,
}) => {
  return (
    <header
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: '72px',
        zIndex: 20,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        background: theme === 'dark' ? 'var(--bg-alt)' : 'var(--bg)',
        borderBottom: `2px solid ${theme === 'dark' ? 'var(--border)' : '#163767'}`,
        boxShadow: 'var(--shadow-raised)',
      }}
    >
      <EfreiBrand theme={theme} />

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        {/* État de la source de données — aria-live pour annoncer les changements */}
        <div
          role="status"
          aria-live="polite"
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          title={isConnected ? 'Connexion aux bases de données active' : 'Données locales de secours'}
        >
          <span
            className={isConnected ? '' : 'blink-soft'}
            style={{ width: '8px', height: '8px', borderRadius: '50%', background: isConnected ? 'var(--success)' : 'var(--warning)', flexShrink: 0 }}
            aria-hidden="true"
          />
          <span style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-mention)' }}>
            {isConnected ? 'Données live · PostgreSQL / Cassandra' : 'Mode local · hors ligne'}
          </span>
        </div>

        <div style={{ width: '1px', height: '32px', background: 'var(--border)' }} />

        {/* Panneaux */}
        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            onClick={() => setShowControlPanel(!showControlPanel)}
            className={`dsfr-btn dsfr-btn--tertiary ${showControlPanel ? 'is-active' : ''}`}
            aria-pressed={showControlPanel}
            title="Afficher / masquer les filtres"
          >
            <SlidersHorizontal size={16} /> Filtres
          </button>
          <button
            onClick={() => setShowDataPanel(!showDataPanel)}
            className={`dsfr-btn dsfr-btn--tertiary ${showDataPanel ? 'is-active' : ''}`}
            aria-pressed={showDataPanel}
            title="Afficher / masquer les indicateurs"
          >
            <BarChart3 size={16} /> Indicateurs
          </button>
          <button
            onClick={() => setShowTable(!showTable)}
            className={`dsfr-btn dsfr-btn--tertiary ${showTable ? 'is-active' : ''}`}
            aria-pressed={showTable}
            title="Tableau des données par arrondissement"
          >
            <TableProperties size={16} /> Tableau
          </button>
          <button
            onClick={() => setShowTableExplorer(!showTableExplorer)}
            className={`dsfr-btn dsfr-btn--tertiary ${showTableExplorer ? 'is-active' : ''}`}
            aria-pressed={showTableExplorer}
            title="Explorateur de tables SQL / NoSQL"
          >
            <Database size={16} /> Tables
          </button>
        </div>

        {/* Mode de carte (segmenté) */}
        <div role="group" aria-label="Mode de carte" style={{ display: 'flex', border: '1px solid var(--border)', borderRadius: '6px', overflow: 'hidden' }}>
          <button
            onClick={() => setMapMode('2d')}
            className={`dsfr-btn dsfr-btn--tertiary ${mapMode === '2d' ? 'is-active' : ''}`}
            aria-pressed={mapMode === '2d'}
            style={{ borderRadius: 0 }}
            title="Carte 2D · fond de plan IGN"
          >
            <Map size={16} /> 2D · IGN
          </button>
          <button
            onClick={() => setMapMode('3d')}
            className={`dsfr-btn dsfr-btn--tertiary ${mapMode === '3d' ? 'is-active' : ''}`}
            aria-pressed={mapMode === '3d'}
            style={{ borderRadius: 0 }}
            title="Carte 3D · extrusion des bâtiments"
          >
            <Box size={16} /> 3D
          </button>
        </div>

        {/* Thème & paramètres */}
        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
            className="dsfr-btn dsfr-btn--tertiary"
            style={{ padding: '8px' }}
            title={theme === 'light' ? 'Passer en thème sombre' : 'Passer en thème clair'}
            aria-label="Changer de thème"
            aria-pressed={theme === 'dark'}
          >
            {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
          </button>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`dsfr-btn dsfr-btn--tertiary ${showSettings ? 'is-active' : ''}`}
            aria-pressed={showSettings}
            style={{ padding: '8px' }}
            title="Paramètres"
            aria-label="Paramètres"
          >
            <Settings size={18} />
          </button>
        </div>
      </div>
    </header>
  );
};

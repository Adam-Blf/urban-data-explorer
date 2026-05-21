import React from 'react';
import { Layers, Filter, Sparkles, X } from 'lucide-react';

interface ControlPanelProps {
  granularity: number;
  setGranularity: (val: number) => void;
  activeFamily: string;
  setActiveFamily: (val: string) => void;
  style?: React.CSSProperties;
  onClose?: () => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  granularity,
  setGranularity,
  activeFamily,
  setActiveFamily,
  style,
  onClose
}) => {
  return (
    <div 
      className="glass-panel" 
      style={{ 
        position: 'absolute', 
        top: '110px', 
        left: '20px', 
        bottom: '20px', 
        width: '380px', 
        zIndex: 10, 
        padding: '24px', 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '24px', 
        overflowY: 'auto',
        ...style 
      }}
    >
      {/* Configuration Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '-8px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 800, color: 'var(--text-primary)' }}>Configuration</h2>
        {onClose && (
          <button 
            onClick={onClose}
            className="btn-tab"
            style={{ 
              padding: '6px', 
              background: 'none', 
              border: 'none', 
              borderRadius: '6px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            title="Masquer"
          >
            <X size={16} />
          </button>
        )}
      </div>

      {/* Granularity Selector */}
      <div>
        <h3 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Layers size={14} /> Granularité progressive
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {[
            { level: 0, name: 'Ville (Paris)', desc: 'Métriques consolidées globales' },
            { level: 1, name: 'Arrondissement', desc: 'Découpage administratif principal' },
            { level: 2, name: 'IRIS (Quartier)', desc: 'Maille socio-économique INSEE' },
            { level: 3, name: 'Rue', desc: 'Réseau viaire et équipements' },
            { level: 4, name: 'Bâtiment', desc: 'Extrusion 3D des hauteurs' }
          ].map((g) => (
            <button
              key={g.level}
              onClick={() => setGranularity(g.level)}
              className={`btn-tab ${granularity === g.level ? 'active' : ''}`}
              style={{ width: '100%', justifyContent: 'flex-start', textAlign: 'left', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', padding: '10px 14px' }}
            >
              <span style={{ fontSize: '13px', fontWeight: 600 }}>{g.name}</span>
              <span style={{ fontSize: '10px', opacity: 0.8, fontWeight: 400 }}>{g.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Thematic Filters */}
      <div>
        <h3 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Filter size={14} /> Filtrage thématique
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button
            onClick={() => setActiveFamily('all')}
            className={`btn-tab ${activeFamily === 'all' ? 'active' : ''}`}
            style={{ fontSize: '12px', justifyContent: 'center', width: '100%', padding: '12px', fontWeight: 600 }}
          >
            Synthèse globale
          </button>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
            {[
              { id: 'immobilier', name: 'Marché Immobilier' },
              { id: 'logement_social', name: 'Logement Social' },
              { id: 'revenus', name: 'Revenus & Socio-Éco' },
              { id: 'cadre_vie', name: 'Cadre de vie' },
              { id: 'environnement', name: 'Environnement', fullWidth: true }
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setActiveFamily(f.id)}
                className={`btn-tab ${activeFamily === f.id ? 'active' : ''}`}
                style={{
                  fontSize: '12px',
                  justifyContent: 'center',
                  padding: '8px 4px',
                  height: '44px',
                  textAlign: 'center',
                  lineHeight: '1.2',
                  gridColumn: f.fullWidth ? 'span 2' : 'auto'
                }}
              >
                {f.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Consolidation Section */}
      <div className={`glass-panel ${activeFamily !== 'all' ? 'grayed-out' : ''}`} style={{ padding: '16px', borderRadius: '12px', background: 'rgba(255, 255, 255, 0.02)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <h4 style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent-purple)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Sparkles size={14} /> Indicateur croisé consolidé
        </h4>
        <p style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
          Affiche le score global moyen des 5 catégories pour chaque arrondissement. Sélectionnez une catégorie ci-dessus pour colorer la carte par indicateur.
        </p>
      </div>
    </div>
  );
};

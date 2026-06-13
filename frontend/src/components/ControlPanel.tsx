import React, { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Layers, Filter, Info, X } from 'lucide-react';

interface ControlPanelProps {
  granularity: number;
  setGranularity: (val: number) => void;
  activeFamily: string;
  setActiveFamily: (val: string) => void;
  isVisible: boolean;
  onClose?: () => void;
}

const GRANULARITIES = [
  { level: 0, name: 'Ville (Paris)', desc: 'Métriques consolidées globales' },
  { level: 1, name: 'Arrondissement', desc: 'Découpage administratif principal' },
  { level: 2, name: 'IRIS (quartier)', desc: 'Maille socio-économique INSEE' },
  { level: 3, name: 'Rue', desc: 'Réseau viaire et équipements' },
  { level: 4, name: 'Bâtiment', desc: 'Extrusion 3D des hauteurs' },
];

const FAMILIES = [
  { id: 'immobilier', name: 'Marché immobilier' },
  { id: 'logement_social', name: 'Logement social' },
  { id: 'revenus', name: 'Revenus & socio-éco' },
  { id: 'cadre_vie', name: 'Cadre de vie' },
  { id: 'environnement', name: 'Environnement', fullWidth: true },
];

export const ControlPanel = React.memo<ControlPanelProps>(function ControlPanel({
  granularity,
  setGranularity,
  activeFamily,
  setActiveFamily,
  isVisible,
  onClose,
}) {
  const panelRef = useRef<HTMLElement>(null);

  /* inert via DOM — keeps off-screen content fully inoperable */
  useEffect(() => {
    const el = panelRef.current;
    if (!el) return;
    if (!isVisible) el.setAttribute('inert', '');
    else el.removeAttribute('inert');
  }, [isVisible]);

  return (
    <motion.aside
      ref={panelRef}
      className="dsfr-surface"
      initial={false}
      animate={{ x: isVisible ? 0 : -432 }}
      transition={{ type: 'tween', ease: [0.4, 0, 0.2, 1], duration: 0.3 }}
      style={{
        position: 'absolute',
        top: '88px',
        left: '16px',
        bottom: '16px',
        width: '380px',
        zIndex: 15,
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
        overflowY: 'auto',
      }}
    >
      {/* En-tête */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <span className="dsfr-eyebrow">Paramétrage</span>
          <h2 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-title)', marginTop: '2px' }}>
            Filtres & granularité
          </h2>
        </div>
        {onClose && (
          <button onClick={onClose} className="dsfr-btn dsfr-btn--tertiary" style={{ padding: '6px' }} title="Masquer" aria-label="Masquer le panneau">
            <X size={16} />
          </button>
        )}
      </div>

      {/* Granularité */}
      <section>
        <h3 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-title)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={15} style={{ color: 'var(--blue-france)' }} /> Granularité progressive
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {GRANULARITIES.map((g) => (
            <button
              key={g.level}
              onClick={() => setGranularity(g.level)}
              aria-pressed={granularity === g.level}
              className={`dsfr-segment ${granularity === g.level ? 'is-active' : ''}`}
              style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '1px' }}
            >
              <span style={{ fontSize: '13px', fontWeight: 600 }}>{g.name}</span>
              <span style={{ fontSize: '11px', opacity: 0.85, fontWeight: 400 }}>{g.desc}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Filtrage thématique */}
      <section>
        <h3 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-title)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={15} style={{ color: 'var(--blue-france)' }} /> Filtrage thématique
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <button
            onClick={() => setActiveFamily('all')}
            aria-pressed={activeFamily === 'all'}
            className={`dsfr-segment ${activeFamily === 'all' ? 'is-active' : ''}`}
            style={{ textAlign: 'center', fontWeight: 600 }}
          >
            Synthèse globale
          </button>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px' }}>
            {FAMILIES.map((f) => (
              <button
                key={f.id}
                onClick={() => setActiveFamily(f.id)}
                aria-pressed={activeFamily === f.id}
                className={`dsfr-segment ${activeFamily === f.id ? 'is-active' : ''}`}
                style={{
                  textAlign: 'center',
                  justifyContent: 'center',
                  padding: '10px 6px',
                  minHeight: '46px',
                  display: 'flex',
                  alignItems: 'center',
                  gridColumn: f.fullWidth ? 'span 2' : 'auto',
                }}
              >
                {f.name}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Note explicative */}
      <div className="dsfr-card--alt dsfr-accent-left" style={{ padding: '14px 16px', display: 'flex', gap: '10px' }}>
        <Info size={16} style={{ color: 'var(--blue-france)', flexShrink: 0, marginTop: '1px' }} />
        <p style={{ fontSize: '12px', color: 'var(--text-default)', lineHeight: 1.5 }}>
          La <strong style={{ color: 'var(--text-title)' }}>synthèse globale</strong> colore la carte par score moyen des 5 catégories.
          Sélectionnez une thématique pour appliquer une coloration choroplèthe dédiée.
        </p>
      </div>
    </motion.aside>
  );
});

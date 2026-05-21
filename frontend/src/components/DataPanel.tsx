import React from 'react';
import { TrendingUp, Activity, RefreshCw, X } from 'lucide-react';
import { District, Overview, TimelinePoint, EventLog } from '../types';

interface DataPanelProps {
  selectedDistrict: string | null;
  setSelectedDistrict: React.Dispatch<React.SetStateAction<string | null>>;
  comparedDistrict: string | null;
  setComparedDistrict: React.Dispatch<React.SetStateAction<string | null>>;
  districts: District[];
  overview: Overview | null;
  timeline: TimelinePoint[];
  events: EventLog[];
  activeFamily: string;
  maxActivity: number;
  style?: React.CSSProperties;
  onClose?: () => void;
}

const formatValue = (key: string, val: number) => {
  if (key === 'prix_m2') {
    return `${Math.round(val).toLocaleString('fr-FR')} €/m²`;
  }
  if (key === 'revenu_median') {
    return `${Math.round(val).toLocaleString('fr-FR')} €/an`;
  }
  if (key === 'logement_social_pct') {
    return `${val.toFixed(1)} %`;
  }
  if (key === 'sales_volume') {
    return `${val} ventes`;
  }
  if (key === 'logements_sociaux_count') {
    return `${val.toLocaleString('fr-FR')} log.`;
  }
  return `${val}%`;
};

const getTimelineValue = (t: TimelinePoint, family: string) => {
  if (family === 'immobilier') return t.immobilier_idx;
  if (family === 'logement_social') return t.logement_social_idx;
  if (family === 'revenus') return t.revenu_idx;
  if (family === 'cadre_vie') return t.cadre_vie_idx;
  if (family === 'environnement') return t.environnement_idx;
  return t.activity;
};

const getTimelineLabel = (family: string) => {
  if (family === 'immobilier') return "Indice Marché Immobilier (Tendance)";
  if (family === 'logement_social') return "Indice Logement Social (Tendance)";
  if (family === 'revenus') return "Indice Revenus & Socio-Éco (Tendance)";
  if (family === 'cadre_vie') return "Indice Cadre de Vie (Tendance)";
  if (family === 'environnement') return "Indice Environnement (Tendance)";
  return "Activité Globale (Messages Kafka)";
};

export const DataPanel: React.FC<DataPanelProps> = ({
  selectedDistrict,
  setSelectedDistrict,
  comparedDistrict,
  setComparedDistrict,
  districts,
  overview,
  timeline,
  events,
  activeFamily,
  maxActivity,
  style,
  onClose
}) => {
  const selectedA = districts.find(d => d.code === selectedDistrict);
  const selectedB = districts.find(d => d.code === comparedDistrict);

  // Indicators calculations
  const avgScore = districts.length 
    ? Math.round(districts.reduce((acc, d) => acc + d.score, 0) / districts.length)
    : 58;

  const indicators = [
    {
      id: 'score',
      label: 'Score Global de Synthèse',
      idxA: selectedA?.score,
      idxB: selectedB?.score,
      idxAvg: avgScore,
      rawA: selectedA ? `${selectedA.score}%` : null,
      rawB: selectedB ? `${selectedB.score}%` : null,
      rawAvg: `${avgScore}%`,
      familyId: 'all'
    },
    {
      id: 'immobilier',
      label: 'Marché Immobilier & Prix',
      idxA: selectedA?.immobilier_idx,
      idxB: selectedB?.immobilier_idx,
      idxAvg: overview?.immobilier_idx || 65,
      rawA: selectedA ? `${formatValue('prix_m2', selectedA.prix_m2)} (${selectedA.sales_volume} ventes)` : null,
      rawB: selectedB ? `${formatValue('prix_m2', selectedB.prix_m2)} (${selectedB.sales_volume} ventes)` : null,
      rawAvg: overview ? `${formatValue('prix_m2', overview.prix_m2)}` : null,
      familyId: 'immobilier'
    },
    {
      id: 'logement_social',
      label: 'Logement Social & Mixité',
      idxA: selectedA?.logement_social_idx,
      idxB: selectedB?.logement_social_idx,
      idxAvg: overview?.logement_social_idx || 22,
      rawA: selectedA ? `${formatValue('logement_social_pct', selectedA.logement_social_pct)} (${selectedA.logements_sociaux_count} log.)` : null,
      rawB: selectedB ? `${formatValue('logement_social_pct', selectedB.logement_social_pct)} (${selectedB.logements_sociaux_count} log.)` : null,
      rawAvg: overview ? `${formatValue('logement_social_pct', overview.logement_social_pct)}` : null,
      familyId: 'logement_social'
    },
    {
      id: 'revenus',
      label: 'Revenus & Socio-Éco',
      idxA: selectedA?.revenu_idx,
      idxB: selectedB?.revenu_idx,
      idxAvg: overview?.revenu_idx || 55,
      rawA: selectedA ? formatValue('revenu_median', selectedA.revenu_median) : null,
      rawB: selectedB ? formatValue('revenu_median', selectedB.revenu_median) : null,
      rawAvg: overview ? formatValue('revenu_median', overview.revenu_median) : null,
      familyId: 'revenus'
    },
    {
      id: 'cadre_vie',
      label: 'Cadre de Vie & Attractivité',
      idxA: selectedA?.cadre_vie_idx,
      idxB: selectedB?.cadre_vie_idx,
      idxAvg: overview?.cadre_vie_idx || 68,
      rawA: selectedA ? `Accessibilité: ${selectedA.accessibility_index}%` : null,
      rawB: selectedB ? `Accessibilité: ${selectedB.accessibility_index}%` : null,
      rawAvg: overview ? `Accessibilité: ${overview.accessibility_index}%` : null,
      familyId: 'cadre_vie'
    },
    {
      id: 'environnement',
      label: 'Qualité de l\'Environnement',
      idxA: selectedA?.environnement_idx,
      idxB: selectedB?.environnement_idx,
      idxAvg: overview?.environnement_idx || 72,
      rawA: selectedA ? `Espaces Verts: ${selectedA.family_counts.green_space || 0}` : null,
      rawB: selectedB ? `Espaces Verts: ${selectedB.family_counts.green_space || 0}` : null,
      rawAvg: 'Espaces Verts: Moyen',
      familyId: 'environnement'
    }
  ];

  // Dynamic Timeline metrics
  const activeTimelineMax = timeline.length 
    ? Math.max(...timeline.map(t => getTimelineValue(t, activeFamily)))
    : 100;

  return (
    <div className="glass-panel" style={{ position: 'absolute', top: '110px', right: '20px', bottom: '20px', width: '440px', zIndex: 10, padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto', ...style }}>

      {/* Selection & Comparison Header */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 800, color: 'var(--text-primary)' }}>
            {selectedA ? `${selectedA.label} - ${selectedA.name}` : 'Paris (Consolidé)'}
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {selectedDistrict && (
              <button
                onClick={() => { setSelectedDistrict(null); setComparedDistrict(null); }}
                style={{ background: 'none', border: 'none', color: 'var(--accent-pink)', cursor: 'pointer', fontSize: '11px', fontWeight: 600 }}
              >
                Effacer sélection
              </button>
            )}
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
        </div>
        <p style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
          <TrendingUp size={11} style={{ color: 'var(--accent-cyan)' }} />
          {selectedA ? 'Explorez les indices et comparez avec un autre secteur.' : 'Sélectionnez un arrondissement pour débuter.'}
        </p>

        {selectedDistrict && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 600 }}>Comparer :</span>
            <select
              value={comparedDistrict || ''}
              onChange={(e) => setComparedDistrict(e.target.value || null)}
              style={{
                background: 'rgba(10, 12, 16, 0.85)',
                border: '1px solid rgba(6, 182, 212, 0.2)',
                color: 'var(--text-primary)',
                borderRadius: '6px',
                padding: '5px 8px',
                fontSize: '11px',
                outline: 'none',
                cursor: 'pointer',
                flex: 1
              }}
            >
              <option value="">-- Moyenne de la Ville --</option>
              {districts
                .filter(d => d.code !== selectedDistrict)
                .map(d => (
                  <option key={d.code} value={d.code}>
                    {d.label} - {d.name}
                  </option>
                ))}
            </select>
            {comparedDistrict && (
              <button
                onClick={() => setComparedDistrict(null)}
                style={{ background: 'none', border: 'none', color: 'var(--accent-pink)', cursor: 'pointer', fontSize: '11px', fontWeight: 600 }}
              >
                Annuler
              </button>
            )}
          </div>
        )}
      </div>

      {/* Side-by-Side Indicators */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {indicators.map((ind) => {
          const isDimmed = activeFamily !== 'all' && activeFamily !== ind.familyId;
          const isFocus = activeFamily === ind.familyId;
          return (
            <div
              key={ind.id}
              className="glass-panel"
              style={{
                padding: '12px 14px',
                borderRadius: '10px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                opacity: isDimmed ? 0.35 : 1,
                border: isFocus ? '1px solid rgba(6, 182, 212, 0.45)' : '1px solid rgba(255,255,255,0.03)',
                boxShadow: isFocus ? '0 0 10px rgba(6, 182, 212, 0.15)' : 'none',
                transition: 'all 0.3s ease'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-secondary)' }}>
                  {ind.label}
                </span>
                {isFocus && (
                  <span style={{ fontSize: '9px', background: 'rgba(6, 182, 212, 0.2)', color: 'var(--accent-cyan)', padding: '1px 5px', borderRadius: '3px', fontWeight: 700 }}>
                    MAP ACTIVE
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {/* Bar A */}
                {selectedA ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}>
                      <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{selectedA.label} {selectedA.name}</span>
                      <span style={{ color: 'var(--text-primary)' }}>{ind.rawA} (Idx: {ind.idxA})</span>
                    </div>
                    <div style={{ height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${ind.idxA}%`, background: 'linear-gradient(to right, #0891b2, #06b6d4)', borderRadius: '2px' }} />
                    </div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Moyenne Paris</span>
                      <span style={{ color: 'var(--text-primary)' }}>{ind.rawAvg} (Idx: {ind.idxAvg})</span>
                    </div>
                    <div style={{ height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${ind.idxAvg}%`, background: 'linear-gradient(to right, #6b21a8, #8b5cf6)', borderRadius: '2px' }} />
                    </div>
                  </div>
                )}

                {/* Bar B (Comparison or Avg Reference) */}
                {selectedDistrict && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', borderTop: '1px solid rgba(255,255,255,0.03)', paddingTop: '4px' }}>
                    {selectedB ? (
                      <>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}>
                          <span style={{ color: 'var(--accent-pink)', fontWeight: 600 }}>{selectedB.label} {selectedB.name}</span>
                          <span style={{ color: 'var(--text-primary)' }}>{ind.rawB} (Idx: {ind.idxB})</span>
                        </div>
                        <div style={{ height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${ind.idxB}%`, background: 'linear-gradient(to right, #db2777, #e879f9)', borderRadius: '2px' }} />
                        </div>
                      </>
                    ) : (
                      <>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}>
                          <span style={{ color: 'var(--text-muted)' }}>Moyenne de la Ville</span>
                          <span style={{ color: 'var(--text-primary)' }}>{ind.rawAvg} (Idx: {ind.idxAvg})</span>
                        </div>
                        <div style={{ height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${ind.idxAvg}%`, background: 'linear-gradient(to right, #6b21a8, #8b5cf6)', borderRadius: '2px' }} />
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* SVG Graph Timeline */}
      <div className="glass-panel" style={{ padding: '14px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.03)' }}>
        <h3 style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <TrendingUp size={13} style={{ color: 'var(--accent-cyan)' }} /> {getTimelineLabel(activeFamily)}
        </h3>
        <div style={{ width: '100%', height: '80px', position: 'relative' }}>
          {timeline.length > 0 ? (
            <svg width="100%" height="100%" viewBox="0 0 380 80" preserveAspectRatio="none">
              <defs>
                <linearGradient id="glow-grad-thematic" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={activeFamily === 'all' ? 'var(--accent-cyan)' : 'var(--accent-purple)'} stopOpacity="0.4" />
                  <stop offset="100%" stopColor={activeFamily === 'all' ? 'var(--accent-cyan)' : 'var(--accent-purple)'} stopOpacity="0" />
                </linearGradient>
              </defs>
              <path
                d={`M 0 80 ${timeline.map((t, idx) => `L ${idx * 34.5} ${80 - (getTimelineValue(t, activeFamily) / activeTimelineMax) * 60}`).join(' ')} L 380 80 Z`}
                fill="url(#glow-grad-thematic)"
              />
              <path
                d={timeline.map((t, idx) => `${idx === 0 ? 'M' : 'L'} ${idx * 34.5} ${80 - (getTimelineValue(t, activeFamily) / activeTimelineMax) * 60}`).join(' ')}
                fill="none"
                stroke={activeFamily === 'all' ? 'var(--accent-cyan)' : 'var(--accent-purple)'}
                strokeWidth="2"
              />
              {timeline.map((t, idx) => (
                <circle
                  key={idx}
                  cx={idx * 34.5}
                  cy={80 - (getTimelineValue(t, activeFamily) / activeTimelineMax) * 60}
                  r="3.0"
                  fill="var(--bg-main)"
                  stroke={activeFamily === 'all' ? 'var(--accent-cyan)' : 'var(--accent-purple)'}
                  strokeWidth="1.5"
                />
              ))}
            </svg>
          ) : (
            <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '11px' }}>
              Chargement des tendances...
            </div>
          )}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px', color: 'var(--text-muted)', marginTop: '6px' }}>
          <span>{timeline[0]?.label || 'Début'}</span>
          <span>{timeline[timeline.length - 1]?.label || 'Fin'}</span>
        </div>
      </div>

      {/* Real-time Logs Feed */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <h3 style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Activity size={13} className="pulse-element" style={{ color: 'var(--accent-pink)' }} />
          Flux d'Ingestion & Événements Cassandra
        </h3>
        <div className="glass-panel" style={{ padding: '12px', borderRadius: '10px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '130px', border: '1px solid rgba(255,255,255,0.03)' }}>
          {events.length > 0 ? (
            events.slice(0, 8).map((evt) => (
              <div key={evt.event_id} style={{ display: 'flex', flexDirection: 'column', gap: '2px', borderBottom: '1px solid rgba(255,255,255,0.03)', paddingBottom: '4px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '9px' }}>
                  <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{evt.event_type}</span>
                  <span style={{ color: 'var(--text-muted)' }}>
                    {new Date(evt.event_time).toLocaleTimeString()}
                  </span>
                </div>
                <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>
                  {evt.payload.message || `Message du district ${evt.district_code}`}
                </span>
              </div>
            ))
          ) : (
            <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '10px', padding: '10px 0' }}>
              En attente d'événements Kafka...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Activity, X, Play, Pause } from 'lucide-react';
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
  isVisible: boolean;
  onClose?: () => void;
}

const formatValue = (key: string, val: number) => {
  if (key === 'prix_m2') return `${Math.round(val).toLocaleString('fr-FR')} €/m²`;
  if (key === 'revenu_median') return `${Math.round(val).toLocaleString('fr-FR')} €/an`;
  if (key === 'logement_social_pct') return `${val.toFixed(1)} %`;
  if (key === 'sales_volume') return `${val} ventes`;
  if (key === 'logements_sociaux_count') return `${val.toLocaleString('fr-FR')} log.`;
  return `${val} %`;
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
  if (family === 'immobilier') return 'Indice marché immobilier (tendance)';
  if (family === 'logement_social') return 'Indice logement social (tendance)';
  if (family === 'revenus') return 'Indice revenus & socio-éco (tendance)';
  if (family === 'cadre_vie') return 'Indice cadre de vie (tendance)';
  if (family === 'environnement') return 'Indice environnement (tendance)';
  return 'Activité globale (flux Kafka)';
};

/* Une barre d'indicateur : libellé + valeur brute + jauge */
const Gauge: React.FC<{ label: string; raw: string | null; idx?: number; color: string; muted?: boolean }> = ({ label, raw, idx, color, muted }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', fontSize: '11px' }}>
      <span style={{ color: muted ? 'var(--text-mention)' : color, fontWeight: 600 }}>{label}</span>
      <span className="tabular" style={{ color: 'var(--text-title)', fontWeight: 500 }}>
        {raw}{idx != null && <span style={{ color: 'var(--text-mention)', fontWeight: 400 }}> · idx {idx}</span>}
      </span>
    </div>
    <div style={{ height: '6px', background: 'var(--bg-contrast)', overflow: 'hidden' }}>
      <div style={{ height: '100%', width: `${Math.max(0, Math.min(100, idx ?? 0))}%`, background: color, transition: 'width 0.4s ease' }} />
    </div>
  </div>
);

export const DataPanel = React.memo<DataPanelProps>(function DataPanel({
  selectedDistrict,
  setSelectedDistrict,
  comparedDistrict,
  setComparedDistrict,
  districts,
  overview,
  timeline,
  events,
  activeFamily,
  isVisible,
  onClose,
}) {
  const panelRef = useRef<HTMLElement>(null);

  /* Timeline replay state */
  const [isPlaying, setIsPlaying] = useState(false);
  const [playIndex, setPlayIndex] = useState<number | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const prefersReducedMotion = useMemo(
    () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    []
  );

  /* inert via DOM */
  useEffect(() => {
    const el = panelRef.current;
    if (!el) return;
    if (!isVisible) el.setAttribute('inert', '');
    else el.removeAttribute('inert');
  }, [isVisible]);

  /* Cleanup interval on unmount */
  useEffect(() => {
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, []);

  /* Stop playback when timeline changes */
  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setIsPlaying(false);
    setPlayIndex(null);
  }, [timeline]);

  const togglePlay = useCallback(() => {
    if (isPlaying) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      setIsPlaying(false);
      return;
    }

    if (prefersReducedMotion) {
      setPlayIndex(timeline.length - 1);
      return;
    }

    const startIdx = playIndex !== null && playIndex < timeline.length - 1 ? playIndex : 0;
    setPlayIndex(startIdx);
    setIsPlaying(true);

    let i = startIdx;
    intervalRef.current = setInterval(() => {
      i++;
      if (i >= timeline.length) {
        clearInterval(intervalRef.current!);
        intervalRef.current = null;
        setIsPlaying(false);
      } else {
        setPlayIndex(i);
      }
    }, 600);
  }, [isPlaying, playIndex, timeline.length, prefersReducedMotion]);

  const selectedA = useMemo(
    () => districts.find((d) => d.code === selectedDistrict),
    [districts, selectedDistrict]
  );
  const selectedB = useMemo(
    () => districts.find((d) => d.code === comparedDistrict),
    [districts, comparedDistrict]
  );

  const avgScore = useMemo(
    () => districts.length ? Math.round(districts.reduce((acc, d) => acc + d.score, 0) / districts.length) : 58,
    [districts]
  );

  const indicators = useMemo(() => [
    {
      id: 'score', label: 'Score global de synthèse', familyId: 'all',
      idxA: selectedA?.score, idxB: selectedB?.score, idxAvg: avgScore,
      rawA: selectedA ? `${selectedA.score} %` : null,
      rawB: selectedB ? `${selectedB.score} %` : null,
      rawAvg: `${avgScore} %`,
    },
    {
      id: 'immobilier', label: 'Marché immobilier & prix', familyId: 'immobilier',
      idxA: selectedA?.immobilier_idx, idxB: selectedB?.immobilier_idx, idxAvg: overview?.immobilier_idx || 65,
      rawA: selectedA ? `${formatValue('prix_m2', selectedA.prix_m2)}` : null,
      rawB: selectedB ? `${formatValue('prix_m2', selectedB.prix_m2)}` : null,
      rawAvg: overview ? `${formatValue('prix_m2', overview.prix_m2)}` : null,
    },
    {
      id: 'logement_social', label: 'Logement social & mixité', familyId: 'logement_social',
      idxA: selectedA?.logement_social_idx, idxB: selectedB?.logement_social_idx, idxAvg: overview?.logement_social_idx || 22,
      rawA: selectedA ? `${formatValue('logement_social_pct', selectedA.logement_social_pct)}` : null,
      rawB: selectedB ? `${formatValue('logement_social_pct', selectedB.logement_social_pct)}` : null,
      rawAvg: overview ? `${formatValue('logement_social_pct', overview.logement_social_pct)}` : null,
    },
    {
      id: 'revenus', label: 'Revenus & socio-éco', familyId: 'revenus',
      idxA: selectedA?.revenu_idx, idxB: selectedB?.revenu_idx, idxAvg: overview?.revenu_idx || 55,
      rawA: selectedA ? formatValue('revenu_median', selectedA.revenu_median) : null,
      rawB: selectedB ? formatValue('revenu_median', selectedB.revenu_median) : null,
      rawAvg: overview ? formatValue('revenu_median', overview.revenu_median) : null,
    },
    {
      id: 'cadre_vie', label: 'Cadre de vie & attractivité', familyId: 'cadre_vie',
      idxA: selectedA?.cadre_vie_idx, idxB: selectedB?.cadre_vie_idx, idxAvg: overview?.cadre_vie_idx || 68,
      rawA: selectedA ? `Accessibilité ${selectedA.accessibility_index} %` : null,
      rawB: selectedB ? `Accessibilité ${selectedB.accessibility_index} %` : null,
      rawAvg: overview ? `Accessibilité ${overview.accessibility_index} %` : null,
    },
    {
      id: 'environnement', label: "Qualité de l'environnement", familyId: 'environnement',
      idxA: selectedA?.environnement_idx, idxB: selectedB?.environnement_idx, idxAvg: overview?.environnement_idx || 72,
      rawA: selectedA ? `${selectedA.family_counts.green_space || 0} espaces verts` : null,
      rawB: selectedB ? `${selectedB.family_counts.green_space || 0} espaces verts` : null,
      rawAvg: 'Espaces verts : moyen',
    },
  ], [selectedA, selectedB, avgScore, overview]);

  /* Fix: avoid 388/(length-1) division by zero when timeline has 1 point */
  const divisor = Math.max(1, timeline.length - 1);

  const activeTimelineMax = useMemo(
    () => timeline.length ? Math.max(...timeline.map((t) => getTimelineValue(t, activeFamily))) : 100,
    [timeline, activeFamily]
  );

  const timelineLabel = getTimelineLabel(activeFamily);
  const svgDescText = timeline.length
    ? `${timeline.length} points de ${timeline[0]?.label} à ${timeline[timeline.length - 1]?.label}`
    : 'Aucune donnée';

  /* SVG coordinate helper */
  const cx = (idx: number) => idx * (388 / divisor);
  const cy = (val: number) => 76 - (val / activeTimelineMax) * 60;

  return (
    <motion.aside
      ref={panelRef}
      className="dsfr-surface"
      initial={false}
      animate={{ x: isVisible ? 0 : 480 }}
      transition={{ type: 'tween', ease: [0.4, 0, 0.2, 1], duration: 0.3 }}
      style={{
        position: 'absolute',
        top: '88px',
        right: '16px',
        bottom: '16px',
        width: '420px',
        zIndex: 15,
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '18px',
        overflowY: 'auto',
      }}
    >
      {/* En-tête : sélection & comparaison */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <span className="dsfr-eyebrow">{selectedA ? 'Secteur sélectionné' : 'Vue consolidée'}</span>
            <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '21px', fontWeight: 800, color: 'var(--text-title)', letterSpacing: '-0.01em', marginTop: '2px' }}>
              {selectedA ? `${selectedA.label} arrondissement` : 'Paris'}
            </h2>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            {selectedDistrict && (
              <button
                onClick={() => { setSelectedDistrict(null); setComparedDistrict(null); }}
                className="dsfr-btn dsfr-btn--tertiary"
                style={{ fontSize: '12px', color: 'var(--red-marianne-text)', padding: '6px 8px' }}
              >
                Effacer
              </button>
            )}
            {onClose && (
              <button onClick={onClose} className="dsfr-btn dsfr-btn--tertiary" style={{ padding: '6px' }} title="Masquer" aria-label="Masquer le panneau">
                <X size={16} />
              </button>
            )}
          </div>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-mention)', marginTop: '4px', lineHeight: 1.4 }}>
          {selectedA
            ? 'Comparez ce secteur à un autre arrondissement ou à la moyenne parisienne.'
            : "Sélectionnez un arrondissement sur la carte pour démarrer l'analyse."}
        </p>

        {selectedDistrict && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-default)', fontWeight: 600, whiteSpace: 'nowrap' }}>Comparer à</span>
            <select
              value={comparedDistrict || ''}
              onChange={(e) => setComparedDistrict(e.target.value || null)}
              className="dsfr-select"
              aria-label="Comparer à un autre arrondissement"
            >
              <option value="">Moyenne de la ville</option>
              {districts
                .filter((d) => d.code !== selectedDistrict)
                .map((d) => (
                  <option key={d.code} value={d.code}>{d.label} · {d.name}</option>
                ))}
            </select>
          </div>
        )}
      </div>

      {/* Légende A / B */}
      {selectedA && (
        <div style={{ display: 'flex', gap: '16px', fontSize: '11px', fontWeight: 600 }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--blue-france)' }}>
            <span style={{ width: '12px', height: '4px', background: 'var(--blue-france)' }} /> {selectedA.label} arr.
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: selectedB ? 'var(--red-marianne-text)' : 'var(--text-mention)' }}>
            <span style={{ width: '12px', height: '4px', background: selectedB ? 'var(--red-marianne)' : 'var(--text-mention)' }} />
            {selectedB ? `${selectedB.label} arr.` : 'Moyenne ville'}
          </span>
        </div>
      )}

      {/* Indicateurs */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {indicators.map((ind) => {
          const isDimmed = activeFamily !== 'all' && activeFamily !== ind.familyId;
          const isFocus = activeFamily === ind.familyId;
          return (
            <div
              key={ind.id}
              className={`dsfr-card ${isFocus ? 'dsfr-accent-left' : ''} ${isDimmed ? 'is-dimmed' : ''}`}
              style={{ padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '10px' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-title)' }}>{ind.label}</span>
                {isFocus && <span className="dsfr-tag">Carte active</span>}
              </div>

              {selectedA ? (
                <Gauge label={`${selectedA.label} arr.`} raw={ind.rawA} idx={ind.idxA} color="var(--blue-france)" />
              ) : (
                <Gauge label="Moyenne Paris" raw={ind.rawAvg} idx={ind.idxAvg} color="var(--blue-france)" muted />
              )}

              {selectedDistrict && (
                selectedB ? (
                  <Gauge label={`${selectedB.label} arr.`} raw={ind.rawB} idx={ind.idxB} color="var(--red-marianne-text)" />
                ) : (
                  <Gauge label="Moyenne ville" raw={ind.rawAvg} idx={ind.idxAvg} color="var(--text-mention)" muted />
                )
              )}
            </div>
          );
        })}
      </div>

      {/* Tendance temporelle */}
      <div className="dsfr-card" style={{ padding: '14px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h3 style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-title)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={14} style={{ color: 'var(--blue-france)' }} /> {timelineLabel}
          </h3>
          {timeline.length > 1 && (
            <button
              onClick={togglePlay}
              aria-pressed={isPlaying}
              className="dsfr-btn dsfr-btn--tertiary"
              style={{ padding: '4px 8px', fontSize: '11px', gap: '4px' }}
              title={isPlaying ? 'Pause' : 'Lecture'}
            >
              {isPlaying ? <Pause size={12} /> : <Play size={12} />}
              {isPlaying ? 'Pause' : 'Lecture'}
            </button>
          )}
        </div>
        <div style={{ width: '100%', height: '84px', position: 'relative' }}>
          {timeline.length > 0 ? (
            <>
              <svg
                width="100%"
                height="100%"
                viewBox="0 0 388 84"
                preserveAspectRatio="none"
                role="img"
                aria-labelledby="trend-title trend-desc"
              >
                <title id="trend-title">{timelineLabel}</title>
                <desc id="trend-desc">{svgDescText}</desc>
                <defs>
                  <linearGradient id="trend-fill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--blue-france)" stopOpacity="0.18" />
                    <stop offset="100%" stopColor="var(--blue-france)" stopOpacity="0" />
                  </linearGradient>
                </defs>
                {/* Lignes de repère */}
                {[0, 0.5, 1].map((g) => (
                  <line key={g} x1="0" x2="388" y1={8 + g * 64} y2={8 + g * 64} stroke="var(--border)" strokeWidth="1" aria-hidden="true" />
                ))}
                <path
                  d={`M 0 76 ${timeline.map((t, idx) => `L ${cx(idx)} ${cy(getTimelineValue(t, activeFamily))}`).join(' ')} L 388 76 Z`}
                  fill="url(#trend-fill)"
                  aria-hidden="true"
                />
                <path
                  d={timeline.map((t, idx) => `${idx === 0 ? 'M' : 'L'} ${cx(idx)} ${cy(getTimelineValue(t, activeFamily))}`).join(' ')}
                  fill="none"
                  stroke="var(--blue-france)"
                  strokeWidth="2"
                  aria-hidden="true"
                />
                {/* Cursor line for playback */}
                {playIndex !== null && (
                  <line
                    x1={cx(playIndex)}
                    x2={cx(playIndex)}
                    y1="0"
                    y2="84"
                    stroke="var(--blue-france)"
                    strokeWidth="1"
                    strokeDasharray="3 2"
                    opacity="0.6"
                    aria-hidden="true"
                  />
                )}
                {/* Active point label */}
                {playIndex !== null && timeline[playIndex] && (
                  <text
                    x={Math.min(Math.max(cx(playIndex), 24), 364)}
                    y="14"
                    textAnchor="middle"
                    fontSize="9.5"
                    fill="var(--text-title)"
                    fontFamily="var(--font-sans)"
                    fontWeight="600"
                    aria-hidden="true"
                  >
                    {timeline[playIndex].label} · {getTimelineValue(timeline[playIndex], activeFamily).toFixed(0)}
                  </text>
                )}
                {/* Data points */}
                {timeline.map((t, idx) => (
                  <circle
                    key={idx}
                    cx={cx(idx)}
                    cy={cy(getTimelineValue(t, activeFamily))}
                    r={playIndex === idx ? 4 : 2.5}
                    fill={playIndex === idx ? 'var(--blue-france)' : 'var(--bg)'}
                    stroke="var(--blue-france)"
                    strokeWidth="1.5"
                    aria-hidden="true"
                  />
                ))}
              </svg>
              {/* Text alternative for screen readers */}
              <span className="sr-only">
                {timeline.map((t) => `${t.label}: ${getTimelineValue(t, activeFamily).toFixed(0)}`).join(', ')}
              </span>
            </>
          ) : (
            <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-mention)', fontSize: '12px' }}>
              Chargement des tendances…
            </div>
          )}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-mention)', marginTop: '6px' }}>
          <span>{timeline[0]?.label || 'Début'}</span>
          {playIndex !== null && timeline[playIndex] && (
            <span style={{ color: 'var(--blue-france)', fontWeight: 600 }}>{timeline[playIndex].label}</span>
          )}
          <span>{timeline[timeline.length - 1]?.label || 'Fin'}</span>
        </div>
      </div>

      {/* Flux d'événements */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <h3 style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-title)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={14} className="blink-soft" style={{ color: 'var(--red-marianne)' }} />
          Flux d'ingestion · événements Cassandra
        </h3>
        <div className="dsfr-card--alt" style={{ padding: '4px 12px', overflowY: 'auto', maxHeight: '140px' }}>
          {events.length > 0 ? (
            events.slice(0, 8).map((evt) => (
              <div key={evt.event_id} style={{ display: 'flex', flexDirection: 'column', gap: '2px', borderBottom: '1px solid var(--border)', padding: '8px 0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px' }}>
                  <span style={{ color: 'var(--blue-france)', fontWeight: 600 }}>{evt.event_type}</span>
                  <span className="tabular" style={{ color: 'var(--text-mention)' }}>{new Date(evt.event_time).toLocaleTimeString('fr-FR')}</span>
                </div>
                <span style={{ fontSize: '11px', color: 'var(--text-default)' }}>
                  {evt.payload.message || `Message du district ${evt.district_code}`}
                </span>
              </div>
            ))
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-mention)', fontSize: '11px', padding: '16px 0' }}>
              En attente d'événements Kafka…
            </div>
          )}
        </div>
      </div>
    </motion.aside>
  );
});

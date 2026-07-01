import React, { useState, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X, ArrowUpDown, ArrowUp, ArrowDown,
  Download, Search, TableProperties,
} from 'lucide-react';
import { District } from '../types';

interface DataTableProps {
  districts: District[];
  selectedDistrict: string | null;
  setSelectedDistrict: (code: string | null) => void;
  isVisible: boolean;
  onClose: () => void;
}

type SortKey =
  | 'label' | 'score'
  | 'prix_m2' | 'logement_social_pct' | 'revenu_median'
  | 'cadre_vie_idx' | 'environnement_idx' | 'sales_volume';

type SortDir = 'asc' | 'desc';

const COLUMNS: { key: SortKey; label: string; fmt: (d: District) => string; align?: 'right' }[] = [
  { key: 'label',               label: 'Arr.',         fmt: (d) => `${d.label} · ${d.name}` },
  { key: 'score',               label: 'Score',        fmt: (d) => `${d.score}`,                  align: 'right' },
  { key: 'prix_m2',             label: 'Prix/m²',      fmt: (d) => `${Math.round(d.prix_m2).toLocaleString('fr-FR')} €`, align: 'right' },
  { key: 'logement_social_pct', label: 'Logt social',  fmt: (d) => `${d.logement_social_pct.toFixed(1)} %`, align: 'right' },
  { key: 'revenu_median',       label: 'Revenus',      fmt: (d) => `${Math.round(d.revenu_median).toLocaleString('fr-FR')} €`, align: 'right' },
  { key: 'cadre_vie_idx',       label: 'Cadre de vie', fmt: (d) => `${d.cadre_vie_idx}`,          align: 'right' },
  { key: 'environnement_idx',   label: 'Environ.',     fmt: (d) => `${d.environnement_idx}`,      align: 'right' },
  { key: 'sales_volume',        label: 'Ventes',       fmt: (d) => `${d.sales_volume}`,           align: 'right' },
];

function scoreColor(s: number): string {
  if (s >= 75) return 'var(--success)';
  if (s >= 50) return '#F59E0B';
  return 'var(--error)';
}

function ScoreBadge({ value }: { value: number }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      minWidth: '36px', height: '22px', borderRadius: '4px', fontSize: '11px',
      fontWeight: 700, fontVariantNumeric: 'tabular-nums',
      background: scoreColor(value) + '22',
      color: scoreColor(value),
      border: `1px solid ${scoreColor(value)}44`,
    }}>
      {value}
    </span>
  );
}

function IdxBar({ value }: { value: number }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      <div style={{ width: '48px', height: '4px', background: 'var(--bg-contrast)', borderRadius: '2px', overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${Math.min(100, value)}%`,
          background: scoreColor(value), transition: 'width 0.3s ease',
        }} />
      </div>
      <span style={{ fontSize: '11px', color: 'var(--text-mention)', fontVariantNumeric: 'tabular-nums', minWidth: '22px' }}>
        {value}
      </span>
    </div>
  );
}

function exportCSV(districts: District[]) {
  const headers = COLUMNS.map((c) => c.label);
  const rows = districts.map((d) => COLUMNS.map((c) => {
    const raw = c.fmt(d).replace(/\s*€\s*/g, '').replace(/\s*%\s*/g, '').replace(/\s/g, '');
    return raw;
  }));
  const csv = [headers, ...rows].map((r) => r.join(';')).join('\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'urban_data_explorer_arrondissements.csv';
  a.click();
  URL.revokeObjectURL(url);
}

export const DataTable: React.FC<DataTableProps> = React.memo(function DataTable({
  districts,
  selectedDistrict,
  setSelectedDistrict,
  isVisible,
  onClose,
}) {
  const [sortKey, setSortKey] = useState<SortKey>('score');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [query, setQuery] = useState('');

  const handleSort = useCallback((key: SortKey) => {
    setSortKey((prev) => {
      if (prev === key) { setSortDir((d) => d === 'asc' ? 'desc' : 'asc'); return key; }
      setSortDir('desc');
      return key;
    });
  }, []);

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    return districts.filter((d) =>
      !q || d.name.toLowerCase().includes(q) || d.label.toLowerCase().includes(q) || d.code.includes(q)
    );
  }, [districts, query]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const av = sortKey === 'label' ? a.label : (a[sortKey] as number);
      const bv = sortKey === 'label' ? b.label : (b[sortKey] as number);
      if (typeof av === 'string') return sortDir === 'asc' ? av.localeCompare(bv as string) : (bv as string).localeCompare(av);
      return sortDir === 'asc' ? (av as number) - (bv as number) : (bv as number) - (av as number);
    });
  }, [filtered, sortKey, sortDir]);

  const SortIcon = ({ k }: { k: SortKey }) => {
    if (sortKey !== k) return <ArrowUpDown size={11} style={{ opacity: 0.35 }} />;
    return sortDir === 'asc' ? <ArrowUp size={11} /> : <ArrowDown size={11} />;
  };

  const thStyle: React.CSSProperties = {
    padding: '10px 12px', fontSize: '11px', fontWeight: 700,
    color: 'var(--text-mention)', textTransform: 'uppercase', letterSpacing: '0.06em',
    borderBottom: '2px solid var(--border)', whiteSpace: 'nowrap',
    position: 'sticky', top: 0, background: 'var(--bg-alt)', zIndex: 2,
    cursor: 'pointer', userSelect: 'none',
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ y: '100%', opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: '100%', opacity: 0 }}
          transition={{ type: 'tween', ease: [0.4, 0, 0.2, 1], duration: 0.28 }}
          style={{
            position: 'absolute', bottom: 0, left: 0, right: 0,
            height: '42vh', minHeight: '260px', maxHeight: '520px',
            zIndex: 25,
            background: 'var(--bg-alt)',
            borderTop: '2px solid #163767',
            boxShadow: '0 -4px 24px rgba(0,0,0,0.14)',
            display: 'flex', flexDirection: 'column',
          }}
          role="dialog"
          aria-label="Tableau des arrondissements"
        >
          {/* Toolbar */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: '12px',
            padding: '10px 16px', borderBottom: '1px solid var(--border)',
            flexShrink: 0,
          }}>
            <TableProperties size={16} style={{ color: '#163767', flexShrink: 0 }} />
            <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-title)', flexShrink: 0 }}>
              Tableau des arrondissements
              <span style={{ fontWeight: 400, color: 'var(--text-mention)', marginLeft: '8px' }}>
                {sorted.length} / {districts.length}
              </span>
            </span>

            {/* Recherche */}
            <div style={{ position: 'relative', flex: 1, maxWidth: '260px' }}>
              <Search size={13} style={{
                position: 'absolute', left: '9px', top: '50%', transform: 'translateY(-50%)',
                color: 'var(--text-mention)', pointerEvents: 'none',
              }} />
              <input
                type="search"
                placeholder="Rechercher un arrondissement..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                style={{
                  width: '100%', paddingLeft: '30px', paddingRight: '8px',
                  height: '32px', fontSize: '12px',
                  border: '1px solid var(--border)', borderRadius: '4px',
                  background: 'var(--bg)', color: 'var(--text-default)',
                  outline: 'none',
                }}
                aria-label="Rechercher un arrondissement"
              />
            </div>

            <div style={{ flex: 1 }} />

            {/* Export CSV */}
            <button
              onClick={() => exportCSV(sorted)}
              className="dsfr-btn dsfr-btn--tertiary"
              style={{ fontSize: '11px', gap: '5px' }}
              title="Exporter en CSV"
            >
              <Download size={13} /> CSV
            </button>

            {/* Fermer */}
            <button
              onClick={onClose}
              className="dsfr-btn dsfr-btn--tertiary"
              style={{ padding: '6px' }}
              aria-label="Fermer le tableau"
            >
              <X size={16} />
            </button>
          </div>

          {/* Table */}
          <div style={{ flex: 1, overflowY: 'auto', overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed' }}>
              <colgroup>
                <col style={{ width: '200px' }} />
                <col style={{ width: '80px' }} />
                <col style={{ width: '110px' }} />
                <col style={{ width: '110px' }} />
                <col style={{ width: '120px' }} />
                <col style={{ width: '130px' }} />
                <col style={{ width: '110px' }} />
                <col style={{ width: '80px' }} />
              </colgroup>
              <thead>
                <tr>
                  {COLUMNS.map((col) => (
                    <th
                      key={col.key}
                      style={{ ...thStyle, textAlign: col.align ?? 'left' }}
                      onClick={() => handleSort(col.key)}
                      aria-sort={sortKey === col.key ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
                    >
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        {col.label}
                        <SortIcon k={col.key} />
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sorted.map((d) => {
                  const isSelected = d.code === selectedDistrict;
                  return (
                    <tr
                      key={d.code}
                      onClick={() => setSelectedDistrict(isSelected ? null : d.code)}
                      style={{
                        cursor: 'pointer',
                        background: isSelected ? '#163767' + '18' : undefined,
                        borderBottom: '1px solid var(--border)',
                        transition: 'background 0.15s',
                      }}
                      aria-selected={isSelected}
                    >
                      {/* Arrondissement */}
                      <td style={{ padding: '9px 12px', fontSize: '12px', color: 'var(--text-title)', fontWeight: isSelected ? 700 : 500 }}>
                        <span style={{
                          display: 'inline-block', width: '26px', height: '18px',
                          lineHeight: '18px', textAlign: 'center', borderRadius: '3px',
                          background: isSelected ? '#163767' : 'var(--bg-contrast)',
                          color: isSelected ? '#fff' : 'var(--text-mention)',
                          fontSize: '10px', fontWeight: 700, marginRight: '6px', flexShrink: 0,
                        }}>
                          {d.label.replace(/[^0-9]/g, '')}
                        </span>
                        <span style={{ color: 'var(--text-default)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {d.name}
                        </span>
                      </td>

                      {/* Score */}
                      <td style={{ padding: '9px 12px', textAlign: 'right' }}>
                        <ScoreBadge value={d.score} />
                      </td>

                      {/* Prix/m² */}
                      <td style={{ padding: '9px 12px', textAlign: 'right', fontSize: '12px', fontVariantNumeric: 'tabular-nums', color: 'var(--text-default)' }}>
                        {Math.round(d.prix_m2).toLocaleString('fr-FR')} €
                      </td>

                      {/* Logt social */}
                      <td style={{ padding: '9px 12px', textAlign: 'right', fontSize: '12px', fontVariantNumeric: 'tabular-nums', color: 'var(--text-default)' }}>
                        {d.logement_social_pct.toFixed(1)} %
                      </td>

                      {/* Revenus */}
                      <td style={{ padding: '9px 12px', textAlign: 'right', fontSize: '12px', fontVariantNumeric: 'tabular-nums', color: 'var(--text-default)' }}>
                        {Math.round(d.revenu_median).toLocaleString('fr-FR')} €
                      </td>

                      {/* Cadre de vie */}
                      <td style={{ padding: '9px 12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                          <IdxBar value={d.cadre_vie_idx} />
                        </div>
                      </td>

                      {/* Environnement */}
                      <td style={{ padding: '9px 12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                          <IdxBar value={d.environnement_idx} />
                        </div>
                      </td>

                      {/* Ventes */}
                      <td style={{ padding: '9px 12px', textAlign: 'right', fontSize: '12px', fontVariantNumeric: 'tabular-nums', color: 'var(--text-mention)' }}>
                        {d.sales_volume}
                      </td>
                    </tr>
                  );
                })}

                {sorted.length === 0 && (
                  <tr>
                    <td colSpan={COLUMNS.length} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-mention)', fontSize: '12px' }}>
                      Aucun arrondissement ne correspond a la recherche.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
});

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X, Database, Table2, ChevronRight, ChevronDown,
  RefreshCw, Search, ChevronLeft, ChevronRight as ChevronRightIcon,
  AlertCircle, Wifi, WifiOff, Copy, Check,
} from 'lucide-react';
import { API_BASE } from '../services/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface TableMeta { name: string; row_estimate?: number }
interface SchemaMeta { name: string; tables: TableMeta[] }

interface PgSource {
  id: 'pg'; label: string; type: 'sql';
  status: 'connected' | 'unavailable'; error?: string;
  schemas: SchemaMeta[];
}
interface CassSource {
  id: 'cass'; label: string; type: 'nosql';
  status: 'connected' | 'unavailable'; error?: string;
  keyspace: string; tables: TableMeta[];
}
type Source = PgSource | CassSource;

interface ColMeta {
  column_name: string;
  data_type: string;
  is_nullable?: string;
  kind?: string;
}

interface TableData {
  source: string;
  schema?: string;
  table: string;
  columns: ColMeta[];
  rows: Record<string, unknown>[];
  total?: number;
  page?: number;
  page_size?: number;
  pages?: number;
  note?: string;
}

interface Selection { source: 'pg' | 'cass'; schema?: string; table: string }

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------
async function fetchInventory(): Promise<Source[]> {
  const r = await fetch(`${API_BASE}/tables/`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const data = await r.json();
  return data.sources as Source[];
}

async function fetchTableData(
  sel: Selection, page: number, pageSize: number, filterCol?: string, filterVal?: string
): Promise<TableData> {
  let url: string;
  if (sel.source === 'pg') {
    url = `${API_BASE}/tables/pg/${sel.schema ?? 'public'}/${sel.table}?page=${page}&page_size=${pageSize}`;
    if (filterCol && filterVal) url += `&filter_col=${filterCol}&filter_val=${encodeURIComponent(filterVal)}`;
  } else {
    url = `${API_BASE}/tables/cass/${sel.table}?page_size=${pageSize}`;
  }
  const r = await fetch(url);
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: `HTTP ${r.status}` }));
    throw new Error(err.detail ?? `HTTP ${r.status}`);
  }
  return r.json();
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatusDot({ status }: { status: 'connected' | 'unavailable' }) {
  return (
    <span style={{
      width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
      background: status === 'connected' ? 'var(--success)' : 'var(--error)',
      display: 'inline-block',
    }} />
  );
}

function CopyBtn({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return (
    <button
      onClick={copy}
      style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px 4px', color: 'var(--text-mention)', lineHeight: 1 }}
      title="Copier la valeur"
    >
      {copied ? <Check size={11} /> : <Copy size={11} />}
    </button>
  );
}

function TypeBadge({ type, kind }: { type: string; kind?: string }) {
  const color =
    type.includes('int') || type.includes('bigint') || type.includes('float') || type.includes('double') || type.includes('decimal') || type.includes('numeric')
      ? '#F59E0B'
      : type.includes('text') || type.includes('varchar') || type.includes('char') || type.includes('uuid')
      ? '#0C78B4'
      : type.includes('bool')
      ? '#10B981'
      : type.includes('timestamp') || type.includes('date')
      ? '#FF43B8'
      : 'var(--text-mention)';

  return (
    <span style={{
      fontSize: '9px', fontWeight: 600, padding: '1px 5px', borderRadius: 3,
      background: color + '22', color, border: `1px solid ${color}33`,
      textTransform: 'uppercase', letterSpacing: '0.04em', whiteSpace: 'nowrap',
    }}>
      {kind === 'partition_key' ? 'PK · ' : kind === 'clustering' ? 'CK · ' : ''}{type.replace('character varying', 'varchar').replace('timestamp without time zone', 'timestamp')}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Sidebar tree
// ---------------------------------------------------------------------------

function SidebarTree({
  sources,
  selected,
  onSelect,
}: {
  sources: Source[];
  selected: Selection | null;
  onSelect: (s: Selection) => void;
}) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const toggle = (k: string) => setExpanded(p => ({ ...p, [k]: !p[k] }));

  return (
    <div style={{ padding: '8px 0' }}>
      {sources.map(src => (
        <div key={src.id}>
          {/* Source header */}
          <div
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 12px', cursor: 'pointer',
              fontWeight: 700, fontSize: 11, textTransform: 'uppercase',
              letterSpacing: '0.06em', color: 'var(--text-mention)',
            }}
            onClick={() => toggle(src.id)}
          >
            {expanded[src.id] ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            <Database size={13} style={{ flexShrink: 0 }} />
            <span style={{ flex: 1 }}>{src.label}</span>
            <StatusDot status={src.status} />
          </div>

          {/* PG - schemas + tables */}
          {expanded[src.id] && src.type === 'sql' && (src as PgSource).schemas.map(sch => (
            <div key={sch.name}>
              <div
                style={{
                  display: 'flex', alignItems: 'center', gap: 5,
                  padding: '4px 12px 4px 28px', cursor: 'pointer',
                  fontSize: 11, color: 'var(--text-mention)', fontWeight: 600,
                }}
                onClick={() => toggle(`pg_${sch.name}`)}
              >
                {expanded[`pg_${sch.name}`] ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
                <span>{sch.name}</span>
                <span style={{ marginLeft: 'auto', fontSize: 10, opacity: 0.6 }}>{sch.tables.length}</span>
              </div>
              {expanded[`pg_${sch.name}`] && sch.tables.map(t => {
                const isActive = selected?.source === 'pg' && selected.schema === sch.name && selected.table === t.name;
                return (
                  <div
                    key={t.name}
                    onClick={() => onSelect({ source: 'pg', schema: sch.name, table: t.name })}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 6,
                      padding: '5px 12px 5px 44px', cursor: 'pointer',
                      fontSize: 12,
                      background: isActive ? '#163767' + '20' : 'transparent',
                      color: isActive ? '#163767' : 'var(--text-default)',
                      fontWeight: isActive ? 600 : 400,
                      borderRight: isActive ? '2px solid #163767' : '2px solid transparent',
                    }}
                  >
                    <Table2 size={12} style={{ flexShrink: 0, opacity: 0.7 }} />
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.name}</span>
                    {t.row_estimate != null && (
                      <span style={{ fontSize: 10, color: 'var(--text-mention)', flexShrink: 0 }}>
                        ~{t.row_estimate > 1000 ? `${Math.round(t.row_estimate / 1000)}k` : t.row_estimate}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          ))}

          {/* Cassandra - tables directes */}
          {expanded[src.id] && src.type === 'nosql' && (
            <div>
              <div style={{ padding: '2px 12px 2px 28px', fontSize: 10, color: 'var(--text-mention)', fontStyle: 'italic' }}>
                keyspace: {(src as CassSource).keyspace}
              </div>
              {(src as CassSource).tables.map(t => {
                const isActive = selected?.source === 'cass' && selected.table === t.name;
                return (
                  <div
                    key={t.name}
                    onClick={() => onSelect({ source: 'cass', table: t.name })}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 6,
                      padding: '5px 12px 5px 28px', cursor: 'pointer',
                      fontSize: 12,
                      background: isActive ? '#163767' + '20' : 'transparent',
                      color: isActive ? '#163767' : 'var(--text-default)',
                      fontWeight: isActive ? 600 : 400,
                      borderRight: isActive ? '2px solid #163767' : '2px solid transparent',
                    }}
                  >
                    <Table2 size={12} style={{ flexShrink: 0, opacity: 0.7 }} />
                    <span>{t.name}</span>
                  </div>
                );
              })}
              {src.status === 'unavailable' && (
                <div style={{ padding: '4px 12px 4px 28px', fontSize: 11, color: 'var(--error)' }}>
                  <WifiOff size={10} style={{ marginRight: 4 }} />
                  {(src as CassSource & { error?: string }).error?.slice(0, 60)}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Data grid
// ---------------------------------------------------------------------------

function DataGrid({ data, loading, error }: {
  data: TableData | null;
  loading: boolean;
  error: string | null;
}) {
  const tbodyRef = useRef<HTMLDivElement>(null);

  if (loading) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 12 }}>
        <div style={{ width: 32, height: 32, border: '3px solid var(--border)', borderTop: '3px solid #163767', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
        <span style={{ fontSize: 12, color: 'var(--text-mention)' }}>Chargement des donnees...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 10, padding: 32 }}>
        <AlertCircle size={32} style={{ color: 'var(--error)', opacity: 0.7 }} />
        <span style={{ fontSize: 13, color: 'var(--error)', textAlign: 'center', maxWidth: 360 }}>{error}</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 10, opacity: 0.4 }}>
        <Database size={48} style={{ color: 'var(--text-mention)' }} />
        <span style={{ fontSize: 13, color: 'var(--text-mention)' }}>Selectionnez une table dans le panneau gauche</span>
      </div>
    );
  }

  const { columns, rows } = data;

  return (
    <div ref={tbodyRef} style={{ flex: 1, overflow: 'auto', fontSize: 12 }}>
      <table style={{ width: 'max-content', minWidth: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{
              width: 48, minWidth: 48, padding: '8px 10px',
              borderBottom: '2px solid var(--border)', borderRight: '1px solid var(--border)',
              background: 'var(--bg-alt)', position: 'sticky', top: 0, left: 0, zIndex: 3,
              fontSize: 10, color: 'var(--text-mention)', textAlign: 'center',
            }}>#</th>
            {columns.map(col => (
              <th
                key={col.column_name}
                style={{
                  padding: '8px 12px', textAlign: 'left', whiteSpace: 'nowrap',
                  borderBottom: '2px solid var(--border)', borderRight: '1px solid var(--border)',
                  background: 'var(--bg-alt)', position: 'sticky', top: 0, zIndex: 2,
                  minWidth: 120,
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <span style={{ fontWeight: 700, fontSize: 11, color: 'var(--text-title)' }}>{col.column_name}</span>
                  <TypeBadge type={col.data_type} kind={col.kind} />
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length + 1}
                style={{ padding: 24, textAlign: 'center', color: 'var(--text-mention)', fontSize: 12 }}
              >
                Table vide.
              </td>
            </tr>
          ) : rows.map((row, ri) => (
            <tr
              key={ri}
              style={{ borderBottom: '1px solid var(--border)' }}
              className="table-row-hover"
            >
              <td style={{
                padding: '6px 10px', textAlign: 'center', fontSize: 10,
                color: 'var(--text-mention)', fontVariantNumeric: 'tabular-nums',
                background: 'var(--bg-alt)', position: 'sticky', left: 0, zIndex: 1,
                borderRight: '1px solid var(--border)',
              }}>
                {ri + 1}
              </td>
              {columns.map(col => {
                const val = row[col.column_name];
                const isNull = val === null || val === undefined;
                const isLong = typeof val === 'string' && val.length > 80;
                return (
                  <td
                    key={col.column_name}
                    style={{
                      padding: '6px 12px', borderRight: '1px solid var(--border)',
                      maxWidth: 320, whiteSpace: isLong ? 'normal' : 'nowrap',
                      overflow: 'hidden', textOverflow: isLong ? 'clip' : 'ellipsis',
                    }}
                  >
                    {isNull ? (
                      <span style={{ color: 'var(--text-mention)', fontStyle: 'italic', fontSize: 11 }}>NULL</span>
                    ) : typeof val === 'boolean' ? (
                      <span style={{ color: val ? 'var(--success)' : 'var(--error)', fontWeight: 600, fontSize: 11 }}>
                        {val ? 'true' : 'false'}
                      </span>
                    ) : (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        <span style={{ color: 'var(--text-default)', fontVariantNumeric: 'tabular-nums' }}>
                          {String(val)}
                        </span>
                        <CopyBtn text={String(val)} />
                      </span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export const TableExplorer: React.FC<{ isVisible: boolean; onClose: () => void }> = ({ isVisible, onClose }) => {
  const [sources, setSources] = useState<Source[]>([]);
  const [inventoryLoading, setInventoryLoading] = useState(false);
  const [inventoryError, setInventoryError] = useState<string | null>(null);

  const [selected, setSelected] = useState<Selection | null>(null);
  const [tableData, setTableData] = useState<TableData | null>(null);
  const [dataLoading, setDataLoading] = useState(false);
  const [dataError, setDataError] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [filterCol, setFilterCol] = useState('');
  const [filterVal, setFilterVal] = useState('');
  const [filterDraft, setFilterDraft] = useState('');

  const loadInventory = useCallback(async () => {
    setInventoryLoading(true);
    setInventoryError(null);
    try {
      const s = await fetchInventory();
      setSources(s);
      // Auto-expand first available source
      const first = s.find(x => x.status === 'connected');
      if (first) {
        const firstEl = document.querySelector(`[data-src="${first.id}"]`);
        if (firstEl) (firstEl as HTMLElement).click();
      }
    } catch (e) {
      setInventoryError(String(e));
    } finally {
      setInventoryLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isVisible && sources.length === 0) loadInventory();
  }, [isVisible, sources.length, loadInventory]);

  const loadTable = useCallback(async (sel: Selection, pg: number, fc?: string, fv?: string) => {
    setDataLoading(true);
    setDataError(null);
    try {
      const d = await fetchTableData(sel, pg, pageSize, fc, fv);
      setTableData(d);
    } catch (e) {
      setDataError(String(e));
      setTableData(null);
    } finally {
      setDataLoading(false);
    }
  }, [pageSize]);

  const handleSelect = (sel: Selection) => {
    setSelected(sel);
    setPage(1);
    setFilterCol('');
    setFilterVal('');
    setFilterDraft('');
    loadTable(sel, 1);
  };

  const applyFilter = () => {
    if (!selected) return;
    setFilterVal(filterDraft);
    setPage(1);
    loadTable(selected, 1, filterCol || undefined, filterDraft || undefined);
  };

  const goPage = (p: number) => {
    if (!selected) return;
    setPage(p);
    loadTable(selected, p, filterCol || undefined, filterVal || undefined);
  };

  const pages = tableData?.pages ?? 1;
  const total = tableData?.total;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.97 }}
          transition={{ type: 'tween', ease: [0.4, 0, 0.2, 1], duration: 0.22 }}
          style={{
            position: 'absolute', inset: 0,
            zIndex: 30,
            display: 'flex', flexDirection: 'column',
            background: 'var(--bg)',
          }}
          role="dialog"
          aria-label="Explorateur de tables"
        >
          {/* Topbar */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 12,
            padding: '0 16px', height: 48, flexShrink: 0,
            borderBottom: '2px solid #163767',
            background: 'var(--bg-alt)',
          }}>
            <Database size={16} style={{ color: '#163767' }} />
            <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-title)' }}>Table Editor</span>

            {/* Filtre */}
            {selected && selected.source === 'pg' && tableData && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 16 }}>
                <select
                  value={filterCol}
                  onChange={e => setFilterCol(e.target.value)}
                  style={{
                    height: 28, fontSize: 11, border: '1px solid var(--border)',
                    borderRadius: 4, background: 'var(--bg)', color: 'var(--text-default)',
                    padding: '0 6px',
                  }}
                  aria-label="Colonne de filtre"
                >
                  <option value="">-- colonne --</option>
                  {tableData.columns.map(c => (
                    <option key={c.column_name} value={c.column_name}>{c.column_name}</option>
                  ))}
                </select>
                <input
                  type="text"
                  placeholder="valeur..."
                  value={filterDraft}
                  onChange={e => setFilterDraft(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && applyFilter()}
                  style={{
                    height: 28, fontSize: 11, border: '1px solid var(--border)',
                    borderRadius: 4, background: 'var(--bg)', color: 'var(--text-default)',
                    padding: '0 8px', width: 140,
                  }}
                  aria-label="Valeur de filtre"
                />
                <button
                  onClick={applyFilter}
                  className="dsfr-btn dsfr-btn--tertiary"
                  style={{ height: 28, fontSize: 11, padding: '0 10px' }}
                >
                  <Search size={12} /> Filtrer
                </button>
                {filterVal && (
                  <button
                    onClick={() => { setFilterVal(''); setFilterDraft(''); setFilterCol(''); loadTable(selected, 1); }}
                    className="dsfr-btn dsfr-btn--tertiary"
                    style={{ height: 28, fontSize: 11, padding: '0 8px', color: 'var(--error)' }}
                  >
                    <X size={12} />
                  </button>
                )}
              </div>
            )}

            <div style={{ flex: 1 }} />

            {/* Status */}
            {selected && tableData && (
              <span style={{ fontSize: 11, color: 'var(--text-mention)' }}>
                {total != null ? `${total.toLocaleString('fr-FR')} lignes` : `${tableData.rows.length} lignes`}
                {tableData.note && ` · ${tableData.note}`}
              </span>
            )}

            <button
              onClick={loadInventory}
              className="dsfr-btn dsfr-btn--tertiary"
              style={{ padding: '6px', marginLeft: 4 }}
              title="Actualiser"
              aria-label="Actualiser l'inventaire"
            >
              <RefreshCw size={14} className={inventoryLoading ? 'spin' : ''} />
            </button>

            <button
              onClick={onClose}
              className="dsfr-btn dsfr-btn--tertiary"
              style={{ padding: '6px' }}
              aria-label="Fermer l'explorateur"
            >
              <X size={16} />
            </button>
          </div>

          {/* Body */}
          <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
            {/* Sidebar */}
            <div style={{
              width: 220, flexShrink: 0, borderRight: '1px solid var(--border)',
              background: 'var(--bg-alt)', overflowY: 'auto',
            }}>
              {inventoryError ? (
                <div style={{ padding: 12, fontSize: 11, color: 'var(--error)' }}>
                  <AlertCircle size={12} style={{ marginRight: 4 }} />{inventoryError}
                </div>
              ) : inventoryLoading ? (
                <div style={{ padding: 16, fontSize: 11, color: 'var(--text-mention)', textAlign: 'center' }}>
                  Connexion...
                </div>
              ) : (
                <SidebarTree sources={sources} selected={selected} onSelect={handleSelect} />
              )}
            </div>

            {/* Main grid area */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              {/* Breadcrumb */}
              {selected && (
                <div style={{
                  padding: '6px 16px', borderBottom: '1px solid var(--border)',
                  fontSize: 11, color: 'var(--text-mention)',
                  display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0,
                  background: 'var(--bg)',
                }}>
                  <span style={{ fontWeight: 600, color: selected.source === 'pg' ? '#0C78B4' : '#F59E0B' }}>
                    {selected.source === 'pg' ? 'PostgreSQL' : 'Cassandra'}
                  </span>
                  <ChevronRight size={10} />
                  {selected.schema && (
                    <><span>{selected.schema}</span><ChevronRight size={10} /></>
                  )}
                  <span style={{ fontWeight: 700, color: 'var(--text-title)' }}>{selected.table}</span>
                  {tableData?.columns && (
                    <span style={{ marginLeft: 8, opacity: 0.6 }}>{tableData.columns.length} colonnes</span>
                  )}
                </div>
              )}

              {/* Grid */}
              <DataGrid data={tableData} loading={dataLoading} error={dataError} />

              {/* Pagination (PG uniquement) */}
              {tableData && selected?.source === 'pg' && pages > 1 && (
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '8px 16px', borderTop: '1px solid var(--border)',
                  flexShrink: 0, background: 'var(--bg-alt)',
                }}>
                  <button
                    onClick={() => goPage(1)}
                    disabled={page === 1}
                    className="dsfr-btn dsfr-btn--tertiary"
                    style={{ padding: '4px 8px', fontSize: 11 }}
                  >
                    «
                  </button>
                  <button
                    onClick={() => goPage(page - 1)}
                    disabled={page === 1}
                    className="dsfr-btn dsfr-btn--tertiary"
                    style={{ padding: '4px 8px', fontSize: 11 }}
                  >
                    <ChevronLeft size={13} />
                  </button>

                  <span style={{ fontSize: 11, color: 'var(--text-mention)', fontVariantNumeric: 'tabular-nums' }}>
                    Page <strong>{page}</strong> / {pages}
                  </span>

                  <button
                    onClick={() => goPage(page + 1)}
                    disabled={page >= pages}
                    className="dsfr-btn dsfr-btn--tertiary"
                    style={{ padding: '4px 8px', fontSize: 11 }}
                  >
                    <ChevronRightIcon size={13} />
                  </button>
                  <button
                    onClick={() => goPage(pages)}
                    disabled={page >= pages}
                    className="dsfr-btn dsfr-btn--tertiary"
                    style={{ padding: '4px 8px', fontSize: 11 }}
                  >
                    »
                  </button>

                  <div style={{ flex: 1 }} />
                  <span style={{ fontSize: 11, color: 'var(--text-mention)' }}>
                    {pageSize} lignes / page
                  </span>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

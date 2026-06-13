\connect ude

-- ==========================================================================
-- Modèle en étoile – Urban Data Explorer
-- C1.1: Base relationnelle normalisée, intégrité des données
-- ==========================================================================

-- ── Dimensions ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS dim_source (
  source_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  family TEXT NOT NULL,
  catalog_url TEXT NOT NULL,
  provider TEXT NOT NULL DEFAULT 'Ville de Paris',
  metadata_only BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS dim_arrondissement (
  code_arrondissement TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  name TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS dim_iris (
  code_iris TEXT PRIMARY KEY,
  nom_iris TEXT NOT NULL,
  code_arrondissement TEXT NOT NULL REFERENCES dim_arrondissement(code_arrondissement),
  typ_iris TEXT DEFAULT 'H'
);

CREATE TABLE IF NOT EXISTS dim_family (
  family_key TEXT PRIMARY KEY,
  label_fr TEXT NOT NULL
);

INSERT INTO dim_family VALUES
  ('green_space', 'Espaces verts'),
  ('mobility', 'Mobilité'),
  ('public_service', 'Services publics'),
  ('education', 'Éducation'),
  ('culture', 'Culture'),
  ('health', 'Santé'),
  ('housing', 'Logement'),
  ('pressure', 'Pression / travaux')
ON CONFLICT DO NOTHING;

-- Insertion des 20 arrondissements
INSERT INTO dim_arrondissement (code_arrondissement, label, name) VALUES
  ('75001', 'Paris 1er', 'Louvre'),
  ('75002', 'Paris 2e', 'Bourse'),
  ('75003', 'Paris 3e', 'Temple'),
  ('75004', 'Paris 4e', 'Hôtel-de-Ville'),
  ('75005', 'Paris 5e', 'Panthéon'),
  ('75006', 'Paris 6e', 'Luxembourg'),
  ('75007', 'Paris 7e', 'Palais-Bourbon'),
  ('75008', 'Paris 8e', 'Élysée'),
  ('75009', 'Paris 9e', 'Opéra'),
  ('75010', 'Paris 10e', 'Entrepôt'),
  ('75011', 'Paris 11e', 'Popincourt'),
  ('75012', 'Paris 12e', 'Reuilly'),
  ('75013', 'Paris 13e', 'Gobelins'),
  ('75014', 'Paris 14e', 'Observatoire'),
  ('75015', 'Paris 15e', 'Vaugirard'),
  ('75016', 'Paris 16e', 'Passy'),
  ('75017', 'Paris 17e', 'Batignolles-Monceau'),
  ('75018', 'Paris 18e', 'Buttes-Montmartre'),
  ('75019', 'Paris 19e', 'Buttes-Chaumont'),
  ('75020', 'Paris 20e', 'Ménilmontant')
ON CONFLICT DO NOTHING;

-- ── Faits ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fact_arrondissement_dashboard (
  arrondissement_code TEXT PRIMARY KEY REFERENCES dim_arrondissement(code_arrondissement),
  green_space_count INTEGER NOT NULL DEFAULT 0,
  mobility_count INTEGER NOT NULL DEFAULT 0,
  public_service_count INTEGER NOT NULL DEFAULT 0,
  education_count INTEGER NOT NULL DEFAULT 0,
  culture_count INTEGER NOT NULL DEFAULT 0,
  health_count INTEGER NOT NULL DEFAULT 0,
  housing_count INTEGER NOT NULL DEFAULT 0,
  pressure_count INTEGER NOT NULL DEFAULT 0,
  accessibility_index DOUBLE PRECISION NOT NULL DEFAULT 0,
  pressure_index DOUBLE PRECISION NOT NULL DEFAULT 0,
  attractiveness_index DOUBLE PRECISION NOT NULL DEFAULT 0,
  immobilier_idx INTEGER NOT NULL DEFAULT 0,
  logement_social_idx INTEGER NOT NULL DEFAULT 0,
  revenu_idx INTEGER NOT NULL DEFAULT 0,
  cadre_vie_idx INTEGER NOT NULL DEFAULT 0,
  prix_m2 DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  logements_sociaux_count INTEGER NOT NULL DEFAULT 0,
  logement_social_pct DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  revenu_median DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  sales_volume INTEGER NOT NULL DEFAULT 0,
  score INTEGER NOT NULL DEFAULT 0,
  environnement_idx INTEGER NOT NULL DEFAULT 0,
  m2_abordables DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  accessibilite_idx INTEGER NOT NULL DEFAULT 0,
  data_source TEXT NOT NULL DEFAULT 'reference'
);

CREATE TABLE IF NOT EXISTS fact_arrondissement_timeline (
  arrondissement_code TEXT NOT NULL REFERENCES dim_arrondissement(code_arrondissement),
  year INTEGER NOT NULL,
  month INTEGER NOT NULL,
  record_count INTEGER NOT NULL DEFAULT 0,
  accessibility_index DOUBLE PRECISION NOT NULL DEFAULT 0,
  pressure_index DOUBLE PRECISION NOT NULL DEFAULT 0,
  attractiveness_index DOUBLE PRECISION NOT NULL DEFAULT 0,
  immobilier_idx DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  logement_social_idx DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  revenu_idx DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  cadre_vie_idx DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  environnement_idx DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  PRIMARY KEY (arrondissement_code, year, month)
);

-- ── Pipeline ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS pipeline_runs (
  run_date TEXT NOT NULL,
  stage TEXT NOT NULL,
  status TEXT NOT NULL,
  row_count INTEGER NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (run_date, stage)
);

-- ── Index de performance ─────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_fact_dashboard_accessibility
  ON fact_arrondissement_dashboard (accessibility_index DESC);

CREATE INDEX IF NOT EXISTS idx_fact_timeline_period
  ON fact_arrondissement_timeline (year, month);

CREATE INDEX IF NOT EXISTS idx_dim_iris_arrondissement
  ON dim_iris (code_arrondissement);

export interface District {
  code: string;
  name: string;
  label: string;
  family_counts: Record<string, number>;
  accessibility_index: number;
  pressure_index: number;
  attractiveness_index: number;
  score: number;
  immobilier_idx: number;
  logement_social_idx: number;
  revenu_idx: number;
  cadre_vie_idx: number;
  prix_m2: number;
  logements_sociaux_count: number;
  logement_social_pct: number;
  revenu_median: number;
  sales_volume: number;
}

export interface Overview {
  source_count: number;
  family_count: number;
  district_count: number;
  accessibility_index: number;
  pressure_index: number;
  attractiveness_index: number;
  source_family_counts: Record<string, number>;
  immobilier_idx: number;
  logement_social_idx: number;
  revenu_idx: number;
  cadre_vie_idx: number;
  prix_m2: number;
  logement_social_pct: number;
  revenu_median: number;
}

export interface TimelinePoint {
  month: string;
  label: string;
  activity: number;
  accessibility_index: number;
  pressure_index: number;
  attractiveness_index: number;
  immobilier_idx: number;
  logement_social_idx: number;
  revenu_idx: number;
  cadre_vie_idx: number;
}

export interface EventLog {
  event_id: string;
  event_type: string;
  source_id: string;
  district_code: string | null;
  payload: {
    family?: string;
    score?: number;
    message?: string;
  };
  event_time: string;
}

export interface District {
  code: string;
  name: string;
  label: string;
  family_counts: Record<string, number>;
  accessibility_index: number;
  pressure_index: number;
  attractiveness_index: number;
  score: number;
}

export interface Overview {
  source_count: number;
  family_count: number;
  district_count: number;
  accessibility_index: number;
  pressure_index: number;
  attractiveness_index: number;
  source_family_counts: Record<string, number>;
}

export interface TimelinePoint {
  month: string;
  label: string;
  activity: number;
  accessibility_index: number;
  pressure_index: number;
  attractiveness_index: number;
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

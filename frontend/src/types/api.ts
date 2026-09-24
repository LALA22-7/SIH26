// ─────────────────────────────────────────────────────────────────────────────
// CycloneWatch — API response types
// Single source of truth for every shape that crosses the network boundary.
// ─────────────────────────────────────────────────────────────────────────────

/** A single classification center from the PS70 backend */
export interface ClassificationCenter {
  lat: number;
  lon: number;
}

/** A single pattern classification result */
export interface PatternResult {
  label: string;
  confidence: number;
}

/** A single classification entry from the PS70 classifications endpoint */
export interface Classification {
  timestamp: string;
  center: ClassificationCenter;
  pattern: PatternResult;
  model?: { name: string; version?: string };
}

/** Response from /api/ps70/classifications/:eventId */
export interface ClassificationsResponse {
  event_id: string;
  classifications: Classification[];
}

/** Prediction sub-object within a replay step */
export interface StepPrediction {
  t12?: { center: ClassificationCenter };
  t24?: { center: ClassificationCenter };
}

/** Error metrics sub-object within a replay step */
export interface StepErrors {
  t12_km?: number;
  t24_km?: number;
}

/** A single step within a replay sequence */
export interface ReplayStep {
  time: string;
  observation_frame: string;
  prediction?: StepPrediction;
  errors?: StepErrors;
}

/** Response from /api/replay/:eventId */
export interface ReplayResponse {
  event_id: string;
  steps: ReplayStep[];
}

/** Response from /api/metrics?event_id=:eventId */
export interface MetricsResponse {
  event_id: string;
  [key: string]: unknown;
}

/** Response from /api/coastline/distance */
export interface CoastlineDistanceResponse {
  distance_km: number;
}

/** Derived observation used throughout the UI */
export interface CurrentObservation {
  timestamp: string;
  lat: number;
  lng: number;
  prevLat: number | null;
  prevLng: number | null;
  hoursSincePrev: number | null;
  step: ReplayStep;
  classification: Classification;
}

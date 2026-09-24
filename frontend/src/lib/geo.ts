// ─────────────────────────────────────────────────────────────────────────────
// CycloneWatch — Geospatial utility functions
//
// Haversine distance and related calculations extracted from MetricsPanel.
// ─────────────────────────────────────────────────────────────────────────────

const EARTH_RADIUS_KM = 6371;

/**
 * Calculate the great-circle distance between two points using the Haversine
 * formula. Returns distance in kilometres.
 */
export function haversineDistanceKm(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return EARTH_RADIUS_KM * 2 * Math.asin(Math.sqrt(a));
}

/**
 * Estimate the translational speed of a storm given two consecutive
 * observations and the elapsed time between them.
 * Returns speed in km/h, or the provided fallback if inputs are invalid.
 */
export function estimateStormSpeed(
  prevLat: number | null,
  prevLng: number | null,
  lat: number,
  lng: number,
  hoursSincePrev: number | null,
  fallbackKmh = 15,
): number {
  if (
    prevLat === null ||
    prevLng === null ||
    hoursSincePrev === null ||
    hoursSincePrev <= 0
  ) {
    return fallbackKmh;
  }
  const dist = haversineDistanceKm(prevLat, prevLng, lat, lng);
  return dist / hoursSincePrev;
}

// ─────────────────────────────────────────────────────────────────────────────
// CycloneWatch — Centralized API client
//
// This is the ONLY file that knows about endpoint URLs and fetch mechanics.
// To connect a real backend, change ONLY this file.
// ─────────────────────────────────────────────────────────────────────────────

import type {
  ReplayResponse,
  MetricsResponse,
  ClassificationsResponse,
  CoastlineDistanceResponse,
} from '../types/api';

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api';

/**
 * Thin wrapper around fetch that throws on non-OK responses.
 * Returns `null` when a request fails so the UI can degrade gracefully.
 */
async function request<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

// ── Event data (historical replay) ──────────────────────────────────────────

export async function fetchReplay(
  eventId: string,
): Promise<ReplayResponse | null> {
  return request<ReplayResponse>(`${API_BASE}/replay/${eventId}`);
}

export async function fetchMetrics(
  eventId: string,
): Promise<MetricsResponse | null> {
  return request<MetricsResponse>(`${API_BASE}/metrics?event_id=${eventId}`);
}

export async function fetchClassifications(
  eventId: string,
): Promise<ClassificationsResponse | null> {
  return request<ClassificationsResponse>(
    `${API_BASE}/ps70/classifications/${eventId}`,
  );
}

// ── Live meteorological data ────────────────────────────────────────────────

interface OpenMeteoWeather {
  current?: {
    time?: string;
    temperature_2m?: number;
    relative_humidity_2m?: number;
    precipitation?: number;
    surface_pressure?: number;
    wind_speed_10m?: number;
    wind_direction_10m?: number;
  };
}

interface OpenMeteoMarine {
  current?: {
    wave_height?: number;
    ocean_current_velocity?: number;
    ocean_current_direction?: number;
  };
}

export async function fetchWeather(
  lat: number,
  lng: number,
): Promise<OpenMeteoWeather | null> {
  return request<OpenMeteoWeather>(
    `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}` +
      `&current=temperature_2m,relative_humidity_2m,precipitation,surface_pressure,wind_speed_10m,wind_direction_10m` +
      `&wind_speed_unit=kmh`,
  );
}

export async function fetchMarine(
  lat: number,
  lng: number,
): Promise<OpenMeteoMarine | null> {
  return request<OpenMeteoMarine>(
    `https://marine-api.open-meteo.com/v1/marine?latitude=${lat}&longitude=${lng}` +
      `&current=wave_height,ocean_current_velocity,ocean_current_direction`,
  );
}

// ── Coastline distance ──────────────────────────────────────────────────────

export async function fetchCoastlineDistance(
  lat: number,
  lon: number,
): Promise<CoastlineDistanceResponse | null> {
  return request<CoastlineDistanceResponse>(
    `${API_BASE}/coastline/distance?lat=${lat}&lon=${lon}`,
  );
}

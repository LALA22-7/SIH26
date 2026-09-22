import L from 'leaflet';

export const INDIA_BOUNDS = L.latLngBounds(
  L.latLng(-5, 30),
  L.latLng(40, 115),
);

export const INDIA_CENTER: [number, number] = [20, 78];
export const DEFAULT_ZOOM = 4.5;
export const MIN_ZOOM = 3.5;
export const MAX_ZOOM = 9;

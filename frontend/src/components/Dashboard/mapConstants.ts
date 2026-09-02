import L from 'leaflet';

export const INDIA_BOUNDS = L.latLngBounds(
  L.latLng(0, 35),
  L.latLng(35, 110),
);

export const INDIA_CENTER: [number, number] = [17, 78];
export const DEFAULT_ZOOM = 5;
export const MIN_ZOOM = 4.5;
export const MAX_ZOOM = 9;

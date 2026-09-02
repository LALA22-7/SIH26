import L from 'leaflet';
import { INDIA_BOUNDS, INDIA_CENTER, DEFAULT_ZOOM } from './mapConstants';

let _mapRef: L.Map | null = null;

export function registerMap(map: L.Map) { _mapRef = map; }

export function mapResetView()  { _mapRef?.flyTo(INDIA_CENTER, DEFAULT_ZOOM, { duration: 1 }); }
export function mapFitBounds()  { _mapRef?.fitBounds(INDIA_BOUNDS, { padding: [20, 20] }); }
export function mapFitTrack(coords: [number, number][]) {
  if (!_mapRef || coords.length === 0) return;
  _mapRef.fitBounds(L.latLngBounds(coords), { padding: [40, 40], maxZoom: 7 });
}
export function mapZoomIn()  { _mapRef?.zoomIn();  }
export function mapZoomOut() { _mapRef?.zoomOut(); }

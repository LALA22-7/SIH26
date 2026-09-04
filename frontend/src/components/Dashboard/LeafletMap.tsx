import { useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Circle, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useCycloneStore } from '../../store/useCycloneStore';
import { INDIA_BOUNDS, INDIA_CENTER, DEFAULT_ZOOM, MIN_ZOOM, MAX_ZOOM } from './mapConstants';
import { registerMap } from './mapHelpers';

// ── Custom icons ────────────────────────────────────────────────────────────
const CycloneCentreIcon = L.divIcon({
  className: '',
  html: `<div style="position:relative;width:20px;height:20px;">
    <div style="position:absolute;inset:0;border:1.5px solid #FF7A45;border-radius:50%;animation:pulse-ring 2s ease-out infinite;"></div>
    <div style="position:absolute;top:5px;left:5px;width:10px;height:10px;background:#FF7A45;border-radius:50%;box-shadow:0 0 8px #FF7A45;"></div>
  </div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

const LiveCentreIcon = L.divIcon({
  className: '',
  html: `<div style="position:relative;width:16px;height:16px;">
    <div style="position:absolute;inset:0;border:1.5px solid #6FE3B4;border-radius:50%;animation:pulse-ring 2s ease-out infinite;"></div>
    <div style="position:absolute;top:4px;left:4px;width:8px;height:8px;background:#6FE3B4;border-radius:50%;box-shadow:0 0 8px #6FE3B4;"></div>
  </div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

// ── Layer visibility context (passed down via props) ────────────────────────
export interface LayerVisibility {
  satellite: boolean;
  trajectory: boolean;
  structure: boolean;
  centre: boolean;
  forecastTrack: boolean;
  forecastCone: boolean;
  wind: boolean;
  ocean: boolean;
}

// ── Internal component that can access the map instance ─────────────────────
interface MapControllerProps {
  onMapReady: (map: L.Map) => void;
}
function MapController({ onMapReady }: MapControllerProps) {
  const map = useMap();
  useEffect(() => { onMapReady(map); }, [map, onMapReady]);
  return null;
}

// ── Main component ───────────────────────────────────────────────────────────
interface LeafletMapProps {
  layers: LayerVisibility;
  onCentreClick?: () => void;
}

export function LeafletMap({ layers, onCentreClick }: LeafletMapProps) {
  const { mode, activeEventId, getCurrentObservation, liveData, apiClassificationsData, timelineIndex } = useCycloneStore();
  const obs = getCurrentObservation();
  const mapInstanceRef = useRef<L.Map | null>(null);

  // Store map instance on ready
  const handleMapReady = useCallback((map: L.Map) => {
    mapInstanceRef.current = map;
    registerMap(map);
  }, []);

  // Fly to cyclone when event changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !obs) return;
    if (mode === 'HISTORICAL') {
      map.flyTo([obs.lat, obs.lng], 5, { duration: 1.4, easeLinearity: 0.25 });
    } else {
      map.flyTo(INDIA_CENTER, DEFAULT_ZOOM, { duration: 1.2, easeLinearity: 0.25 });
    }
  }, [mode, activeEventId]); // Only fly on event switch, not every timeline step

  // Build the historical track coordinates up to current timeline index
  const trackCoords: [number, number][] = [];
  if (mode === 'HISTORICAL' && apiClassificationsData?.classifications) {
    for (let i = 0; i <= timelineIndex; i++) {
      const c = apiClassificationsData.classifications[i];
      if (c && c.center) {
        trackCoords.push([c.center.lat, c.center.lon]);
      }
    }
  }

  // Build the forecast coords for this specific step (t12, t24)
  const forecastCoords: [number, number][] = [];
  if (mode === 'HISTORICAL' && obs?.step?.prediction) {
    forecastCoords.push([obs.lat, obs.lng]); // Start at current center
    if (obs.step.prediction.t12?.center) {
      forecastCoords.push([obs.step.prediction.t12.center.lat, obs.step.prediction.t12.center.lon]);
    }
    if (obs.step.prediction.t24?.center) {
      forecastCoords.push([obs.step.prediction.t24.center.lat, obs.step.prediction.t24.center.lon]);
    }
  }
  
  // Try to parse uncertainty geometry if the backend provided it
  // In the stub API contract, this is provided at the predict endpoint.
  // We'll leave the cone as a circle for now if not available.
  const uncertaintyRadiusM = 85_000; 

  return (
    <div className="absolute inset-0 w-full h-full">
      <MapContainer
        center={INDIA_CENTER}
        zoom={DEFAULT_ZOOM}
        minZoom={MIN_ZOOM}
        maxZoom={MAX_ZOOM}
        maxBounds={INDIA_BOUNDS}
        maxBoundsViscosity={1.0}
        worldCopyJump={false}
        zoomControl={false}
        attributionControl={false}
        style={{ width: '100%', height: '100%', background: '#080e18' }}
      >
        <MapController onMapReady={handleMapReady} />

        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          attribution="© Esri"
          zIndex={1}
          className="base-tiles"
        />

        {/* NASA GIBS Cloud Layer (Historical) */}
        {mode === 'HISTORICAL' && layers.satellite && obs && (
          <TileLayer
            url={`https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/${obs.timestamp.split('T')[0]}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`}
            opacity={0.65}
            zIndex={2}
            className="cloud-layer"
          />
        )}

        {/* Live fake cloud layer for visual */}
        {mode === 'LIVE' && layers.satellite && (
           <TileLayer
             url="https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/2023-06-13/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg"
             opacity={0.65}
             zIndex={2}
             className="cloud-layer"
           />
        )}

        {mode === 'HISTORICAL' && obs && (
          <>
            {/* Observed track */}
            {layers.trajectory && trackCoords.length > 1 && (
              <Polyline
                positions={trackCoords}
                pathOptions={{ color: '#E7EEF4', weight: 2, opacity: 0.85 }}
              />
            )}

            {/* Forecast track */}
            {layers.forecastTrack && forecastCoords.length > 1 && (
              <Polyline
                positions={forecastCoords}
                pathOptions={{ color: '#FF7A45', weight: 2, dashArray: '5, 7', opacity: 0.75 }}
              />
            )}

            {/* Uncertainty cone */}
            {layers.forecastCone && forecastCoords.length > 1 && (
              <Circle
                center={forecastCoords.at(-1)!}
                radius={uncertaintyRadiusM}
                pathOptions={{
                  color: '#FF7A45', weight: 1, dashArray: '3, 5',
                  fillColor: '#FF7A45', fillOpacity: 0.07,
                }}
              />
            )}

            {/* Cyclone structure halo */}
            {layers.structure && (
              <Circle
                center={[obs.lat, obs.lng]}
                radius={220_000}
                pathOptions={{
                  color: '#4FC3E0', weight: 0,
                  fillColor: '#4FC3E0', fillOpacity: 0.10,
                }}
              />
            )}

            {/* Centre marker */}
            {layers.centre && (
              <Marker
                position={[obs.lat, obs.lng]}
                icon={CycloneCentreIcon}
                eventHandlers={{ click: () => onCentreClick?.() }}
              />
            )}
          </>
        )}

        {/* ── Live mode centre indicator ── */}
        {mode === 'LIVE' && layers.centre && liveData.cyclone.active && (
          <Marker
            position={[15.0, 88.0]}
            icon={LiveCentreIcon}
          />
        )}

      </MapContainer>

      {/* Leaflet CSS overrides */}
      <style>{`
        .leaflet-container { background: #080e18 !important; }
        .base-tiles        { filter: brightness(0.65) contrast(1.1) saturate(0.75) !important; }
        .cloud-layer       { filter: contrast(1.05) brightness(1.05) !important; }
        .leaflet-pane      { z-index: auto !important; }
        .leaflet-top, .leaflet-bottom { z-index: 10 !important; }
        @keyframes pulse-ring {
          0%   { transform: scale(0.4); opacity: 0.9; }
          100% { transform: scale(2.4); opacity: 0;   }
        }
      `}</style>
    </div>
  );
}

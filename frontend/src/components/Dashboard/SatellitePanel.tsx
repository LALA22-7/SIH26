import { useState, useRef, useEffect } from 'react';
import {
  Plus, Minus, Layers, Radio, MoreHorizontal,
  Navigation, Maximize2, Database, Clock,
  Eye, Wind, Waves, Map, GitBranch, Triangle,
} from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import { LeafletMap } from './LeafletMap';
import { mapResetView, mapFitBounds, mapFitTrack, mapZoomIn, mapZoomOut } from './mapHelpers';
import { Timeline } from './Timeline';
import { useCycloneStore } from '../../store/useCycloneStore';
import { CYCLONES } from '../../data/cyclones';
import type { LayerVisibility } from './LeafletMap';

// ── Layer definitions ────────────────────────────────────────────────────────
const LAYER_DEFS: {
  key: keyof LayerVisibility;
  label: string;
  icon: React.ReactNode;
  alwaysAvailable: boolean;
}[] = [
  { key: 'satellite',     label: 'Satellite / Base',   icon: <Map size={13} />,       alwaysAvailable: true  },
  { key: 'trajectory',    label: 'Cyclone Trajectory', icon: <GitBranch size={13} />, alwaysAvailable: false },
  { key: 'structure',     label: 'Cyclone Structure',  icon: <Wind size={13} />,      alwaysAvailable: false },
  { key: 'centre',        label: 'Cyclone Centre',     icon: <Eye size={13} />,       alwaysAvailable: false },
  { key: 'forecastTrack', label: 'Forecast Track',     icon: <Navigation size={13} />,alwaysAvailable: false },
  { key: 'forecastCone',  label: 'Forecast Cone',      icon: <Triangle size={13} />,  alwaysAvailable: false },
  { key: 'wind',          label: 'Wind Field',         icon: <Wind size={13} />,      alwaysAvailable: false },
  { key: 'ocean',         label: 'Ocean Currents',     icon: <Waves size={13} />,     alwaysAvailable: false },
];

// Quick-preset modes
type Preset = 'CYCLONE_VIEW' | 'TRAJECTORY_ONLY' | 'CLEAN_MAP';

const PRESETS: Record<Preset, LayerVisibility> = {
  CYCLONE_VIEW: {
    satellite: true, trajectory: true, structure: true,
    centre: true, forecastTrack: true, forecastCone: true, wind: true, ocean: true,
  },
  TRAJECTORY_ONLY: {
    satellite: false, trajectory: true, structure: false,
    centre: true, forecastTrack: true, forecastCone: false, wind: false, ocean: false,
  },
  CLEAN_MAP: {
    satellite: true, trajectory: false, structure: false,
    centre: false, forecastTrack: false, forecastCone: false, wind: false, ocean: false,
  },
};

export function SatellitePanel({ onCentreClick }: { onCentreClick?: () => void }) {
  const { mode, getCurrentObservation, liveData, activeEventId, apiClassificationsData, timelineIndex } = useCycloneStore();
  const activeCycloneMeta = CYCLONES.find(c => c.id === activeEventId) || CYCLONES[0];
  const obs = getCurrentObservation();
  const isLive = mode === 'LIVE';

  // Layer state
  const [layers, setLayers] = useState<LayerVisibility>({
    satellite: true, trajectory: true, structure: true,
    centre: true, forecastTrack: true, forecastCone: true,
    wind: false, ocean: false,
  });

  // Popover states
  const [layersOpen, setLayersOpen] = useState(false);
  const [dotMenuOpen, setDotMenuOpen] = useState(false);
  const layerRef  = useRef<HTMLDivElement>(null);
  const dotRef    = useRef<HTMLDivElement>(null);

  // Close popovers on outside click
  useEffect(() => {
    function handle(e: MouseEvent) {
      if (layerRef.current && !layerRef.current.contains(e.target as Node)) setLayersOpen(false);
      if (dotRef.current  && !dotRef.current.contains(e.target as Node))  setDotMenuOpen(false);
    }
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, []);

  const toggleLayer = (key: keyof LayerVisibility) =>
    setLayers(prev => ({ ...prev, [key]: !prev[key] }));

  const applyPreset = (p: Preset) => {
    setLayers(PRESETS[p]);
    setLayersOpen(false);
  };

  const displayTime = isLive
    ? (liveData.lastUpdated
        ? new Date(liveData.lastUpdated).toUTCString().replace(' GMT', ' UTC')
        : 'FETCHING...')
    : (obs ? obs.timestamp.replace('T', ' ').replace('Z', ' UTC') : '...');

  // Track coords for fit-track action
  const trackCoords: [number, number][] = [];
  if (mode === 'HISTORICAL' && apiClassificationsData?.classifications) {
    for (let i = 0; i <= timelineIndex; i++) {
      const c = apiClassificationsData.classifications[i];
      if (c && c.center) trackCoords.push([c.center.lat, c.center.lon]);
    }
  }

  return (
    <div className="relative w-full h-full bg-ocean-950">

      {/* ── Map ── */}
      <LeafletMap layers={layers} onCentreClick={onCentreClick} />

      {/* ── Vignette depth ── */}
      <div className="absolute inset-0 z-[11] pointer-events-none"
        style={{ background: 'radial-gradient(circle at 50% 50%, transparent 65%, rgba(8,14,24,0.55) 100%)' }} />

      {/* ══════════════════ MAP CONTROLS ══════════════════ */}

      {/* Zoom controls — top-left */}
      <div className="absolute top-4 left-4 z-20 flex flex-col gap-1">
        <div className="glass-chrome rounded-lg overflow-hidden flex flex-col">
          <button
            onClick={mapZoomIn}
            className="w-8 h-8 flex items-center justify-center text-text-muted hover:text-text-primary transition-colors"
            title="Zoom in"
          >
            <Plus size={14} />
          </button>
          <div className="w-5 h-px bg-ocean-800 mx-auto" />
          <button
            onClick={mapZoomOut}
            className="w-8 h-8 flex items-center justify-center text-text-muted hover:text-text-primary transition-colors"
            title="Zoom out"
          >
            <Minus size={14} />
          </button>
        </div>
      </div>

      {/* ── Layer toggle — top-right ── */}
      <div className="absolute top-4 right-4 z-20 flex flex-col gap-2" ref={layerRef}>
        <button
          onClick={() => { setLayersOpen(v => !v); setDotMenuOpen(false); }}
          className={`w-8 h-8 glass-chrome rounded-lg flex items-center justify-center transition-colors ${
            layersOpen ? 'text-wv' : 'text-text-muted hover:text-text-primary'
          }`}
          title="Layer controls"
        >
          <Layers size={14} />
        </button>

        <AnimatePresence>
          {layersOpen && (
            <motion.div
              initial={{ opacity: 0, x: 8, scale: 0.96 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 8, scale: 0.96 }}
              transition={{ duration: 0.15 }}
              className="absolute top-0 right-10 w-56 glass-chrome rounded-xl p-3 shadow-glass"
            >
              {/* Header */}
              <div className="metric-label text-text-primary mb-3 pb-2 border-b border-ocean-800">
                MAP LAYERS
              </div>

              {/* Quick presets */}
              <div className="grid grid-cols-3 gap-1 mb-3">
                {(['CYCLONE_VIEW', 'TRAJECTORY_ONLY', 'CLEAN_MAP'] as Preset[]).map(p => (
                  <button
                    key={p}
                    onClick={() => applyPreset(p)}
                    className="text-[9px] font-semibold tracking-wide py-1.5 px-1 rounded-md
                      bg-ocean-850 text-text-primary hover:bg-ocean-800
                      transition-colors leading-tight text-center"
                  >
                    {p === 'CYCLONE_VIEW' ? 'CYCLONE' : p === 'TRAJECTORY_ONLY' ? 'TRACK' : 'CLEAN'}
                  </button>
                ))}
              </div>

              <div className="h-px bg-ocean-800 mb-2" />

              {/* Individual toggles */}
              <div className="flex flex-col gap-0.5">
                {LAYER_DEFS.map((def) => {
                  let available = def.alwaysAvailable || mode === 'HISTORICAL';
                  // Wind and Ocean raster datasets are not available for historical dossiers
                  if (mode === 'HISTORICAL' && (def.key === 'wind' || def.key === 'ocean')) {
                    available = false;
                  }
                  return (
                    <button
                      key={def.key}
                      onClick={() => available && toggleLayer(def.key)}
                      disabled={!available}
                      className={`flex items-center justify-between px-2 py-1.5 rounded-md transition-colors
                        ${available ? 'hover:bg-ocean-850 cursor-pointer' : 'opacity-35 cursor-not-allowed'}
                      `}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-text-secondary">{def.icon}</span>
                        <span className="text-[11px] text-text-primary font-medium">{def.label}</span>
                      </div>
                      <div className={`w-7 h-4 rounded-full relative transition-colors ${
                        layers[def.key] && available ? 'bg-wv' : 'bg-ocean-800'
                      }`}>
                        <div className={`absolute top-0.5 w-3 h-3 rounded-full bg-white transition-all ${
                          layers[def.key] && available ? 'left-[14px]' : 'left-0.5'
                        }`} />
                      </div>
                    </button>
                  );
                })}
              </div>

              {!isLive && mode === 'HISTORICAL' ? null : (
                <p className="text-[9px] text-text-faint mt-2 pt-2 border-t border-ocean-800">
                  Cyclone layers available in Historical mode
                </p>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Three-dot menu — bottom-right ── */}
      <div className="absolute bottom-28 right-4 z-20" ref={dotRef}>
        <button
          onClick={() => { setDotMenuOpen(v => !v); setLayersOpen(false); }}
          className={`w-8 h-8 glass-chrome rounded-lg flex items-center justify-center transition-colors ${
            dotMenuOpen ? 'text-confidence' : 'text-text-muted hover:text-text-primary'
          }`}
          title="Map actions"
        >
          <MoreHorizontal size={14} />
        </button>

        <AnimatePresence>
          {dotMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: 6, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 6, scale: 0.96 }}
              transition={{ duration: 0.15 }}
              className="absolute bottom-10 right-0 w-48 glass-chrome rounded-xl p-1.5 shadow-glass"
            >
              {[
                { icon: <Navigation size={13} />, label: 'Reset View',       action: mapResetView },
                { icon: <Maximize2   size={13} />, label: 'Fit Monitoring Region', action: mapFitBounds },
                ...(mode === 'HISTORICAL' ? [{
                  icon: <GitBranch size={13} />,
                  label: 'Fit Cyclone Track',
                  action: () => mapFitTrack(trackCoords),
                }] : []),
                { icon: <Database size={13} />, label: 'Data Source: NASA GIBS', action: () => {} },
                { icon: <Clock size={13} />,    label: displayTime.slice(0, 20) + '…', action: () => {} },
              ].map((item, i) => (
                <button
                  key={i}
                  onClick={() => { item.action(); setDotMenuOpen(false); }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg
                    text-text-muted hover:text-text-primary hover:bg-ocean-850
                    transition-colors text-left"
                >
                  <span className="flex-shrink-0">{item.icon}</span>
                  <span className="text-[11px]">{item.label}</span>
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Status badges — top-centre ── */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex gap-2 pointer-events-none">
        {isLive ? (
          <div className={`glass-pill flex items-center gap-2 px-3 py-1.5 rounded-full ${
            liveData.status === 'LIVE'
              ? 'border-ir/40 text-ir'
              : 'border-amber-500/40 text-amber-400'
          }`}>
            <Radio size={11} className={liveData.status === 'LIVE' ? 'animate-blink' : ''} />
            <span className="metric-label text-current">
              {liveData.status === 'LIVE' ? 'LIVE SATELLITE FEED'
                : liveData.status === 'UPDATING' ? 'FETCHING SATELLITE...'
                : 'STALE SATELLITE DATA'}
            </span>
          </div>
        ) : (
          <div className="glass-pill flex items-center gap-2 px-3 py-1.5 rounded-full text-text-primary">
            <span className="metric-label">HISTORICAL ARCHIVE · {activeCycloneMeta.name} {activeCycloneMeta.year}</span>
          </div>
        )}

        <div className="glass-pill px-3 py-1.5 rounded-full pointer-events-auto">
          <span className="font-mono text-[10px] text-text-primary tracking-widest">
            {isLive
              ? (liveData.lastUpdated
                  ? new Date(liveData.lastUpdated).toISOString().slice(0, 19).replace('T', ' ') + ' UTC'
                  : 'UPDATING...')
              : (obs ? obs.timestamp.replace('T', ' ').replace('Z', ' UTC') : '...')}
          </span>
        </div>

        <div className="glass-pill px-3 py-1.5 rounded-full">
          <span className="metric-label text-text-secondary">SRC: NASA GIBS</span>
        </div>
      </div>

      {/* ── Timeline ── */}
      <div className={isLive ? 'pointer-events-none opacity-25' : ''}>
        <Timeline />
      </div>
    </div>
  );
}

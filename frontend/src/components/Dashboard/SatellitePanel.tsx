import { useState, useRef, useEffect } from 'react';
import {
  Plus, Minus, Radio, MoreHorizontal,
  Navigation, Maximize2, Database, Clock,
  Eye, Wind, Waves, Map, GitBranch, Triangle, Layers
} from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import { LeafletMap } from './LeafletMap';
import { mapResetView, mapFitBounds, mapFitTrack, mapZoomIn, mapZoomOut } from './mapHelpers';
import { Timeline } from './Timeline';
import { useCycloneStore } from '../../store/useCycloneStore';
import { CYCLONES } from '../../data/cyclones';
import { formatIST, addHoursToISO } from '../../lib/formatting';
import { IconButton } from '../ui';
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
  const [dotMenuOpen, setDotMenuOpen] = useState(false);
  const [layersPanelOpen, setLayersPanelOpen] = useState(false);
  const dotRef = useRef<HTMLDivElement>(null);
  const layersRef = useRef<HTMLDivElement>(null);

  // Close popovers on outside click
  useEffect(() => {
    function handle(e: MouseEvent) {
      if (dotRef.current && !dotRef.current.contains(e.target as Node)) setDotMenuOpen(false);
      if (layersRef.current && !layersRef.current.contains(e.target as Node)) setLayersPanelOpen(false);
    }
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, []);

  const toggleLayer = (key: keyof LayerVisibility) =>
    setLayers(prev => ({ ...prev, [key]: !prev[key] }));

  const displayTime = isLive
    ? (liveData.lastUpdated ? formatIST(liveData.lastUpdated) : 'FETCHING...')
    : (obs ? formatIST(obs.timestamp) : '...');

  // Track coords for fit-track action
  const trackCoords: [number, number][] = [];
  if (mode === 'HISTORICAL' && apiClassificationsData?.classifications) {
    for (let i = 0; i <= timelineIndex; i++) {
      const c = apiClassificationsData.classifications[i];
      if (c?.center) trackCoords.push([c.center.lat, c.center.lon]);
    }
  }

  return (
    <div className="relative w-full h-full bg-ocean-950" role="region" aria-label="Satellite map view">

      {/* Map */}
      <LeafletMap layers={layers} onCentreClick={onCentreClick} />

      {/* Vignette depth */}
      <div className="absolute inset-0 z-[11] pointer-events-none"
        style={{ background: 'radial-gradient(circle at 50% 50%, transparent 65%, rgba(8,14,24,0.55) 100%)' }}
        aria-hidden="true"
      />

      {/* Zoom controls */}
      <div className="absolute top-4 left-4 z-20 flex flex-col gap-1">
        <div className="glass-chrome rounded-lg overflow-hidden flex flex-col">
          <IconButton onClick={mapZoomIn} label="Zoom in" className="glass-chrome">
            <Plus size={14} />
          </IconButton>
          <div className="w-5 h-px bg-ocean-800 mx-auto" aria-hidden="true" />
          <IconButton onClick={mapZoomOut} label="Zoom out" className="glass-chrome">
            <Minus size={14} />
          </IconButton>
        </div>
      </div>

      {/* Map Layers Toggle Button & Panel */}
      <div className="absolute top-[88px] left-4 z-20" ref={layersRef}>
        <IconButton
          onClick={() => setLayersPanelOpen(!layersPanelOpen)}
          label="Map Layers"
          active={layersPanelOpen}
          className="glass-chrome shadow-glass"
        >
          <Layers size={14} />
        </IconButton>

        <AnimatePresence>
          {layersPanelOpen && (
            <motion.div
              initial={{ opacity: 0, x: -6, scale: 0.96 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: -6, scale: 0.96 }}
              transition={{ duration: 0.15 }}
              className="absolute top-0 left-10 w-52 glass-chrome rounded-xl p-3 shadow-glass border border-white/10 bg-ocean-950/40 backdrop-blur-md"
              role="group"
              aria-label="Map layer controls"
            >
              <div className="metric-label text-text-primary mb-3 pb-2 border-b border-ocean-800">
                MAP LAYERS
              </div>

              <div className="flex flex-col gap-1">
                {LAYER_DEFS.map((def) => {
                  let available = def.alwaysAvailable || mode === 'HISTORICAL';
                  if (mode === 'HISTORICAL' && (def.key === 'wind' || def.key === 'ocean')) {
                    available = false;
                  }
                  return (
                    <button
                      key={def.key}
                      onClick={() => available && toggleLayer(def.key)}
                      disabled={!available}
                      aria-pressed={layers[def.key] && available}
                      className={`flex items-center justify-between px-2 py-1.5 rounded-lg transition-colors
                        ${available ? 'hover:bg-ocean-800/80 cursor-pointer' : 'opacity-35 cursor-not-allowed'}
                      `}
                    >
                      <div className="flex items-center gap-2">
                        <span className={`transition-colors ${layers[def.key] && available ? 'text-blue-400' : 'text-text-secondary'}`}>{def.icon}</span>
                        <span className={`text-xs font-medium ${layers[def.key] && available ? 'text-white' : 'text-text-primary'}`}>{def.label}</span>
                      </div>
                      <div className={`w-7 h-4 rounded-full relative transition-colors border ${
                        layers[def.key] && available ? 'bg-blue-500/20 border-blue-500/50' : 'bg-ocean-800 border-ocean-700'
                      }`} aria-hidden="true">
                        <div className={`absolute top-0.5 w-2.5 h-2.5 rounded-full bg-white transition-all ${
                          layers[def.key] && available ? 'left-[15px] shadow-[0_0_5px_rgba(255,255,255,0.8)]' : 'left-1 opacity-50'
                        }`} />
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Quick presets */}
              <div className="grid grid-cols-3 gap-1 mt-3 pt-3 border-t border-ocean-800">
                {(['CYCLONE_VIEW', 'TRAJECTORY_ONLY', 'CLEAN_MAP'] as Preset[]).map(p => (
                  <button
                    key={p}
                    onClick={() => setLayers(PRESETS[p])}
                    className="text-xs font-bold tracking-wide py-1.5 px-1 rounded-md
                      bg-ocean-900 text-text-primary hover:bg-ocean-800 border border-white/5
                      transition-colors leading-tight text-center"
                  >
                    {p === 'CYCLONE_VIEW' ? 'ALL' : p === 'TRAJECTORY_ONLY' ? 'TRACK' : 'NONE'}
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Three-dot menu */}
      <div className="absolute bottom-28 right-4 z-20" ref={dotRef}>
        <IconButton
          onClick={() => setDotMenuOpen(v => !v)}
          label="Map actions"
          active={dotMenuOpen}
          className="glass-chrome"
        >
          <MoreHorizontal size={14} />
        </IconButton>

        <AnimatePresence>
          {dotMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: 6, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 6, scale: 0.96 }}
              transition={{ duration: 0.15 }}
              className="absolute bottom-10 right-0 w-48 glass-chrome rounded-xl p-1.5 shadow-glass"
              role="menu"
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
                { icon: <Clock size={13} />,    label: displayTime.slice(0, 24), action: () => {} },
              ].map((item, i) => (
                <button
                  key={i}
                  role="menuitem"
                  onClick={() => { item.action(); setDotMenuOpen(false); }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg
                    text-text-muted hover:text-text-primary hover:bg-ocean-850
                    transition-colors text-left"
                >
                  <span className="flex-shrink-0" aria-hidden="true">{item.icon}</span>
                  <span className="text-xs">{item.label}</span>
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Status badges — top-centre */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 flex gap-2 pointer-events-none">
        {isLive ? (
          <div className={`glass-pill flex items-center gap-2 px-3 py-1.5 rounded-full pointer-events-auto ${
            liveData.status === 'LIVE'
              ? 'border-green-500/40 text-green-400'
              : 'border-amber-500/40 text-amber-400'
          }`} role="status">
            {liveData.status === 'LIVE' && (
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" aria-hidden="true" />
            )}
            <Radio size={11} className={liveData.status === 'LIVE' ? 'animate-blink' : ''} aria-hidden="true" />
            <span className="metric-label text-current">
              {liveData.status === 'LIVE' ? 'LIVE SATELLITE FEED'
                : liveData.status === 'UPDATING' ? 'FETCHING SATELLITE...'
                : 'STALE SATELLITE DATA'}
            </span>
          </div>
        ) : (
          <div className="glass-pill flex items-center gap-2 px-3 py-1.5 rounded-full text-text-primary pointer-events-auto">
            <span className="metric-label">HISTORICAL ARCHIVE · {activeCycloneMeta.name} {activeCycloneMeta.year}</span>
          </div>
        )}

        <div className="glass-pill px-3 py-1.5 rounded-full pointer-events-auto flex flex-col items-center">
          <span className="font-mono text-xs text-text-primary tracking-widest">
            {isLive
              ? (liveData.lastUpdated
                  ? `FRAME CAPTURED: ${formatIST(liveData.lastUpdated)}`
                  : 'FETCHING FRAME...')
              : (obs ? formatIST(obs.timestamp) : '...')}
          </span>
          {isLive && liveData.lastUpdated && (
             <span className="font-mono text-xs text-text-muted tracking-widest mt-0.5">
               NEXT UPCOMING: {formatIST(addHoursToISO(liveData.lastUpdated, 1))}
             </span>
          )}
        </div>

        <div className="glass-pill px-3 py-1.5 rounded-full pointer-events-auto">
          <span className="metric-label text-text-secondary">SRC: NASA GIBS</span>
        </div>
      </div>

      {/* Timeline */}
      <div className={isLive ? 'pointer-events-none opacity-25' : ''} aria-hidden={isLive}>
        <Timeline />
      </div>
    </div>
  );
}

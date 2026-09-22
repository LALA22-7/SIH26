import { useState, useRef, useEffect } from 'react';
import {
  Plus, Minus, Radio, MoreHorizontal,
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
  const [dotMenuOpen, setDotMenuOpen] = useState(false);
  const dotRef    = useRef<HTMLDivElement>(null);

  // Close popovers on outside click
  useEffect(() => {
    function handle(e: MouseEvent) {
      if (dotRef.current  && !dotRef.current.contains(e.target as Node))  setDotMenuOpen(false);
    }
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, []);

  const toggleLayer = (key: keyof LayerVisibility) =>
    setLayers(prev => ({ ...prev, [key]: !prev[key] }));

  const applyPreset = (p: Preset) => {
    setLayers(PRESETS[p]);
  };

  const formatIST = (isoString: string) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) + ' IST';
  };

  const displayTime = isLive
    ? (liveData.lastUpdated
        ? formatIST(liveData.lastUpdated)
        : 'FETCHING...')
    : (obs ? formatIST(obs.timestamp) : '...');

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

      {/* ── Layer panel (Permanent floating widget) ── */}
      <div className="absolute top-[88px] left-4 z-20 w-52">
        <div className="glass-chrome rounded-xl p-3 shadow-glass border border-white/10 bg-ocean-950/40 backdrop-blur-md">
          {/* Header */}
          <div className="metric-label text-text-primary mb-3 pb-2 border-b border-ocean-800">
            MAP LAYERS
          </div>

          {/* Individual toggles */}
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
                  className={`flex items-center justify-between px-2 py-1.5 rounded-lg transition-colors
                    ${available ? 'hover:bg-ocean-800/80 cursor-pointer' : 'opacity-35 cursor-not-allowed'}
                  `}
                >
                  <div className="flex items-center gap-2">
                    <span className={`transition-colors ${layers[def.key] && available ? 'text-blue-400' : 'text-text-secondary'}`}>{def.icon}</span>
                    <span className={`text-[11px] font-medium ${layers[def.key] && available ? 'text-white' : 'text-text-primary'}`}>{def.label}</span>
                  </div>
                  <div className={`w-7 h-4 rounded-full relative transition-colors border ${
                    layers[def.key] && available ? 'bg-blue-500/20 border-blue-500/50' : 'bg-ocean-800 border-ocean-700'
                  }`}>
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
                onClick={() => applyPreset(p)}
                className="text-[8px] font-bold tracking-wide py-1.5 px-1 rounded-md
                  bg-ocean-900 text-text-primary hover:bg-ocean-800 border border-white/5
                  transition-colors leading-tight text-center"
              >
                {p === 'CYCLONE_VIEW' ? 'ALL' : p === 'TRAJECTORY_ONLY' ? 'TRACK' : 'NONE'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Three-dot menu — bottom-right ── */}
      <div className="absolute bottom-28 right-4 z-20" ref={dotRef}>
        <button
          onClick={() => { setDotMenuOpen(v => !v); }}
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
              ? 'border-green-500/40 text-green-400'
              : 'border-amber-500/40 text-amber-400'
          }`}> 
            {liveData.status === 'LIVE' && (
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            )}
            <Radio size={11} className={liveData.status === 'LIVE' ? 'animate-blink' : ''} />
            <span className="metric-label text-current">
              {liveData.status === 'LIVE' ? 'LIVE SATELLITE FEED'
                : liveData.status === 'UPDATING' ? 'FETCHING SATELLITE...'
                : 'STALE SATELLITE DATA'}
            </span>
          </div>
        ) : (
          <div className="glass-pill flex items-center gap-2 px-3 py-1.5 rounded-full text-text-primary group relative cursor-pointer hover:bg-white/5 transition-colors">
            <span className="metric-label">HISTORICAL ARCHIVE · {activeCycloneMeta.name} {activeCycloneMeta.year}</span>
            {/* Dropdown for historical cyclone selection */}
            <div className="hidden group-hover:block absolute top-full mt-2 left-1/2 -translate-x-1/2 w-56 glass-chrome rounded-xl p-1.5 shadow-glass z-50">
               {CYCLONES.map(c => (
                  <div 
                    key={c.id} 
                    onClick={() => useCycloneStore.getState().setActiveCyclone(c.id)} 
                    className={`px-3 py-2 text-xs hover:bg-white/10 cursor-pointer rounded-lg flex justify-between ${c.id === activeEventId ? 'text-blue-400 bg-white/5' : ''}`}
                  >
                     <span>{c.name} {c.year}</span>
                  </div>
               ))}
            </div>
          </div>
        )}

        <div className="glass-pill px-3 py-1.5 rounded-full pointer-events-auto flex flex-col items-center">
          <span className="font-mono text-[10px] text-text-primary tracking-widest">
            {isLive
              ? (liveData.lastUpdated
                  ? `FRAME FETCHED: ${formatIST(liveData.lastUpdated)}`
                  : 'FETCHING FRAME...')
              : (obs ? formatIST(obs.timestamp) : '...')}
          </span>
          {isLive && liveData.lastUpdated && (
             <span className="font-mono text-[9px] text-text-muted tracking-widest mt-0.5">
               NEXT UPCOMING: {formatIST(new Date(new Date(liveData.lastUpdated).getTime() + 3*60*60*1000).toISOString())}
             </span>
          )}
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

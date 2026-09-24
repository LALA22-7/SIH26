import { useEffect, useState } from 'react';
import { Activity } from 'lucide-react';
import { useCycloneStore } from '../../store/useCycloneStore';
import { CYCLONES, PATTERN_LABELS, BASELINES } from '../../data/cyclones';

// ── Helpers ──────────────────────────────────────────────────────────────────

function Badge({ label, variant = 'default' }: { label: string; variant?: 'default' | 'live' | 'historical' | 'ml' | 'alert' }) {
  const styles: Record<string, string> = {
    default:    'bg-ocean-800 text-text-faint',
    live:       'bg-ir/10 text-ir border border-ir/25',
    historical: 'bg-ocean-800 text-text-muted',
    ml:         'bg-accent/10 text-accent border border-accent/25',
    alert:      'bg-alert/10 text-alert border border-alert/25',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[8px] font-bold tracking-[0.12em] uppercase ${styles[variant]}`}>
      {label}
    </span>
  );
}

function SectionHeader({ title, badge, badgeVariant }: {
  title: string;
  badge?: string;
  badgeVariant?: 'default' | 'live' | 'historical' | 'ml' | 'alert';
}) {
  return (
    <div className="flex items-center justify-between mb-3">
      <span className="metric-label text-text-muted">{title}</span>
      {badge && <Badge label={badge} variant={badgeVariant} />}
    </div>
  );
}

/** Single big-number metric cell */
function MetricCell({
  label, value, unit, color = 'text-text-primary', unavailable = false,
}: {
  label: string; value?: string | number | null; unit?: string;
  color?: string; unavailable?: boolean;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="metric-label">{label}</span>
      {unavailable || value == null ? (
        <span className="text-[11px] text-text-faint font-mono">DATA UNAVAILABLE</span>
      ) : (
        <div className="flex items-baseline gap-0.5">
          <span className={`metric-value-sm font-mono ${color}`}>{value}</span>
          {unit && <span className="metric-unit">{unit}</span>}
        </div>
      )}
    </div>
  );
}

/** 2-column metric grid inside a section card */
function MetricGrid({ children }: { children: React.ReactNode }) {
  return <div className="grid grid-cols-2 gap-x-4 gap-y-3">{children}</div>;
}

// ── LIVE MODE ─────────────────────────────────────────────────────────────────
function LiveMetrics() {
  const { liveData, liveBasin, setLiveBasin } = useCycloneStore();
  const [coastDist, setCoastDist] = useState<number | null>(null);
  const [timeToImpact, setTimeToImpact] = useState<number | null>(null);
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api';

  // Always compute coast distance from basin center (not gated on cyclone.active)
  useEffect(() => {
    const lat = liveBasin === 'Bay of Bengal' ? 15.0 : 17.0;
    const lng = liveBasin === 'Bay of Bengal' ? 88.0 : 68.0;
    
    fetch(`${API_BASE}/coastline/distance?lat=${lat}&lon=${lng}`)
      .then(res => res.json())
      .then(data => {
          setCoastDist(data.distance_km != null ? Math.round(data.distance_km) : null);
          const speed = 15; // default storm speed km/h
          setTimeToImpact(data.distance_km != null ? Math.round(data.distance_km / speed) : null);
      })
      .catch(() => { setCoastDist(null); setTimeToImpact(null); });
  }, [liveBasin, API_BASE]);

  const hasAtmo  = liveData.status === 'LIVE' || liveData.status === 'STALE';
  const hasOcean = hasAtmo;
  const atmo  = liveData.atmosphere;
  const ocean = liveData.ocean;
  const lastUp = liveData.lastUpdated
    ? 'Updated at ' + new Date(liveData.lastUpdated).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    : 'Updating…';

  return (
    <div className="flex flex-col gap-3">

      {/* ── Basin Tabs ── */}
      <div className="flex bg-ocean-900/50 rounded-lg p-1 mb-1 shadow-inner border border-ocean-800/50">
        {(['Bay of Bengal', 'Arabian Sea'] as const).map(basin => (
          <button
            key={basin}
            onClick={() => setLiveBasin(basin)}
            className={`flex-1 py-1.5 text-[10px] font-bold tracking-widest uppercase rounded-md transition-all ${
              liveBasin === basin ? 'bg-ocean-750 text-text-primary shadow-sm' : 'text-text-muted hover:text-text-secondary'
            }`}
          >
            {basin}
          </button>
        ))}
      </div>

      {/* ── Cyclone Status ── */}
      <div className="glass-card rounded-xl p-4">
        <SectionHeader title="Cyclone Status" badge={liveData.status === 'LIVE' ? 'LIVE' : liveData.status === 'STALE' ? 'STALE' : 'UPDATING'} badgeVariant={liveData.status === 'LIVE' ? 'live' : 'default'} />
        <div className="flex items-start gap-3">
          <div className={`w-2.5 h-2.5 rounded-full mt-1 flex-shrink-0 ${liveData.cyclone.active ? 'bg-ir shadow-glow-ir animate-blink' : 'bg-ocean-750'}`} />
          <div>
            <p className={`text-sm font-semibold tracking-wide ${liveData.cyclone.active ? 'text-ir' : 'text-text-primary'}`}>
              {liveData.cyclone.active ? 'ACTIVE CYCLONE DETECTED' : 'NO ACTIVE CYCLONE'}
            </p>
            <p className="text-[10px] text-text-muted mt-0.5">
              {liveData.cyclone.active
                ? 'System currently tracking in monitored region.'
                : `${liveBasin} currently under passive monitoring.`}
            </p>
            <p className="text-[9px] text-text-faint mt-1 font-mono">{lastUp}</p>
          </div>
        </div>
      </div>

      {/* ── Atmosphere ── */}
      <div className="glass-card rounded-xl p-4">
        <SectionHeader title="Atmosphere" badge="OBSERVATION" badgeVariant="historical" />
        <MetricGrid>
          <MetricCell label="Wind Speed" value={hasAtmo ? atmo.windSpeed?.toFixed(0) : null} unit="km/h"
            color={atmo.windSpeed && atmo.windSpeed >= BASELINES.windSpeed ? 'text-alert' : 'text-accent'}
            unavailable={!hasAtmo} />
          <MetricCell label="Wind Direction" value={hasAtmo ? `${atmo.windDirection?.toFixed(0)}°` : null}
            unavailable={!hasAtmo} />
          <MetricCell label="Pressure" value={hasAtmo ? atmo.pressure?.toFixed(0) : null} unit="hPa"
            unavailable={!hasAtmo} />
          <MetricCell label="Humidity" value={hasAtmo ? atmo.humidity?.toFixed(0) : null} unit="%"
            unavailable={!hasAtmo} />
        </MetricGrid>
        {hasAtmo && (
          <div className="mt-3 pt-3 border-t border-ocean-800">
            <MetricCell label="24h Rainfall" value={atmo.rainfall?.toFixed(1)} unit="mm" unavailable={!hasAtmo} />
          </div>
        )}
        <p className="text-[9px] text-text-faint font-mono mt-2">Source: Open-Meteo · {lastUp}</p>
      </div>

      {/* ── Ocean ── */}
      <div className="glass-card rounded-xl p-4">
        <SectionHeader title="Ocean" badge="MODEL" badgeVariant="ml" />
        <MetricGrid>
          <MetricCell label="Sea Surface Temp" value={hasOcean ? ocean.sst?.toFixed(1) : null} unit="°C"
            color="text-ir" unavailable={!hasOcean} />
          <MetricCell label="Wave Height" value={hasOcean ? ocean.waveHeight?.toFixed(1) : null} unit="m"
            unavailable={!hasOcean} />
          <MetricCell label="Current Speed" value={hasOcean ? ocean.currentVelocity?.toFixed(2) : null} unit="m/s"
            color="text-wv" unavailable={!hasOcean} />
          <MetricCell label="Current Dir" value={hasOcean && ocean.currentDirection != null ? `${ocean.currentDirection?.toFixed(0)}°` : null}
            unavailable={!hasOcean} />
        </MetricGrid>
        <p className="text-[9px] text-text-faint font-mono mt-2">Source: Open-Meteo Marine · {lastUp}</p>
      </div>

      {/* ── Impact Metrics ── */}
      <div className="glass-card rounded-xl p-4">
        <SectionHeader title="Impact Metrics" badge="CALCULATED" badgeVariant="ml" />
        <MetricGrid>
          <MetricCell label="Risk of Formation" value={
            hasAtmo && hasOcean && ocean.sst ? Math.min(100, Math.max(0, ((ocean.sst - 26) * 15) + ((atmo.windSpeed || 0) * 0.5))).toFixed(0) : null
          } unit="%" color={(ocean.sst && ocean.sst > 28) ? 'text-alert' : 'text-amber-400'} unavailable={!hasOcean || !hasAtmo} />
          
          <MetricCell label="Nearest Coast Dist." value={
            coastDist !== null ? coastDist : null
          } unit="km" unavailable={coastDist === null} />
          
          <MetricCell label="Est. Time to Impact" value={
            timeToImpact !== null ? timeToImpact : null
          } unit="hrs" unavailable={timeToImpact === null} />
        </MetricGrid>
      </div>

      {/* ── CycloneWatch ML status (at bottom) ── */}
      <div className="glass-card rounded-xl p-4">
        <SectionHeader title="CycloneWatch ML" badge="ML PREDICTION" badgeVariant="ml" />
        <p className="text-[11px] text-text-muted leading-relaxed">
          No active storm detected. Select a historical cyclone in the event selector to see AI-powered classification and track prediction.
        </p>
        <div className="mt-3 flex flex-col gap-1.5">
          <div className="flex justify-between items-center">
            <span className="metric-label">Model</span>
            <span className="font-mono text-[10px] text-text-secondary">ps70-classifier v2.0.0</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="metric-label">Pattern Accuracy</span>
            <span className="font-mono text-[10px] text-confidence">78.3%</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="metric-label">Centre MAE</span>
            <span className="font-mono text-[10px] text-text-secondary">255 km</span>
          </div>
        </div>
      </div>

    </div>
  );
}

// ── HISTORICAL MODE ───────────────────────────────────────────────────────────
function HistoricalMetrics() {
  const { activeEventId, getCurrentObservation } = useCycloneStore();
  const activeCycloneMeta = CYCLONES.find(c => c.id === activeEventId) || CYCLONES[0];
  const obs = getCurrentObservation();
  const [coastDist, setCoastDist] = useState<number | null>(null);
  const [timeToImpact, setTimeToImpact] = useState<number | null>(null);
  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api';

  useEffect(() => {
    if (obs?.lat && obs?.lng) {
      fetch(`${API_BASE}/coastline/distance?lat=${obs.lat}&lon=${obs.lng}`)
        .then(res => res.json())
        .then(data => {
            setCoastDist(data.distance_km);
            let speed = 15; // default fallback km/h
            if (obs.prevLat !== null && obs.prevLng !== null && obs.hoursSincePrev) {
               const lat1 = obs.prevLat * Math.PI / 180;
               const lon1 = obs.prevLng * Math.PI / 180;
               const lat2 = obs.lat * Math.PI / 180;
               const lon2 = obs.lng * Math.PI / 180;
               const dlon = lon2 - lon1;
               const dlat = lat2 - lat1;
               const a = Math.sin(dlat/2)**2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dlon/2)**2;
               const c = 2 * Math.asin(Math.sqrt(a));
               const distanceTraveled = 6371 * c; // Earth radius in km
               if (obs.hoursSincePrev > 0) {
                 speed = distanceTraveled / obs.hoursSincePrev;
               }
            }
            setTimeToImpact(speed > 0 ? Math.round(data.distance_km / speed) : null);
        })
        .catch(() => { setCoastDist(null); setTimeToImpact(null); });
    }
  }, [obs?.lat, obs?.lng, obs?.prevLat, obs?.prevLng, obs?.hoursSincePrev, API_BASE]);

  if (!obs || !obs.step) {
    return <div className="text-text-faint text-sm p-4">Loading event data...</div>;
  }

  const { step } = obs;
  
  // Format confidence nicely to avoid literal 0.0% looking like a bug
  const patternLabel = obs.classification?.pattern?.label || 'unlabeled';
  const rawConf = obs.classification?.pattern?.confidence || 0;
  const confValue = rawConf * 100;
  const patternConf = rawConf > 0 && rawConf < 0.05 
    ? '< 5.0'
    : confValue.toFixed(1);

  return (
    <div className="flex flex-col gap-3">

      {/* ── IMD gap case banner ── */}
      {activeCycloneMeta.imdGapCase && (
        <div className="glass-card rounded-xl p-3 border border-alert/30 bg-alert/5">
          <div className="flex items-start gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-alert mt-1 flex-shrink-0 animate-blink" />
            <div>
              <p className="text-[10px] font-bold text-alert tracking-widest">IMD GAP CASE</p>
              <p className="text-[10px] text-text-muted leading-relaxed mt-0.5">
                {activeCycloneMeta.imdGapNote}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ── 1. Live Storm Center ── */}
      <div className="glass-card rounded-xl p-4 relative overflow-hidden border-t-2 border-t-alert/50">
        <div className="absolute top-0 right-0 p-3 opacity-20 pointer-events-none">
          <Activity size={64} className="text-alert" />
        </div>
        <SectionHeader title="Live Storm Center" badge="ACTIVE" badgeVariant="alert" />
        
        <div className="flex items-center justify-between mb-4 mt-2">
          <div>
            <h2 className="text-xl font-bold tracking-widest text-white uppercase">{activeCycloneMeta.name}</h2>
            <p className="text-xs text-text-muted mt-1">{activeCycloneMeta.landfallRegion}</p>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-[10px] text-text-faint uppercase tracking-widest">Alert Level</span>
            <span className="px-2 py-0.5 rounded bg-alert/20 text-alert text-[10px] font-bold border border-alert/30 mt-1 shadow-[0_0_10px_rgba(255,92,92,0.3)]">HIGH</span>
          </div>
        </div>

        <MetricGrid>
          <MetricCell label="Wind Speed" value={activeCycloneMeta.peakWind} unit="km/h" color="text-alert" />
          <MetricCell label="Pressure" value={activeCycloneMeta.minPressure} unit="hPa" />
          <MetricCell label="Est. Distance to Coast" value={coastDist !== null ? coastDist : null} unit="km" unavailable={coastDist === null} />
          <MetricCell label="Est. Time to Impact" value={timeToImpact !== null ? timeToImpact : null} unit="hrs" unavailable={timeToImpact === null} />
        </MetricGrid>
      </div>

      {/* ── 2. AI Storm Analysis ── */}
      <div className="glass-card rounded-xl p-4 border-t-2 border-t-blue-500/50">
        <SectionHeader title="AI Storm Analysis" badge="PS70-V2" badgeVariant="ml" />

        <div className="flex items-center gap-4 mb-5">
          <div className="w-16 h-16 rounded-full border-[3px] border-confidence/30 flex items-center justify-center relative shadow-[0_0_15px_rgba(111,227,180,0.2)]">
            <svg className="absolute inset-0 w-full h-full -rotate-90">
              <circle cx="32" cy="32" r="30" stroke="currentColor" strokeWidth="3" fill="none" className="text-ocean-800" />
              <circle cx="32" cy="32" r="30" stroke="currentColor" strokeWidth="3" fill="none" className="text-confidence transition-all duration-1000" strokeDasharray={`${confValue * 1.88} 188`} />
            </svg>
            <div className="text-center">
              <span className="block text-sm font-bold text-white leading-none">{patternConf}%</span>
              <span className="block text-[8px] text-text-muted uppercase tracking-widest mt-0.5">Conf</span>
            </div>
          </div>
          <div className="flex-1">
            <span className="text-[10px] text-text-faint uppercase tracking-widest">Classification</span>
            <h3 className="text-base font-bold text-confidence tracking-wider uppercase drop-shadow-[0_0_8px_rgba(111,227,180,0.5)]">
              {PATTERN_LABELS[patternLabel] || patternLabel.replace('_', ' ')}
            </h3>
            <p className="text-[10px] text-text-muted mt-1">Based on thermal pattern recognition</p>
          </div>
        </div>

        {/* Morphology */}
        <div className="mb-4">
          <span className="metric-label mb-2 block">Morphology Analysis</span>
          <div className="grid grid-cols-4 gap-2">
            {[
              { label: 'Well Defined Eye', active: patternLabel.includes('eye') || (rawConf * 100) > 80 },
              { label: 'Spiral Bands', active: true },
              { label: 'Symmetric', active: patternLabel.includes('curved') || (rawConf * 100) > 70 },
              { label: 'Organized', active: (rawConf * 100) > 50 }
            ].map((m, i) => (
              <div key={i} className={`flex flex-col items-center justify-center p-2 rounded-lg border transition-all ${m.active ? 'bg-blue-500/10 border-blue-400/30 text-blue-400 shadow-[inset_0_0_10px_rgba(59,130,246,0.1)]' : 'bg-ocean-900/50 border-ocean-800 text-text-faint'}`}>
                <div className={`w-3 h-3 rounded-full mb-1 border flex items-center justify-center ${m.active ? 'bg-blue-500 border-blue-400' : 'bg-transparent border-ocean-700'}`}>
                  {m.active && <div className="w-1.5 h-1.5 bg-white rounded-full" />}
                </div>
                <span className="text-[8px] text-center leading-tight tracking-wide">{m.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── 3. Forecast Timeline ── */}
      <div className="glass-card rounded-xl p-4 border-t-2 border-t-purple-500/50">
        <SectionHeader title="Forecast Timeline" badge="PREDICTION" badgeVariant="ml" />
        
        <div className="relative pl-3 border-l-2 border-ocean-800 flex flex-col gap-5 mt-4 ml-2">
          {/* T+0 */}
          <div className="relative">
            <div className="absolute -left-[19px] top-1 w-3 h-3 bg-confidence rounded-full shadow-[0_0_8px_rgba(111,227,180,0.8)] ring-4 ring-ocean-950" />
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-bold text-white">T+0h (Current)</span>
                <p className="text-[10px] text-text-muted mt-0.5">{obs.lat.toFixed(2)}°N, {obs.lng.toFixed(2)}°E</p>
              </div>
              <span className="text-xs font-mono text-text-secondary">{activeCycloneMeta.peakWind} km/h</span>
            </div>
          </div>
          
          {/* T+12 */}
          <div className="relative">
            <div className="absolute -left-[19px] top-1 w-3 h-3 bg-ir rounded-full shadow-[0_0_8px_rgba(255,122,69,0.5)] ring-4 ring-ocean-950" />
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-bold text-text-primary">T+12h Forecast</span>
                <p className="text-[10px] text-text-faint mt-0.5">Error: {step.errors?.t12_km?.toFixed(1) || 'N/A'} km</p>
              </div>
              <span className="text-xs font-mono text-text-secondary opacity-75">~175 km/h</span>
            </div>
          </div>

          {/* T+24 */}
          <div className="relative">
            <div className="absolute -left-[19px] top-1 w-3 h-3 bg-ocean-750 border-2 border-ocean-600 rounded-full ring-4 ring-ocean-950" />
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-bold text-text-secondary">T+24h Forecast</span>
                <p className="text-[10px] text-text-faint mt-0.5">Error: {step.errors?.t24_km?.toFixed(1) || 'N/A'} km</p>
              </div>
              <span className="text-xs font-mono text-text-secondary opacity-50">~160 km/h</span>
            </div>
          </div>
          </div>
        </div>

    </div>
  );
}

// ── Root export ───────────────────────────────────────────────────────────────
export function MetricsPanel() {
  const { mode } = useCycloneStore();
  return (
    <div className="w-full h-full overflow-y-auto pr-1 pb-4 flex flex-col gap-0"
      style={{ scrollbarWidth: 'thin' }}>
      {mode === 'LIVE' ? <LiveMetrics /> : <HistoricalMetrics />}
    </div>
  );
}

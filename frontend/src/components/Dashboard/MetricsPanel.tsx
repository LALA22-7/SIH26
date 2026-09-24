// ─────────────────────────────────────────────────────────────────────────────
// CycloneWatch — MetricsPanel
//
// Refactored from 410 lines to ~300 by:
//  - Extracting Badge, SectionHeader, MetricCell, MetricGrid to ui/index.tsx
//  - Using centralized api.ts and geo.ts utilities
//  - Using shared formatIST from lib/formatting.ts
//  - Bumping all sub-11px font sizes for WCAG compliance
// ─────────────────────────────────────────────────────────────────────────────

import { useEffect, useState } from 'react';
import { Activity } from 'lucide-react';
import { useCycloneStore } from '../../store/useCycloneStore';
import { CYCLONES, PATTERN_LABELS, BASELINES } from '../../data/cyclones';
import { SectionHeader, MetricCell, MetricGrid, GlassCard, Badge } from '../ui';
import { formatTimeShort } from '../../lib/formatting';
import { estimateStormSpeed } from '../../lib/geo';
import { fetchCoastlineDistance } from '../../lib/api';

// ── LIVE MODE ─────────────────────────────────────────────────────────────────
function LiveMetrics() {
  const { liveData, liveBasin, setLiveBasin } = useCycloneStore();
  const [coastDist, setCoastDist] = useState<number | null>(null);
  const [timeToImpact, setTimeToImpact] = useState<number | null>(null);

  useEffect(() => {
    if (!liveData.cyclone.active || !liveData.cyclone.lat || !liveData.cyclone.lng) {
      setCoastDist(null);
      setTimeToImpact(null);
      return;
    }

    fetchCoastlineDistance(liveData.cyclone.lat, liveData.cyclone.lng)
      .then(data => {
        if (!data) { setCoastDist(null); setTimeToImpact(null); return; }
        setCoastDist(Math.round(data.distance_km));
        const speed = liveData.cyclone.speed || 15;
        setTimeToImpact(Math.round(data.distance_km / speed));
      });
  }, [liveData.cyclone]);

  const hasData = liveData.status === 'LIVE' || liveData.status === 'STALE';
  const atmo = liveData.atmosphere;
  const ocean = liveData.ocean;
  const lastUp = liveData.lastUpdated
    ? `Updated at ${formatTimeShort(liveData.lastUpdated)}`
    : 'Updating…';

  return (
    <div className="flex flex-col gap-3">

      {/* Basin Tabs */}
      <div className="flex bg-black/60 rounded-lg p-1 mb-1 shadow-inner border border-ocean-800/50" role="tablist" aria-label="Basin selection">
        {(['Bay of Bengal', 'Arabian Sea'] as const).map(basin => (
          <button
            key={basin}
            role="tab"
            aria-selected={liveBasin === basin}
            onClick={() => setLiveBasin(basin)}
            className={`flex-1 py-1.5 text-xs font-bold tracking-widest uppercase rounded-md transition-all ${
              liveBasin === basin ? 'bg-ocean-750 text-text-primary shadow-sm' : 'text-text-muted hover:text-text-secondary'
            }`}
          >
            {basin}
          </button>
        ))}
      </div>

      {/* Cyclone Status */}
      <GlassCard>
        <SectionHeader
          title="Cyclone Status"
          badge={liveData.status === 'LIVE' ? 'LIVE' : liveData.status === 'STALE' ? 'STALE' : 'UPDATING'}
          badgeVariant={liveData.status === 'LIVE' ? 'live' : 'default'}
        />
        <div className="flex items-start gap-3">
          <div
            className={`w-2.5 h-2.5 rounded-full mt-1 flex-shrink-0 ${liveData.cyclone.active ? 'bg-ir shadow-glow-ir animate-blink' : 'bg-ocean-750'}`}
            aria-hidden="true"
          />
          <div>
            <p className={`text-sm font-semibold tracking-wide ${liveData.cyclone.active ? 'text-ir' : 'text-text-primary'}`}>
              {liveData.cyclone.active ? 'ACTIVE CYCLONE DETECTED' : 'NO ACTIVE CYCLONE'}
            </p>
            <p className="text-xs text-text-muted mt-0.5">
              {liveData.cyclone.active
                ? 'System currently tracking in monitored region.'
                : `${liveBasin} currently under passive monitoring.`}
            </p>
            <p className="text-xs text-text-faint mt-1 font-mono">{lastUp}</p>
          </div>
        </div>
      </GlassCard>

      {/* Atmosphere */}
      <GlassCard>
        <SectionHeader title="Atmosphere" badge="OBSERVATION" badgeVariant="historical" />
        <MetricGrid>
          <MetricCell label="Wind Speed" value={hasData ? atmo.windSpeed?.toFixed(0) : null} unit="km/h"
            color={atmo.windSpeed && atmo.windSpeed >= BASELINES.windSpeed ? 'text-alert' : 'text-accent'}
            unavailable={!hasData} />
          <MetricCell label="Wind Direction" value={hasData ? `${atmo.windDirection?.toFixed(0)}°` : null}
            unavailable={!hasData} />
          <MetricCell label="Pressure" value={hasData ? atmo.pressure?.toFixed(0) : null} unit="hPa"
            unavailable={!hasData} />
          <MetricCell label="Humidity" value={hasData ? atmo.humidity?.toFixed(0) : null} unit="%"
            unavailable={!hasData} />
        </MetricGrid>
        {hasData && (
          <div className="mt-3 pt-3 border-t border-ocean-800">
            <MetricCell label="24h Rainfall" value={atmo.rainfall?.toFixed(1)} unit="mm" unavailable={!hasData} />
          </div>
        )}
        <p className="text-xs text-text-faint font-mono mt-2">Source: Open-Meteo · {lastUp}</p>
      </GlassCard>

      {/* Ocean */}
      <GlassCard>
        <SectionHeader title="Ocean" badge="MODEL" badgeVariant="ml" />
        <MetricGrid>
          <MetricCell label="Sea Surface Temp" value={hasData ? ocean.sst?.toFixed(1) : null} unit="°C"
            color="text-ir" unavailable={!hasData} />
          <MetricCell label="Wave Height" value={hasData ? ocean.waveHeight?.toFixed(1) : null} unit="m"
            unavailable={!hasData} />
          <MetricCell label="Current Speed" value={hasData ? ocean.currentVelocity?.toFixed(2) : null} unit="m/s"
            color="text-wv" unavailable={!hasData} />
          <MetricCell label="Current Dir" value={hasData && ocean.currentDirection != null ? `${ocean.currentDirection?.toFixed(0)}°` : null}
            unavailable={!hasData} />
        </MetricGrid>
        <p className="text-xs text-text-faint font-mono mt-2">Source: Open-Meteo Marine · {lastUp}</p>
      </GlassCard>

      {/* Impact Metrics */}
      <GlassCard>
        <SectionHeader title="Impact Metrics" badge="CALCULATED" badgeVariant="ml" />
        <MetricGrid>
          <MetricCell label="Risk of Formation" value={
            hasData && ocean.sst ? Math.min(100, Math.max(0, ((ocean.sst - 26) * 15) + ((atmo.windSpeed || 0) * 0.5))).toFixed(0) : null
          } unit="%" color={(ocean.sst && ocean.sst > 28) ? 'text-alert' : 'text-amber-400'} unavailable={!hasData} />
          <MetricCell label="Nearest Coast Dist." value={coastDist} unit="km" unavailable={coastDist === null} />
          <MetricCell label="Est. Time to Impact" value={timeToImpact} unit="hrs" unavailable={timeToImpact === null} />
        </MetricGrid>
      </GlassCard>

      {/* CycloneWatch ML status */}
      <GlassCard>
        <SectionHeader title="CycloneWatch ML" badge="ML PREDICTION" badgeVariant="ml" />
        <p className="text-xs text-text-muted leading-relaxed">
          No active storm detected. Select a historical cyclone in the event selector to see AI-powered classification and track prediction.
        </p>
        <div className="mt-3 flex flex-col gap-1.5">
          {[
            ['Model', 'ps70-classifier v2.0.0', 'text-text-secondary'],
            ['Pattern Accuracy', '78.3%', 'text-confidence'],
            ['Centre MAE', '255 km', 'text-text-secondary'],
          ].map(([label, value, color]) => (
            <div key={label} className="flex justify-between items-center">
              <span className="metric-label">{label}</span>
              <span className={`font-mono text-xs ${color}`}>{value}</span>
            </div>
          ))}
        </div>
      </GlassCard>
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

  useEffect(() => {
    if (!obs?.lat || !obs?.lng) return;

    fetchCoastlineDistance(obs.lat, obs.lng).then(data => {
      if (!data) { setCoastDist(null); setTimeToImpact(null); return; }
      setCoastDist(data.distance_km);
      const speed = estimateStormSpeed(obs.prevLat, obs.prevLng, obs.lat, obs.lng, obs.hoursSincePrev);
      setTimeToImpact(speed > 0 ? Math.round(data.distance_km / speed) : null);
    });
  }, [obs?.lat, obs?.lng, obs?.prevLat, obs?.prevLng, obs?.hoursSincePrev]);

  if (!obs || !obs.step) {
    return <div className="text-text-faint text-sm p-4">Loading event data...</div>;
  }

  const { step } = obs;
  const patternLabel = obs.classification?.pattern?.label || 'unlabeled';
  const rawConf = obs.classification?.pattern?.confidence || 0;
  const confValue = rawConf * 100;
  const patternConf = rawConf > 0 && rawConf < 0.05 ? '< 5.0' : confValue.toFixed(1);

  return (
    <div className="flex flex-col gap-3">

      {/* IMD gap case banner */}
      {activeCycloneMeta.imdGapCase && (
        <GlassCard className="border border-alert/30 bg-alert/5">
          <div className="flex items-start gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-alert mt-1 flex-shrink-0 animate-blink" aria-hidden="true" />
            <div>
              <p className="text-xs font-bold text-alert tracking-widest">IMD GAP CASE</p>
              <p className="text-xs text-text-muted leading-relaxed mt-0.5">
                {activeCycloneMeta.imdGapNote}
              </p>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Live Storm Center */}
      <GlassCard borderAccent="border-t-alert/50" className="relative overflow-hidden">
        <div className="absolute top-0 right-0 p-3 opacity-20 pointer-events-none" aria-hidden="true">
          <Activity size={64} className="text-alert" />
        </div>
        <SectionHeader title="Live Storm Center" badge="ACTIVE" badgeVariant="alert" />

        <div className="flex items-center justify-between mb-4 mt-2">
          <div>
            <h2 className="text-xl font-bold tracking-widest text-white uppercase">{activeCycloneMeta.name}</h2>
            <p className="text-xs text-text-muted mt-1">{activeCycloneMeta.landfallRegion}</p>
          </div>
          <div className="flex flex-col items-end">
            <span className="text-xs text-text-faint uppercase tracking-widest">Alert Level</span>
            <Badge label="HIGH" variant="alert" />
          </div>
        </div>

        <MetricGrid>
          <MetricCell label="Wind Speed" value={activeCycloneMeta.peakWind} unit="km/h" color="text-alert" />
          <MetricCell label="Pressure" value={activeCycloneMeta.minPressure} unit="hPa" />
          <MetricCell label="Est. Distance to Coast" value={coastDist !== null ? coastDist : null} unit="km" unavailable={coastDist === null} />
          <MetricCell label="Est. Time to Impact" value={timeToImpact !== null ? timeToImpact : null} unit="hrs" unavailable={timeToImpact === null} />
        </MetricGrid>
      </GlassCard>

      {/* AI Storm Analysis */}
      <GlassCard borderAccent="border-t-blue-500/50">
        <SectionHeader title="AI Storm Analysis" badge="PS70-V2" badgeVariant="ml" />

        <div className="flex items-center gap-4 mb-5">
          <div className="w-16 h-16 rounded-full border-[3px] border-confidence/30 flex items-center justify-center relative shadow-[0_0_15px_rgba(111,227,180,0.2)]" role="img" aria-label={`Pattern confidence: ${patternConf}%`}>
            <svg className="absolute inset-0 w-full h-full -rotate-90" aria-hidden="true">
              <circle cx="32" cy="32" r="30" stroke="currentColor" strokeWidth="3" fill="none" className="text-ocean-800" />
              <circle cx="32" cy="32" r="30" stroke="currentColor" strokeWidth="3" fill="none" className="text-confidence transition-all duration-1000" strokeDasharray={`${confValue * 1.88} 188`} />
            </svg>
            <div className="text-center">
              <span className="block text-sm font-bold text-white leading-none">{patternConf}%</span>
              <span className="block text-xs text-text-muted uppercase tracking-widest mt-0.5">Conf</span>
            </div>
          </div>
          <div className="flex-1">
            <span className="text-xs text-text-faint uppercase tracking-widest">Classification</span>
            <h3 className="text-base font-bold text-confidence tracking-wider uppercase drop-shadow-[0_0_8px_rgba(111,227,180,0.5)]">
              {PATTERN_LABELS[patternLabel] || patternLabel.replace('_', ' ')}
            </h3>
            <p className="text-xs text-text-muted mt-1">Based on thermal pattern recognition</p>
          </div>
        </div>

        {/* Morphology */}
        <div className="mb-4">
          <span className="metric-label mb-2 block">Morphology Analysis</span>
          <div className="grid grid-cols-4 gap-2">
            {[
              { label: 'Well Defined Eye', active: patternLabel.includes('eye') || confValue > 80 },
              { label: 'Spiral Bands', active: true },
              { label: 'Symmetric', active: patternLabel.includes('curved') || confValue > 70 },
              { label: 'Organized', active: confValue > 50 },
            ].map((m, i) => (
              <div key={i} className={`flex flex-col items-center justify-center p-2 rounded-lg border transition-all ${m.active ? 'bg-blue-500/10 border-blue-400/30 text-blue-400 shadow-[inset_0_0_10px_rgba(59,130,246,0.1)]' : 'bg-ocean-900/50 border-ocean-800 text-text-faint'}`}>
                <div className={`w-3 h-3 rounded-full mb-1 border flex items-center justify-center ${m.active ? 'bg-blue-500 border-blue-400' : 'bg-transparent border-ocean-700'}`} aria-hidden="true">
                  {m.active && <div className="w-1.5 h-1.5 bg-white rounded-full" />}
                </div>
                <span className="text-xs text-center leading-tight tracking-wide">{m.label}</span>
              </div>
            ))}
          </div>
        </div>
      </GlassCard>

      {/* Forecast Timeline */}
      <GlassCard borderAccent="border-t-purple-500/50">
        <SectionHeader title="Forecast Timeline" badge="PREDICTION" badgeVariant="ml" />

        <div className="relative pl-3 border-l-2 border-ocean-800 flex flex-col gap-5 mt-4 ml-2" role="list" aria-label="Forecast timeline">
          {/* T+0 */}
          <div className="relative" role="listitem">
            <div className="absolute -left-[19px] top-1 w-3 h-3 bg-confidence rounded-full shadow-[0_0_8px_rgba(111,227,180,0.8)] ring-4 ring-ocean-950" aria-hidden="true" />
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-bold text-white">T+0h (Current)</span>
                <p className="text-xs text-text-muted mt-0.5">{obs.lat.toFixed(2)}°N, {obs.lng.toFixed(2)}°E</p>
              </div>
              <span className="text-xs font-mono text-text-secondary">{activeCycloneMeta.peakWind} km/h</span>
            </div>
          </div>

          {/* T+12 */}
          <div className="relative" role="listitem">
            <div className="absolute -left-[19px] top-1 w-3 h-3 bg-ir rounded-full shadow-[0_0_8px_rgba(255,122,69,0.5)] ring-4 ring-ocean-950" aria-hidden="true" />
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-bold text-text-primary">T+12h Forecast</span>
                <p className="text-xs text-text-faint mt-0.5">Error: {step.errors?.t12_km?.toFixed(1) || 'N/A'} km</p>
              </div>
              <span className="text-xs font-mono text-text-secondary opacity-75">—</span>
            </div>
          </div>

          {/* T+24 */}
          <div className="relative" role="listitem">
            <div className="absolute -left-[19px] top-1 w-3 h-3 bg-ocean-750 border-2 border-ocean-700 rounded-full ring-4 ring-ocean-950" aria-hidden="true" />
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-bold text-text-secondary">T+24h Forecast</span>
                <p className="text-xs text-text-faint mt-0.5">Error: {step.errors?.t24_km?.toFixed(1) || 'N/A'} km</p>
              </div>
              <span className="text-xs font-mono text-text-secondary opacity-50">—</span>
            </div>
          </div>
        </div>
      </GlassCard>
    </div>
  );
}

// ── Root export ───────────────────────────────────────────────────────────────
export function MetricsPanel() {
  const { mode } = useCycloneStore();
  return (
    <div
      className="w-full h-full overflow-y-auto pr-1 pb-4 flex flex-col gap-0"
      style={{ scrollbarWidth: 'thin' }}
    >
      {mode === 'LIVE' ? <LiveMetrics /> : <HistoricalMetrics />}
    </div>
  );
}

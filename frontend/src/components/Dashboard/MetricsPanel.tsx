import { useEffect, useState } from 'react';
import { useCycloneStore } from '../../store/useCycloneStore';
import { CYCLONES, PATTERN_LABELS, PATTERN_COLORS, BASELINES } from '../../data/cyclones';

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
  const [now, setNow] = useState(() => Date.now());
  
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 60000);
    return () => clearInterval(id);
  }, []);

  const hasAtmo  = liveData.status === 'LIVE' || liveData.status === 'STALE';
  const hasOcean = hasAtmo;
  const atmo  = liveData.atmosphere;
  const ocean = liveData.ocean;
  const lastUp = liveData.lastUpdated
    ? 'Updated ' + Math.round((now - new Date(liveData.lastUpdated).getTime()) / 60000) + ' min ago'
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

      {/* ── CycloneWatch ML status ── */}
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
  const { activeEventId, getCurrentObservation, apiMetricsData } = useCycloneStore();
  const activeCycloneMeta = CYCLONES.find(c => c.id === activeEventId) || CYCLONES[0];
  const obs = getCurrentObservation();

  if (!obs || !obs.step) {
    return <div className="text-text-faint text-sm p-4">Loading event data...</div>;
  }

  const { classification, step } = obs;
  // Truncate frame_id for cleaner display
  const displayFrameId = obs.classification?.frame_id 
    ? obs.classification.frame_id.substring(0, 16) + '...'
    : 'N/A';

  // Format confidence nicely to avoid literal 0.0% looking like a bug
  const patternLabel = obs.classification?.pattern?.label || 'unlabeled';
  const rawConf = obs.classification?.pattern?.confidence || 0;
  const patternConf = rawConf > 0 && rawConf < 0.05 
    ? '< 5.0'
    : (rawConf * 100).toFixed(1);
    
  const confColor = rawConf > 0.8 ? 'text-ir' : 'text-confidence';

  const obsTimestamp = obs.timestamp.replace('T', ' ').replace('Z', ' UTC');

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

      {/* ── CycloneWatch classification ── */}
      <div className="glass-card rounded-xl p-4">
        <SectionHeader title="Classification Inference" badge="LIVE MODEL" badgeVariant="ml" />

        {/* Pattern display */}
        <div className="flex items-start gap-3 mb-4">
          <div className="w-2.5 h-2.5 rounded-full flex-shrink-0 mt-1.5"
            style={{ background: PATTERN_COLORS[patternLabel] ?? '#6495ED',
                     boxShadow: `0 0 8px ${PATTERN_COLORS[patternLabel] ?? '#6495ED'}` }} />
          <div className="flex-1">
            <div className="flex justify-between items-baseline mb-4">
              <div>
                <h3 className="text-sm font-bold text-text-primary tracking-widest uppercase">
                  {PATTERN_LABELS[patternLabel] || patternLabel.replace('_', ' ')}
                </h3>
                <p className="text-[10px] text-text-muted mt-1">Current structural pattern</p>
              </div>
              <div className="text-right">
                <span className={`text-sm font-mono font-bold ${confColor}`}>
                  {patternConf}%
                </span>
                <p className="text-[8px] tracking-[0.2em] text-text-muted mt-1 uppercase">Confidence</p>
              </div>
            </div>

            {/* Confidence bar */}
            <div className="w-full h-1 bg-ocean-800 rounded-full overflow-hidden">
              <div className="h-full bg-confidence rounded-full transition-all duration-300" style={{ width: `${parseFloat(patternConf) > 100 ? 100 : patternConf}%` }} />
            </div>
          </div>
        </div>

        <MetricGrid>
          <MetricCell label="Center Lat" value={`${obs.lat.toFixed(2)}°N`} />
          <MetricCell label="Center Lon" value={`${obs.lng.toFixed(2)}°E`} />
          <MetricCell label="Model" value={classification?.model?.name || 'ps70-classifier'} />
          <MetricCell label="Frame ID" value={displayFrameId} />
        </MetricGrid>
        <p className="text-[9px] text-text-faint font-mono mt-2">
          {obsTimestamp}
        </p>
      </div>

      {/* ── Forecast Performance ── */}
      <div className="glass-card rounded-xl p-4">
        <SectionHeader title="Temporal Prediction" badge="T+12 / T+24" badgeVariant="ml" />
        
        <MetricGrid>
          <MetricCell label="T+12 Forecast Error" 
            value={step.errors?.t12_km?.toFixed(1) || 'N/A'} 
            unit="km" 
            color={step.errors?.t12_km > 100 ? 'text-amber-400' : 'text-text-primary'} />
          <MetricCell label="T+24 Forecast Error" 
            value={step.errors?.t24_km?.toFixed(1) || 'N/A'} 
            unit="km" 
            color={step.errors?.t24_km > 200 ? 'text-alert' : 'text-text-primary'} />
        </MetricGrid>

        <div className="mt-3 pt-3 border-t border-ocean-800">
          <p className="text-[9px] text-text-faint font-mono mt-1">
            Prediction distance to actual track (Haversine)
          </p>
        </div>
      </div>

      {/* ── Event Metrics Aggregation ── */}
      {apiMetricsData && (
        <div className="glass-card rounded-xl p-4">
          <SectionHeader title="Event Evaluation Metrics" badge="AGGREGATED" badgeVariant="default" />
          <MetricGrid>
            <MetricCell label="Avg MAE (T+12)" value={apiMetricsData.track?.mae_km_t12?.toFixed(1) || 'N/A'} unit="km" />
            <MetricCell label="Avg MAE (T+24)" value={apiMetricsData.track?.mae_km_t24?.toFixed(1) || 'N/A'} unit="km" />
            <MetricCell label="Classification Acc." value={apiMetricsData.classification?.accuracy ? (apiMetricsData.classification.accuracy * 100).toFixed(1) : 'N/A'} unit="%" color="text-confidence" />
            <MetricCell label="Sample Size" value={apiMetricsData.classification?.sample_count || '0'} unit="frames" />
          </MetricGrid>
        </div>
      )}

      {/* ── Baseline Information ── */}
      <div className="glass-card rounded-xl p-4">
        <SectionHeader title="Storm Identity" badge="ARCHIVE" badgeVariant="historical" />
        <MetricGrid>
          <MetricCell label="Peak Wind" value={activeCycloneMeta.peakWind} unit="km/h" />
          <MetricCell label="Min Pressure" value={activeCycloneMeta.minPressure} unit="hPa" />
        </MetricGrid>

        <div className="mt-3 pt-3 border-t border-ocean-800">
          <p className="metric-label text-text-faint mb-1">LANDFALL DATA</p>
          <p className="text-[11px] text-text-secondary font-mono leading-relaxed">
            Time: {activeCycloneMeta.landfallTime.replace('T', ' ').replace('Z', ' UTC')}<br />
            Region: {activeCycloneMeta.landfallRegion}
          </p>
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

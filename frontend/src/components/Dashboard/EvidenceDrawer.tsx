import { X, Satellite, Clock, Hash, MapPin, Brain, Database, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useCycloneStore } from '../../store/useCycloneStore';
import { CYCLONES, PATTERN_LABELS, PATTERN_COLORS } from '../../data/cyclones';

interface EvidenceDrawerProps {
  open: boolean;
  onClose: () => void;
}

function Row({ icon, label, value, mono = false, highlight }: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
  mono?: boolean;
  highlight?: string;
}) {
  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-ocean-800 last:border-b-0">
      <span className="text-text-faint flex-shrink-0 mt-0.5">{icon}</span>
      <div className="flex-1 min-w-0">
        <p className="metric-label mb-0.5">{label}</p>
        <p className={`text-[11px] break-words ${mono ? 'font-mono' : ''} ${highlight ?? 'text-text-secondary'}`}>
          {value}
        </p>
      </div>
    </div>
  );
}

export function EvidenceDrawer({ open, onClose }: EvidenceDrawerProps) {
  const { activeEventId, getCurrentObservation, mode } = useCycloneStore();
  const activeCycloneMeta = CYCLONES.find(c => c.id === activeEventId) || CYCLONES[0];
  const obs = getCurrentObservation();

  if (!obs || !obs.classification) return null;

  const { classification, step } = obs;
  const patternLabel   = classification.pattern.label;
  const patternConf    = classification.pattern.confidence ? (classification.pattern.confidence * 100).toFixed(1) : 0;
  const patternColor   = PATTERN_COLORS[patternLabel] ?? '#6495ED';

  const frameId = mode === 'HISTORICAL'
    ? step.observation_frame
    : 'live_frame';

  const obsTime = obs.timestamp.replace('T', ' ').replace('Z', ' UTC');

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-ocean-950/60 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Drawer panel */}
          <motion.div
            key="drawer"
            initial={{ x: 360, opacity: 0 }}
            animate={{ x: 0,   opacity: 1 }}
            exit={{ x: 360,    opacity: 0 }}
            transition={{ type: 'spring', stiffness: 320, damping: 32 }}
            className="fixed top-0 right-0 h-full w-[340px] z-50 flex flex-col glass-panel border-l border-ocean-800 shadow-glass overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-ocean-800 flex-shrink-0">
              <div>
                <p className="metric-label text-text-faint">Level 3 — Evidence</p>
                <p className="text-sm font-semibold text-text-primary mt-0.5">Source Provenance</p>
              </div>
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-lg bg-ocean-800 flex items-center justify-center text-text-muted hover:text-text-primary transition-colors"
              >
                <X size={14} />
              </button>
            </div>

            {/* Satellite image placeholder */}
            <div className="mx-5 mt-4 mb-3 h-36 rounded-xl border border-ocean-800 overflow-hidden relative flex-shrink-0">
              {/* Simulated IR cloud structure */}
              <div className="absolute inset-0"
                style={{
                  background: `radial-gradient(circle at 45% 45%,
                    rgba(255,122,69,0.18) 0%,
                    rgba(79,195,224,0.10) 30%,
                    rgba(10,18,28,1) 70%)`,
                }} />
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <Satellite size={20} className="text-ocean-750 mb-1" />
                <p className="text-[9px] font-mono text-text-faint tracking-widest">HISTORICAL SATELLITE IMAGERY</p>
                <p className="text-[8px] text-text-faint opacity-60 mt-0.5">
                  {obs.timestamp.split('T')[0]} · {activeCycloneMeta.name}
                </p>
              </div>
              {/* Channel color strip */}
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-ir/50" />
            </div>

            {/* Pattern summary */}
            <div className="mx-5 mb-3 flex-shrink-0">
              <div className="glass-card rounded-xl px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ background: patternColor, boxShadow: `0 0 6px ${patternColor}` }} />
                  <span className="text-sm font-semibold text-text-primary">
                    {PATTERN_LABELS[patternLabel] ?? patternLabel}
                  </span>
                </div>
                <div className="text-right">
                  <p className="font-mono text-base font-semibold text-confidence">{patternConf}%</p>
                  <p className="metric-label">CONFIDENCE</p>
                </div>
              </div>
            </div>

            {/* Provenance rows — scrollable */}
            <div className="flex-1 overflow-y-auto px-5 pb-5 min-h-0">
              <p className="metric-label text-text-faint mb-2 pt-1">PROVENANCE FIELDS</p>

              <Row icon={<Satellite size={12} />} label="Satellite Source"
                value="NASA GIBS / MODIS Terra" />
              <Row icon={<Database size={12} />}   label="Data Provider"
                value="NOAA GridSat-B1 (historical)" mono />
              <Row icon={<Hash size={12} />}        label="Frame ID"
                value={frameId} mono />
              <Row icon={<Clock size={12} />}       label="Observation Time"
                value={obsTime} mono highlight="text-text-primary" />
              <Row icon={<MapPin size={12} />}      label="Centre Estimate"
                value={`${obs.lat.toFixed(2)}°N, ${obs.lng.toFixed(2)}°E`} mono />
              <Row icon={<Brain size={12} />}       label="Pattern Classification"
                value={`${PATTERN_LABELS[patternLabel]} (${patternConf}%)`}
                highlight="text-confidence" />
              <Row icon={<Brain size={12} />}       label="Model Version"
                value={classification.model?.name || "ps70-classifier v2.0.0"} mono />
              <Row icon={<Database size={12} />}    label="Preprocessing Version"
                value="standardize_data.py v1.0" mono />
              <Row icon={<Database size={12} />}    label="Normalization"
                value="per_frame_min_max" mono />

              {/* IMD gap note if applicable */}
              {activeCycloneMeta.imdGapCase && activeCycloneMeta.imdGapNote && (
                <div className="mt-4 glass-card rounded-xl p-3 border border-alert/25">
                  <div className="flex gap-2">
                    <AlertTriangle size={12} className="text-alert flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="metric-label text-alert mb-1">IMD GAP CASE</p>
                      <p className="text-[10px] text-text-muted leading-relaxed">
                        {activeCycloneMeta.imdGapNote}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Disclaimer */}
              <div className="mt-4 px-3 py-2.5 rounded-lg bg-ocean-850 border border-ocean-800">
                <p className="text-[9px] text-text-faint leading-relaxed">
                  Confidence score is model-derived. Not yet calibrated against held-out coverage.
                  Calibrated version arrives Day 6. Do not present as a measured probability.
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

import { ChevronDown, FlaskConical, Zap, Archive } from 'lucide-react';
import { useCycloneStore } from '../store/useCycloneStore';
import { CYCLONES } from '../data/cyclones';
import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export function TopNavigation() {
  const { mode, setMode, activeEventId, setActiveCyclone } = useCycloneStore();
  const activeCycloneMeta = CYCLONES.find(c => c.id === activeEventId) || CYCLONES[0];
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handle(e: MouseEvent) {
      if (dropRef.current && !dropRef.current.contains(e.target as Node)) setDropdownOpen(false);
    }
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, []);

  return (
    <div className="relative z-50 w-full h-14 border-b border-ocean-800 flex items-center px-5 gap-6 flex-shrink-0"
      style={{ background: 'rgba(16,27,40,0.70)', backdropFilter: 'blur(16px)' }}>

      {/* ── Brand ── */}
      <div className="flex items-center gap-2.5 mr-2 flex-shrink-0">
        <FlaskConical size={16} className="text-wv" />
        <span className="text-[13px] font-semibold tracking-[0.08em] text-text-primary">
          CYCLONE PREDICTION SYSTEM
        </span>
      </div>

      {/* ── Mode tabs ── */}
      <div className="flex items-center h-full gap-6">
        <button
          onClick={() => setMode('LIVE')}
          className={`flex items-center gap-1.5 h-14 text-[11px] font-semibold tracking-widest transition-colors relative
            ${mode === 'LIVE' ? 'text-text-primary' : 'text-text-faint hover:text-text-muted'}`}
        >
          <Zap size={11} className={mode === 'LIVE' ? 'text-ir' : 'text-text-faint'} />
          REALTIME MONITORING
          {mode === 'LIVE' && (
            <motion.div
              layoutId="tab-indicator"
              className="absolute bottom-0 left-0 right-0 h-[2px] bg-text-primary"
              style={{ boxShadow: '0 0 6px rgba(255,255,255,0.6)' }}
            />
          )}
        </button>

        <button
          onClick={() => setMode('HISTORICAL')}
          className={`flex items-center gap-1.5 h-14 text-[11px] font-semibold tracking-widest transition-colors relative
            ${mode === 'HISTORICAL' ? 'text-text-primary' : 'text-text-faint hover:text-text-muted'}`}
        >
          <Archive size={11} className={mode === 'HISTORICAL' ? 'text-wv' : 'text-text-faint'} />
          HISTORICAL ARCHIVE
          {mode === 'HISTORICAL' && (
            <motion.div
              layoutId="tab-indicator"
              className="absolute bottom-0 left-0 right-0 h-[2px] bg-text-primary"
              style={{ boxShadow: '0 0 6px rgba(255,255,255,0.6)' }}
            />
          )}
        </button>
      </div>

      {/* ── Spacer ── */}
      <div className="flex-1" />

      {/* ── Event selector ── */}
      <div className="relative" ref={dropRef}>
        <button
          onClick={() => setDropdownOpen(v => !v)}
          className="flex items-center gap-2 h-9 px-3 rounded-lg bg-ocean-850 border border-ocean-800
            hover:bg-ocean-800 hover:border-ocean-750 transition-colors"
        >
          {/* Basin dot */}
          <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
            mode === 'HISTORICAL'
              ? (activeCycloneMeta.basin === 'Arabian Sea' ? 'bg-ir' : 'bg-wv')
              : 'bg-ocean-750'
          }`} />
          <span className="text-[11px] font-medium text-text-secondary truncate max-w-[160px]">
            {mode === 'HISTORICAL'
              ? `${activeCycloneMeta.name} ${activeCycloneMeta.year} · ${activeCycloneMeta.basin}`
              : 'Select historical event…'}
          </span>
          <ChevronDown size={12} className={`text-text-faint transition-transform flex-shrink-0 ${dropdownOpen ? 'rotate-180' : ''}`} />
        </button>

        <AnimatePresence>
          {dropdownOpen && (
            <motion.div
              initial={{ opacity: 0, y: -6, scale: 0.97 }}
              animate={{ opacity: 1, y: 0,  scale: 1    }}
              exit={{   opacity: 0, y: -6, scale: 0.97 }}
              transition={{ duration: 0.15 }}
              className="absolute top-full right-0 mt-1.5 w-72 rounded-xl py-1.5 z-50 shadow-glass overflow-hidden border border-ocean-750"
              style={{ background: 'rgba(13, 20, 32, 0.95)', backdropFilter: 'blur(16px)' }}
            >
              {/* Basin groupings */}
              {(['Arabian Sea', 'Bay of Bengal'] as const).map(basin => {
                const group = CYCLONES.filter(c => c.basin === basin);
                if (!group.length) return null;
                return (
                  <div key={basin}>
                    <div className="px-3 py-1.5 metric-label text-text-faint border-b border-ocean-800">{basin}</div>
                    {group.map(cyclone => (
                      <button
                        key={cyclone.id}
                        onClick={() => { setActiveCyclone(cyclone.id); setDropdownOpen(false); }}
                        className={`w-full flex items-center gap-3 px-4 py-2.5 hover:bg-ocean-850 transition-colors text-left ${
                          activeEventId === cyclone.id && mode === 'HISTORICAL' ? 'bg-ocean-850' : ''
                        }`}
                      >
                        {/* Category color dot */}
                        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                          cyclone.peakWind >= 200 ? 'bg-alert' :
                          cyclone.peakWind >= 150 ? 'bg-ir'    :
                          cyclone.peakWind >= 100 ? 'bg-amber-400' : 'bg-confidence'
                        }`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-[11px] font-semibold text-text-primary tracking-wide">
                            {cyclone.name} {cyclone.year}
                          </p>
                          <p className="text-[9px] text-text-faint truncate">
                            {cyclone.peakWind} km/h peak · {cyclone.minPressure} hPa
                            {cyclone.imdGapCase ? ' · ⚠ IMD gap case' : ''}
                          </p>
                        </div>
                        {activeEventId === cyclone.id && mode === 'HISTORICAL' && (
                          <div className="w-1.5 h-1.5 rounded-full bg-wv flex-shrink-0" />
                        )}
                      </button>
                    ))}
                  </div>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

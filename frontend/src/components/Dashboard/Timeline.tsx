import { useCycloneStore } from '../../store/useCycloneStore';
import { formatTimelineLabel } from '../../lib/formatting';

export function Timeline() {
  const { apiReplayData, timelineIndex, setTimelineIndex } = useCycloneStore();
  const steps = apiReplayData?.steps ?? [];

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 w-full max-w-4xl px-4">
      <div
        className="glass-chrome rounded-full px-4 lg:px-8 py-3 shadow-glass relative overflow-hidden flex items-center"
        role="slider"
        aria-label="Timeline scrubber"
        aria-valuemin={0}
        aria-valuemax={steps.length - 1}
        aria-valuenow={timelineIndex}
      >
        {/* Scrollable Container */}
        <div
          className="w-full overflow-x-auto no-scrollbar flex items-center gap-4 relative py-2"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {/* Track line */}
          <div className="absolute left-0 right-0 top-[18px] h-[2px] bg-white/10 z-0 min-w-full" aria-hidden="true" />

          {/* Timestamps */}
          {steps.map((step, idx) => {
            const active = idx === timelineIndex;
            const { date, time } = formatTimelineLabel(step.time);
            return (
              <button
                key={idx}
                onClick={() => setTimelineIndex(idx)}
                aria-label={`${date} ${time}`}
                className={`relative z-10 flex flex-col items-center justify-center transition-all duration-300 cursor-pointer group flex-shrink-0 w-12 ${
                  active ? 'text-text-primary scale-110' : 'text-white/70 hover:text-white'
                }`}
              >
                <div
                  className={`w-3 h-3 rounded-full mb-1.5 transition-all shadow-sm ${
                    active ? 'bg-white shadow-white/50' : 'bg-white/20 group-hover:bg-white/50'
                  }`}
                  aria-hidden="true"
                />
                <span className="text-xs font-mono font-bold tracking-wide">{date}</span>
                <span className="text-xs font-mono opacity-80">{time}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

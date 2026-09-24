import { useCycloneStore } from '../../store/useCycloneStore';
import { formatTimelineLabel } from '../../lib/formatting';

export function Timeline() {
  const { apiReplayData, timelineIndex, setTimelineIndex } = useCycloneStore();
  const steps = apiReplayData?.steps ?? [];

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 w-full max-w-3xl px-4">
      <div
        className="glass-chrome rounded-full px-4 lg:px-6 py-2 shadow-glass relative overflow-hidden flex items-center bg-ocean-950/60 backdrop-blur-xl"
        role="slider"
        aria-label="Timeline scrubber"
        aria-valuemin={0}
        aria-valuemax={steps.length - 1}
        aria-valuenow={timelineIndex}
      >
        {/* Scrollable Container */}
        <div
          className="w-full overflow-x-auto no-scrollbar flex items-center gap-3 relative py-1.5"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {/* Track line */}
          <div className="absolute left-0 right-0 top-[14px] h-[2px] bg-yellow-300/20 z-0 min-w-full" aria-hidden="true" />

          {/* Timestamps */}
          {steps.map((step, idx) => {
            const active = idx === timelineIndex;
            const { date, time } = formatTimelineLabel(step.time);
            return (
              <button
                key={idx}
                onClick={() => setTimelineIndex(idx)}
                aria-label={`${date} ${time}`}
                className={`relative z-10 flex flex-col items-center justify-center transition-all duration-300 cursor-pointer group flex-shrink-0 w-10 ${
                  active ? 'text-yellow-300 scale-110' : 'text-yellow-300/70 hover:text-yellow-300'
                }`}
              >
                <div
                  className={`w-2 h-2 rounded-full mb-1 transition-all shadow-sm ${
                    active ? 'bg-yellow-300 shadow-yellow-300/50' : 'bg-yellow-300/30 group-hover:bg-yellow-300/60'
                  }`}
                  aria-hidden="true"
                />
                <span className="text-[10px] font-mono font-bold tracking-wide">{date}</span>
                <span className="text-[9px] font-mono opacity-80">{time}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

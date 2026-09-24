import { useRef } from 'react';
import { useCycloneStore } from '../../store/useCycloneStore';
import { formatTimelineLabel } from '../../lib/formatting';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export function Timeline() {
  const { apiReplayData, timelineIndex, setTimelineIndex } = useCycloneStore();
  const steps = apiReplayData?.steps ?? [];
  const scrollRef = useRef<HTMLDivElement>(null);
  const scrollRafRef = useRef<number | null>(null);

  const startScroll = (direction: 'left' | 'right') => {
    stopScroll();
    const scrollStep = () => {
      if (scrollRef.current) {
        scrollRef.current.scrollBy({ left: direction === 'left' ? -8 : 8 });
      }
      scrollRafRef.current = requestAnimationFrame(scrollStep);
    };
    scrollRafRef.current = requestAnimationFrame(scrollStep);
  };

  const stopScroll = () => {
    if (scrollRafRef.current !== null) {
      cancelAnimationFrame(scrollRafRef.current);
      scrollRafRef.current = null;
    }
  };

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 w-full max-w-3xl px-4 flex items-center justify-center gap-3">
      <button
        onMouseDown={() => startScroll('left')}
        onMouseUp={stopScroll}
        onMouseLeave={stopScroll}
        onTouchStart={() => startScroll('left')}
        onTouchEnd={stopScroll}
        className="w-9 h-9 flex-shrink-0 flex items-center justify-center rounded-full bg-black/80 backdrop-blur-xl border border-white/10 text-yellow-300 hover:bg-ocean-800 transition-colors shadow-md"
        aria-label="Scroll left"
      >
        <ChevronLeft size={18} />
      </button>

      <div
        className="glass-chrome rounded-full px-4 lg:px-6 py-2 shadow-glass relative overflow-hidden flex items-center bg-black/80 backdrop-blur-xl flex-grow"
        role="slider"
        aria-label="Timeline scrubber"
        aria-valuemin={0}
        aria-valuemax={steps.length - 1}
        aria-valuenow={timelineIndex}
      >
        {/* Scrollable Container */}
        <div
          ref={scrollRef}
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

      <button
        onMouseDown={() => startScroll('right')}
        onMouseUp={stopScroll}
        onMouseLeave={stopScroll}
        onTouchStart={() => startScroll('right')}
        onTouchEnd={stopScroll}
        className="w-9 h-9 flex-shrink-0 flex items-center justify-center rounded-full bg-black/80 backdrop-blur-xl border border-white/10 text-yellow-300 hover:bg-ocean-800 transition-colors shadow-md"
        aria-label="Scroll right"
      >
        <ChevronRight size={18} />
      </button>
    </div>
  );
}

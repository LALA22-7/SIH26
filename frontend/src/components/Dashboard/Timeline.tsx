import { useCycloneStore } from '../../store/useCycloneStore';

function formatLabel(ts: string): { date: string; time: string } {
  const d = new Date(ts);
  const date = d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', timeZone: 'UTC' }).toUpperCase();
  const time = d.toISOString().slice(11, 16) + ' UTC';
  return { date, time };
}

export function Timeline() {
  const { apiReplayData, timelineIndex, setTimelineIndex } = useCycloneStore();

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 w-full max-w-4xl px-4">
      <div className="glass-chrome rounded-full px-4 lg:px-8 py-3 shadow-glass relative overflow-hidden flex items-center">
        
        {/* Scrollable Container */}
        <div className="w-full overflow-x-auto no-scrollbar flex items-center gap-4 relative py-2"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
          
          {/* Track line spanning full scroll width */}
          <div className="absolute left-0 right-0 top-[18px] h-[2px] bg-white/10 z-0 min-w-full" />

          {/* Timestamps */}
          {(apiReplayData?.steps || []).map((step: any, idx: number) => {
            const active = idx === timelineIndex;
            const { date, time } = formatLabel(step.time);
            return (
              <button
                key={idx}
                onClick={() => setTimelineIndex(idx)}
                className={`relative z-10 flex flex-col items-center justify-center transition-all duration-300 cursor-pointer group flex-shrink-0 w-12 ${
                  active ? 'text-text-primary scale-110' : 'text-white/70 hover:text-white'
                }`}
              >
                <div 
                  className={`w-3 h-3 rounded-full mb-1.5 transition-all shadow-sm ${
                    active ? 'bg-white shadow-white/50' : 'bg-white/20 group-hover:bg-white/50'
                  }`} 
                />
                <span className="text-[9px] font-mono font-bold tracking-wide">{date}</span>
                <span className="text-[8px] font-mono opacity-80">{time}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

import { useEffect } from 'react';
import { useCycloneStore } from './store/useCycloneStore';
import { IntroAnimation } from './components/IntroAnimation';
import { SideNav } from './components/Navigation/SideNav';
import { SatellitePanel } from './components/Dashboard/SatellitePanel';
import { MetricsPanel } from './components/Dashboard/MetricsPanel';
import { EvidenceDrawer } from './components/Dashboard/EvidenceDrawer';
import { Bell, User } from 'lucide-react';

function App() {
  const {
    introComplete, isPlaying, timelineIndex,
    setTimelineIndex, mode, activeEventId,
    fetchLiveData, evidenceOpen, openEvidence, closeEvidence,
  } = useCycloneStore();

  // Fetch event data when active event changes
  useEffect(() => {
    if (mode === 'HISTORICAL') {
      useCycloneStore.getState().fetchEventData(activeEventId);
    }
  }, [mode, activeEventId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Initial live data fetch
  useEffect(() => {
    if (mode === 'LIVE') fetchLiveData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Timeline auto-play
  useEffect(() => {
    if (!isPlaying || mode !== 'HISTORICAL') return;
    const total = useCycloneStore.getState().apiReplayData?.steps?.length || 0;
    if (total === 0) return;
    
    const id = window.setInterval(() => {
      setTimelineIndex(timelineIndex + 1 >= total ? 0 : timelineIndex + 1);
    }, 1600);
    return () => clearInterval(id);
  }, [isPlaying, timelineIndex, mode, setTimelineIndex]);

  return (
    <div className="w-full h-screen bg-[#040814] text-text-primary overflow-hidden flex flex-col p-3 lg:p-4">

      {/* Intro splash */}
      {!introComplete && <IntroAnimation />}

      {/* Top utility bar (Account/Alerts) */}
      <header
        className="flex justify-end items-center w-full px-2 mb-3 transition-opacity duration-700 pointer-events-none"
        style={{ opacity: introComplete ? 1 : 0 }}
      >
        <div className="flex items-center gap-3 pointer-events-auto">
          <button className="h-9 px-4 rounded-xl glass-chrome flex items-center gap-2 text-text-muted hover:text-text-primary transition-all hover:bg-ocean-800">
            <Bell size={14} fill="currentColor" className="text-alert drop-shadow-[0_0_8px_rgba(255,92,92,0.6)]" />
            <span className="text-[10px] font-bold tracking-[0.14em] text-white">2 ALERTS</span>
          </button>
          <button className="w-9 h-9 rounded-xl glass-chrome flex items-center justify-center text-text-muted hover:text-text-primary transition-all hover:bg-ocean-800">
            <User size={16} />
          </button>
        </div>
      </header>

      {/* Main workspace */}
      <main
        className="flex-1 min-h-0 w-full max-w-[1920px] mx-auto rounded-[1.5rem] border border-white/5 flex overflow-hidden transition-opacity duration-700 shadow-glass"
        style={{
          opacity: introComplete ? 1 : 0,
          background: 'rgba(11, 17, 32, 0.65)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)'
        }}
      >
        {/* Left Navigation */}
        <SideNav />

        <div className="flex-1 min-h-0 flex flex-col lg:flex-row gap-0">

          {/* ── Left: Map (70%) ── */}
          <div className="flex-none h-[50vh] lg:h-auto lg:flex-[0.70] min-h-0 flex flex-col border-b lg:border-b-0 lg:border-r border-ocean-800">
            {/* Section label */}
            <div className="flex-shrink-0 flex items-center justify-between px-4 py-2 border-b border-ocean-800/50">
             <div className="flex items-center gap-2">
  {mode === 'LIVE' && (
    <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
  )}

  <span className="metric-label text-text-primary font-semibold">
    {mode === 'LIVE' ? 'LIVE SATELLITE IMAGING' : 'HISTORICAL SATELLITE ARCHIVE'}
  </span>
</div>
              {mode === 'HISTORICAL' && (
                <button
                  onClick={openEvidence}
                  className="text-[9px] font-semibold tracking-widest text-wv hover:text-text-primary
                    transition-colors px-2 py-0.5 rounded border border-wv/25 hover:border-wv/50"
                >
                  VIEW EVIDENCE
                </button>
              )}
            </div>

        <div className="flex-1 min-w-0 flex flex-col lg:flex-row gap-0">
          {/* ── Center: Map ── */}
          <div className="flex-none h-[50vh] lg:h-auto lg:flex-1 min-w-0 min-h-0 flex flex-col border-b lg:border-b-0 lg:border-r border-white/5">
            {/* Map container */}
            <div className="flex-1 min-h-0 relative">
              <SatellitePanel onCentreClick={openEvidence} />
            </div>
          </div>

          {/* ── Right: Widgets ── */}
          <div className="flex-none lg:w-[420px] xl:w-[480px] min-h-0 flex flex-col bg-ocean-950/20">
            <div className="flex-1 min-h-0 overflow-y-auto p-4 custom-scrollbar">
              <MetricsPanel />
            </div>
          </div>

        </div>
      </main>

      {/* Evidence drawer — portal-style */}
      <EvidenceDrawer open={evidenceOpen} onClose={closeEvidence} />
    </div>
  );
}

export default App;

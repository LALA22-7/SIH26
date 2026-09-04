import { useEffect } from 'react';
import { useCycloneStore } from './store/useCycloneStore';
import { IntroAnimation } from './components/IntroAnimation';
import { TopNavigation } from './components/TopNavigation';
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
    <div className="w-full h-screen bg-ocean-950 text-text-primary overflow-hidden flex flex-col p-3 lg:p-5">

      {/* Intro splash */}
      {!introComplete && <IntroAnimation />}

      {/* Brand header */}
      <header
        className="flex justify-between items-center w-full px-1 mb-3 transition-opacity duration-700"
        style={{ opacity: introComplete ? 1 : 0 }}
      >
        <h1 className="text-xl tracking-[0.15em] text-text-primary font-bold uppercase">CYCLOWATCH</h1>
        <div className="flex items-center gap-2">
          <button className="w-8 h-8 rounded-lg glass-chrome flex items-center justify-center text-text-muted hover:text-text-primary transition-colors">
            <User size={13} />
          </button>
          <button className="h-8 px-3 rounded-lg glass-chrome flex items-center gap-1.5 text-text-muted hover:text-text-primary transition-colors">
            <Bell size={12} fill="currentColor" className="text-ir" />
            <span className="text-[9px] font-bold tracking-[0.14em] text-text-primary">ALERT</span>
          </button>
        </div>
      </header>

      {/* Main workspace */}
      <main
        className="flex-1 min-h-0 w-full max-w-[1920px] mx-auto rounded-2xl border border-ocean-800 flex flex-col overflow-hidden transition-opacity duration-700 shadow-glass"
        style={{
          opacity: introComplete ? 1 : 0,
          background: 'rgba(13, 20, 32, 0.85)',
        }}
      >
        <TopNavigation />

        <div className="flex-1 min-h-0 flex flex-col lg:flex-row gap-0">

          {/* ── Left: Map (65%) ── */}
          <div className="flex-none h-[50vh] lg:h-auto lg:flex-[0.65] min-h-0 flex flex-col border-b lg:border-b-0 lg:border-r border-ocean-800">
            {/* Section label */}
            <div className="flex-shrink-0 flex items-center justify-between px-4 py-2 border-b border-ocean-800/50">
              <span className="metric-label text-text-faint">
                {mode === 'LIVE' ? 'LIVE SATELLITE IMAGING' : 'HISTORICAL SATELLITE ARCHIVE'}
              </span>
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

            {/* Map container */}
            <div className="flex-1 min-h-0 relative">
              <SatellitePanel onCentreClick={openEvidence} />
            </div>
          </div>

          {/* ── Right: Metrics (35%) ── */}
          <div className="flex-none lg:flex-[0.35] min-h-0 flex flex-col">
            <div className="flex-shrink-0 px-4 py-2 border-b border-ocean-800/50">
              <span className="metric-label text-text-faint">
                {mode === 'LIVE' ? 'LIVE INTELLIGENCE' : 'HISTORICAL ANALYSIS'}
              </span>
            </div>
            <div className="flex-1 min-h-0 overflow-y-auto p-4">
              <MetricsPanel />
            </div>
          </div>

        </div>
      </main>

      {/* Evidence drawer — portal-style, rendered outside main for proper z-index */}
      <EvidenceDrawer open={evidenceOpen} onClose={closeEvidence} />
    </div>
  );
}

export default App;

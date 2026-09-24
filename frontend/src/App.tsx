import { useEffect, useState, useRef } from 'react';
import { useCycloneStore } from './store/useCycloneStore';
import { IntroAnimation } from './components/IntroAnimation';
import { SideNav } from './components/Navigation/SideNav';
import { SatellitePanel } from './components/Dashboard/SatellitePanel';
import { MetricsPanel } from './components/Dashboard/MetricsPanel';
import { EvidenceDrawer } from './components/Dashboard/EvidenceDrawer';
import { HomePage } from './components/Pages/HomePage';
import { ArchitecturePage } from './components/Pages/ArchitecturePage';
import { ReportsPage } from './components/Pages/ReportsPage';
import { User, ExternalLink, Info, LogIn, ChevronDown } from 'lucide-react';
import { CYCLONES } from './data/cyclones';

/** Timeline auto-play interval in milliseconds */
const TIMELINE_TICK_MS = 1600;

function App() {
  const {
    introComplete, isPlaying,
    mode, activeEventId, activePage,
    fetchLiveData, evidenceOpen, openEvidence, closeEvidence,
  } = useCycloneStore();

  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [cycloneMenuOpen, setCycloneMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const cycloneMenuRef = useRef<HTMLDivElement>(null);

  // Close menus on outside click
  useEffect(() => {
    function handle(e: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
      if (cycloneMenuRef.current && !cycloneMenuRef.current.contains(e.target as Node)) {
        setCycloneMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, []);

  // Fetch event data when active event changes
  useEffect(() => {
    if (mode === 'HISTORICAL') {
      useCycloneStore.getState().fetchEventData(activeEventId);
    }
  }, [mode, activeEventId]);

  // Initial live data fetch
  useEffect(() => {
    if (mode === 'LIVE') fetchLiveData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Timeline auto-play — uses functional update to avoid stale closure
  useEffect(() => {
    if (!isPlaying || mode !== 'HISTORICAL') return;

    const id = window.setInterval(() => {
      const { apiReplayData, timelineIndex, setTimelineIndex } = useCycloneStore.getState();
      const total = apiReplayData?.steps?.length ?? 0;
      if (total === 0) return;
      setTimelineIndex(timelineIndex + 1 >= total ? 0 : timelineIndex + 1);
    }, TIMELINE_TICK_MS);

    return () => clearInterval(id);
  }, [isPlaying, mode]);

  const isMapPage = activePage === 'live' || activePage === 'historical';

  return (
    <div className="w-full h-screen bg-[#040814] text-text-primary overflow-hidden flex flex-col p-2 sm:p-3 lg:p-4">

      {/* Intro splash */}
      {!introComplete && <IntroAnimation />}

      {/* Main workspace */}
      <main
        className="flex-1 min-h-0 w-full max-w-[1920px] mx-auto rounded-[1.5rem] border border-white/5 flex overflow-hidden transition-opacity duration-700 shadow-glass"
        style={{
          opacity: introComplete ? 1 : 0,
          background: 'rgba(11, 17, 32, 0.65)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)'
        }}
        role="application"
        aria-label="CycloneWatch Dashboard"
      >
        {/* Left Navigation */}
        <SideNav />

        {/* Content area */}
        <div className="flex-1 min-w-0 flex flex-col relative">

          {/* Top bar */}
          <header className="flex-shrink-0 flex justify-end items-center px-4 py-2 border-b border-ocean-800/50">
            {isMapPage && (
              <div className="flex items-center gap-2 mr-auto">
                {mode === 'LIVE' && (
                  <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" aria-hidden="true" />
                )}
                <span className="metric-label text-text-primary font-semibold">
                  {mode === 'LIVE' ? 'LIVE SATELLITE IMAGING' : 'HISTORICAL SATELLITE ARCHIVE'}
                </span>
                {mode === 'HISTORICAL' && (
                  <button
                    onClick={openEvidence}
                    className="text-xs font-semibold tracking-widest text-wv hover:text-text-primary
                      transition-colors px-2 py-0.5 rounded border border-wv/25 hover:border-wv/50 ml-3"
                  >
                    VIEW EVIDENCE
                  </button>
                )}
              </div>
            )}

            <div className="flex items-center gap-4">
              {/* Cyclone selection dropdown (Historical Only) */}
              {mode === 'HISTORICAL' && (
                <div className="relative" ref={cycloneMenuRef}>
                  <button
                    onClick={() => setCycloneMenuOpen(v => !v)}
                    aria-haspopup="listbox"
                    aria-expanded={cycloneMenuOpen}
                    className="h-9 px-3 rounded-xl glass-chrome flex items-center justify-center gap-2 text-text-muted hover:text-text-primary transition-all hover:bg-ocean-800 border border-white/5"
                  >
                    <span className="text-xs font-semibold">SELECT CYCLONE</span>
                    <ChevronDown size={14} />
                  </button>

                  {cycloneMenuOpen && (
                    <div
                      role="listbox"
                      aria-label="Select a cyclone event"
                      className="absolute top-11 right-0 w-56 glass-chrome rounded-xl p-1.5 shadow-glass z-50 border border-white/10"
                    >
                      {CYCLONES.map(c => (
                        <div
                          key={c.id}
                          role="option"
                          aria-selected={c.id === activeEventId}
                          onClick={() => { useCycloneStore.getState().setActiveCyclone(c.id); setCycloneMenuOpen(false); }}
                          className={`px-3 py-2 text-xs hover:bg-white/10 cursor-pointer rounded-lg flex justify-between transition-colors ${c.id === activeEventId ? 'text-blue-400 bg-white/5' : 'text-text-muted hover:text-text-primary'}`}
                        >
                           <span>{c.name} {c.year}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

            {/* User dropdown */}
            <div className="relative" ref={userMenuRef}>
              <button
                onClick={() => setUserMenuOpen(v => !v)}
                aria-haspopup="menu"
                aria-expanded={userMenuOpen}
                aria-label="User menu"
                className="w-9 h-9 rounded-xl glass-chrome flex items-center justify-center text-text-muted hover:text-text-primary transition-all hover:bg-ocean-800"
              >
                <User size={16} />
              </button>

              {userMenuOpen && (
                <div role="menu" className="absolute top-11 right-0 w-48 glass-chrome rounded-xl p-1.5 shadow-glass z-50 border border-white/10">
                  {[
                    { icon: ExternalLink, label: 'Source Code', action: () => window.open('https://github.com/LALA22-7/SIH26', '_blank') },
                    { icon: Info, label: 'About CycloneWatch', action: () => { useCycloneStore.getState().setActivePage('home'); setUserMenuOpen(false); } },
                    { icon: LogIn, label: 'Login', action: () => setUserMenuOpen(false) },
                  ].map((item, i) => (
                    <button
                      key={i}
                      role="menuitem"
                      onClick={item.action}
                      className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg
                        text-text-muted hover:text-text-primary hover:bg-ocean-850
                        transition-colors text-left"
                    >
                      <item.icon size={14} />
                      <span className="text-xs">{item.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            </div>
          </header>

          {/* Page content */}
          <div className="flex-1 min-h-0 flex flex-col lg:flex-row">
            {activePage === 'home' && <HomePage />}
            {activePage === 'architecture' && <ArchitecturePage />}
            {activePage === 'reports' && <ReportsPage />}

            {isMapPage && (
              <>
                {/* Map area */}
                <div className="flex-1 min-h-0 min-w-0 flex flex-col border-b lg:border-b-0 lg:border-r border-ocean-800">
                  <div className="flex-1 min-h-0 relative">
                    <SatellitePanel onCentreClick={openEvidence} />
                  </div>
                </div>

                {/* Right metrics panel */}
                <aside className="flex-none h-[40vh] lg:h-auto lg:w-[380px] xl:w-[420px] min-h-0 flex flex-col bg-ocean-950/20">
                  <div className="flex-1 min-h-0 overflow-y-auto p-3 custom-scrollbar">
                    <MetricsPanel />
                  </div>
                </aside>
              </>
            )}
          </div>
        </div>
      </main>

      {/* Evidence drawer — portal-style */}
      <EvidenceDrawer open={evidenceOpen} onClose={closeEvidence} />
    </div>
  );
}

export default App;

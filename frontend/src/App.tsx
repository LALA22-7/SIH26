import { useEffect, useState, useRef } from 'react';
import { useCycloneStore } from './store/useCycloneStore';
import { SideNav } from './components/Navigation/SideNav';
import { SatellitePanel } from './components/Dashboard/SatellitePanel';
import { MetricsPanel } from './components/Dashboard/MetricsPanel';
import { EvidenceDrawer } from './components/Dashboard/EvidenceDrawer';
import { HomePage } from './components/Pages/HomePage';
import { ArchitecturePage } from './components/Pages/ArchitecturePage';
import { ReportsPage } from './components/Pages/ReportsPage';
import { User, ExternalLink, Info, LogIn, ChevronDown } from 'lucide-react';
import { CYCLONES } from './data/cyclones';

function App() {
  const {
    isPlaying, timelineIndex,
    setTimelineIndex, mode, activeEventId, activePage,
    fetchLiveData, evidenceOpen, openEvidence, closeEvidence,
  } = useCycloneStore();

  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [cycloneMenuOpen, setCycloneMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const cycloneMenuRef = useRef<HTMLDivElement>(null);

  // Close user menu on outside click
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

  // Should we show the map+metrics layout?
  const isMapPage = activePage === 'live' || activePage === 'historical';

  return (
    <div className="w-full h-screen bg-[#040814] text-text-primary overflow-hidden flex flex-col p-2 sm:p-3 lg:p-4">

      {/* Main workspace */}
      <main
        className="flex-1 min-h-0 w-full max-w-[1920px] mx-auto rounded-[1.5rem] border border-white/5 flex overflow-hidden shadow-glass"
        style={{
          background: 'rgba(11, 17, 32, 0.65)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)'
        }}
      >
        {/* Left Navigation */}
        <SideNav />

        {/* Content area */}
        <div className="flex-1 min-w-0 flex flex-col relative">

          {/* Top bar — user menu (shown on all pages) */}
          <div className="flex-shrink-0 flex justify-end items-center px-4 py-2 border-b border-ocean-800/50">
            {isMapPage && (
              <div className="flex items-center gap-2 mr-auto">
                {mode === 'LIVE' && (
                  <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                )}
                <span className="metric-label text-text-primary font-semibold">
                  {mode === 'LIVE' ? 'LIVE SATELLITE IMAGING' : 'HISTORICAL SATELLITE ARCHIVE'}
                </span>
                {mode === 'HISTORICAL' && (
                  <button
                    onClick={openEvidence}
                    className="text-[9px] font-semibold tracking-widest text-wv hover:text-text-primary
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
                    className="h-9 px-3 rounded-xl glass-chrome flex items-center justify-center gap-2 text-text-muted hover:text-text-primary transition-all hover:bg-ocean-800 border border-white/5"
                  >
                    <span className="text-xs font-semibold">SELECT CYCLONE</span>
                    <ChevronDown size={14} />
                  </button>

                  {cycloneMenuOpen && (
                    <div className="absolute top-11 right-0 w-56 glass-chrome rounded-xl p-1.5 shadow-glass z-50 border border-white/10">
                      {CYCLONES.map(c => (
                        <div 
                          key={c.id} 
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
                className="w-9 h-9 rounded-xl glass-chrome flex items-center justify-center text-text-muted hover:text-text-primary transition-all hover:bg-ocean-800"
              >
                <User size={16} />
              </button>

              {userMenuOpen && (
                <div className="absolute top-11 right-0 w-48 glass-chrome rounded-xl p-1.5 shadow-glass z-50 border border-white/10">
                  {[
                    { icon: ExternalLink, label: 'Source Code', action: () => window.open('https://github.com/LALA22-7/SIH26', '_blank') },
                    { icon: Info, label: 'About CycloneWatch', action: () => { useCycloneStore.getState().setActivePage('home'); setUserMenuOpen(false); } },
                    { icon: LogIn, label: 'Login', action: () => setUserMenuOpen(false) },
                  ].map((item, i) => (
                    <button
                      key={i}
                      onClick={item.action}
                      className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg
                        text-text-muted hover:text-text-primary hover:bg-ocean-850
                        transition-colors text-left"
                    >
                      <item.icon size={14} />
                      <span className="text-[11px]">{item.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            </div>
          </div>

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
                <div className="flex-none h-[40vh] lg:h-auto lg:w-[380px] xl:w-[420px] min-h-0 flex flex-col bg-ocean-950/20">
                  <div className="flex-1 min-h-0 overflow-y-auto p-3 custom-scrollbar">
                    <MetricsPanel />
                  </div>
                </div>
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

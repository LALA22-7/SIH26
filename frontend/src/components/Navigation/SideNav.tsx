import { useState, useRef, useEffect } from 'react';
import { Home, Activity, Clock, Cpu, FileText, ChevronLeft, ChevronRight, Menu, X } from 'lucide-react';
import { useCycloneStore } from '../../store/useCycloneStore';
import type { AppPage } from '../../store/useCycloneStore';

export function SideNav() {
  const { activePage, setActivePage, setMode, sidebarCollapsed, setSidebarCollapsed } = useCycloneStore();
  const [mobileOpen, setMobileOpen] = useState(false);
  const navRef = useRef<HTMLDivElement>(null);

  // Close mobile menu on outside click
  useEffect(() => {
    function handle(e: MouseEvent) {
      if (mobileOpen && navRef.current && !navRef.current.contains(e.target as Node)) {
        setMobileOpen(false);
      }
    }
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, [mobileOpen]);

  const navItems: { id: AppPage; icon: typeof Home; label: string; modeSwitch?: 'LIVE' | 'HISTORICAL' }[] = [
    { id: 'home', icon: Home, label: 'Home' },
    { id: 'live', icon: Activity, label: 'Live Map', modeSwitch: 'LIVE' },
    { id: 'historical', icon: Clock, label: 'Historical Replay', modeSwitch: 'HISTORICAL' },
    { id: 'architecture', icon: Cpu, label: 'Architecture' },
    { id: 'reports', icon: FileText, label: 'Reports' },
  ];

  const handleNav = (item: typeof navItems[0]) => {
    setActivePage(item.id);
    if (item.modeSwitch) setMode(item.modeSwitch);
    setMobileOpen(false);
  };

  const navContent = (
    <>
      {/* Brand logo area */}
      <div className={`flex items-center gap-3 mb-8 ${sidebarCollapsed ? 'justify-center px-0' : 'px-2'}`}>
        <div className="w-10 h-10 rounded-xl overflow-hidden shadow-[0_0_20px_rgba(79,195,224,0.3)] bg-ocean-900 border border-ocean-700/50 flex items-center justify-center flex-shrink-0">
          <img src="/logo.png" alt="CycloneWatch Logo" className="w-full h-full object-cover" />
        </div>
        {!sidebarCollapsed && (
          <div className="min-w-0 whitespace-nowrap overflow-hidden text-ellipsis">
            <span className="text-white font-bold tracking-wide text-base">CycloneWatch</span>
            <sub className="text-[9px] text-cyan-400/80 uppercase tracking-widest ml-1">AI-Powered Tracker</sub>
          </div>
        )}
      </div>

      {/* Nav Links */}
      <div className="flex-1 flex flex-col gap-1.5" role="list">
        {navItems.map((item) => {
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleNav(item)}
              title={sidebarCollapsed ? item.label : undefined}
              aria-current={isActive ? 'page' : undefined}
              className={`flex items-center gap-3 ${sidebarCollapsed ? 'justify-center px-0 py-2.5' : 'px-3 py-2.5'} rounded-xl transition-all duration-200 ${
                isActive
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]'
                  : 'text-text-secondary hover:bg-ocean-800/50 hover:text-text-primary'
              }`}
            >
              <item.icon size={18} strokeWidth={isActive ? 2.5 : 2} className={`flex-shrink-0 ${isActive ? 'text-blue-400 drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]' : ''}`} />
              {!sidebarCollapsed && (
                <span className={`text-sm font-medium truncate ${isActive ? 'text-white' : ''}`}>{item.label}</span>
              )}
            </button>
          );
        })}
      </div>

      {/* Collapse toggle — desktop only */}
      <div className="mt-auto hidden lg:block">
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-text-muted hover:text-text-primary hover:bg-ocean-800/50 transition-all w-full"
        >
          {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          {!sidebarCollapsed && <span className="text-sm font-medium">Collapse</span>}
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setMobileOpen(true)}
        aria-label="Open navigation menu"
        className="fixed top-4 left-4 z-50 lg:hidden w-10 h-10 rounded-xl glass-chrome flex items-center justify-center text-text-muted hover:text-text-primary transition-colors"
      >
        <Menu size={20} />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <nav
        ref={navRef}
        aria-label="Main navigation"
        className={`
          ${sidebarCollapsed ? 'lg:w-16' : 'lg:w-56'}
          fixed lg:relative inset-y-0 left-0 z-50 lg:z-auto
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          w-64 lg:w-auto border-r border-ocean-800 bg-ocean-950/95 lg:bg-ocean-950/40
          backdrop-blur-xl lg:backdrop-blur-none
          flex flex-col p-4 transition-all duration-300
        `}
      >
        {/* Mobile close button */}
        <button
          onClick={() => setMobileOpen(false)}
          aria-label="Close navigation menu"
          className="absolute top-4 right-4 lg:hidden text-text-muted hover:text-text-primary"
        >
          <X size={20} />
        </button>

        {navContent}
      </nav>
    </>
  );
}

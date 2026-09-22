import { Home, Map, Activity, Clock, Bell, FileText, Settings } from 'lucide-react';
import { useCycloneStore } from '../../store/useCycloneStore';

export function SideNav() {
  const { mode, setMode } = useCycloneStore();

  const navItems = [
    { id: 'home', icon: Home, label: 'Home', disabled: true },
    { id: 'live', icon: Activity, label: 'Live Map', active: mode === 'LIVE', onClick: () => setMode('LIVE') },
    { id: 'forecast', icon: Map, label: 'Forecast', disabled: true },
    { id: 'historical', icon: Clock, label: 'Historical Replay', active: mode === 'HISTORICAL', onClick: () => setMode('HISTORICAL') },
    { id: 'alerts', icon: Bell, label: 'Alerts', disabled: true },
    { id: 'reports', icon: FileText, label: 'Reports', disabled: true },
  ];

  return (
    <nav className="w-64 border-r border-ocean-800 bg-ocean-950/40 flex flex-col p-4">
      {/* Brand logo area */}
      <div className="flex items-center gap-3 mb-8 px-2">
        <div className="w-10 h-10 rounded-xl overflow-hidden shadow-[0_0_20px_rgba(79,195,224,0.3)] bg-ocean-900 border border-ocean-700/50 flex items-center justify-center">
          <img src="/logo.png" alt="CycloneWatch Logo" className="w-full h-full object-cover" />
        </div>
        <div className="flex flex-col">
          <span className="text-white font-bold tracking-wide text-sm">CycloneWatch</span>
          <span className="text-[9px] text-cyan-400/80 uppercase tracking-widest">AI-Powered Tracker</span>
        </div>
      </div>

      {/* Nav Links */}
      <div className="flex-1 flex flex-col gap-2">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={item.onClick}
            disabled={item.disabled}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ${
              item.active 
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]' 
                : item.disabled 
                  ? 'text-ocean-750 cursor-not-allowed'
                  : 'text-text-secondary hover:bg-ocean-800/50 hover:text-text-primary'
            }`}
          >
            <item.icon size={18} strokeWidth={item.active ? 2.5 : 2} className={item.active ? 'text-blue-400 drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]' : ''} />
            <span className={`text-sm font-medium ${item.active ? 'text-white' : ''}`}>{item.label}</span>
          </button>
        ))}
      </div>

      {/* Settings */}
      <div className="mt-auto">
        <button disabled className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-ocean-750 cursor-not-allowed w-full">
          <Settings size={18} />
          <span className="text-sm font-medium">Settings</span>
        </button>
      </div>
    </nav>
  );
}

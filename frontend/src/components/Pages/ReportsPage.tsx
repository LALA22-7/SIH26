import { useState } from 'react';
import { CYCLONES } from '../../data/cyclones';
import { ChevronDown, ChevronUp, Wind, Gauge, MapPin, Calendar, Anchor, AlertTriangle, Lightbulb } from 'lucide-react';

// Real-world destruction data for each cyclone
const DESTRUCTION_DATA: Record<string, { deaths: string; damage: string; affected: string; summary: string }> = {
  biparjoy_2023: {
    deaths: '2 confirmed',
    damage: '$2.8 billion',
    affected: '~900,000 evacuated from Gujarat coast',
    summary: 'Biparjoy was the longest-lasting Arabian Sea cyclone in decades. It caused widespread flooding across Gujarat and Rajasthan, destroyed fishing infrastructure along the Saurashtra coast, and disrupted shipping lanes for over a week. The Jakhau salt works were severely damaged.',
  },
  amphan_2020: {
    deaths: '128 confirmed',
    damage: '$13.6 billion (costliest ever in North Indian Ocean)',
    affected: '~4.9 million displaced in India & Bangladesh',
    summary: 'Super Cyclone Amphan devastated the Sundarbans, flattened parts of Kolkata, and destroyed telecommunications infrastructure across West Bengal. The storm surge reached 5 meters in coastal areas. It was the first super cyclone in the Bay of Bengal since 1999.',
  },
  fani_2019: {
    deaths: '89 confirmed',
    damage: '$8.1 billion',
    affected: '~28 million people in Odisha',
    summary: 'FANI was the strongest cyclone to hit Odisha in 20 years. It destroyed 500,000 houses, uprooted millions of trees, and caused massive power outages lasting weeks. However, India\'s largest-ever evacuation (1.2 million people in 48 hours) saved thousands of lives.',
  },
  tauktae_2021: {
    deaths: '174 confirmed (including 86 from Barge P-305 sinking)',
    damage: '$2.1 billion',
    affected: '~200,000 evacuated across Gujarat, Goa, Maharashtra',
    summary: 'Tauktae intensified extremely rapidly near the coast, catching offshore oil platforms off guard. The ONGC Barge P-305 capsized off Mumbai, killing 86 workers. The storm caused severe damage along the entire western coast from Kerala to Gujarat.',
  },
  ockhi_2017: {
    deaths: '218+ confirmed (mostly fishermen at sea)',
    damage: '$5.2 billion',
    affected: '~14,000 fishing boats damaged or destroyed',
    summary: 'Ockhi is the deadliest gap case in recent Indian history. It formed rapidly near Sri Lanka on Nov 29, but IMD\'s first cyclone watch came only on Dec 1 — by then, thousands of fishermen from Kerala and Tamil Nadu were already trapped at sea. 218 lives were lost, many whose bodies were never recovered.',
  },
  hudhud_2014: {
    deaths: '124 confirmed',
    damage: '$7 billion',
    affected: '~920,000 evacuated in Andhra Pradesh',
    summary: 'Hudhud made a direct hit on Visakhapatnam with 185 km/h winds, destroying the iconic Kailasagiri hilltop garden and flattening large parts of the city. The port suffered extensive damage. The storm intensified from a severe cyclone to extremely severe in just 24 hours.',
  },
  phailin_2013: {
    deaths: '45 confirmed',
    damage: '$4.5 billion',
    affected: '~13 million in Odisha & Andhra Pradesh',
    summary: 'Phailin was one of the strongest storms to hit India in 14 years, with 215 km/h winds. However, India\'s massive evacuation operation (nearly 1 million people) kept deaths remarkably low. Extensive crop damage occurred across Odisha.',
  },
};

export function ReportsPage() {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="w-full h-full overflow-y-auto custom-scrollbar">
      <div className="max-w-4xl mx-auto px-6 py-10 flex flex-col gap-8">

        {/* Header */}
        <section className="text-center mb-4">
          <h1 className="text-3xl font-bold text-white mb-3">Cyclone Reports</h1>
          <p className="text-text-secondary text-sm max-w-2xl mx-auto leading-relaxed">
            Detailed analysis of the 7 historical cyclones in our database — the destruction they caused 
            and how CycloneWatch's early detection could have made a difference.
          </p>
        </section>

        {/* Cyclone Cards */}
        {CYCLONES.map((cyclone) => {
          const isExpanded = expandedId === cyclone.id;
          const destruction = DESTRUCTION_DATA[cyclone.id];

          return (
            <div
              key={cyclone.id}
              className={`glass-card rounded-2xl overflow-hidden border transition-all duration-300 ${
                isExpanded ? 'border-cyan-500/30 shadow-[0_0_20px_rgba(79,195,224,0.1)]' : 'border-ocean-800'
              }`}
            >
              {/* Header — always visible */}
              <button
                onClick={() => setExpandedId(isExpanded ? null : cyclone.id)}
                className="w-full flex items-center justify-between p-5 hover:bg-ocean-800/30 transition-colors text-left"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-lg font-bold ${
                    cyclone.basin === 'Arabian Sea' 
                      ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                      : 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                  }`}>
                    {cyclone.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white tracking-wide">{cyclone.name}</h3>
                    <p className="text-[11px] text-text-muted mt-0.5">
                      {cyclone.year} · {cyclone.basin} · Landfall: {cyclone.landfallRegion}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {cyclone.imdGapCase && (
                    <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded text-[8px] font-bold tracking-widest uppercase bg-alert/10 text-alert border border-alert/25">
                      IMD GAP CASE
                    </span>
                  )}
                  {isExpanded ? <ChevronUp size={18} className="text-text-muted" /> : <ChevronDown size={18} className="text-text-muted" />}
                </div>
              </button>

              {/* Expanded content */}
              {isExpanded && (
                <div className="px-5 pb-6 flex flex-col gap-5 border-t border-ocean-800 pt-5">
                  {/* Stats grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                      { icon: Wind, label: 'Peak Wind', value: `${cyclone.peakWind} km/h`, color: 'text-alert' },
                      { icon: Gauge, label: 'Min Pressure', value: `${cyclone.minPressure} hPa`, color: 'text-cyan-400' },
                      { icon: MapPin, label: 'Track Length', value: `${cyclone.trackLengthKm.toLocaleString()} km`, color: 'text-purple-400' },
                      { icon: Calendar, label: 'Year', value: `${cyclone.year}`, color: 'text-text-primary' },
                    ].map((stat, i) => (
                      <div key={i} className="flex flex-col items-center p-3 rounded-xl bg-ocean-900/50 border border-ocean-800">
                        <stat.icon size={16} className="text-text-muted mb-1" />
                        <span className={`text-lg font-bold font-mono ${stat.color}`}>{stat.value}</span>
                        <span className="text-[9px] text-text-faint uppercase tracking-widest">{stat.label}</span>
                      </div>
                    ))}
                  </div>

                  {/* Destruction */}
                  {destruction && (
                    <div className="rounded-xl p-5 bg-alert/5 border border-alert/20">
                      <div className="flex items-center gap-2 mb-3">
                        <AlertTriangle size={16} className="text-alert" />
                        <h4 className="text-sm font-bold text-alert tracking-widest uppercase">Destruction Caused</h4>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
                        <div>
                          <span className="text-[9px] text-text-faint uppercase tracking-widest block">Deaths</span>
                          <span className="text-sm text-alert font-semibold">{destruction.deaths}</span>
                        </div>
                        <div>
                          <span className="text-[9px] text-text-faint uppercase tracking-widest block">Economic Damage</span>
                          <span className="text-sm text-white font-semibold">{destruction.damage}</span>
                        </div>
                        <div>
                          <span className="text-[9px] text-text-faint uppercase tracking-widest block">People Affected</span>
                          <span className="text-sm text-text-secondary font-semibold">{destruction.affected}</span>
                        </div>
                      </div>
                      <p className="text-text-secondary text-[12px] leading-relaxed">{destruction.summary}</p>
                    </div>
                  )}

                  {/* What if CycloneWatch existed? */}
                  {cyclone.imdGapNote && (
                    <div className="rounded-xl p-5 bg-cyan-500/5 border border-cyan-500/20">
                      <div className="flex items-center gap-2 mb-3">
                        <Lightbulb size={16} className="text-cyan-400" />
                        <h4 className="text-sm font-bold text-cyan-400 tracking-widest uppercase">What if CycloneWatch Existed?</h4>
                      </div>
                      <p className="text-text-secondary text-[12px] leading-relaxed">
                        {cyclone.imdGapNote}
                      </p>
                      <p className="text-text-muted text-[11px] mt-3 italic">
                        In simple terms: Our AI would have spotted the storm's dangerous structural changes in satellite images 
                        <span className="text-cyan-400 font-semibold"> hours before the official warnings</span> were issued, 
                        giving emergency responders and coastal communities more time to evacuate and prepare.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}

        <p className="text-center text-text-faint text-xs pb-8">
          Data sources: IMD/RSMC New Delhi, IBTrACS v4, NDMA post-disaster reports
        </p>
      </div>
    </div>
  );
}

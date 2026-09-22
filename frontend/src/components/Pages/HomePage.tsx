import { useCycloneStore } from '../../store/useCycloneStore';
import { Activity, Clock, Shield, Zap, Target, Eye, BarChart3, ArrowRight } from 'lucide-react';

export function HomePage() {
  const { setActivePage, setMode } = useCycloneStore();

  return (
    <div className="w-full h-full overflow-y-auto custom-scrollbar">
      <div className="max-w-5xl mx-auto px-6 py-10 flex flex-col gap-16">

        {/* ── Hero ── */}
        <section className="text-center flex flex-col items-center gap-6">
          <div className="flex items-center gap-3 mb-2">
            <img src="/logo.png" alt="CycloneWatch" className="w-14 h-14 rounded-2xl shadow-[0_0_30px_rgba(79,195,224,0.4)]" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-white leading-tight">
            CycloneWatch
          </h1>
          <p className="text-lg text-cyan-400/80 font-medium tracking-widest uppercase">
            AI-Powered Cyclone Early Warning System
          </p>
          <p className="text-text-secondary text-base max-w-2xl leading-relaxed">
            A deep-learning platform that analyzes satellite imagery in real-time to classify cyclone structural patterns, 
            predict storm trajectories, and provide early warnings — filling critical gaps in traditional forecasting.
          </p>
          <div className="flex gap-4 mt-4 flex-wrap justify-center">
            <button
              onClick={() => { setMode('LIVE'); setActivePage('live'); }}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold 
                shadow-[0_0_20px_rgba(79,195,224,0.3)] hover:shadow-[0_0_30px_rgba(79,195,224,0.5)] transition-all 
                flex items-center gap-2 text-sm"
            >
              <Activity size={16} /> Explore Live Map <ArrowRight size={14} />
            </button>
            <button
              onClick={() => { setMode('HISTORICAL'); setActivePage('historical'); }}
              className="px-6 py-3 rounded-xl glass-card border border-ocean-700 text-text-primary font-semibold 
                hover:bg-ocean-800/50 transition-all flex items-center gap-2 text-sm"
            >
              <Clock size={16} /> View Historical Replay <ArrowRight size={14} />
            </button>
          </div>
        </section>

        {/* ── The Problem ── */}
        <section className="glass-card rounded-2xl p-8 border border-alert/20 bg-alert/5">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-alert/20 flex items-center justify-center">
              <Shield size={20} className="text-alert" />
            </div>
            <h2 className="text-2xl font-bold text-white">The Problem</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="flex flex-col gap-3">
              <h3 className="text-sm font-bold text-alert tracking-widest uppercase">Delayed Warnings Kill</h3>
              <p className="text-text-secondary text-sm leading-relaxed">
                In November 2017, Cyclone Ockhi formed rapidly off the coast of Sri Lanka. 
                India Meteorological Department (IMD) issued its first cyclone watch only on December 1st — 
                <span className="text-alert font-semibold"> 36-48 hours too late</span>. 
                By then, 218 fishermen had already been lost at sea with zero warning.
              </p>
            </div>
            <div className="flex flex-col gap-3">
              <h3 className="text-sm font-bold text-alert tracking-widest uppercase">Human Bottleneck</h3>
              <p className="text-text-secondary text-sm leading-relaxed">
                Traditional cyclone analysis relies on trained meteorologists manually interpreting satellite images 
                using the Dvorak technique — a subjective process that takes hours per assessment and varies between analysts. 
                Rapid intensification events are <span className="text-alert font-semibold">routinely underestimated</span> by 
                numerical weather prediction (NWP) models.
              </p>
            </div>
          </div>
        </section>

        {/* ── Our Solution ── */}
        <section className="glass-card rounded-2xl p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/20 flex items-center justify-center">
              <Zap size={20} className="text-cyan-400" />
            </div>
            <h2 className="text-2xl font-bold text-white">Our Solution</h2>
          </div>
          <p className="text-text-secondary text-sm leading-relaxed mb-6">
            CycloneWatch is an AI-powered satellite imagery analysis system that automatically detects, classifies, 
            and tracks cyclone structural patterns in near real-time. Instead of waiting for manual analysis, 
            our deep learning model processes each satellite frame in <span className="text-cyan-400 font-bold">12 milliseconds</span> — 
            providing instant structural classification the moment a new image arrives.
          </p>
          <div className="grid md:grid-cols-3 gap-4">
            {[
              { icon: Eye, title: 'Pattern Recognition', desc: 'Classifies cyclone morphology into 5 structural patterns: Eye, Banding, Curved Band, Shear-Affected, Disorganized' },
              { icon: Target, title: 'Center Tracking', desc: 'Estimates storm center coordinates from thermal imagery, enabling trajectory prediction at T+12h and T+24h' },
              { icon: BarChart3, title: 'Gap Detection', desc: 'Identifies structural signatures of rapid intensification before official bulletins — like the Ockhi case' },
            ].map((item, i) => (
              <div key={i} className="flex flex-col gap-2 p-4 rounded-xl bg-ocean-900/50 border border-ocean-800">
                <item.icon size={20} className="text-cyan-400" />
                <h4 className="text-sm font-bold text-white">{item.title}</h4>
                <p className="text-[11px] text-text-muted leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Why CycloneWatch is Better ── */}
        <section className="glass-card rounded-2xl p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-confidence/20 flex items-center justify-center">
              <BarChart3 size={20} className="text-confidence" />
            </div>
            <h2 className="text-2xl font-bold text-white">Traditional NWP vs CycloneWatch</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ocean-800">
                  <th className="text-left py-3 px-4 text-text-muted font-medium tracking-widest uppercase text-[10px]">Aspect</th>
                  <th className="text-left py-3 px-4 text-text-muted font-medium tracking-widest uppercase text-[10px]">Traditional (NWP/Dvorak)</th>
                  <th className="text-left py-3 px-4 text-cyan-400 font-medium tracking-widest uppercase text-[10px]">CycloneWatch AI</th>
                </tr>
              </thead>
              <tbody className="text-text-secondary">
                {[
                  ['Analysis Speed', 'Hours per assessment', '12ms per frame'],
                  ['Subjectivity', 'Varies between analysts', 'Consistent & repeatable'],
                  ['Rapid Intensification', 'Routinely underestimated', 'Pattern-detected early'],
                  ['Coverage', 'Manual monitoring gaps', '24/7 automated scanning'],
                  ['Early Warning Lead', 'Standard bulletin cycle', 'Up to 36h earlier detection'],
                  ['Cost', 'Supercomputer infrastructure', 'Runs on a single GPU/CPU'],
                ].map(([aspect, trad, cw], i) => (
                  <tr key={i} className="border-b border-ocean-800/50">
                    <td className="py-3 px-4 font-medium text-text-primary">{aspect}</td>
                    <td className="py-3 px-4">{trad}</td>
                    <td className="py-3 px-4 text-cyan-400 font-medium">{cw}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* ── Quick Stats ── */}
        <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { value: '78.3%', label: 'Pattern Accuracy', color: 'text-confidence' },
            { value: '12ms', label: 'Inference Speed', color: 'text-cyan-400' },
            { value: '7', label: 'Cyclones Analyzed', color: 'text-ir' },
            { value: '51', label: 'Pipeline Ready', color: 'text-purple-400' },
          ].map((stat, i) => (
            <div key={i} className="glass-card rounded-xl p-5 text-center flex flex-col gap-1">
              <span className={`text-3xl font-bold font-mono ${stat.color}`}>{stat.value}</span>
              <span className="text-[10px] text-text-muted uppercase tracking-widest font-semibold">{stat.label}</span>
            </div>
          ))}
        </section>

        {/* ── Footer note ── */}
        <p className="text-center text-text-faint text-xs pb-8">
          Built for Smart India Hackathon 2026 · Problem Statement PS70
        </p>
      </div>
    </div>
  );
}

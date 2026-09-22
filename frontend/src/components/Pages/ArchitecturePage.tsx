import { ArrowDown } from 'lucide-react';

const PIPELINE_STEPS = [
  { title: 'Satellite Data Ingestion', detail: 'GridSat-B1 infrared (IR) and water vapor (WV) satellite imagery is downloaded from NOAA archives via the Kaggle pipeline. Each frame covers the Indian Ocean basin at ~8km resolution, captured every 3 hours.', color: 'text-cyan-400', bg: 'bg-cyan-500/10 border-cyan-500/30' },
  { title: 'Preprocessing & Normalization', detail: 'Raw NetCDF files are cropped to the North Indian Ocean (0–35°N, 30–110°E), resampled to 128×128 pixels, and normalized to [0,1]. Output: .npz tensors with shape [2, 128, 128] — two channels (IR brightness temperature + WV).', color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/30' },
  { title: 'Ground Truth Labeling', detail: 'IBTrACS best-track data provides verified storm center coordinates and timestamps. Each frame is labeled with one of 5 structural patterns based on the Dvorak technique: Eye, Banding, Curved Band, Shear-Affected, or Disorganized.', color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/30' },
  { title: 'CNN Feature Extraction', detail: 'A custom CycloneCNN takes [2, 128, 128] input tensors through 4 convolutional blocks (Conv2d → BatchNorm → ReLU → MaxPool), progressively extracting spatial features from edges → textures → spiral arms → eye structure.', color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/30' },
  { title: 'GRU Temporal Modeling', detail: 'A CycloneTemporalModel wraps the CNN with a GRU (Gated Recurrent Unit) layer. It processes sequences of frames to learn temporal evolution patterns — how a disorganized cloud mass transitions into organized banding and eventually forms an eye.', color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/30' },
  { title: 'Multi-Head Output', detail: 'The model outputs: (1) Pattern classification — 5-class softmax, (2) Center coordinates — [lat, lon] regression, (3) T+12h and T+24h position predictions via temporal extrapolation. All in ~12ms per frame.', color: 'text-confidence', bg: 'bg-confidence/10 border-confidence/30' },
];

const TAXONOMY = [
  { pattern: 'Eye', emoji: '🌀', desc: 'A clear, circular eye has formed at the center. The storm has reached its most organized and dangerous state. Wind speeds typically exceed 120 km/h. This is the easiest pattern for the AI to detect (F1: 1.00).', color: 'text-red-400', border: 'border-red-500/30' },
  { pattern: 'Banding', emoji: '🌊', desc: 'Dense spiral rain bands are wrapping around the center. The storm is intensifying and organizing its convection. This is a precursor to eye formation and indicates significant strengthening ahead (F1: 0.79).', color: 'text-orange-400', border: 'border-orange-500/30' },
  { pattern: 'Curved Band', emoji: '🌙', desc: 'A single curved convective band is partially encircling the center. The storm is in its developing phase — not yet fully organized but showing clear cyclonic structure. This is the hardest pattern to classify (F1: 0.55).', color: 'text-yellow-400', border: 'border-yellow-500/30' },
  { pattern: 'Shear-Affected', emoji: '💨', desc: 'Environmental wind shear is tilting the storm, pushing the cloud mass away from the low-level center. The convection appears lopsided or displaced. This indicates the storm may weaken or fail to intensify (F1: 0.80).', color: 'text-purple-400', border: 'border-purple-500/30' },
  { pattern: 'Disorganized', emoji: '☁️', desc: 'The cloud structure is scattered with no clear cyclonic pattern. This is the initial stage of development or a system that has weakened significantly. Most common class in the training data (F1: 0.88).', color: 'text-gray-400', border: 'border-gray-500/30' },
];

export function ArchitecturePage() {
  return (
    <div className="w-full h-full overflow-y-auto custom-scrollbar">
      <div className="max-w-4xl mx-auto px-6 py-10 flex flex-col gap-12">

        {/* Header */}
        <section className="text-center">
          <h1 className="text-3xl font-bold text-white mb-3">How CycloneWatch Works</h1>
          <p className="text-text-secondary text-sm max-w-2xl mx-auto leading-relaxed">
            From raw satellite imagery to structural pattern classification in 12 milliseconds — 
            here's the complete data pipeline and model architecture.
          </p>
        </section>

        {/* ── Pipeline Flow ── */}
        <section>
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <span className="w-8 h-8 rounded-lg bg-cyan-500/20 flex items-center justify-center text-cyan-400 text-sm font-bold">1</span>
            Data Pipeline & Model Architecture
          </h2>
          <div className="flex flex-col gap-3">
            {PIPELINE_STEPS.map((step, i) => (
              <div key={i}>
                <div className={`rounded-xl p-5 border ${step.bg} transition-all`}>
                  <h3 className={`text-sm font-bold ${step.color} tracking-wide uppercase mb-2`}>{step.title}</h3>
                  <p className="text-text-secondary text-[12px] leading-relaxed">{step.detail}</p>
                </div>
                {i < PIPELINE_STEPS.length - 1 && (
                  <div className="flex justify-center py-1">
                    <ArrowDown size={18} className="text-ocean-700" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* ── 5-Class Taxonomy ── */}
        <section>
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <span className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center text-purple-400 text-sm font-bold">2</span>
            The 5-Class Structural Taxonomy
          </h2>
          <p className="text-text-secondary text-sm mb-6 leading-relaxed">
            Every satellite frame is classified into one of five cyclone structural patterns, inspired by the 
            <span className="text-white font-medium"> Dvorak Technique</span> used by meteorological agencies worldwide.
          </p>
          <div className="grid gap-4">
            {TAXONOMY.map((t, i) => (
              <div key={i} className={`glass-card rounded-xl p-5 border ${t.border} flex gap-4 items-start`}>
                <span className="text-3xl flex-shrink-0">{t.emoji}</span>
                <div>
                  <h3 className={`text-sm font-bold ${t.color} tracking-wide`}>{t.pattern}</h3>
                  <p className="text-text-secondary text-[12px] leading-relaxed mt-1">{t.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Training Details ── */}
        <section className="glass-card rounded-2xl p-8">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <span className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400 text-sm font-bold">3</span>
            Training Details
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="metric-label text-text-muted mb-3">CURRENT MODEL</h3>
              <div className="flex flex-col gap-2">
                {[
                  ['Training Events', '7 cyclones'],
                  ['Total Frames', '423 labeled'],
                  ['Input Shape', '[2, 128, 128] (IR + WV)'],
                  ['Loss Function', 'Class-weighted Cross-Entropy'],
                  ['Optimizer', 'Adam (lr=1e-4)'],
                  ['Accuracy', '78.3% (5-class)'],
                  ['T+12h MAE', '255.5 km'],
                  ['Inference', '~12ms / frame (CPU)'],
                ].map(([k, v], i) => (
                  <div key={i} className="flex justify-between items-center py-1.5 border-b border-ocean-800/50">
                    <span className="text-text-secondary text-xs">{k}</span>
                    <span className="text-white text-xs font-mono">{v}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="metric-label text-text-muted mb-3">NEXT UPGRADE</h3>
              <div className="flex flex-col gap-2">
                {[
                  ['Training Events', '51 cyclones (Kaggle ready)'],
                  ['Input Channels', '2 → 6 (add ERA5 atmo)'],
                  ['Sequence Length', 'T=5 sliding window'],
                  ['Architecture', 'ConvLSTM temporal heads'],
                  ['Target Accuracy', '≥ 88%'],
                  ['Target T+12h MAE', '≤ 120 km'],
                  ['Target T+24h MAE', '≤ 100 km'],
                  ['Impact Heads', 'M+G+S multi-task'],
                ].map(([k, v], i) => (
                  <div key={i} className="flex justify-between items-center py-1.5 border-b border-ocean-800/50">
                    <span className="text-text-secondary text-xs">{k}</span>
                    <span className="text-cyan-400 text-xs font-mono">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <p className="text-center text-text-faint text-xs pb-8">
          CycloneWatch ML Pipeline · PyTorch · GridSat-B1 · IBTrACS v4
        </p>
      </div>
    </div>
  );
}

import { motion } from 'framer-motion';

interface ThresholdMetricProps {
  label: string;
  value: number;
  unit: string;
  baseline?: number;
  trend?: string; // e.g. "↑", "↓" or specific text
  secondaryLabel?: string;
  secondaryValue?: number | string;
  secondaryUnit?: string;
}

export function ThresholdMetric({ 
  label, 
  value, 
  unit, 
  baseline, 
  trend,
  secondaryLabel,
  secondaryValue,
  secondaryUnit 
}: ThresholdMetricProps) {
  const isHazardous = baseline !== undefined && value >= baseline;

  return (
    <div className="flex flex-col py-3 border-b border-glass-border/30 last:border-0 relative overflow-hidden group">
      {/* Background glow when hazardous */}
      <motion.div 
        initial={false}
        animate={{ opacity: isHazardous ? 0.05 : 0 }}
        className="absolute inset-0 bg-danger pointer-events-none"
      />
      
      <div className="flex justify-between items-start mb-1">
        <span className="text-[10px] tracking-[0.15em] font-medium text-text-muted">{label}</span>
        {isHazardous && (
          <motion.span 
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-[9px] tracking-widest font-bold text-danger flex items-center"
          >
            HAZARDOUS <span className="ml-1 text-[8px]">▲</span>
          </motion.span>
        )}
      </div>

      <div className="flex items-baseline space-x-1">
        <motion.span 
          animate={{ color: isHazardous ? '#FF4D4D' : '#F1F4F7' }}
          className="text-2xl font-light font-mono tracking-tight"
        >
          {value}
        </motion.span>
        <span className={`text-xs font-medium ${isHazardous ? 'text-danger/80' : 'text-text-secondary'}`}>
          {unit}
        </span>
        
        {trend && (
          <span className={`ml-2 text-[10px] font-mono ${isHazardous ? 'text-danger/70' : 'text-text-muted'}`}>
            {trend}
          </span>
        )}
      </div>

      {secondaryLabel && (
        <div className="flex items-center space-x-2 mt-1">
          <span className="text-[9px] uppercase tracking-widest text-text-muted/70">{secondaryLabel}</span>
          <span className="text-[10px] font-mono text-text-secondary">{secondaryValue} {secondaryUnit}</span>
        </div>
      )}

      {/* Minimal trend line visual (static mockup) */}
      <div className="mt-2 h-6 w-full flex items-end space-x-0.5 opacity-60">
        {[0.4, 0.5, 0.7, 0.8, 0.9, 1.0, 0.9, 0.95].map((h, i) => (
          <motion.div 
            key={i}
            animate={{ backgroundColor: isHazardous && i > 4 ? '#FF4D4D' : 'rgba(255,255,255,0.2)' }}
            className="flex-1 rounded-t-sm"
            style={{ height: `${h * 100}%` }}
          />
        ))}
      </div>
    </div>
  );
}

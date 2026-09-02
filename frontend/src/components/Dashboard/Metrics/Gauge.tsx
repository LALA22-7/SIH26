import { motion } from 'framer-motion';

interface GaugeProps {
  value: number;
  max: number;
  isHazardous: boolean;
}

export function Gauge({ value, max, isHazardous }: GaugeProps) {
  const radius = 40;
  const circumference = Math.PI * radius;
  const strokeDashoffset = circumference - (Math.min(value, max) / max) * circumference;

  return (
    <div className="relative w-24 h-12 flex items-end justify-center overflow-hidden">
      <svg className="w-full h-[200%] absolute top-0" viewBox="0 0 100 100">
        {/* Background track */}
        <path 
          d="M 10 50 A 40 40 0 0 1 90 50" 
          fill="none" 
          stroke="#2d3342" 
          strokeWidth="6" 
          strokeLinecap="round"
        />
        {/* Value track */}
        <motion.path 
          d="M 10 50 A 40 40 0 0 1 90 50" 
          fill="none" 
          stroke={isHazardous ? "#FF4D4D" : "#d1d5db"} 
          strokeWidth="6" 
          strokeLinecap="round"
          strokeDasharray={circumference}
          animate={{ strokeDashoffset: Math.max(0, strokeDashoffset) }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
        {/* Needle */}
        <motion.line 
          x1="50" y1="50" x2="50" y2="15" 
          stroke="#fff" strokeWidth="2" strokeLinecap="round"
          style={{ transformOrigin: "50px 50px" }}
          animate={{ rotate: (Math.min(value, max) / max) * 180 - 90 }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
        <circle cx="50" cy="50" r="4" fill="#fff" />
      </svg>
    </div>
  );
}

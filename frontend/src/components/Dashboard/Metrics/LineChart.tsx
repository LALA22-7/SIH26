import { motion } from 'framer-motion';

export function LineChart({ data, isHazardous }: { data: number[], isHazardous: boolean }) {
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = max - min;
  
  const w = 200;
  const h = 50;
  const dx = w / (data.length - 1 || 1);
  
  const points = data.map((val, i) => {
    const x = i * dx;
    const y = h - ((val - min) / (range || 1)) * (h - 10) - 5;
    return `${x},${y}`;
  });

  const pathD = `M ${points.join(' L ')}`;
  const areaD = `${pathD} L ${w},${h} L 0,${h} Z`;
  const strokeColor = isHazardous ? "#FF4D4D" : "#5b6475";

  return (
    <svg className="w-full h-full" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="chartGradientHazard" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#FF4D4D" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#FF4D4D" stopOpacity="0.0" />
        </linearGradient>
        <linearGradient id="chartGradientNormal" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#5b6475" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#5b6475" stopOpacity="0.0" />
        </linearGradient>
      </defs>
      
      {/* Grid lines */}
      <line x1="0" y1="25" x2={w} y2="25" stroke="#2d3342" strokeWidth="1" strokeDasharray="2 2" />
      
      <path d={areaD} fill={isHazardous ? "url(#chartGradientHazard)" : "url(#chartGradientNormal)"} />
      <motion.path 
        d={pathD} 
        fill="none" 
        stroke={strokeColor} 
        strokeWidth="2" 
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1 }}
      />
      
      {points.length > 0 && (
        <circle 
          cx={points[points.length-1].split(',')[0]} 
          cy={points[points.length-1].split(',')[1]} 
          r="3" 
          fill="#fff" 
        />
      )}
    </svg>
  );
}

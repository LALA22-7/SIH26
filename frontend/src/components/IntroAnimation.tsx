import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';
import { useCycloneStore } from '../store/useCycloneStore';

export function IntroAnimation() {
  const setIntroComplete = useCycloneStore(state => state.setIntroComplete);
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    // Phase 1: Grid point (0.5s)
    const t1 = setTimeout(() => setPhase(1), 500);
    // Phase 2: Wordmark (1.2s)
    const t2 = setTimeout(() => setPhase(2), 1200);
    // Phase 3: Vortex (1.8s)
    const t3 = setTimeout(() => setPhase(3), 1800);
    // Phase 4: Complete (2.5s)
    const t4 = setTimeout(() => {
      setPhase(4);
      setTimeout(() => setIntroComplete(true), 800); // fade out time
    }, 2500);

    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); clearTimeout(t4); };
  }, [setIntroComplete]);

  return (
    <AnimatePresence>
      {phase < 4 && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-base-900"
          exit={{ opacity: 0, filter: 'blur(10px)' }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
        >
          {/* Phase 1: Coordinate / Grid point */}
          <motion.div
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="absolute w-1 h-1 bg-text-main rounded-full shadow-[0_0_8px_rgba(255,255,255,0.8)]"
          />

          {/* Phase 3: Vortex Scan */}
          {phase >= 3 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8, rotate: -90 }}
              animate={{ opacity: 0.15, scale: 1, rotate: 0 }}
              transition={{ duration: 1, ease: "easeOut" }}
              className="absolute w-[400px] h-[400px] border-[0.5px] border-text-main rounded-full border-dashed opacity-20"
              style={{ animation: 'spin 10s linear infinite' }}
            />
          )}

          {/* Phase 2: Typography */}
          <div className="relative z-10 flex flex-col items-center justify-center mt-12">
            <motion.h1
              initial={{ opacity: 0, filter: 'blur(8px)', y: 10 }}
              animate={phase >= 2 ? { opacity: 1, filter: 'blur(0px)', y: 0 } : {}}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="text-4xl font-light tracking-[0.3em] text-text-main mb-2"
            >
              CYCLOWATCH
            </motion.h1>
            
            <motion.p
              initial={{ opacity: 0, filter: 'blur(4px)' }}
              animate={phase >= 2 ? { opacity: 1, filter: 'blur(0px)' } : {}}
              transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
              className="text-xs font-medium tracking-[0.4em] text-text-muted"
            >
              CYCLONE PREDICTION SYSTEM
            </motion.p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

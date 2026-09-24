/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // ── Ocean palette ────────────────────────────────────────────────────
        // Dark backgrounds for the command-center aesthetic
        ocean: {
          950: '#0A121C',
          900: '#101B28',
          850: '#152436',
          800: '#223347',
          750: '#2A3F56',
          700: '#3A5068',
        },

        // ── Signal colours ───────────────────────────────────────────────────
        ir: '#FF7A45',         // IR channel / active alerts
        wv: '#4FC3E0',         // Water vapour channel
        vis: '#E7EEF4',        // Visible channel
        confidence: '#6FE3B4', // Confidence / positive readouts
        alert: '#FF5C5C',      // High-severity alerts
        accent: '#6495ED',     // Interactive / selected states

        // ── Text — WCAG AA compliant on ocean-950 (#0A121C) ─────────────────
        // All ratios verified against #0A121C background
        text: {
          primary: '#E7EEF4',    // ~14.5:1 — headings, primary content
          secondary: '#A8B5C4',  // ~7.2:1  — body text (AA pass)
          muted: '#8A9AB0',      // ~5.0:1  — labels, captions (AA pass)
          faint: '#6B7D94',      // ~3.6:1  — decorative only, NOT for readable text
        },

        // ── Legacy aliases ───────────────────────────────────────────────────
        danger: { DEFAULT: '#FF5C5C', critical: '#FF3B30' },
        base: { 900: '#0A121C', 800: '#101B28', 700: '#152436' },
        glass: {
          bg: 'rgba(16, 27, 40, 0.60)',
          border: 'rgba(255, 255, 255, 0.08)',
          highlight: 'rgba(255, 255, 255, 0.04)',
        },
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      boxShadow: {
        glass: '0 8px 32px 0 rgba(0,0,0,0.45)',
        glow: '0 0 20px rgba(100,149,237,0.25)',
        'glow-ir': '0 0 14px rgba(255,122,69,0.35)',
        'glow-conf': '0 0 10px rgba(111,227,180,0.30)',
      },
      backdropBlur: {
        xs: '4px',
        sm: '8px',
        md: '16px',
        lg: '24px',
        xl: '32px',
      },
    },
  },
  plugins: [],
};

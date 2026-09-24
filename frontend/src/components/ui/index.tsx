// ─────────────────────────────────────────────────────────────────────────────
// CycloneWatch — Reusable UI primitives
//
// Extracted from the 410-line MetricsPanel.tsx god component.
// Each component is small, typed, and accessible.
// ─────────────────────────────────────────────────────────────────────────────

import type { ReactNode } from 'react';

// ── Badge ───────────────────────────────────────────────────────────────────

export type BadgeVariant = 'default' | 'live' | 'historical' | 'ml' | 'alert';

const BADGE_STYLES: Record<BadgeVariant, string> = {
  default: 'bg-ocean-800 text-text-faint',
  live: 'bg-ir/10 text-ir border border-ir/25',
  historical: 'bg-ocean-800 text-text-muted',
  ml: 'bg-accent/10 text-accent border border-accent/25',
  alert: 'bg-alert/10 text-alert border border-alert/25',
};

export function Badge({
  label,
  variant = 'default',
}: {
  label: string;
  variant?: BadgeVariant;
}) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold tracking-[0.12em] uppercase ${BADGE_STYLES[variant]}`}
    >
      {label}
    </span>
  );
}

// ── Section Header ──────────────────────────────────────────────────────────

export function SectionHeader({
  title,
  badge,
  badgeVariant,
  id,
}: {
  title: string;
  badge?: string;
  badgeVariant?: BadgeVariant;
  id?: string;
}) {
  return (
    <div className="flex items-center justify-between mb-3">
      <span className="metric-label text-text-muted" id={id}>
        {title}
      </span>
      {badge && <Badge label={badge} variant={badgeVariant} />}
    </div>
  );
}

// ── Metric Cell ─────────────────────────────────────────────────────────────

export function MetricCell({
  label,
  value,
  unit,
  color = 'text-text-primary',
  unavailable = false,
}: {
  label: string;
  value?: string | number | null;
  unit?: string;
  color?: string;
  unavailable?: boolean;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="metric-label">{label}</span>
      {unavailable || value == null ? (
        <span className="text-xs text-text-faint font-mono">
          DATA UNAVAILABLE
        </span>
      ) : (
        <div className="flex items-baseline gap-0.5">
          <span className={`metric-value-sm font-mono ${color}`}>{value}</span>
          {unit && <span className="metric-unit">{unit}</span>}
        </div>
      )}
    </div>
  );
}

// ── Metric Grid ─────────────────────────────────────────────────────────────

export function MetricGrid({ children }: { children: ReactNode }) {
  return <div className="grid grid-cols-2 gap-x-4 gap-y-3">{children}</div>;
}

// ── Glass Card Wrapper ──────────────────────────────────────────────────────

export function GlassCard({
  children,
  className = '',
  borderAccent,
}: {
  children: ReactNode;
  className?: string;
  borderAccent?: string;
}) {
  return (
    <div
      className={`glass-card rounded-xl p-4 ${borderAccent ? `border-t-2 ${borderAccent}` : ''} ${className}`}
    >
      {children}
    </div>
  );
}

// ── Icon Button (accessible) ────────────────────────────────────────────────

export function IconButton({
  onClick,
  label,
  children,
  className = '',
  active = false,
}: {
  onClick: () => void;
  label: string;
  children: ReactNode;
  className?: string;
  active?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      aria-label={label}
      title={label}
      className={`w-8 h-8 flex items-center justify-center rounded-lg transition-colors
        focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent
        ${active ? 'text-confidence' : 'text-text-muted hover:text-text-primary'}
        ${className}`}
    >
      {children}
    </button>
  );
}

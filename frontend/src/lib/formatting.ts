// ─────────────────────────────────────────────────────────────────────────────
// CycloneWatch — Shared formatting utilities
//
// Single source for date, number, and label formatting used across the UI.
// Uses Intl.DateTimeFormat for locale-aware, timezone-correct output.
// ─────────────────────────────────────────────────────────────────────────────

const IST_DATE_TIME = new Intl.DateTimeFormat('en-IN', {
  timeZone: 'Asia/Kolkata',
  year: 'numeric',
  month: 'short',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
});

const IST_TIME_SHORT = new Intl.DateTimeFormat('en-IN', {
  timeZone: 'Asia/Kolkata',
  hour: '2-digit',
  minute: '2-digit',
});

const IST_DATE_SHORT = new Intl.DateTimeFormat('en-GB', {
  timeZone: 'Asia/Kolkata',
  day: '2-digit',
  month: 'short',
});

const IST_TIME_HMS = new Intl.DateTimeFormat('en-GB', {
  timeZone: 'Asia/Kolkata',
  hour: '2-digit',
  minute: '2-digit',
});

/**
 * Format an ISO-8601 timestamp to a human-readable IST string.
 * Example: "15 Jun 2023, 07:00 pm IST"
 */
export function formatIST(isoString: string): string {
  if (!isoString) return '';
  return IST_DATE_TIME.format(new Date(isoString)) + ' IST';
}

/**
 * Short time format for badges / compact displays.
 * Example: "07:00 pm"
 */
export function formatTimeShort(isoString: string): string {
  if (!isoString) return '';
  return IST_TIME_SHORT.format(new Date(isoString));
}

/**
 * Format for timeline labels — split into date + time parts.
 */
export function formatTimelineLabel(isoString: string): {
  date: string;
  time: string;
} {
  const d = new Date(isoString);
  return {
    date: IST_DATE_SHORT.format(d).toUpperCase(),
    time: IST_TIME_HMS.format(d) + ' IST',
  };
}

/**
 * Extract the YYYY-MM-DD date portion from an ISO string.
 */
export function extractDateStr(isoString: string): string {
  return isoString.split('T')[0];
}

/**
 * Add hours to an ISO timestamp and return a new ISO string.
 */
export function addHoursToISO(isoString: string, hours: number): string {
  return new Date(
    new Date(isoString).getTime() + hours * 60 * 60 * 1000,
  ).toISOString();
}

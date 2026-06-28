/**
 * Single source of truth for score → color/label mapping.
 * Pure presentation helpers — no data fetching, no business logic.
 * Replaces the slightly-different threshold logic previously duplicated
 * across dashboard, ai-insights, jobs, upload and NotificationBell.
 *
 * Thresholds: 75+ excellent · 60–74 good · 40–59 fair · <40 weak
 */

export const SCORE_THRESHOLDS = { high: 75, mid: 60, low: 40 } as const;

/** Hex color — for SVG strokes, Recharts fills, inline styles. */
export function scoreHex(score: number): string {
  if (score >= SCORE_THRESHOLDS.high) return "#059669"; // emerald-600
  if (score >= SCORE_THRESHOLDS.mid)  return "#0d9488"; // teal-600
  if (score >= SCORE_THRESHOLDS.low)  return "#d97706"; // amber-600
  return "#dc2626";                                     // red-600
}

/** Tailwind background class for progress-bar fills. */
export function scoreBarClass(score: number): string {
  if (score >= SCORE_THRESHOLDS.high) return "bg-brand-600";
  if (score >= SCORE_THRESHOLDS.mid)  return "bg-accent-600";
  if (score >= SCORE_THRESHOLDS.low)  return "bg-amber-500";
  return "bg-red-500";
}

/** Tailwind text-color class for score numbers. */
export function scoreTextClass(score: number): string {
  if (score >= SCORE_THRESHOLDS.high) return "text-brand-600";
  if (score >= SCORE_THRESHOLDS.mid)  return "text-accent-600";
  if (score >= SCORE_THRESHOLDS.low)  return "text-amber-600";
  return "text-red-600";
}

/** Badge class (defined in globals.css). */
export function scoreBadgeClass(score: number): string {
  if (score >= SCORE_THRESHOLDS.high) return "score-high";
  if (score >= SCORE_THRESHOLDS.mid)  return "score-mid";
  return "score-low";
}

/** Human label. */
export function scoreLabel(score: number): string {
  if (score >= SCORE_THRESHOLDS.high) return "Excellent";
  if (score >= SCORE_THRESHOLDS.mid)  return "Good";
  if (score >= SCORE_THRESHOLDS.low)  return "Fair";
  return "Needs Work";
}

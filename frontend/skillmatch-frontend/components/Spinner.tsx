/**
 * Shared loading spinner — replaces the inline border-spinner markup
 * previously duplicated across Login, Register, Upload and Employer pages.
 * Visual-only component.
 */
export default function Spinner({
  size = 16,
  className = "",
  light = true,
}: {
  size?: number;
  className?: string;
  /** light=true → for use on colored/dark buttons; false → slate on white */
  light?: boolean;
}) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={`inline-block animate-spin rounded-full border-2 ${
        light ? "border-white/30 border-t-white" : "border-slate-300 border-t-slate-600"
      } ${className}`}
      style={{ width: size, height: size }}
    />
  );
}

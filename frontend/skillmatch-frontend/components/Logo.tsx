import { useId } from "react";

/**
 * SkillMatch logomark — pure SVG, crisp at any size.
 * A "match found" mark: bold checkmark + spark node on an emerald-teal tile.
 *
 * Visual-only component. No data or business logic.
 */
export function LogoMark({ size = 32, className = "" }: { size?: number; className?: string }) {
  const id = useId();
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      role="img"
      aria-label="SkillMatch logo"
    >
      <defs>
        <linearGradient id={`${id}-bg`} x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="#059669" />
          <stop offset="1" stopColor="#0f766e" />
        </linearGradient>
        <linearGradient id={`${id}-sheen`} x1="0" y1="0" x2="0" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="#ffffff" stopOpacity="0.14" />
          <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="8.5" fill={`url(#${id}-bg)`} />
      <rect width="32" height="32" rx="8.5" fill={`url(#${id}-sheen)`} />
      {/* checkmark — "match found" */}
      <path
        d="M8.5 16.8l4.6 4.7L23 11.2"
        stroke="#ffffff"
        strokeWidth="3.1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* spark node */}
      <circle cx="23.6" cy="20.6" r="2.1" fill="#6ee7b7" />
    </svg>
  );
}

/**
 * Full lockup: mark + wordmark.
 * tone="dark"  → dark text  (light backgrounds)
 * tone="light" → white text (dark/brand backgrounds)
 */
export default function Logo({
  size = 32,
  tone = "dark",
  className = "",
}: {
  size?: number;
  tone?: "dark" | "light";
  className?: string;
}) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <LogoMark size={size} />
      <span
        className={`font-bold tracking-[-0.02em] leading-none ${
          tone === "light" ? "text-white" : "text-slate-900"
        }`}
        style={{ fontSize: Math.round(size * 0.56) }}
      >
        SkillMatch
        <span className={tone === "light" ? "text-brand-300" : "text-brand-600"}>Nepal</span>
      </span>
    </span>
  );
}

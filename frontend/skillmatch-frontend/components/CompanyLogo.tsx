import { mediaUrl } from "@/lib/api";

function hue(seed: string): number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) % 360;
  return h;
}

/** Square company logo — shows the uploaded logo, else a generated
 *  monogram placeholder coloured deterministically from the company name. */
export default function CompanyLogo({
  name, src, size = 40, className = "",
}: { name?: string; src?: string | null; size?: number; className?: string }) {
  const url = mediaUrl(src);
  const label = name?.trim() || "?";
  const letter = label[0]?.toUpperCase() ?? "?";
  const h = hue(label);

  if (url) {
    // eslint-disable-next-line @next/next/no-img-element
    return (
      <img
        src={url}
        alt={label}
        style={{ width: size, height: size }}
        className={`shrink-0 rounded-lg bg-white object-contain ring-1 ring-slate-200/70 ${className}`}
      />
    );
  }
  return (
    <span
      style={{
        width: size, height: size, fontSize: size * 0.42,
        background: `linear-gradient(135deg, hsl(${h} 60% 96%), hsl(${h} 55% 88%))`,
        color: `hsl(${h} 55% 35%)`,
      }}
      className={`inline-flex shrink-0 items-center justify-center rounded-lg font-bold ${className}`}
      aria-label={label}
    >
      {letter}
    </span>
  );
}

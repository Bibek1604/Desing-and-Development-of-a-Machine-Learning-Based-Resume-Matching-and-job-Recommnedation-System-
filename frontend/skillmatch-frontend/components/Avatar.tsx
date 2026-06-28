import { mediaUrl } from "@/lib/api";

function hue(seed: string): number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) % 360;
  return h;
}

/** Round profile avatar — shows the uploaded photo, else a generated
 *  initials placeholder coloured deterministically from the name. */
export default function Avatar({
  name, src, size = 40, className = "",
}: { name?: string; src?: string | null; size?: number; className?: string }) {
  const url = mediaUrl(src);
  const label = name?.trim() || "?";
  const initials = label.split(" ").filter(Boolean).slice(0, 2).map(n => n[0]).join("").toUpperCase() || "?";
  const h = hue(label);

  if (url) {
    // eslint-disable-next-line @next/next/no-img-element
    return (
      <img
        src={url}
        alt={label}
        style={{ width: size, height: size }}
        className={`shrink-0 rounded-full object-cover ring-1 ring-slate-200/70 ${className}`}
      />
    );
  }
  return (
    <span
      style={{
        width: size, height: size, fontSize: size * 0.4,
        background: `linear-gradient(135deg, hsl(${h} 68% 55%), hsl(${(h + 40) % 360} 70% 45%))`,
      }}
      className={`inline-flex shrink-0 items-center justify-center rounded-full font-bold text-white ${className}`}
      aria-label={label}
    >
      {initials}
    </span>
  );
}

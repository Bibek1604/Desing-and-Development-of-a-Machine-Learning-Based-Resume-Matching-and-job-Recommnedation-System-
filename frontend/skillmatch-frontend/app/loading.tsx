import { LogoMark } from "@/components/Logo";

/**
 * Route-level loading UI. Next.js shows this during navigation while the next
 * segment streams in, so transitions never flash a blank page.
 */
export default function Loading() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center gap-4">
      <div className="relative">
        <span className="absolute inset-0 animate-ping rounded-2xl bg-brand-400/30" />
        <span className="relative inline-flex animate-pulse-soft">
          <LogoMark size={40} />
        </span>
      </div>
      <p className="text-sm font-medium text-slate-400">Loading…</p>
    </div>
  );
}

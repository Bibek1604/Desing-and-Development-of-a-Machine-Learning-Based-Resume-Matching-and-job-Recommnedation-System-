# SkillMatch Design System — Token Reference

Single source of truth: `tailwind.config.ts` + `app/globals.css`. Anything not listed here is off-system — don't use it.

## Typography

**Font:** Inter variable (one family, two voices: tight-tracked semibold/bold for headings, regular for body). Loaded via `next/font`, with `cv02/cv03/cv04/cv11` stylistic sets.

| Role | Class | Size | Weight | Tracking | Line height |
|---|---|---|---|---|---|
| Display (hero) | `.display` | fluid 36→56px (clamp) | 700 | −0.03em | 1.08 |
| Section heading | `.heading` | fluid 24→30px | 700 | −0.022em | 1.2 |
| Page title | `.page-title` | 24px | 700 | −0.02em | tight |
| Card title | `.subheading` | 18px | 600 | −0.01em | snug |
| Body large | `.body-lg` | 16→15.5px (`md`) | 400 | 0 | relaxed (1.625) |
| Body | `text-sm` / `text-base` | 14/16px | 400 | 0 | 1.5–1.6 |
| Caption | `.caption` | 12px | 400 | 0 | snug |
| Micro label | `.micro` / `.eyebrow` | 11px (`text-2xs`) | 600 | **+0.08–0.12em, uppercase** | 1 |

**Scale (no other sizes allowed):** 11 (`text-2xs`) · 12 (`xs`) · 14 (`sm`) · 15 (`md`) · 16 (`base`) · 18 (`lg`) · 20 (`xl`) · 24 (`2xl`) · 30 (`3xl`) · fluid display.
**Numbers:** always `tabular-nums` for scores/stats. **Measure:** long paragraphs get `.measure` (68ch max).

## Text colors — exactly three levels

| Level | Token | Hex | Use |
|---|---|---|---|
| Primary | `text-slate-900` (`--text-primary`) | `#0f172a` | Headings, key data (near-black, never pure black) |
| Secondary | `text-slate-600` (`--text-secondary`) | `#475569` | Body copy |
| Tertiary | `text-slate-500` (`--text-tertiary`) | `#64748b` | Captions, meta — minimum for readable text (4.6:1) |

`slate-400` is for **decorative icons only**, never copy.

## Color

Brand emerald `#059669` (one primary action per view) · accent teal `#0d9488` (charts/highlights only) · semantic emerald/amber/red for success/warning/error (via `lib/score.ts` thresholds 75/60/40) · slate neutral ramp. Page background `#f8fafc`, surfaces white.

## Spacing, radius, elevation

4/8px spacing scale (`gap-1..gap-6`, card padding `p-5`/`p-6`). Radius: 8px controls (`rounded-lg`) · 12px cards (`rounded-xl`) · 16px heroes (`rounded-2xl`). Elevation: 1px low-contrast borders first; shadows `card` (resting) → `lift` (hover) → `pop` (overlays), all soft/layered.

## Motion & interaction

150–250ms ease-out only (`duration-150/200`, `cubic-bezier(0.16,1,0.3,1)` entrances). Skeletons (`.skeleton` shimmer) for known-shape content; toasts for action feedback; `active:scale-[0.98]` press states. Links get keyboard `:focus-visible` outlines; buttons/inputs carry focus rings; 44px tap targets on coarse pointers. Active nav page marked with `aria-current` + tinted background.

## Icons

Lucide only. 11–13px inline with text, 15–18px in buttons/nav, 20–26px in feature tiles. Default stroke width except logo/checkmarks (2.5).

import type { ComponentType, ReactNode } from "react";

/**
 * Standard page header: optional gradient icon tile, eyebrow, title, subtitle,
 * and a right-aligned action slot. Use across pages for consistent hierarchy
 * and spacing. Visual only.
 */
export default function PageHeader({
  icon: Icon, eyebrow, title, subtitle, action,
}: {
  icon?: ComponentType<{ size?: number | string }>;
  eyebrow?: string;
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-7 flex flex-wrap items-start justify-between gap-3">
      <div className="flex items-start gap-3.5">
        {Icon && (
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-brand text-white shadow-green">
            <Icon size={20} />
          </span>
        )}
        <div>
          {eyebrow && <p className="eyebrow">{eyebrow}</p>}
          <h1 className="page-title mt-0.5">{title}</h1>
          {subtitle && <p className="muted mt-1 max-w-xl">{subtitle}</p>}
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

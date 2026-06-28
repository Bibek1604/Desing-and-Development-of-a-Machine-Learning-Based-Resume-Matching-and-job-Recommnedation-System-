import Link from "next/link";
import { Compass, Home, Briefcase } from "lucide-react";

export default function NotFound() {
  return (
    <div className="page flex items-center justify-center">
      <div className="card mx-auto max-w-md px-6 py-12 text-center">
        <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-brand-50 text-brand-600 ring-1 ring-inset ring-brand-100">
          <Compass className="h-6 w-6" />
        </span>
        <p className="mt-4 text-5xl font-extrabold tracking-tight text-slate-900">404</p>
        <h1 className="mt-1 text-lg font-semibold text-slate-900">Page not found</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-500">
          The page you're looking for doesn't exist or may have been moved.
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-2.5">
          <Link href="/" className="btn-primary">
            <Home className="h-4 w-4" />
            Home
          </Link>
          <Link href="/jobs" className="btn-outline">
            <Briefcase className="h-4 w-4" />
            Browse jobs
          </Link>
        </div>
      </div>
    </div>
  );
}

import Link from "next/link";
import { MapPin, Briefcase, Clock, Wallet } from "lucide-react";
import { Job } from "@/lib/types";
import MatchRing from "@/components/MatchRing";

export default function JobCard({ job }: { job: Job }) {
  return (
    <div className="card group p-5 transition hover:shadow-lift">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900">{job.title}</h3>
            {job.featured && (
              <span className="chip bg-amber-50 text-amber-700 ring-amber-100">Featured</span>
            )}
          </div>
          <p className="mt-1 text-sm font-medium text-brand-700">{job.company}</p>
        </div>
        <div className="text-center">
          <MatchRing score={job.matchScore} />
          <p className="mt-1 text-2xs font-medium text-slate-500">Match</p>
        </div>
      </div>

      <p className="mt-3 line-clamp-2 text-sm text-slate-600">{job.description}</p>

      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-xs text-slate-500">
        <span className="inline-flex items-center gap-1"><MapPin size={14} /> {job.location}</span>
        <span className="inline-flex items-center gap-1"><Briefcase size={14} /> {job.type}</span>
        <span className="inline-flex items-center gap-1"><Wallet size={14} /> {job.salary}</span>
        <span className="inline-flex items-center gap-1"><Clock size={14} /> {job.postedAt}</span>
      </div>

      <div className="mt-4 flex flex-wrap gap-1.5">
        {job.skills.map((s) => (
          <span key={s} className="chip">{s}</span>
        ))}
      </div>

      <div className="mt-5 flex items-center gap-3">
        <Link href="/dashboard" className="btn-primary flex-1">Apply now</Link>
        <Link href="/dashboard" className="btn-outline">Save</Link>
      </div>
    </div>
  );
}

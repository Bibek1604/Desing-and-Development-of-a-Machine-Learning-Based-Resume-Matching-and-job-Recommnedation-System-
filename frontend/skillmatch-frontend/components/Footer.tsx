import Link from "next/link";
import { Github, Linkedin, Globe, ArrowRight, MapPin } from "lucide-react";
import Logo from "@/components/Logo";

const links = {
  candidates: [
    { href: "/jobs",      label: "Find Jobs" },
    { href: "/upload",    label: "Upload Resume" },
    { href: "/dashboard", label: "My Dashboard" },
    { href: "/register",  label: "Get Started Free" },
  ],
  employers: [
    { href: "/employer", label: "Post a Job" },
    { href: "/employer", label: "Find Candidates" },
    { href: "/register?role=employer", label: "Employer Signup" },
  ],
};

const socials = [
  { href: "https://github.com",   label: "GitHub",   icon: Github },
  { href: "https://linkedin.com", label: "LinkedIn", icon: Linkedin },
  { href: "/",                    label: "Website",  icon: Globe },
];

function FooterColumn({ title, items }: { title: string; items: { href: string; label: string }[] }) {
  return (
    <div>
      <h4 className="mb-4 text-2xs font-bold uppercase tracking-[0.14em] text-brand-200/90">{title}</h4>
      <ul className="space-y-2.5">
        {items.map((l) => (
          <li key={l.href + l.label}>
            <Link
              href={l.href}
              className="group inline-flex items-center gap-1.5 text-sm text-brand-50/70 transition-colors duration-150 hover:text-white"
            >
              <span className="h-px w-0 bg-brand-300 transition-all duration-200 group-hover:w-3" />
              {l.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function Footer() {
  return (
    <footer className="relative mt-24 overflow-hidden bg-gradient-aurora bg-grid-light text-white">
      {/* Ambient glows */}
      <div className="pointer-events-none absolute -top-24 right-0 h-72 w-72 rounded-full bg-brand-400/15 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 left-0 h-72 w-72 rounded-full bg-accent-500/10 blur-3xl" />

      <div className="container-px relative pb-8 pt-16">
        {/* CTA strip */}
        <div className="mb-14 flex flex-col items-start justify-between gap-5 rounded-2xl border border-white/10 bg-white/[0.06] p-6 backdrop-blur-sm sm:flex-row sm:items-center sm:p-8">
          <div>
            <h3 className="text-xl font-bold tracking-[-0.02em] text-white sm:text-2xl">
              Ready to find your match?
            </h3>
            <p className="mt-1 text-sm text-brand-50/75">
              Upload your resume and get AI-matched to IT roles in Nepal — free, in minutes.
            </p>
          </div>
          <div className="flex flex-shrink-0 gap-3">
            <Link href="/register" className="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-2.5 text-sm font-semibold text-brand-700 shadow-sm transition hover:bg-brand-50">
              Get started free <ArrowRight size={15} />
            </Link>
            <Link href="/jobs" className="inline-flex items-center gap-2 rounded-lg border border-white/25 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-white/10">
              Browse jobs
            </Link>
          </div>
        </div>

        {/* Main grid */}
        <div className="grid gap-10 lg:grid-cols-[2fr_1fr_1fr_1fr]">
          {/* Brand */}
          <div className="space-y-4">
            <Logo size={30} tone="light" />
            <p className="max-w-xs text-sm leading-relaxed text-brand-50/70">
              Matching IT graduates in Nepal with the right jobs using machine learning — skills first, always.
            </p>
            <div className="flex items-center gap-2.5">
              {socials.map(({ href, label, icon: Icon }) => (
                <a
                  key={label}
                  href={href}
                  target={href.startsWith("http") ? "_blank" : undefined}
                  rel="noopener noreferrer"
                  aria-label={label}
                  className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/15 bg-white/5 text-brand-50/70 transition hover:border-white/30 hover:bg-white/10 hover:text-white"
                >
                  <Icon size={15} />
                </a>
              ))}
            </div>
          </div>

          <FooterColumn title="For Candidates" items={links.candidates} />
          <FooterColumn title="For Employers" items={links.employers} />

          {/* Project */}
          <div>
            <h4 className="mb-4 text-2xs font-bold uppercase tracking-[0.14em] text-brand-200/90">Project</h4>
            <ul className="space-y-2.5 text-sm text-brand-50/70">
              <li>Final-Year Thesis</li>
              <li>Coventry University</li>
              <li className="inline-flex items-center gap-1.5"><MapPin size={13} className="text-brand-300" /> Kathmandu, Nepal</li>
              <li className="pt-1.5">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-2.5 py-1 text-2xs font-semibold text-brand-100 ring-1 ring-inset ring-white/15">
                  <span className="h-1.5 w-1.5 rounded-full bg-brand-300" /> Research Preview
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-12 flex flex-col items-center justify-between gap-3 border-t border-white/10 pt-6 text-xs text-brand-50/55 sm:flex-row">
          <p>&copy; {new Date().getFullYear()} SkillMatch Nepal. Final-year project demo. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <Link href="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link>
            <span>Built with Next.js, Django REST &amp; Sentence-BERT.</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

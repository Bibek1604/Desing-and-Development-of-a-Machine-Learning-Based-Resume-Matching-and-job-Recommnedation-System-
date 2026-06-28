import Link from "next/link";
import { ShieldCheck, ArrowLeft } from "lucide-react";

export const metadata = { title: "Privacy Policy — SkillMatch Nepal" };

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-2">
      <h2 className="subheading">{title}</h2>
      <div className="text-sm leading-relaxed text-slate-600 space-y-2">{children}</div>
    </section>
  );
}

export default function PrivacyPage() {
  return (
    <div className="page">
      <div className="page-inner-sm space-y-8">
        <div>
          <Link href="/" className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors">
            <ArrowLeft size={15} /> Back
          </Link>
          <div className="mt-4 flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600 ring-1 ring-brand-100">
              <ShieldCheck size={18} />
            </span>
            <h1 className="page-title">Privacy Policy</h1>
          </div>
          <p className="muted mt-1">How SkillMatch Nepal collects, uses, and protects your data.</p>
        </div>

        <Section title="What we collect">
          <p>When you register and use SkillMatch we store your account details (name, email), your profile
          (skills, education, links, preferences), and any resume you upload. The resume text is parsed to
          extract skills and build your match profile.</p>
        </Section>

        <Section title="How we use it">
          <p>Your profile and resume are used solely to match you to relevant job postings and to show employers
          a ranked shortlist of candidates. Match scores are computed by our on-platform ML model. We do not
          sell your data or share it with third parties for advertising.</p>
        </Section>

        <Section title="Consent">
          <p>You must explicitly consent before uploading a resume. You can edit or remove the details we
          extracted at any time from your profile.</p>
        </Section>

        <Section title="Your rights (right to delete)">
          <p>You can permanently delete your account and all associated data at any time from your profile&apos;s
          &ldquo;Danger zone&rdquo;. Deletion removes your account, profile, resumes, and applications. This action
          is immediate and cannot be undone.</p>
        </Section>

        <Section title="Data retention &amp; security">
          <p>Data is retained only while your account is active. Passwords are stored hashed, never in plain text,
          and access to candidate data is restricted by role. This is a final-year research project run locally;
          it is not a commercial service.</p>
        </Section>

        <p className="text-xs text-slate-400">
          SkillMatch Nepal · Final-year thesis · Coventry University. For questions about your data, contact the
          project owner.
        </p>
      </div>
    </div>
  );
}

"use client";

import { useCallback, useState, useRef, type DragEvent } from "react";
import { useRouter } from "next/navigation";
import {
  Upload, CheckCircle, FileText, Sparkles, ArrowRight, AlertCircle,
  CheckCircle2, AlertTriangle, Lightbulb,
} from "lucide-react";
import { useRequireAuth } from "@/context/AuthContext";
import { resumes, humanizeError } from "@/lib/api";
import { useToast } from "@/context/ToastContext";
import PageHeader from "@/components/PageHeader";
import { scoreBarClass, scoreTextClass, scoreLabel } from "@/lib/score";

const MAX_FILE_MB = 10;

type UploadState = "idle" | "uploading" | "done" | "error";

interface ATSResult {
  ats_score: number;
  completeness_score: number;
  keyword_score: number;
  formatting_score: number;
  experience_score: number;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  missing_sections: string[];
}

interface ResumeResult {
  id: number;
  ats_analysis: ATSResult | null;
  extracted_skills: string[];
  original_filename: string;
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const v = Math.min(100, Math.max(0, value));
  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5">
        <span className="font-medium text-slate-600">{label}</span>
        <span className="font-semibold text-slate-800 tabular-nums">{v}/100</span>
      </div>
      <div className="progress-track">
        <div className={`progress-fill ${scoreBarClass(v)}`} style={{ width: `${v}%` }} />
      </div>
    </div>
  );
}

export default function UploadPage() {
  const { isLoading } = useRequireAuth();
  const router = useRouter();
  const toast = useToast();

  const [state,    setState]    = useState<UploadState>("idle");
  const [drag,     setDrag]     = useState(false);
  const [progress, setProgress] = useState(0);
  const [result,   setResult]   = useState<ResumeResult | null>(null);
  const [error,    setError]    = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const uploadFile = useCallback(async (file: File) => {
    if (!file.name.match(/\.(pdf|docx|doc|txt)$/i)) {
      const msg = "Only PDF, DOCX, DOC, or TXT files are supported.";
      setError(msg);
      setState("error");
      toast.error(msg);
      return;
    }
    if (file.size > MAX_FILE_MB * 1024 * 1024) {
      const msg = `File is too large. Please upload a file under ${MAX_FILE_MB} MB.`;
      setError(msg);
      setState("error");
      toast.error(msg);
      return;
    }
    setState("uploading");
    setError("");
    let p = 0;
    const ticker = setInterval(() => {
      p = Math.min(p + Math.random() * 12, 85);
      setProgress(Math.floor(p));
    }, 200);

    try {
      const uploaded = await resumes.upload(file, true);
      clearInterval(ticker);
      setProgress(100);

      let atsData: ATSResult | null = null;
      try { atsData = await resumes.ats(uploaded.id); } catch { /* optional */ }

      const rawSkills = (uploaded.extracted_skills ?? []) as unknown[];
      const skills = rawSkills.map((s) =>
        typeof s === "string" ? s : (s as { name: string }).name
      );

      setResult({
        id: uploaded.id,
        original_filename: uploaded.original_filename ?? file.name,
        extracted_skills:  skills,
        ats_analysis:      atsData,
      });
      setState("done");
      toast.success("Resume uploaded and analysed!");
    } catch (err) {
      clearInterval(ticker);
      setProgress(0);
      const msg = humanizeError(err);
      setError(msg);
      setState("error");
      toast.error(msg);
    }
  }, [toast]);

  const onDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDrag(false);
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  }, [uploadFile]);

  const onFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
  }, [uploadFile]);

  if (isLoading) {
    return (
      <div className="page flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-2 border-brand-600 border-t-transparent animate-spin" role="status" aria-label="Loading" />
      </div>
    );
  }

  const ats = result?.ats_analysis;
  const atsScore = ats?.ats_score ?? 0;
  const atsColor = scoreTextClass(atsScore);

  return (
    <div className="page">
      <div className="mx-auto max-w-2xl">

        {/* Header */}
        <PageHeader
          icon={FileText}
          eyebrow="Resume intelligence"
          title="Upload your CV"
          subtitle="We'll extract your skills and run an ATS analysis to improve your match score."
        />

        {/* Upload zone */}
        {state !== "done" && (
          <div
            onDragOver={e => { e.preventDefault(); setDrag(true); }}
            onDragLeave={() => setDrag(false)}
            onDrop={onDrop}
            onClick={() => state === "idle" && inputRef.current?.click()}
            className={`relative overflow-hidden rounded-xl border-2 border-dashed p-12 text-center transition-all duration-200 ${
              drag
                ? "border-brand-500 bg-brand-50 cursor-copy scale-[1.01]"
                : state === "idle"
                ? "border-slate-200 bg-white hover:border-brand-400 hover:bg-brand-50/30 cursor-pointer"
                : "border-slate-200 bg-white"
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              className="hidden"
              onChange={onFileChange}
            />

            {state === "idle" && (
              <div className="space-y-3">
                <div className="inline-flex h-14 w-14 items-center justify-center rounded-xl bg-brand-50 text-brand-600 ring-1 ring-brand-100 mx-auto">
                  <Upload size={26} strokeWidth={1.8} />
                </div>
                <div>
                  <p className="font-semibold tracking-[-0.01em] text-slate-800">Drag &amp; drop your CV here</p>
                  <p className="text-sm text-slate-500 mt-1">or click to browse files</p>
                </div>
                <p className="text-xs font-medium text-slate-500 bg-slate-50 ring-1 ring-slate-200/70 inline-block px-3 py-1.5 rounded-full">
                  PDF, DOCX, DOC, TXT &middot; Max 10 MB
                </p>
              </div>
            )}

            {state === "uploading" && (
              <div className="space-y-4">
                <div className="inline-flex h-14 w-14 items-center justify-center rounded-xl bg-brand-50 text-brand-600 ring-1 ring-brand-100 mx-auto">
                  <Sparkles size={26} className="animate-pulse-soft" />
                </div>
                <div>
                  <p className="font-semibold text-brand-700">Analysing your CV&hellip;</p>
                  <p className="text-sm text-slate-500 mt-1">Extracting skills and running ATS check</p>
                </div>
                <div className="max-w-xs mx-auto">
                  <div className="progress-track !h-2.5">
                    <div
                      className="progress-fill bg-gradient-to-r from-brand-500 to-accent-600"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <p className="text-xs text-slate-500 mt-2 tabular-nums">{progress}%</p>
                </div>
              </div>
            )}

            {state === "error" && (
              <div className="space-y-3">
                <div className="inline-flex h-14 w-14 items-center justify-center rounded-xl bg-red-50 text-red-500 ring-1 ring-red-100 mx-auto">
                  <AlertCircle size={26} />
                </div>
                <p className="font-medium text-red-600">{error}</p>
                <button
                  onClick={() => { setState("idle"); setError(""); }}
                  className="btn-outline !text-xs !py-1.5"
                >
                  Try again
                </button>
              </div>
            )}
          </div>
        )}

        {/* What happens next — guidance strip */}
        {state === "idle" && (
          <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-3">
            {[
              { icon: FileText,     title: "Extract skills", sub: "Parsed from your CV" },
              { icon: Sparkles,     title: "ATS score",      sub: "Recruiter-readiness" },
              { icon: CheckCircle2, title: "Job matches",    sub: "Ranked for you" },
            ].map(({ icon: Icon, title, sub }) => (
              <div key={title} className="flex items-center gap-3 rounded-xl border border-slate-200/80 bg-white p-3.5 shadow-card">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                  <Icon size={16} />
                </span>
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-slate-800">{title}</p>
                  <p className="text-2xs text-slate-500">{sub}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Results */}
        {state === "done" && result && (
          <div className="space-y-5 animate-slide-up">

            {/* Success banner */}
            <div className="card p-5 flex items-center gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-emerald-50 ring-1 ring-emerald-100">
                <CheckCircle size={24} className="text-emerald-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-slate-900 truncate">{result.original_filename}</p>
                <p className="text-sm text-slate-500">Successfully uploaded and processed</p>
              </div>
              {ats && (
                <div className="text-right shrink-0">
                  <p className={`text-3xl font-bold tabular-nums tracking-[-0.02em] ${atsColor}`}>{atsScore}</p>
                  <p className="text-xs text-slate-500">ATS Score</p>
                </div>
              )}
            </div>

            {/* ATS breakdown */}
            {ats && (
              <div className="card p-6">
                <div className="flex items-center justify-between mb-5">
                  <h2 className="subheading">ATS Analysis</h2>
                  <span className={`text-xs font-bold uppercase tracking-[0.08em] ${atsColor}`}>
                    {scoreLabel(atsScore)}
                  </span>
                </div>
                <div className="space-y-3.5 mb-6">
                  <ScoreBar label="Completeness" value={ats.completeness_score} />
                  <ScoreBar label="Keywords"     value={ats.keyword_score}      />
                  <ScoreBar label="Formatting"   value={ats.formatting_score}   />
                  <ScoreBar label="Experience"   value={ats.experience_score}   />
                </div>

                <div className="grid sm:grid-cols-3 gap-4">
                  {ats.strengths.length > 0 && (
                    <div className="rounded-lg bg-emerald-50/50 border border-emerald-200/50 p-3">
                      <p className="flex items-center gap-1.5 text-xs font-bold text-emerald-700 uppercase tracking-[0.06em] mb-2">
                        <CheckCircle2 size={12} /> Strengths
                      </p>
                      <ul className="space-y-1">
                        {ats.strengths.map((s, i) => (
                          <li key={i} className="text-xs text-slate-600 flex items-start gap-1.5">
                            <span className="text-emerald-400 mt-0.5">•</span>{s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {ats.weaknesses.length > 0 && (
                    <div className="rounded-lg bg-amber-50/50 border border-amber-200/50 p-3">
                      <p className="flex items-center gap-1.5 text-xs font-bold text-amber-700 uppercase tracking-[0.06em] mb-2">
                        <AlertTriangle size={12} /> Weaknesses
                      </p>
                      <ul className="space-y-1">
                        {ats.weaknesses.map((s, i) => (
                          <li key={i} className="text-xs text-slate-600 flex items-start gap-1.5">
                            <span className="text-amber-400 mt-0.5">•</span>{s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {ats.recommendations.length > 0 && (
                    <div className="rounded-lg bg-brand-50/50 border border-brand-200/50 p-3">
                      <p className="flex items-center gap-1.5 text-xs font-bold text-brand-700 uppercase tracking-[0.06em] mb-2">
                        <Lightbulb size={12} /> Tips
                      </p>
                      <ul className="space-y-1">
                        {ats.recommendations.map((s, i) => (
                          <li key={i} className="text-xs text-slate-600 flex items-start gap-1.5">
                            <span className="text-brand-400 mt-0.5">•</span>{s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Skills */}
            {result.extracted_skills.length > 0 && (
              <div className="card p-6">
                <div className="flex items-center gap-2 mb-4">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                    <FileText size={15} />
                  </span>
                  <h2 className="subheading">
                    Extracted Skills
                    <span className="ml-2 text-sm font-normal text-slate-400 tabular-nums">
                      ({result.extracted_skills.length})
                    </span>
                  </h2>
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.extracted_skills.map((s, i) => (
                    <span key={i} className="chip">{s}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => { setState("idle"); setResult(null); setProgress(0); }}
                className="btn-outline flex-1 justify-center"
              >
                Upload Another
              </button>
              <button
                onClick={() => router.push("/dashboard")}
                className="btn-primary flex-1 justify-center"
              >
                View Dashboard <ArrowRight size={15} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

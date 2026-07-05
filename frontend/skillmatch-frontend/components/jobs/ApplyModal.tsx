"use client";

/**
 * ApplyModal — collects an optional cover note before submitting an
 * application. Wired into /jobs and /jobs/[id] so `applications.create()`
 * finally receives the cover_note field that the backend has always
 * accepted.
 */

import { useEffect, useRef, useState } from "react";
import { X, Send } from "lucide-react";
import Spinner from "@/components/Spinner";
import type { Job } from "@/lib/api";

interface ApplyModalProps {
  job: Job | null;
  submitting: boolean;
  onCancel: () => void;
  onSubmit: (coverNote: string) => Promise<void> | void;
}

const MAX_COVER_LEN = 2000;

export default function ApplyModal({ job, submitting, onCancel, onSubmit }: ApplyModalProps) {
  const [note, setNote] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Reset text and focus every time the modal opens for a new job.
  useEffect(() => {
    if (job) {
      setNote("");
      // Focus after mount for a11y.
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  }, [job]);

  // Escape-to-close.
  useEffect(() => {
    if (!job) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && !submitting) onCancel();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [job, submitting, onCancel]);

  if (!job) return null;

  const remaining = MAX_COVER_LEN - note.length;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="apply-modal-title"
    >
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm animate-fade-in"
        onClick={() => !submitting && onCancel()}
      />
      <div className="relative z-10 w-full max-w-lg rounded-2xl bg-white shadow-pop animate-slide-up">
        <div className="flex items-start justify-between border-b border-slate-100 px-6 py-4">
          <div>
            <h2 id="apply-modal-title" className="font-semibold tracking-[-0.01em] text-slate-900">
              Apply to {job.title}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">{job.company} · {job.location}</p>
          </div>
          <button
            type="button"
            aria-label="Close"
            onClick={onCancel}
            disabled={submitting}
            className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors disabled:opacity-40"
          >
            <X size={16} />
          </button>
        </div>

        <div className="p-6">
          <label htmlFor="apply-cover-note" className="block text-sm font-semibold text-slate-700 mb-1.5">
            Cover note <span className="font-normal text-slate-400">(optional)</span>
          </label>
          <p className="text-xs text-slate-500 mb-2">
            A short message the employer sees with your application. Two or three sentences is plenty.
          </p>
          <textarea
            id="apply-cover-note"
            ref={textareaRef}
            rows={6}
            value={note}
            maxLength={MAX_COVER_LEN}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Introduce yourself and mention why you're a good fit for this role…"
            className="input resize-y min-h-[8rem]"
          />
          <p className={`mt-1.5 text-2xs text-right ${remaining < 100 ? "text-amber-600" : "text-slate-400"}`}>
            {remaining} chars left
          </p>
        </div>

        <div className="flex items-center justify-end gap-3 border-t border-slate-100 px-6 py-4">
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            className="btn-ghost !py-2 !px-3.5 !text-sm"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => onSubmit(note.trim())}
            disabled={submitting}
            className="btn-primary !py-2 !px-4 !text-sm"
          >
            {submitting ? <Spinner size={12} /> : <Send size={12} />}
            {submitting ? "Submitting…" : "Submit application"}
          </button>
        </div>
      </div>
    </div>
  );
}

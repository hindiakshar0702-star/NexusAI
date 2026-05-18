"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ShieldCheck, ShieldAlert } from "lucide-react";
import { Topbar } from "@/components/Topbar";
import { api } from "@/lib/api";

type Report = { safe: boolean; severity: string; flags: string[]; explanation: string };

const SEVERITY_STYLE: Record<string, string> = {
  none:   "border-emerald-500/40 text-emerald-600 dark:text-emerald-400",
  low:    "border-amber-500/40 text-amber-600 dark:text-amber-400",
  medium: "border-orange-500/40 text-orange-600 dark:text-orange-400",
  high:   "border-red-500/50 text-red-600 dark:text-red-400",
};

export default function SafetyPage() {
  const [text, setText] = useState("");
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (!text.trim()) return;
    setLoading(true); setError(null);
    try {
      setReport(await api.safety({ text }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Safety check failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Topbar title="Safety Layer" subtitle="rule-based ethics gate" />

      <section className="nx-card mb-4">
        <label className="nx-label">Prompt to check</label>
        <textarea
          className="nx-textarea min-h-[140px]"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste any prompt. We'll flag disallowed content and surface PII for redaction."
        />
        <div className="flex justify-end mt-3">
          <button onClick={submit} disabled={loading || !text.trim()} className="nx-btn-primary">
            <ShieldCheck className="h-4 w-4" />
            {loading ? "checking…" : "Run safety check"}
          </button>
        </div>
      </section>

      {error && (
        <div className="nx-card border border-red-500/40 text-red-600 dark:text-red-400 mb-4">{error}</div>
      )}

      {report && (
        <motion.section
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
          className={"nx-card border " + (SEVERITY_STYLE[report.severity] ?? "")}
        >
          <header className="flex items-center gap-3 mb-2">
            {report.safe ? <ShieldCheck className="h-5 w-5" /> : <ShieldAlert className="h-5 w-5" />}
            <h2 className="font-display text-xl">
              {report.safe ? "Cleared" : "Blocked"}
            </h2>
            <span className="nx-pill nx-mono uppercase border border-current">
              severity · {report.severity}
            </span>
          </header>
          <p className="text-sm opacity-90 mb-3">{report.explanation}</p>
          {report.flags.length > 0 && (
            <div>
              <div className="nx-section-title mb-1">Flags</div>
              <div className="flex flex-wrap gap-1.5">
                {report.flags.map((f) => (
                  <span key={f} className="nx-pill border border-current nx-mono">{f}</span>
                ))}
              </div>
            </div>
          )}
        </motion.section>
      )}
    </>
  );
}

"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Gauge, Wand2 } from "lucide-react";
import { Topbar } from "@/components/Topbar";
import { LoadingShimmer } from "@/components/LoadingShimmer";
import { ScoreBars, OverallScore } from "@/components/ScoreBars";
import { DomainSelect, PlatformSelect } from "@/components/Selectors";
import { api, type Domain, type Platform, type PromptScore } from "@/lib/api";

export default function AnalyzerPage() {
  const [text, setText] = useState("");
  const [platform, setPlatform] = useState<Platform | "auto">("auto");
  const [domain, setDomain] = useState<Domain | "auto">("auto");
  const [score, setScore] = useState<PromptScore | null>(null);
  const [optimized, setOptimized] = useState<{ text: string; score: PromptScore } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setOptimized(null);
    try {
      const result = await api.analyze({
        text,
        platform: platform === "auto" ? undefined : platform,
      });
      setScore(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  };

  const optimize = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.optimize({
        text,
        platform: platform === "auto" ? undefined : platform,
        domain: domain === "auto" ? undefined : domain,
      });
      setOptimized(result);
      setScore(result.score);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Optimization failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Topbar title="Real-Time Analyzer" subtitle="score, diagnose, optimize" />

      <section className="nx-card mb-4">
        <label className="nx-label">Paste a prompt to analyze</label>
        <textarea
          className="nx-textarea min-h-[180px]"
          placeholder="Paste any prompt here. We'll score it and surface concrete improvements."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
          <div>
            <label className="nx-label">Domain (for optimize)</label>
            <DomainSelect value={domain} onChange={setDomain} />
          </div>
          <div>
            <label className="nx-label">Target platform</label>
            <PlatformSelect value={platform} onChange={setPlatform} />
          </div>
          <div className="flex items-end gap-2">
            <button onClick={analyze} disabled={loading || !text.trim()} className="nx-btn-ghost flex-1">
              <Gauge className="h-4 w-4" /> Analyze
            </button>
            <button onClick={optimize} disabled={loading || !text.trim()} className="nx-btn-primary flex-1">
              <Wand2 className="h-4 w-4" /> Optimize
            </button>
          </div>
        </div>
      </section>

      {error && (
        <div className="nx-card border border-red-500/40 text-red-600 dark:text-red-400 mb-4">{error}</div>
      )}

      {loading && <LoadingShimmer lines={4} />}

      {score && !loading && (
        <motion.section
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          className="nx-card space-y-4"
        >
          <header className="flex items-center justify-between">
            <h2 className="font-display text-xl">Score</h2>
            <OverallScore value={score.overall} />
          </header>
          <ScoreBars score={score} />

          {score.weaknesses.length > 0 && (
            <div>
              <div className="nx-section-title mb-1">Weaknesses</div>
              <ul className="space-y-1 text-sm">
                {score.weaknesses.map((w) => (
                  <li key={w} className="flex gap-2">
                    <span className="opacity-60">!</span>
                    <span>{w}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {score.suggestions.length > 0 && (
            <div>
              <div className="nx-section-title mb-1">Suggestions</div>
              <ul className="space-y-1 text-sm">
                {score.suggestions.map((s) => (
                  <li key={s} className="flex gap-2">
                    <span className="opacity-60">→</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.section>
      )}

      {optimized && (
        <motion.section
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          className="nx-card mt-4"
        >
          <div className="nx-section-title mb-2">Optimized text</div>
          <pre className="nx-mono text-[12.5px] leading-[1.6] whitespace-pre-wrap break-words rounded-2xl border border-nx-line/15 dark:border-nx-dark-line p-4 bg-white/40 dark:bg-black/20">
            {optimized.text}
          </pre>
        </motion.section>
      )}
    </>
  );
}

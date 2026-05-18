"use client";

import { motion } from "framer-motion";
import { Copy, Check } from "lucide-react";
import { useState } from "react";
import type { Prompt } from "@/lib/api";
import { OverallScore, ScoreBars } from "./ScoreBars";

export function PromptCard({ prompt, index = 0 }: { prompt: Prompt; index?: number }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(prompt.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  return (
    <motion.article
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className="nx-card flex flex-col gap-4"
    >
      <header className="flex items-start justify-between gap-3">
        <div>
          <div className="nx-section-title">
            {prompt.domain} · {prompt.platform} · {prompt.skill_level}
          </div>
          <h3 className="font-display text-lg leading-tight mt-0.5">{prompt.title}</h3>
        </div>
        {prompt.score && <OverallScore value={prompt.score.overall} />}
      </header>

      <div className="rounded-2xl border border-nx-line/15 dark:border-nx-dark-line bg-white/40 dark:bg-black/20 p-4">
        <pre className="nx-mono text-[12.5px] leading-[1.6] whitespace-pre-wrap break-words">
          {prompt.text}
        </pre>
      </div>

      {prompt.system && (
        <details className="rounded-2xl border border-nx-line/15 dark:border-nx-dark-line p-3">
          <summary className="nx-mono text-[11px] uppercase tracking-wider opacity-70 cursor-pointer">
            System prompt
          </summary>
          <pre className="nx-mono text-xs mt-2 whitespace-pre-wrap">{prompt.system}</pre>
        </details>
      )}

      {prompt.negative && (
        <details className="rounded-2xl border border-nx-line/15 dark:border-nx-dark-line p-3">
          <summary className="nx-mono text-[11px] uppercase tracking-wider opacity-70 cursor-pointer">
            Negative prompt
          </summary>
          <pre className="nx-mono text-xs mt-2 whitespace-pre-wrap">{prompt.negative}</pre>
        </details>
      )}

      {prompt.score && <ScoreBars score={prompt.score} />}

      <div className="flex flex-wrap items-center gap-2">
        {prompt.tags.map((t) => (
          <span key={t} className="nx-pill border border-nx-line/30 dark:border-nx-dark-line">
            {t}
          </span>
        ))}
      </div>

      {prompt.score?.suggestions?.length ? (
        <div>
          <div className="nx-section-title mb-1">Suggestions</div>
          <ul className="space-y-1 text-sm">
            {prompt.score.suggestions.map((s, i) => (
              <li key={i} className="flex gap-2"><span className="opacity-60">→</span><span>{s}</span></li>
            ))}
          </ul>
        </div>
      ) : null}

      <footer className="flex items-center justify-between gap-3">
        <span className="nx-mono text-[11px] opacity-60">
          rationale: {prompt.rationale.slice(0, 90)}{prompt.rationale.length > 90 ? "…" : ""}
        </span>
        <button onClick={copy} className="nx-btn-ghost">
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </footer>
    </motion.article>
  );
}

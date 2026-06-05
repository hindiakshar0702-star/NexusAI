"use client";

import { motion } from "framer-motion";
import type { PromptScore } from "@/lib/api";

const DIMS: Array<{ key: keyof PromptScore; label: string }> = [
  { key: "clarity", label: "Clarity" },
  { key: "specificity", label: "Specificity" },
  { key: "creativity", label: "Creativity" },
  { key: "realism", label: "Realism" },
  { key: "safety", label: "Safety" },
  { key: "platform_fit", label: "Platform fit" },
];

export function ScoreBars({ score }: { score: PromptScore }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {DIMS.map(({ key, label }) => {
        const value = (score[key] as number) ?? 0;
        return (
          <div key={key as string}>
            <div className="flex justify-between mb-1">
              <span className="nx-mono text-[10px] uppercase tracking-wider opacity-70">
                {label}
              </span>
              <span className="nx-mono text-[10px] tabular-nums">{value.toFixed(2)}</span>
            </div>
            <div className="h-1.5 rounded-pill bg-black/10 dark:bg-white/10 overflow-hidden">
              <motion.div
                className="h-full bg-nx-primary dark:bg-[#6aa3ff]"
                initial={{ width: 0 }}
                animate={{ width: `${Math.max(0, Math.min(1, value)) * 100}%` }}
                transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function OverallScore({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-3">
      <div className="relative h-14 w-14 grid place-items-center">
        <svg className="absolute inset-0" viewBox="0 0 36 36">
          <circle
            cx="18" cy="18" r="16"
            fill="none"
            stroke="currentColor"
            strokeOpacity="0.15"
            strokeWidth="2"
          />
          <motion.circle
            cx="18" cy="18" r="16"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            transform="rotate(-90 18 18)"
            initial={{ strokeDasharray: "0 100" }}
            animate={{ strokeDasharray: `${pct} 100` }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            style={{ pathLength: 1 }}
          />
        </svg>
        <span className="nx-mono text-sm font-semibold tabular-nums">{pct}</span>
      </div>
      <div className="leading-tight">
        <div className="nx-mono text-[10px] uppercase tracking-widest opacity-60">Overall</div>
        <div className="font-display text-lg">prompt score</div>
      </div>
    </div>
  );
}

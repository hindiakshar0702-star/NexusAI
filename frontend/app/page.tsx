"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Sparkles, Gauge, GitBranch, Brain, Library, Boxes, ShieldCheck, Database,
  ArrowRight,
} from "lucide-react";
import { Topbar } from "@/components/Topbar";
import { api } from "@/lib/api";

const FEATURES = [
  {
    href: "/generate",
    title: "Autonomous Generator",
    desc: "Turn a half-formed idea into beginner / advanced / pro prompts, tuned for the target platform.",
    icon: Sparkles,
  },
  {
    href: "/analyze",
    title: "Real-Time Analyzer",
    desc: "Score any prompt across clarity, specificity, creativity, realism, safety, and platform fit.",
    icon: Gauge,
  },
  {
    href: "/chains",
    title: "Prompt Chain Builder",
    desc: "Decompose a goal into a dependent chain of sub-prompts. Each step is a real, scored prompt.",
    icon: GitBranch,
  },
  {
    href: "/agents",
    title: "Multi-Agent Loop",
    desc: "Writer · Critic · Optimizer agents collaborate until the prompt clears the quality bar.",
    icon: Brain,
  },
  {
    href: "/library",
    title: "Smart Templates",
    desc: "Reusable expert frameworks. Auto-selected by domain and idea keywords.",
    icon: Library,
  },
  {
    href: "/training",
    title: "Training Automation",
    desc: "Generate synthetic datasets, eval rubrics, and RL reward scenarios from a schema.",
    icon: Boxes,
  },
  {
    href: "/safety",
    title: "Safety Layer",
    desc: "Rule-based ethics gate. Detects unsafe asks and surfaces PII for redaction.",
    icon: ShieldCheck,
  },
  {
    href: "/memory",
    title: "Self-Learning Memory",
    desc: "Tracks successful prompt patterns. Recall by similarity. Feeds the evolution engine.",
    icon: Database,
  },
];

export default function Dashboard() {
  const [memory, setMemory] = useState<{
    prompts: number; feedback_entries: number; success_patterns: number;
    top_patterns: Array<[string, number]>;
  } | null>(null);
  const [healthOk, setHealthOk] = useState<boolean | null>(null);

  useEffect(() => {
    api.health()
      .then(() => setHealthOk(true))
      .catch(() => setHealthOk(false));
    api.memorySnapshot().then(setMemory).catch(() => undefined);
  }, []);

  return (
    <>
      <Topbar
        title="Dashboard"
        subtitle="Autonomous prompt engineering, end-to-end."
        right={
          <span
            className={
              "nx-pill nx-mono border " +
              (healthOk === null
                ? "border-nx-line/30 opacity-60"
                : healthOk
                ? "border-emerald-500/40 text-emerald-600 dark:text-emerald-400"
                : "border-red-500/40 text-red-600 dark:text-red-400")
            }
          >
            <span
              className={
                "h-1.5 w-1.5 rounded-full " +
                (healthOk === null ? "bg-current" : healthOk ? "bg-emerald-500" : "bg-red-500")
              }
            />
            {healthOk === null ? "checking…" : healthOk ? "backend online" : "backend offline"}
          </span>
        }
      />

      <section className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        <Stat label="Prompts in memory" value={memory?.prompts ?? "—"} />
        <Stat label="Feedback entries" value={memory?.feedback_entries ?? "—"} />
        <Stat label="Success patterns" value={memory?.success_patterns ?? "—"} />
      </section>

      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
        {FEATURES.map((f, i) => (
          <motion.div
            key={f.href}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04, duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          >
            <Link href={f.href} className="nx-card group flex flex-col gap-3 hover:border-nx-primary/40 transition-colors h-full">
              <div className="flex items-center justify-between">
                <div className="h-9 w-9 rounded-pill bg-nx-primary/10 dark:bg-white/5 grid place-items-center">
                  <f.icon className="h-4 w-4 text-nx-primary dark:text-[#6aa3ff]" />
                </div>
                <ArrowRight className="h-4 w-4 opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all duration-nx-fast" />
              </div>
              <h3 className="font-display text-lg leading-tight">{f.title}</h3>
              <p className="text-sm opacity-75 leading-relaxed">{f.desc}</p>
            </Link>
          </motion.div>
        ))}
      </section>

      {memory?.top_patterns?.length ? (
        <section className="nx-card">
          <div className="flex items-baseline justify-between mb-3">
            <div>
              <div className="nx-section-title">memory · success patterns</div>
              <h2 className="font-display text-xl">Patterns that score well</h2>
            </div>
            <Link href="/memory" className="nx-mono text-xs uppercase tracking-wider opacity-70 hover:opacity-100">
              view all →
            </Link>
          </div>
          <div className="flex flex-wrap gap-2">
            {memory.top_patterns.slice(0, 18).map(([phrase, count]) => (
              <span key={phrase} className="nx-pill border border-nx-line/20 dark:border-nx-dark-line">
                <span className="opacity-90">{phrase}</span>
                <span className="opacity-60 nx-mono">×{count}</span>
              </span>
            ))}
          </div>
        </section>
      ) : null}
    </>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="nx-card flex flex-col">
      <span className="nx-section-title">{label}</span>
      <span className="font-display text-3xl mt-1 tabular-nums">{value}</span>
    </div>
  );
}

"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Brain, Sparkles, PenTool, Search, Zap } from "lucide-react";
import { Topbar } from "@/components/Topbar";
import { LoadingShimmer } from "@/components/LoadingShimmer";
import { EmptyState } from "@/components/EmptyState";
import { PromptCard } from "@/components/PromptCard";
import { SkillSelect } from "@/components/Selectors";
import { api, type AgentRunResult, type SkillLevel } from "@/lib/api";

const AGENT_META: Record<string, { icon: any; tone: string }> = {
  writer:   { icon: PenTool, tone: "from-blue-500/20 to-blue-500/0 border-blue-500/30" },
  critic:   { icon: Search,  tone: "from-amber-500/20 to-amber-500/0 border-amber-500/30" },
  optimizer:{ icon: Zap,     tone: "from-emerald-500/20 to-emerald-500/0 border-emerald-500/30" },
};

export default function AgentsPage() {
  const [idea, setIdea] = useState("");
  const [skill, setSkill] = useState<SkillLevel>("pro");
  const [result, setResult] = useState<AgentRunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (!idea.trim()) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const r = await api.agents({ raw_idea: idea, skill_level: skill });
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Agent run failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Topbar title="Multi-Agent Loop" subtitle="writer · critic · optimizer" />

      <section className="nx-card mb-4">
        <label className="nx-label">Idea</label>
        <textarea
          className="nx-textarea min-h-[100px]"
          placeholder="The agents will write, critique, and re-optimize until quality plateaus."
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter") submit();
          }}
        />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
          <div>
            <label className="nx-label">Skill level</label>
            <SkillSelect value={skill} onChange={setSkill} />
          </div>
          <div className="sm:col-span-2 flex items-end">
            <button onClick={submit} disabled={loading || !idea.trim()} className="nx-btn-primary w-full">
              <Sparkles className="h-4 w-4" />
              {loading ? "agents working…" : "Run agents"}
            </button>
          </div>
        </div>
      </section>

      {error && (
        <div className="nx-card border border-red-500/40 text-red-600 dark:text-red-400 mb-4">{error}</div>
      )}

      {loading && <LoadingShimmer />}

      {!loading && !result && !error && (
        <EmptyState
          icon={<Brain className="h-6 w-6" />}
          title="Three specialized agents collaborate"
          description="Writer drafts, Critic surfaces weaknesses with the analyzer, Optimizer mutates the prompt and keeps the strongest variant. The loop stops when the score clears the bar or stops improving."
        />
      )}

      {result && (
        <section className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
          <PromptCard prompt={result.final} />

          <aside className="nx-card">
            <div className="nx-section-title mb-3">Trace · {result.trace.length} steps</div>
            <ol className="flex flex-col gap-2">
              {result.trace.map((t, i) => {
                const meta = AGENT_META[t.agent] ?? { icon: Brain, tone: "" };
                const Icon = meta.icon;
                return (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05, duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
                    className={"rounded-2xl p-3 border bg-gradient-to-br " + meta.tone}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="h-6 w-6 grid place-items-center rounded-pill bg-black/10 dark:bg-white/10">
                          <Icon className="h-3.5 w-3.5" />
                        </span>
                        <span className="font-medium text-sm capitalize">{t.agent}</span>
                        <span className="nx-mono text-[10px] opacity-60 uppercase tracking-wider">{t.action}</span>
                      </div>
                      <span className="nx-mono text-xs tabular-nums">
                        {(t.score * 100).toFixed(0)}
                      </span>
                    </div>
                    {t.note && <p className="text-xs opacity-80 mt-2 leading-relaxed">{t.note}</p>}
                  </motion.li>
                );
              })}
            </ol>
          </aside>
        </section>
      )}
    </>
  );
}

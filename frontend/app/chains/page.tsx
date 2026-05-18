"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { GitBranch, Sparkles } from "lucide-react";
import { Topbar } from "@/components/Topbar";
import { LoadingShimmer } from "@/components/LoadingShimmer";
import { EmptyState } from "@/components/EmptyState";
import { PromptCard } from "@/components/PromptCard";
import { PlatformSelect, SkillSelect } from "@/components/Selectors";
import { api, type Platform, type PromptChain, type SkillLevel } from "@/lib/api";

export default function ChainsPage() {
  const [goal, setGoal] = useState("");
  const [platform, setPlatform] = useState<Platform | "auto">("auto");
  const [skill, setSkill] = useState<SkillLevel>("advanced");
  const [chain, setChain] = useState<PromptChain | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState<number>(0);

  const submit = async () => {
    if (!goal.trim()) return;
    setLoading(true); setError(null); setChain(null);
    try {
      const c = await api.chain({
        raw_idea: goal,
        skill_level: skill,
        platform: platform === "auto" ? undefined : platform,
      });
      setChain(c);
      setActiveStep(0);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to build chain.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Topbar title="Prompt Chain Builder" subtitle="goal → dependent steps" />

      <section className="nx-card mb-4">
        <label className="nx-label">Top-level goal</label>
        <input
          className="nx-input"
          placeholder="e.g. launch a marketing site for an AI test runner"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
          <div>
            <label className="nx-label">Skill level</label>
            <SkillSelect value={skill} onChange={setSkill} />
          </div>
          <div>
            <label className="nx-label">Platform bias</label>
            <PlatformSelect value={platform} onChange={setPlatform} />
          </div>
          <div className="flex items-end">
            <button onClick={submit} disabled={loading || !goal.trim()} className="nx-btn-primary w-full">
              <Sparkles className="h-4 w-4" />
              {loading ? "building…" : "Build chain"}
            </button>
          </div>
        </div>
      </section>

      {error && (
        <div className="nx-card border border-red-500/40 text-red-600 dark:text-red-400 mb-4">{error}</div>
      )}

      {loading && <LoadingShimmer />}

      {!loading && !chain && !error && (
        <EmptyState
          icon={<GitBranch className="h-6 w-6" />}
          title="Decompose any goal into a real prompt chain"
          description="Each step is a fully scored, platform-tuned prompt. Steps depend on the previous step's output, so you can run the chain end-to-end."
        />
      )}

      {chain && (
        <section className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-4">
          <aside className="nx-card sticky top-4 self-start">
            <div className="nx-section-title mb-2">Chain · {chain.steps.length} steps</div>
            <ol className="flex flex-col gap-1">
              {chain.steps.map((s, i) => (
                <li key={s.name}>
                  <button
                    onClick={() => setActiveStep(i)}
                    className={
                      "w-full text-left rounded-2xl px-3 py-2 transition-colors duration-nx-fast border " +
                      (i === activeStep
                        ? "bg-nx-primary text-white border-nx-primary"
                        : "border-transparent hover:bg-black/5 dark:hover:bg-white/5")
                    }
                  >
                    <div className="flex items-center gap-2">
                      <span className="nx-mono text-[10px] opacity-70">{String(i + 1).padStart(2, "0")}</span>
                      <span className="font-medium text-sm">{s.name}</span>
                    </div>
                    <div className={"text-xs mt-0.5 " + (i === activeStep ? "opacity-90" : "opacity-60")}>
                      {s.purpose.split(".")[0]}.
                    </div>
                  </button>
                </li>
              ))}
            </ol>
            <div className="mt-3 pt-3 border-t border-nx-line/10 dark:border-nx-dark-line">
              <div className="nx-section-title">rationale</div>
              <p className="text-xs opacity-80 mt-1">{chain.rationale}</p>
            </div>
          </aside>

          <motion.div
            key={activeStep}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
          >
            <PromptCard prompt={chain.steps[activeStep].prompt} />
          </motion.div>
        </section>
      )}
    </>
  );
}

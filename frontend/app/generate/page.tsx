"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, Wand2, Layers } from "lucide-react";
import { Topbar } from "@/components/Topbar";
import { PromptCard } from "@/components/PromptCard";
import { LoadingShimmer } from "@/components/LoadingShimmer";
import { EmptyState } from "@/components/EmptyState";
import { DomainSelect, PlatformSelect, SkillSelect } from "@/components/Selectors";
import { api, type Domain, type Platform, type Prompt, type SkillLevel, type Intent } from "@/lib/api";

export default function GeneratorPage() {
  const [idea, setIdea] = useState("");
  const [domain, setDomain] = useState<Domain | "auto">("auto");
  const [platform, setPlatform] = useState<Platform | "auto">("auto");
  const [skill, setSkill] = useState<SkillLevel>("advanced");
  const [tier, setTier] = useState<"single" | "tiered">("single");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [intent, setIntent] = useState<Intent | null>(null);
  const [results, setResults] = useState<Prompt[]>([]);

  const submit = async () => {
    if (!idea.trim()) return;
    setLoading(true);
    setError(null);
    setResults([]);
    try {
      const args = {
        raw_idea: idea,
        domain: domain === "auto" ? undefined : domain,
        platform: platform === "auto" ? undefined : platform,
      };
      // run intent prediction in parallel for the live "Predicted intent" panel
      const intentP = api.intent(args).catch(() => null);
      const promptsP =
        tier === "tiered"
          ? api.generateTiered(args)
          : api.generate({ ...args, skill_level: skill }).then((p) => [p]);

      const [predicted, prompts] = await Promise.all([intentP, promptsP]);
      setIntent(predicted);
      setResults(prompts);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to generate prompt.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Topbar
        title="Autonomous Generator"
        subtitle="rough idea → expert prompt"
      />

      <section className="nx-card mb-4">
        <label className="nx-label">Your idea</label>
        <textarea
          className="nx-textarea min-h-[120px]"
          placeholder="e.g. cinematic 8s clip of a robot sipping espresso in a parisian cafe at sunset"
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter") submit();
          }}
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
          <div>
            <label className="nx-label">Domain</label>
            <DomainSelect value={domain} onChange={setDomain} />
          </div>
          <div>
            <label className="nx-label">Platform</label>
            <PlatformSelect value={platform} onChange={setPlatform} />
          </div>
          <div>
            <label className="nx-label">Skill level</label>
            <SkillSelect value={skill} onChange={setSkill} />
          </div>
          <div>
            <label className="nx-label">Output</label>
            <div className="flex gap-2">
              <button
                onClick={() => setTier("single")}
                className={`nx-btn flex-1 ${tier === "single" ? "bg-nx-primary text-white border-nx-primary" : ""}`}
              >
                <Wand2 className="h-3.5 w-3.5" /> single
              </button>
              <button
                onClick={() => setTier("tiered")}
                className={`nx-btn flex-1 ${tier === "tiered" ? "bg-nx-primary text-white border-nx-primary" : ""}`}
              >
                <Layers className="h-3.5 w-3.5" /> 3 tiers
              </button>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-between mt-4">
          <span className="nx-mono text-[11px] opacity-60">⌘ + Enter to generate</span>
          <button onClick={submit} disabled={loading || !idea.trim()} className="nx-btn-primary">
            <Sparkles className="h-4 w-4" />
            {loading ? "generating…" : "Generate"}
          </button>
        </div>
      </section>

      {intent && (
        <motion.section
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
          className="nx-card mb-4"
        >
          <div className="nx-section-title mb-2">Predicted intent · confidence {intent.confidence}</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <Field label="Domain" value={intent.domain} />
            <Field label="Platform" value={intent.platform} />
            <Field label="Audience" value={intent.audience} />
            <Field label="Tone" value={intent.tone} />
          </div>
          {intent.goals.length > 0 && (
            <div className="mt-3 text-sm">
              <span className="nx-section-title block mb-1">Goals</span>
              <ul className="list-disc list-inside opacity-90">
                {intent.goals.map((g) => <li key={g}>{g}</li>)}
              </ul>
            </div>
          )}
          {intent.missing_details.length > 0 && (
            <div className="mt-3">
              <span className="nx-section-title block mb-1">Open questions</span>
              <ul className="space-y-1 text-sm">
                {intent.missing_details.map((q) => (
                  <li key={q} className="flex gap-2"><span className="opacity-60">?</span><span>{q}</span></li>
                ))}
              </ul>
            </div>
          )}
        </motion.section>
      )}

      {error && (
        <div className="nx-card border border-red-500/40 text-red-600 dark:text-red-400 mb-4">
          {error}
        </div>
      )}

      {loading && <LoadingShimmer />}

      {!loading && !results.length && !error && (
        <EmptyState
          icon={<Sparkles className="h-6 w-6" />}
          title="Drop a half-formed idea above"
          description="Domain and platform are inferred automatically. Switch to '3 tiers' to compare beginner, advanced, and pro versions of the same prompt."
        />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-3 mt-4">
        {results.map((p, i) => (
          <PromptCard key={p.id} prompt={p} index={i} />
        ))}
      </div>
    </>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-nx-line/15 dark:border-nx-dark-line p-3">
      <div className="nx-section-title">{label}</div>
      <div className="nx-mono text-sm mt-1">{value}</div>
    </div>
  );
}

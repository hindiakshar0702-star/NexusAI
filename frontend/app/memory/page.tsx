"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Database, RefreshCw } from "lucide-react";
import { Topbar } from "@/components/Topbar";
import { api } from "@/lib/api";

export default function MemoryPage() {
  const [snap, setSnap] = useState<Awaited<ReturnType<typeof api.memorySnapshot>> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    api.memorySnapshot().then(setSnap).catch((e) => setError(e.message));
  }, [refreshKey]);

  return (
    <>
      <Topbar
        title="Self-Learning Memory"
        subtitle="successful prompt patterns"
        right={
          <button
            onClick={() => setRefreshKey((k) => k + 1)}
            className="nx-btn-ghost"
          >
            <RefreshCw className="h-4 w-4" /> refresh
          </button>
        }
      />

      {error && (
        <div className="nx-card border border-red-500/40 text-red-600 dark:text-red-400 mb-4">{error}</div>
      )}

      <section className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
        <Stat label="Prompts" value={snap?.prompts ?? "—"} />
        <Stat label="Feedback entries" value={snap?.feedback_entries ?? "—"} />
        <Stat label="Success patterns" value={snap?.success_patterns ?? "—"} />
      </section>

      <section className="nx-card">
        <div className="flex items-baseline justify-between mb-3">
          <div>
            <div className="nx-section-title">top patterns</div>
            <h2 className="font-display text-xl">Frequent token bigrams in high-scoring prompts</h2>
          </div>
        </div>
        {!snap?.top_patterns?.length ? (
          <div className="flex items-center gap-3 text-sm opacity-70">
            <Database className="h-4 w-4" />
            No patterns yet — generate prompts to seed memory.
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {snap.top_patterns.map(([phrase, count], i) => (
              <motion.span
                key={phrase}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.02, duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
                className="nx-pill border border-nx-line/30 dark:border-nx-dark-line"
              >
                <span>{phrase}</span>
                <span className="opacity-60 nx-mono">×{count}</span>
              </motion.span>
            ))}
          </div>
        )}
      </section>
    </>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="nx-card">
      <div className="nx-section-title">{label}</div>
      <div className="font-display text-3xl mt-1 tabular-nums">{value}</div>
    </div>
  );
}

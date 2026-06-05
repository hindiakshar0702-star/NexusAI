"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Library, Search } from "lucide-react";
import { Topbar } from "@/components/Topbar";
import { EmptyState } from "@/components/EmptyState";
import { api, DOMAINS, type Domain } from "@/lib/api";

type Template = Awaited<ReturnType<typeof api.templates>>[number];

export default function LibraryPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [filter, setFilter] = useState<Domain | "all">("all");
  const [search, setSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.templates().then(setTemplates).catch((e) => setError(e.message));
  }, []);

  const filtered = useMemo(() => {
    return templates.filter((t) => {
      if (filter !== "all" && t.domain !== filter) return false;
      if (search.trim()) {
        const q = search.toLowerCase();
        return (
          t.name.toLowerCase().includes(q) ||
          t.description.toLowerCase().includes(q) ||
          t.keywords.some((k) => k.toLowerCase().includes(q))
        );
      }
      return true;
    });
  }, [templates, filter, search]);

  return (
    <>
      <Topbar title="Smart Templates" subtitle="reusable expert frameworks" />

      <section className="nx-card mb-4 flex flex-col gap-3 md:flex-row md:items-end">
        <div className="flex-1">
          <label className="nx-label">Search</label>
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 opacity-60" />
            <input
              className="nx-input pl-10"
              placeholder="search by name, keyword, or description"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
        <div className="md:w-56">
          <label className="nx-label">Filter by domain</label>
          <select
            className="nx-input"
            value={filter}
            onChange={(e) => setFilter(e.target.value as Domain | "all")}
          >
            <option value="all">all domains</option>
            {DOMAINS.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
      </section>

      {error && (
        <div className="nx-card border border-red-500/40 text-red-600 dark:text-red-400 mb-4">{error}</div>
      )}

      {!templates.length && !error && (
        <EmptyState
          icon={<Library className="h-6 w-6" />}
          title="Loading templates…"
          description="Frameworks are loaded from the backend's template library."
        />
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {filtered.map((t, i) => (
          <motion.article
            key={t.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04, duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
            className="nx-card flex flex-col gap-3"
          >
            <header className="flex items-start justify-between">
              <div>
                <div className="nx-section-title">{t.domain}</div>
                <h3 className="font-display text-lg leading-tight">{t.name}</h3>
              </div>
              <span className="nx-pill border border-nx-line/30 dark:border-nx-dark-line nx-mono text-[10px]">
                {t.id}
              </span>
            </header>
            <p className="text-sm opacity-80">{t.description}</p>
            <pre className="nx-mono text-[12px] leading-[1.5] whitespace-pre-wrap break-words rounded-2xl border border-nx-line/15 dark:border-nx-dark-line p-3 bg-white/40 dark:bg-black/20">
              {t.body}
            </pre>
            <div className="flex flex-wrap gap-1.5">
              {t.variables.map((v) => (
                <span key={v} className="nx-pill border border-nx-secondary/30 text-nx-secondary nx-mono">
                  {`{${v}}`}
                </span>
              ))}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {t.keywords.map((k) => (
                <span key={k} className="nx-mono text-[10px] opacity-60">#{k}</span>
              ))}
            </div>
          </motion.article>
        ))}
      </div>
    </>
  );
}

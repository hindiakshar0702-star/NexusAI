"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Boxes, Plus, Sparkles, X } from "lucide-react";
import { Topbar } from "@/components/Topbar";
import { LoadingShimmer } from "@/components/LoadingShimmer";
import { EmptyState } from "@/components/EmptyState";
import { api } from "@/lib/api";

type Field = { name: string; type: string };

const TYPES = ["str", "int", "float", "bool", "list[str]"];

export default function TrainingPage() {
  const [task, setTask] = useState("toxicity_classification");
  const [inputs, setInputs] = useState<Field[]>([
    { name: "text", type: "str" },
    { name: "language", type: "str" },
  ]);
  const [outputs, setOutputs] = useState<Field[]>([
    { name: "label", type: "str" },
    { name: "confidence", type: "float" },
  ]);
  const [n, setN] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [examples, setExamples] = useState<
    Array<{ input: Record<string, unknown>; output: Record<string, unknown>; difficulty: string; tags: string[] }>
  >([]);

  const submit = async () => {
    if (!task.trim()) return;
    setLoading(true); setError(null); setExamples([]);
    try {
      const result = await api.trainingDataset({
        task,
        input_schema: Object.fromEntries(inputs.filter((f) => f.name).map((f) => [f.name, f.type])),
        output_schema: Object.fromEntries(outputs.filter((f) => f.name).map((f) => [f.name, f.type])),
        n_per_difficulty: n,
      });
      setExamples(result.examples);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Topbar title="Training Automation" subtitle="synthetic datasets · evals · rewards" />

      <section className="nx-card mb-4 grid gap-4 lg:grid-cols-[1fr_1fr_1fr]">
        <div>
          <label className="nx-label">Task name</label>
          <input className="nx-input" value={task} onChange={(e) => setTask(e.target.value)} />
        </div>
        <SchemaEditor label="Input schema" fields={inputs} setFields={setInputs} />
        <SchemaEditor label="Output schema" fields={outputs} setFields={setOutputs} />

        <div>
          <label className="nx-label">Examples per difficulty (×3 difficulties)</label>
          <input
            type="number"
            className="nx-input"
            min={1}
            max={20}
            value={n}
            onChange={(e) => setN(Number(e.target.value))}
          />
        </div>
        <div className="lg:col-span-2 flex items-end">
          <button onClick={submit} disabled={loading} className="nx-btn-primary w-full">
            <Sparkles className="h-4 w-4" />
            {loading ? "synthesizing…" : "Generate dataset"}
          </button>
        </div>
      </section>

      {error && (
        <div className="nx-card border border-red-500/40 text-red-600 dark:text-red-400 mb-4">{error}</div>
      )}

      {loading && <LoadingShimmer />}

      {!loading && !examples.length && !error && (
        <EmptyState
          icon={<Boxes className="h-6 w-6" />}
          title="Synthesize a training set from a schema"
          description="The backend produces deterministic examples across easy / medium / hard difficulty buckets. Hand the result to your fine-tuning pipeline."
        />
      )}

      {examples.length > 0 && (
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {examples.map((ex, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03, duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
              className="nx-card"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="nx-pill border border-nx-line/30 dark:border-nx-dark-line">{ex.difficulty}</span>
                <span className="nx-mono text-[10px] opacity-60">#{i + 1}</span>
              </div>
              <div className="nx-section-title">input</div>
              <pre className="nx-mono text-[11.5px] whitespace-pre-wrap break-words rounded-2xl border border-nx-line/15 dark:border-nx-dark-line p-2 mb-2 bg-white/40 dark:bg-black/20">
                {JSON.stringify(ex.input, null, 2)}
              </pre>
              <div className="nx-section-title">output</div>
              <pre className="nx-mono text-[11.5px] whitespace-pre-wrap break-words rounded-2xl border border-nx-line/15 dark:border-nx-dark-line p-2 bg-white/40 dark:bg-black/20">
                {JSON.stringify(ex.output, null, 2)}
              </pre>
            </motion.div>
          ))}
        </section>
      )}
    </>
  );
}

function SchemaEditor({
  label, fields, setFields,
}: {
  label: string;
  fields: Field[];
  setFields: (f: Field[]) => void;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="nx-label !mb-0">{label}</span>
        <button
          onClick={() => setFields([...fields, { name: "", type: "str" }])}
          className="nx-btn-ghost !py-1 !px-2"
        >
          <Plus className="h-3 w-3" /> add
        </button>
      </div>
      <div className="flex flex-col gap-2">
        {fields.map((f, i) => (
          <div key={i} className="flex gap-1.5">
            <input
              className="nx-input flex-1"
              placeholder="field name"
              value={f.name}
              onChange={(e) => {
                const copy = [...fields];
                copy[i] = { ...f, name: e.target.value };
                setFields(copy);
              }}
            />
            <select
              className="nx-input w-28"
              value={f.type}
              onChange={(e) => {
                const copy = [...fields];
                copy[i] = { ...f, type: e.target.value };
                setFields(copy);
              }}
            >
              {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <button
              onClick={() => setFields(fields.filter((_, j) => j !== i))}
              className="nx-btn-ghost !py-1 !px-2"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

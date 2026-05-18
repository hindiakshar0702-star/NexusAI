// Thin wrapper over the FastAPI backend. All paths are routed through the
// /api/nexus/* rewrite defined in next.config.mjs so dev/prod use the same code.

export type Domain =
  | "text" | "image" | "video" | "animation" | "ui_ux" | "website" | "app"
  | "voice" | "music" | "3d" | "game" | "code" | "marketing" | "storytelling"
  | "training";

export type Platform =
  | "chatgpt" | "claude" | "gemini" | "midjourney" | "stable_diffusion"
  | "leonardo" | "runway" | "sora" | "figma" | "v0" | "bolt" | "cursor"
  | "generic";

export type SkillLevel = "beginner" | "advanced" | "pro";

export interface PromptScore {
  clarity: number;
  specificity: number;
  creativity: number;
  realism: number;
  safety: number;
  platform_fit: number;
  overall: number;
  weaknesses: string[];
  suggestions: string[];
}

export interface Prompt {
  id: string;
  text: string;
  domain: Domain;
  platform: Platform;
  skill_level: SkillLevel;
  title: string;
  system: string | null;
  negative: string | null;
  parameters: Record<string, unknown>;
  tags: string[];
  rationale: string;
  score: PromptScore | null;
  parent_id: string | null;
  created_at: number;
}

export interface Intent {
  raw_idea: string;
  domain: Domain;
  platform: Platform;
  audience: string;
  tone: string;
  goals: string[];
  emotions: string[];
  constraints: string[];
  missing_details: string[];
  confidence: number;
}

export interface ChainStep {
  name: string;
  purpose: string;
  prompt: Prompt;
  depends_on: string[];
}

export interface PromptChain {
  id: string;
  goal: string;
  steps: ChainStep[];
  rationale: string;
}

export interface AgentTrace {
  agent: string;
  action: string;
  prompt_id: string;
  score: number;
  note: string;
}

export interface AgentRunResult {
  final: Prompt;
  trace: AgentTrace[];
}

const BASE = "/api/nexus";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = (data.detail as string) || detail;
    } catch { /* ignore */ }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => request<{ status: string; memory: Record<string, number> }>("/health"),

  generate: (body: {
    raw_idea: string;
    domain?: Domain;
    platform?: Platform;
    skill_level?: SkillLevel;
    include_negative?: boolean;
  }) => request<Prompt>("/generate", { method: "POST", body: JSON.stringify(body) }),

  generateTiered: (body: { raw_idea: string; domain?: Domain; platform?: Platform }) =>
    request<Prompt[]>("/generate/tiered", { method: "POST", body: JSON.stringify(body) }),

  intent: (body: { raw_idea: string; domain?: Domain; platform?: Platform }) =>
    request<Intent>("/intent", { method: "POST", body: JSON.stringify(body) }),

  analyze: (body: { text: string; platform?: Platform }) =>
    request<PromptScore>("/analyze", { method: "POST", body: JSON.stringify(body) }),

  optimize: (body: { text: string; domain?: Domain; platform?: Platform }) =>
    request<{ text: string; score: PromptScore }>(
      "/optimize",
      { method: "POST", body: JSON.stringify(body) }
    ),

  evolve: (body: {
    text: string; domain?: Domain; platform?: Platform;
    skill_level?: SkillLevel; generations?: number; feedback_score?: number;
  }) => request<{ best: Prompt; history: Prompt[]; generations_run: number }>(
    "/evolve", { method: "POST", body: JSON.stringify(body) }
  ),

  chain: (body: { raw_idea: string; skill_level?: SkillLevel; platform?: Platform }) =>
    request<PromptChain>("/chain", { method: "POST", body: JSON.stringify(body) }),

  agents: (body: { raw_idea: string; skill_level?: SkillLevel }) =>
    request<AgentRunResult>("/agents/run", { method: "POST", body: JSON.stringify(body) }),

  feedback: (body: { prompt_id: string; score: number }) =>
    request<{ prompt_id: string; score: number; average: number }>(
      "/feedback", { method: "POST", body: JSON.stringify(body) }
    ),

  templates: () => request<Array<{
    id: string; name: string; domain: Domain; description: string;
    body: string; variables: string[]; keywords: string[];
  }>>("/templates"),

  safety: (body: { text: string }) =>
    request<{ safe: boolean; severity: string; flags: string[]; explanation: string }>(
      "/safety/review", { method: "POST", body: JSON.stringify(body) }
    ),

  trainingDataset: (body: {
    task: string; input_schema: Record<string, string>;
    output_schema: Record<string, string>; n_per_difficulty?: number;
  }) => request<{ task: string; examples: Array<{
    input: Record<string, unknown>; output: Record<string, unknown>;
    difficulty: string; tags: string[];
  }> }>("/training/dataset", { method: "POST", body: JSON.stringify(body) }),

  memorySnapshot: () => request<{
    prompts: number; feedback_entries: number; success_patterns: number;
    top_patterns: Array<[string, number]>;
  }>("/memory/snapshot"),
};

// Static catalogs (kept in sync with the backend enums).
export const DOMAINS: Domain[] = [
  "text", "image", "video", "animation", "ui_ux", "website", "app",
  "voice", "music", "3d", "game", "code", "marketing", "storytelling", "training",
];

export const PLATFORMS: Platform[] = [
  "chatgpt", "claude", "gemini", "midjourney", "stable_diffusion", "leonardo",
  "runway", "sora", "figma", "v0", "bolt", "cursor", "generic",
];

export const SKILLS: SkillLevel[] = ["beginner", "advanced", "pro"];

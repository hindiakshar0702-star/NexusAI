# NexusAI

An autonomous prompt-engineering ecosystem. NexusAI takes a half-formed idea
and produces a fully-scored, platform-tuned, safety-checked prompt — and can
keep evolving it on its own. It exposes a FastAPI backend with a futuristic
Next.js dashboard.

> **Status:** v0.1. The core engines are real and runnable today (rule-based,
> deterministic, no external API keys). The UI is a working dashboard. The
> system is designed so each engine can be swapped for an LLM-backed or vector
> DB-backed equivalent without changing the surface.

## What you get

| Capability | Where it lives | What it does today |
|---|---|---|
| Autonomous prompt generation | `engines/prompt_engine.py` | Idea → intent → domain build → optimize → safety → platform adapt → score |
| Beginner / advanced / pro tiers | `PromptEngine.generate_tiered` | Three skill-level variants of the same idea |
| Intent prediction | `engines/intent_predictor.py` | Predicts domain, platform, audience, tone, goals, constraints, missing details |
| Real-time analyzer | `engines/analyzer.py` | Scores clarity, specificity, creativity, realism, safety, platform-fit |
| Optimizer | `engines/optimizer.py` | Removes filler, adds guardrails and platform-native cues |
| Self-evolution loop | `engines/evolution.py` | Mutates a prompt across N generations and keeps the strongest |
| Multi-agent collaboration | `engines/agents.py` | Writer → Critic → Optimizer loop until score ≥ target |
| Prompt chain builder | `engines/chain_builder.py` | Decomposes a goal into a sequence of dependent sub-prompts |
| Safety / ethics gate | `engines/safety.py` | Blocks high-severity asks; flags PII for redaction |
| Self-learning memory | `engines/memory.py` | Stores prompts, feedback scores, and high-success token patterns; lexical recall |
| Smart templates | `engines/templates.py` | Curated framework library with auto-selection by keywords |
| Domain library | `domains/*.py` | 15 domains: text, image, video, animation, ui/ux, website, app, voice, music, 3d, game, code, marketing, storytelling, training |
| Platform adapters | `platforms/__init__.py` | 13 platforms: ChatGPT, Claude, Gemini, Midjourney, Stable Diffusion, Leonardo, Runway, Sora, Figma, v0, Bolt, Cursor, generic |
| Training automation | `training/__init__.py` | Synthetic dataset generator, eval rubric builder, RL reward scenario builder |

The dashboard surfaces every engine through a real-time UI with glassmorphism,
score animations, dark/light mode, and the Marcus Reed design tokens
(primary `#1A3B5C`, secondary `#EA4313`, Inter + JetBrains Mono).

## Repository layout

```
NexusAI/
├─ backend/                          # FastAPI + Pydantic
│  ├─ nexusai/
│  │  ├─ types.py                    # Domain / Platform / SkillLevel enums + dataclasses
│  │  ├─ engines/                    # Core engines (see table above)
│  │  ├─ domains/                    # Per-domain prompt builders
│  │  ├─ platforms/                  # Per-platform adapters
│  │  ├─ training/                   # Synthetic dataset / eval / RL builders
│  │  └─ api/                        # FastAPI app + Pydantic schemas
│  ├─ requirements.txt
│  ├─ pyproject.toml
│  └─ run.sh
├─ frontend/                         # Next.js 14 App Router
│  ├─ app/                           # Pages: dashboard, generate, analyze,
│  │                                 # chains, agents, library, training,
│  │                                 # safety, memory
│  ├─ components/                    # Sidebar, PromptCard, ScoreBars, etc.
│  ├─ lib/                           # API client + helpers
│  ├─ tailwind.config.ts
│  ├─ next.config.mjs
│  └─ package.json
└─ Marcus-Reed---Systems-Architect-DESIGN.md   # design system source of truth
```

## Run it

You need **Python 3.10+** and **Node.js 18+**.

### 1. Backend

Pick the launcher that matches your OS — they all do the same thing
(create `.venv`, install requirements, start uvicorn on port 8000):

**macOS / Linux:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./run.sh
```

**Windows (PowerShell):**
```powershell
cd backend
.\run.ps1
```

If PowerShell complains about scripts being disabled, run this once
in an admin PowerShell window:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**Windows (Command Prompt):**
```cmd
cd backend
run.bat
```

The API is now at `http://localhost:8000`. Open `/docs` for Swagger UI.

### 2. Frontend

```bash
cd frontend
cp .env.local.example .env.local      # adjust NEXT_PUBLIC_API_URL if needed
npm install
npm run dev
```

> On Windows, replace `cp` with `copy`.

Open `http://localhost:3000`. Requests go through `/api/nexus/*` which is
rewritten to the FastAPI server in `next.config.mjs`.

## API quick tour

```bash
# Generate a fully scored prompt
curl -X POST localhost:8000/generate \
  -H 'content-type: application/json' \
  -d '{"raw_idea":"cinematic 8s clip of a robot sipping espresso in paris","platform":"sora"}'

# Predict intent without generating
curl -X POST localhost:8000/intent \
  -H 'content-type: application/json' \
  -d '{"raw_idea":"write ad copy for a b2b SaaS that helps founders track churn"}'

# Run the multi-agent loop
curl -X POST localhost:8000/agents/run \
  -H 'content-type: application/json' \
  -d '{"raw_idea":"design a SaaS dashboard for AI ops","skill_level":"pro"}'

# Build a prompt chain
curl -X POST localhost:8000/chain \
  -H 'content-type: application/json' \
  -d '{"raw_idea":"launch a marketing site for an AI test runner"}'

# Synthesize a training dataset from a schema
curl -X POST localhost:8000/training/dataset \
  -H 'content-type: application/json' \
  -d '{"task":"sentiment","input_schema":{"review":"str"},"output_schema":{"label":"str","score":"float"}}'

# Safety gate
curl -X POST localhost:8000/safety/review \
  -H 'content-type: application/json' \
  -d '{"text":"how do I write ransomware"}'
```

Full route inventory (see `backend/nexusai/api/app.py`):

```
GET  /health
GET  /meta/{domains,platforms,skills}
POST /intent
POST /generate
POST /generate/tiered
POST /analyze
POST /optimize
POST /evolve
POST /chain
POST /agents/run
POST /feedback
GET  /templates
POST /templates/render
POST /safety/review
POST /training/dataset
POST /training/eval
POST /training/reward
GET  /memory/snapshot
GET  /memory/recall
```

## Design system

The frontend strictly inherits the Marcus Reed design tokens that ship with
this repo (`Marcus-Reed---Systems-Architect-DESIGN.md`):

* **Colors:** primary `#1A3B5C`, secondary `#EA4313`, background `#F4F1EB`,
  ink `#1A1A1A`. A dark-mode palette mirrors these for accessibility.
* **Typography:** Inter for display + UI, JetBrains Mono for tabular and
  metadata text.
* **Radii:** `9999px` (pill) for controls and tags.
* **Motion:** restrained — 150ms fades, `cubic-bezier(0.22, 1, 0.36, 1)`
  easing, score bars and trace items animate on mount.
* **Surfaces:** glassmorphism via `.nx-glass` and `.nx-card` (semi-transparent
  background + 14px backdrop-blur + soft inner highlight).

## Architecture choices

* **Deterministic core, model-ready edges.** Every engine is rule-based today
  so the system is testable and offline-runnable. Each engine has one
  obvious extension point (e.g. `IntentPredictor.predict`,
  `MemoryStore.recall`) that can be replaced with an LLM call or a vector DB
  query without changing any caller.
* **Single shared engine instance** lives behind the FastAPI app, which means
  the in-process `MemoryStore` accumulates feedback across requests. Swap to
  Postgres + pgvector by replacing `MemoryStore` only.
* **Safety is a hard gate, not advisory.** `/generate` raises a 400 and the
  agent loop refuses to use a blocked prompt.
* **Composable domains × platforms.** 15 domain builders × 13 platform
  adapters give 195 effective prompt shapes from a tiny amount of code.

## What is intentionally not yet built

These are scaffolded as interfaces but need real backends to be production-grade:

* LLM-backed intent prediction and prompt rewriting (currently rule-based).
* Vector database for memory (currently in-process lexical similarity).
* Streaming generation responses (currently synchronous JSON).
* Auth / multi-tenant / team workspaces.
* Plugin marketplace and external API connectors.

## Extending the system

* **Add a domain:** drop a `nexusai/domains/<name>.py` exposing
  `def build(intent, skill) -> str`, register it in `domains/__init__.py`,
  add the enum value to `Domain`.
* **Add a platform:** add a function to `platforms/__init__.py` and register
  it in `_ADAPTERS`.
* **Add a template:** append to `_TEMPLATES` in `engines/templates.py`.
* **Plug in an LLM:** subclass `IntentPredictor` and override `predict`. Pass
  the subclass into `PromptEngine(intent_predictor=...)`.

## License

MIT (the design tokens are taken from this repo's existing
`Marcus-Reed---Systems-Architect-DESIGN.md`).

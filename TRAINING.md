# Train your own NexusAI prompt-engineer model

This guide walks you from a fresh clone to a working **fine-tuned Llama 3.2
3B** that talks like NexusAI. The whole thing fits on Google Colab's free
T4 GPU and finishes in roughly 1 hour.

> **Heads up.** Your local machine (Windows, AMD Ryzen 3 3200G, 16 GB RAM,
> Vega integrated graphics) **cannot train this model locally** — Vega
> doesn't support CUDA. We use Colab for training and your local box for
> data export and inference. That's the standard setup.

---

## Big picture

```
┌────────────────────┐      ┌─────────────────┐      ┌───────────────────┐
│  NexusAI (local)   │ ───► │ JSONL dataset   │ ───► │  Colab Notebook   │
│  generates 1000s   │      │ (~5-20 MB)      │      │  Llama 3.2 3B +   │
│  of expert prompts │      │                 │      │  LoRA fine-tune   │
└────────────────────┘      └─────────────────┘      └────────┬──────────┘
                                                              │
                                          ┌───────────────────┼─────────────────┐
                                          ▼                   ▼                 ▼
                                   ┌───────────┐      ┌──────────────┐   ┌────────────┐
                                   │ HuggingFace│      │  Ollama on   │   │ NexusAI    │
                                   │   Hub     │      │  your laptop │   │ replaces   │
                                   │  (share)  │      │   (.gguf)    │   │ rules with │
                                   └───────────┘      └──────────────┘   │ your model │
                                                                         └────────────┘
```

You will:

1. Generate a JSONL dataset from NexusAI (3-10 minutes locally)
2. Open the included Colab notebook (browser, free GPU)
3. Train (30-60 minutes)
4. Test the model live in the notebook
5. Save it (Hugging Face Hub, GGUF for local use, or both)

---

## Prerequisites

| What | Why | Where to get |
|---|---|---|
| Python 3.10+ | Run the data exporter locally | https://python.org |
| Google account | Free Colab GPU | https://colab.research.google.com |
| Hugging Face account | Save / share your trained model (free, 10 GB) | https://huggingface.co/join |
| OpenAI API key (optional) | Better quality training data via GPT-4 teacher | https://platform.openai.com/api-keys |

You **already have** all of these. Skip ahead.

---

## Step 1 — Set up the backend locally

Open a terminal in the repo root.

```bash
cd backend
python -m venv .venv

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

Verify it works:

```bash
python -c "from nexusai.training import FineTuneDataExporter; print('ok')"
```

Should print `ok`.

---

## Step 2 — Generate your training dataset

There are **three ways** to do this. Pick whichever is most comfortable.

### Option A — CLI (recommended)

The fastest path. One command, watches its own progress, validates the
output file.

```bash
# 500 high-quality examples in llama format. ~30 seconds locally.
python -m scripts.export_training_data \
    --n 500 \
    --format llama \
    --min-score 0.75 \
    --out nexusai_train.jsonl
```

You'll see a progress bar and a summary like:

```
NexusAI training data export complete
============================================================
  Output file          nexusai_train.jsonl
  Requested            500
  Kept                 487
  Dropped (low score)  13
  Average score        0.8214
  Domains covered      animation, app, code, image, marketing, ...
  Duration (s)         12.34

validated: 487 valid JSON lines in nexusai_train.jsonl
```

#### Use your OpenAI key for higher-quality data

Your NexusAI outputs are already structurally great, but the language is
templated. The GPT-4 teacher rewrites them to sound natural while keeping
the structure. **Cost**: ~$0.50-2 for 500 examples with `gpt-4o-mini`.

```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."
pip install openai

python -m scripts.export_training_data \
    --n 500 \
    --use-teacher \
    --teacher-model gpt-4o-mini \
    --min-score 0.75 \
    --out nexusai_train.jsonl
```

```bash
# macOS/Linux
export OPENAI_API_KEY="sk-..."
pip install openai

python -m scripts.export_training_data \
    --n 500 --use-teacher --min-score 0.75 \
    --out nexusai_train.jsonl
```

This run takes a few minutes longer because each example makes one OpenAI
call (parallelized 4 at a time). The summary will show teacher stats:

```
  Teacher requested    487
  Teacher enhanced     485
  Teacher cache hits   0
  Teacher failed       2
```

#### Other useful CLI flags

```bash
# Restrict to specific domains (great if your model only needs to handle
# image + code + marketing).
--domains image code marketing

# Pump up the quality bar (fewer examples kept, but each is excellent)
--min-score 0.80

# Different output formats
--format alpaca    # for trainers that expect {instruction, input, output}
--format openai    # for OpenAI fine-tuning API

# Reproducibility
--seed 42

# Suppress the progress bar (useful in CI logs)
--quiet
```

### Option B — REST API

Keep the FastAPI server running and POST from anywhere.

```bash
# Terminal 1 — start the server
cd backend && ./run.sh

# Terminal 2 — request a download
curl -X POST http://localhost:8000/training/finetune/download \
    -H "content-type: application/json" \
    -d '{"n_examples": 500, "fmt": "llama", "min_score": 0.75}' \
    -o nexusai_train.jsonl
```

Other useful endpoints:

| Route | When to use |
|---|---|
| `POST /training/finetune/export` | Get records + stats inline as JSON |
| `POST /training/finetune/stream` | NDJSON stream — record per line, ideal for long runs |
| `POST /training/finetune/download` | Direct `.jsonl` file download with Content-Disposition |
| `GET /training/finetune/teacher-status` | Check whether GPT-4 polish is enabled |

### Option C — Python from a notebook

```python
from nexusai.training import FineTuneDataExporter, ExportConfig
from nexusai.types import Domain

cfg = ExportConfig(
    n_examples=500,
    fmt="llama",
    min_score=0.75,
    domains=[Domain.IMAGE, Domain.CODE, Domain.MARKETING],
    use_teacher=True,           # needs OPENAI_API_KEY
)
records, stats = FineTuneDataExporter().export(cfg, out_path="nexusai_train.jsonl")
print(stats.to_dict())
```

---

## Step 3 — How big should my dataset be?

| Examples | Use case | Time on Colab T4 | Quality |
|---|---|---|---|
| 200 | Smoke test the pipeline | 10 min | Underfit, language is off |
| **500** | **Recommended starting point** | **~30 min** | **Good** |
| 1000-2000 | Production-ish narrow model | 45-90 min | Very good |
| 5000+ | Multi-domain expert | 3-6 hours (Colab Pro) | Excellent |

For your first run, **stick to 500**. You'll see how the whole pipeline
works in under an hour. Iterate from there.

---

## Step 4 — Train on Colab

1. Open Google Colab: https://colab.research.google.com
2. **File → Upload notebook** → choose `notebooks/train_nexusai_model.ipynb`
3. **Runtime → Change runtime type → T4 GPU** (free tier)
4. Run cells top-to-bottom (`Shift+Enter` each, or **Runtime → Run all**)

The notebook is fully commented. Key checkpoints:

| Cell | What you should see |
|---|---|
| `nvidia-smi` | Tesla T4, 16280 MiB |
| Install Unsloth | `install ok` (~3 min first time) |
| Load Llama 3.2 3B | `params: 3.21B`, `vram in use: ~2.5 GB` |
| Attach LoRA | `trainable params: ~24M / 3.21B (~0.75%)` |
| Upload dataset | File picker — pick your `nexusai_train.jsonl` |
| Train | Loss should drop from ~2.0 to ~0.6-1.0 over 2 epochs |
| Test | Three sample generations look like NexusAI prompts |

### When training, watch the loss

```
Step 5     loss=1.9824
Step 10    loss=1.4231
Step 25    loss=0.9876
Step 50    loss=0.7234
Step 100   loss=0.6512
```

A healthy run drops fast at first then plateaus. If loss stays >1.5 at the
end, your dataset is too small or too noisy — generate more data with
`--min-score 0.80` and `--use-teacher`.

If loss drops to <0.3, the model is **memorizing** — reduce epochs to 1.

---

## Step 5 — Test your model

The notebook's "Step 9" cell runs three test prompts. Compare the output
to what NexusAI's rule-based engine produces for the same idea. You should
see:

- Same overall structure (`[domain | platform | skill]` header, body, sections)
- More natural language (especially if you used `--use-teacher`)
- Correct domain/platform routing on prompts not in training set

### A quick sanity check

Try an out-of-distribution prompt the model has never seen verbatim:

```python
generate("design an admin panel for a hospital scheduling system")
```

If it routes to `ui_ux` / `figma` and produces sensible content, your
fine-tune worked.

---

## Step 6 — Save and deploy

You have **three** ways to keep your trained model. Pick what you need.

### A) Hugging Face Hub (recommended — share + reuse from anywhere)

In the notebook:

1. Run the `notebook_login()` cell, paste your write-scope HF token from
   https://huggingface.co/settings/tokens
2. Edit the `HF_REPO` variable (e.g. `"yourname/nexusai-prompt-engineer"`)
3. Run `model.push_to_hub(...)` — uploads ~50-100 MB

Now anyone (including future-you on a different machine) can load it:

```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="yourname/nexusai-prompt-engineer",
    max_seq_length=2048,
    load_in_4bit=True,
)
FastLanguageModel.for_inference(model)
```

### B) GGUF for local use with Ollama

If you want the model running on **your laptop** (no API costs, fully
offline):

1. In the notebook, run the GGUF export cell (Step 12). Takes ~10 minutes.
2. Download the resulting `.gguf` file to your local machine (it's ~2 GB).
3. Install [Ollama](https://ollama.com) on Windows.
4. Create a `Modelfile`:
   ```
   FROM ./nexusai-llama3.2-3b-q4_k_m.gguf
   TEMPLATE """{{ if .System }}<|start_header_id|>system<|end_header_id|>{{ .System }}<|eot_id|>{{ end }}<|start_header_id|>user<|end_header_id|>{{ .Prompt }}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
   PARAMETER temperature 0.4
   ```
5. Build and run:
   ```bash
   ollama create nexusai -f Modelfile
   ollama run nexusai "design a saas dashboard for analytics"
   ```

> Your AMD APU **can** run inference (CPU mode) on the 4-bit GGUF. Expect
> 5-15 tokens/second — slow but workable. Faster if you upgrade to a discrete
> GPU later.

### C) Plug it back into NexusAI

Replace the deterministic `IntentPredictor` with your trained model. This
is roughly 30 lines of glue code — see the section below.

---

## Plugging your model into NexusAI

After training, you can swap NexusAI's rule-based engine for your model.
The cleanest extension point is `PromptEngine`:

```python
# backend/nexusai/engines/llm_backed_engine.py  (new file)
import os
import requests
from .prompt_engine import PromptEngine
from ..types import Domain, Platform, Prompt, SkillLevel


class LlmBackedPromptEngine(PromptEngine):
    """PromptEngine that calls your fine-tuned model instead of the rules."""

    def __init__(self, model_url: str, **kwargs):
        super().__init__(**kwargs)
        self.model_url = model_url   # e.g. "http://localhost:11434/api/chat" for Ollama

    def generate(self, raw_idea, skill_level=SkillLevel.ADVANCED,
                 domain=None, platform=None, include_negative=True):
        # Still run the deterministic intent predictor as a sanity layer
        intent = self.intent.predict(raw_idea, hint_domain=domain, hint_platform=platform)

        # Ask your model for the prompt body
        body = self._call_model(raw_idea, intent)

        # Run the existing safety + analyzer pipeline so callers get the same shape
        safety_report = self.safety.review(body)
        if not safety_report.safe:
            raise SafetyViolation(...)

        score = self.analyzer.analyze(body, intent.platform)
        return Prompt(
            id=Prompt.new_id(),
            text=body,
            domain=intent.domain,
            platform=intent.platform,
            skill_level=skill_level,
            title=raw_idea[:80],
            score=score,
            tags=["llm-backed"],
            rationale=f"generated by fine-tuned model ({self.model_url})",
        )

    def _call_model(self, raw_idea: str, intent) -> str:
        # Adapt this to your hosting choice (Ollama / HF Inference / Modal / etc.)
        response = requests.post(
            self.model_url,
            json={
                "model": "nexusai",
                "messages": [
                    {"role": "system", "content": "You are NexusAI..."},
                    {"role": "user",   "content": raw_idea},
                ],
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
```

Then wire it up in `api/app.py`:

```python
from nexusai.engines.llm_backed_engine import LlmBackedPromptEngine

if os.environ.get("NEXUSAI_USE_LLM"):
    engine = LlmBackedPromptEngine(
        model_url=os.environ.get("NEXUSAI_LLM_URL", "http://localhost:11434/api/chat"),
    )
else:
    engine = PromptEngine()   # default: rule-based
```

Now you can flip between rule-based and your trained model with an env var.

---

## Iteration loop (going from "good" to "great")

Most fine-tunes are 80% there after one round. To close the gap:

1. **Run the model on real ideas you care about.** Note where it fails.
2. **Generate targeted training data** for those failure modes:
   ```bash
   # Failures clustered in image domain? Train more on image.
   python -m scripts.export_training_data \
       --n 1000 --domains image \
       --min-score 0.80 --use-teacher \
       --out nexusai_train_v2.jsonl
   ```
3. **Concatenate datasets** (just `cat v1.jsonl v2.jsonl > combined.jsonl`).
4. **Retrain** with the combined dataset. The notebook's training cell
   handles any size you throw at it.
5. **Repeat.** Each round, score the model on a **fixed held-out set** of
   prompts so improvements are measurable.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `CUDA out of memory` during training | Sequence length too long | Set `MAX_SEQ_LENGTH = 1024` in the load cell |
| Loss doesn't drop below 1.5 | Dataset too small or noisy | Generate more with `--min-score 0.80 --use-teacher` |
| Loss drops to ~0 in 1 epoch | Overfitting / memorizing | Reduce `num_train_epochs` to 1 |
| Model generates gibberish at inference | Forgot `FastLanguageModel.for_inference(model)` | Add it before `generate()` |
| Colab disconnects mid-training | Free tier idle timeout (~90 min) | Train fewer steps, or upgrade to Colab Pro |
| `ImportError: openai` when using teacher | Package not installed | `pip install openai` |
| Teacher returns `None` for every example | Wrong API key, rate limit | Check `OPENAI_API_KEY` and your usage dashboard |
| GGUF file is huge (~7 GB) | Used `q8_0` instead of `q4_k_m` | Use `quantization_method="q4_k_m"` |
| Ollama responds slowly on AMD APU | No GPU acceleration, CPU only | Expected. ~5-15 t/s on Ryzen 3 |

---

## Cost summary (your setup)

| Item | Cost |
|---|---|
| NexusAI data export (local) | $0 |
| GPT-4o-mini teacher (500 examples) | ~$1-2 |
| Colab T4 training | $0 (free tier) |
| Hugging Face hosting | $0 (free for public models) |
| Ollama local inference | $0 |
| **Total for first model** | **~$2** |

If you skip the teacher (`--use-teacher` off), it's literally **$0**.

---

## What you've built

After this guide, you have:

- A reproducible **data pipeline** (`scripts/export_training_data.py`) that
  produces fresh training data on demand
- A reproducible **training notebook** (`notebooks/train_nexusai_model.ipynb`)
  you can re-run with new data anytime
- A **fine-tuned 3B-parameter model** that talks like NexusAI
- The model **hosted on Hugging Face** for sharing
- A **GGUF version** for offline use on your laptop
- Plug-and-play integration with NexusAI's existing engines

That's a complete training operation. Most of the work is now data
curation — the more diverse, high-quality data you feed it, the better
your model gets.

Happy training.

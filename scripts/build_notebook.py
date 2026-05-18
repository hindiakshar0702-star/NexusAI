#!/usr/bin/env python3
"""Build train_nexusai_model.ipynb from clean cell sources.

Editing .ipynb JSON by hand is error-prone (escaping, cell IDs, metadata).
This script keeps the cell *content* in plain triple-quoted strings here
and emits a valid notebook on demand. Re-run after editing.

Usage:
    python scripts/build_notebook.py [--out path/to/notebook.ipynb]
"""
from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List

# ----------------------------------------------------------------- cell sources

CELLS: List[Dict[str, Any]] = [
    {
        "type": "markdown",
        "src": """\
# Train your own NexusAI prompt engineer

This notebook fine-tunes **Llama 3.2 3B Instruct** on the JSONL dataset you
exported from NexusAI. It uses [Unsloth](https://github.com/unslothai/unsloth)
for ~2x speed and ~50% less VRAM, so it fits on a free Colab T4 GPU.

**Total time on free T4:** ~30-60 minutes for 500-1000 examples.

## What you'll do
1. Connect to a free GPU runtime
2. Install Unsloth and its dependencies
3. Load Llama 3.2 3B (4-bit quantized)
4. Attach LoRA adapters (only trains 1% of parameters)
5. Upload your `nexusai_train.jsonl`
6. Train for 1-3 epochs
7. Test the model on a fresh prompt
8. Save adapter weights and (optionally) push to Hugging Face Hub

## Before you start
- Runtime → Change runtime type → **T4 GPU** (free tier is fine)
- Have your NexusAI JSONL file ready (`nexusai_train.jsonl` in `llama` format)
- Hugging Face account if you want to push the trained model
""",
    },
    {
        "type": "markdown",
        "src": """\
## Step 1 — Confirm GPU is available

The cell below should print something like:
```
Tue Jan  1 00:00:00 2025
+-----------------------------------------------------------------------------+
| NVIDIA-SMI ...                Driver Version: ...   CUDA Version: ...      |
| ... Tesla T4 ... 16280MiB ...                                              |
+-----------------------------------------------------------------------------+
```
If you see "command not found" or no GPU rows, switch the runtime to GPU first.
""",
    },
    {
        "type": "code",
        "src": """\
!nvidia-smi""",
    },
    {
        "type": "markdown",
        "src": """\
## Step 2 — Install Unsloth and friends

Unsloth installs PyTorch, transformers, TRL, and bitsandbytes pinned to
versions that work together. The `colab-new` extra targets recent Colab
runtimes. This cell takes ~3 minutes the first time.
""",
    },
    {
        "type": "code",
        "src": """\
%%capture
# Pinned versions known to work on free Colab T4 (Jan 2025+).
!pip install --upgrade --quiet pip
!pip install --quiet "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
!pip install --quiet --no-deps "trl<0.9.0" "peft" "accelerate" "bitsandbytes"
!pip install --quiet datasets

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
print("install ok")""",
    },
    {
        "type": "markdown",
        "src": """\
## Step 3 — Load Llama 3.2 3B Instruct (4-bit)

Unsloth handles the 4-bit quantization automatically. The model is ~2.5 GB
of VRAM, leaving plenty of room on a 16 GB T4 for activations and gradients.

If you ever hit "CUDA out of memory" later, drop `max_seq_length` to 1024.
""",
    },
    {
        "type": "code",
        "src": """\
from unsloth import FastLanguageModel
import torch

MAX_SEQ_LENGTH = 2048   # NexusAI prompts rarely exceed ~600 tokens; 2048 is safe.
DTYPE = None            # auto: bfloat16 on Ampere+, float16 on T4
LOAD_IN_4BIT = True

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Llama-3.2-3B-Instruct-bnb-4bit",
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=DTYPE,
    load_in_4bit=LOAD_IN_4BIT,
)

print(f"loaded: {model.config.model_type}")
print(f"params: {model.num_parameters()/1e9:.2f}B")
print(f"vram in use: {torch.cuda.memory_allocated()/1e9:.2f} GB")""",
    },
    {
        "type": "markdown",
        "src": """\
## Step 4 — Attach LoRA adapters

LoRA (Low-Rank Adaptation) freezes the base model and only trains small
adapter matrices on the attention and MLP layers. We end up training
roughly **1% of the parameters** — the rest stay frozen, which is why this
fits in 16 GB and finishes in under an hour.

`r=16` is a good default; bump to 32 if you want slightly higher quality
and have time to spare.
""",
    },
    {
        "type": "code",
        "src": """\
model = FastLanguageModel.get_peft_model(
    model,
    r=16,                          # LoRA rank
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_alpha=16,
    lora_dropout=0.0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=42,
    use_rslora=False,
    loftq_config=None,
)

trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
print(f"trainable params: {trainable/1e6:.2f}M / {total/1e9:.2f}B "
      f"({100*trainable/total:.2f}%)")""",
    },
    {
        "type": "markdown",
        "src": """\
## Step 5 — Upload your NexusAI dataset

Run the cell below and a file picker will appear. Choose your
**`nexusai_train.jsonl`** file (the `llama` format — `{"messages": [...]}`
per line). This is what the NexusAI CLI generates by default:

```bash
python -m scripts.export_training_data --n 1000 --format llama --out nexusai_train.jsonl
```

If you'd rather pull the file from a URL or Google Drive, replace the
upload block with `!wget <url>` or `from google.colab import drive`.
""",
    },
    {
        "type": "code",
        "src": """\
from google.colab import files
print("Choose your nexusai_train.jsonl file:")
uploaded = files.upload()

# Pick the first .jsonl file the user uploaded.
DATA_PATH = next(name for name in uploaded if name.endswith(".jsonl"))
print(f"using: {DATA_PATH}")""",
    },
    {
        "type": "markdown",
        "src": """\
## Step 6 — Load and inspect the dataset

We sanity-check that:
- Every line is valid JSON
- Each record has a `messages` field with at least user + assistant turns
- We can see one full example to confirm the format
""",
    },
    {
        "type": "code",
        "src": """\
import json
from datasets import Dataset

def _load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"line {line_no} is not valid JSON: {e}")
            if "messages" not in rec or not isinstance(rec["messages"], list):
                raise ValueError(f"line {line_no} is missing a 'messages' list. "
                                 f"Did you export with --format llama?")
            roles = {m.get("role") for m in rec["messages"]}
            if not {"user", "assistant"}.issubset(roles):
                raise ValueError(f"line {line_no} must contain at least user + assistant turns")
            rows.append(rec)
    return rows

rows = _load_jsonl(DATA_PATH)
dataset = Dataset.from_list(rows)
print(f"loaded {len(dataset)} examples")
print()
print("--- first example ---")
ex = dataset[0]["messages"]
for m in ex:
    role = m["role"].upper()
    content = m["content"]
    print(f"[{role}]")
    print(content[:300] + ("..." if len(content) > 300 else ""))
    print()""",
    },
    {
        "type": "markdown",
        "src": """\
## Step 7 — Apply the Llama 3 chat template

Unsloth's `get_chat_template` configures the tokenizer to format
`{messages: [...]}` rows using Llama 3's official template. We then map
each row into a single `text` column the trainer expects.
""",
    },
    {
        "type": "code",
        "src": """\
from unsloth.chat_templates import get_chat_template

tokenizer = get_chat_template(
    tokenizer,
    chat_template="llama-3.1",   # also works for 3.2 family
)

def _format(batch):
    convos = batch["messages"]
    texts = [
        tokenizer.apply_chat_template(c, tokenize=False, add_generation_prompt=False)
        for c in convos
    ]
    return {"text": texts}

dataset = dataset.map(_format, batched=True, remove_columns=dataset.column_names)
print(f"formatted {len(dataset)} examples")
print("--- first formatted text (truncated) ---")
print(dataset[0]["text"][:600])""",
    },
    {
        "type": "markdown",
        "src": """\
## Step 8 — Train!

We use `SFTTrainer` from TRL (the standard supervised fine-tuning trainer).

**Settings explained:**
- `per_device_train_batch_size=2` — keeps VRAM headroom
- `gradient_accumulation_steps=4` — gives you an effective batch size of 8
- `num_train_epochs=2` — usually plenty for narrow tasks; bump to 3 if loss is still trending down
- `max_steps=-1` — train through all epochs (set to a small number like 60 for a quick smoke test)
- `learning_rate=2e-4` — Unsloth-recommended for LoRA on Llama
- `warmup_steps=5` — short warmup; we don't have many steps total

The first cell of training prints the dataset length and effective steps.
Watch the loss column — it should drop from ~2.0 to ~0.5-1.0 over training.
""",
    },
    {
        "type": "code",
        "src": """\
from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LENGTH,
    dataset_num_proc=2,
    packing=False,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        num_train_epochs=2,
        max_steps=-1,
        learning_rate=2e-4,
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=5,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=42,
        output_dir="outputs",
        report_to="none",
        save_strategy="no",
    ),
)

print(f"training on {len(dataset)} examples")
print(f"effective batch size: {2 * 4}")
print(f"approx steps: {(len(dataset) // 8) * 2}")
print()

stats = trainer.train()
print()
print(f"training complete in {stats.metrics['train_runtime']:.1f}s")
print(f"final loss: {stats.metrics['train_loss']:.4f}")""",
    },
    {
        "type": "markdown",
        "src": """\
## Step 9 — Test the trained model

Try a fresh idea the model has never seen verbatim. The trained model
should produce a structured prompt with the same shape it learned from
NexusAI: `[domain | platform | skill]` header, then the body, then
optional `--- system ---` / `--- negative ---` / `--- parameters ---`
sections.
""",
    },
    {
        "type": "code",
        "src": """\
from unsloth.chat_templates import get_chat_template

# Re-apply template just in case (idempotent)
tokenizer = get_chat_template(tokenizer, chat_template="llama-3.1")
FastLanguageModel.for_inference(model)   # 2x faster generation

SYSTEM = (
    "You are NexusAI, an expert prompt engineer. Given a short raw idea "
    "from a user, produce a high-quality, structured prompt suitable for "
    "the right AI tool. Adapt to the user's domain, target platform, "
    "audience, and skill level. Be specific, concrete, and platform-native."
)

def generate(idea: str, max_new_tokens: int = 512) -> str:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user",   "content": idea},
    ]
    inputs = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_tensors="pt"
    ).to("cuda")
    out = model.generate(
        input_ids=inputs,
        max_new_tokens=max_new_tokens,
        temperature=0.4,
        top_p=0.9,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )
    text = tokenizer.decode(out[0][inputs.shape[-1]:], skip_special_tokens=True)
    return text

print("--- test 1: image ---")
print(generate("photorealistic close-up of an old astronaut helmet on a desk"))
print()
print("--- test 2: code ---")
print(generate("write a python function that retries an http call with exponential backoff"))
print()
print("--- test 3: ui_ux ---")
print(generate("design a settings screen for a meditation app"))""",
    },
    {
        "type": "markdown",
        "src": """\
## Step 10 — Save the LoRA adapter

This saves only the small LoRA weights (~50-100 MB), not the full base
model. You can load them later by calling `FastLanguageModel.from_pretrained`
with the same base model + your adapter directory.
""",
    },
    {
        "type": "code",
        "src": """\
LOCAL_DIR = "nexusai-prompt-engineer-lora"
model.save_pretrained(LOCAL_DIR)
tokenizer.save_pretrained(LOCAL_DIR)
print(f"saved to: {LOCAL_DIR}")
!ls -lh {LOCAL_DIR}""",
    },
    {
        "type": "markdown",
        "src": """\
## Step 11 — (Optional) Push to Hugging Face Hub

Public LoRAs are free to host on the Hub. Run the login cell, paste your
**write-scope** token from
[huggingface.co/settings/tokens](https://huggingface.co/settings/tokens),
and the next cell uploads your adapter to `<your-username>/<repo-name>`.

Skip these cells if you only want to use the model inside Colab.
""",
    },
    {
        "type": "code",
        "src": """\
from huggingface_hub import notebook_login
notebook_login()""",
    },
    {
        "type": "code",
        "src": """\
# Replace with your own repo name. Will be created if it doesn't exist.
HF_REPO = "your-username/nexusai-prompt-engineer"

model.push_to_hub(HF_REPO, private=False)
tokenizer.push_to_hub(HF_REPO, private=False)
print(f"pushed to: https://huggingface.co/{HF_REPO}")""",
    },
    {
        "type": "markdown",
        "src": """\
## Step 12 — (Optional) Export merged GGUF for Ollama / llama.cpp

If you want to run the model **locally** on your laptop with Ollama or
llama.cpp, export it as merged 4-bit GGUF. This produces a single file
~2 GB you can `ollama create` from. Skip this cell if you only need the
adapter.

> Note: GGUF export takes 5-10 minutes on Colab T4.
""",
    },
    {
        "type": "code",
        "src": """\
# This merges the LoRA into the base weights and saves a quantized GGUF.
# Comment out the formats you don't need.
model.save_pretrained_gguf(
    "nexusai-gguf",
    tokenizer,
    quantization_method="q4_k_m",   # 4-bit, balanced quality/size; ~2GB
)
print("done. download the .gguf file from the file panel on the left.")
!ls -lh nexusai-gguf/""",
    },
    {
        "type": "markdown",
        "src": """\
## What next?

You now have a fine-tuned prompt engineer. Useful things to do:

- **Use it inside NexusAI.** Replace `IntentPredictor` and `PromptEngine`
  with calls to your hosted model — see `TRAINING.md` for the snippet.
- **Run it offline with Ollama.**
  ```bash
  ollama create nexusai -f Modelfile      # Modelfile points to the gguf
  ollama run nexusai
  ```
- **Iterate.** Generate more training data
  (`python -m scripts.export_training_data --n 5000 --use-teacher`),
  retrain, and benchmark side-by-side.
- **Evaluate.** Use NexusAI's `/analyze` endpoint to score the trained
  model's outputs on a held-out set, and compare against the rule-based
  engine.

Happy prompting!
""",
    },
]


# ----------------------------------------------------------------- ipynb spec

def _make_cell(c: Dict[str, Any]) -> Dict[str, Any]:
    common = {
        "id": uuid.uuid4().hex[:12],
        "metadata": {},
        "source": c["src"].splitlines(keepends=True),
    }
    if c["type"] == "markdown":
        return {**common, "cell_type": "markdown"}
    return {
        **common,
        "cell_type": "code",
        "execution_count": None,
        "outputs": [],
    }


def build_notebook(cells: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "cells": [_make_cell(c) for c in cells],
        "metadata": {
            "accelerator": "GPU",
            "colab": {
                "name": "train_nexusai_model.ipynb",
                "provenance": [],
                "gpuType": "T4",
            },
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.10",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parent.parent /
                    "notebooks" / "train_nexusai_model.ipynb"),
    )
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    notebook = build_notebook(CELLS)
    out.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(CELLS)} cells -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

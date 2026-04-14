#!/usr/bin/env python3
"""
Stage 4 (Gemma 4 variant): QLoRA Fine-Tuning with Unsloth.

Trains a LoRA adapter on Gemma 4 E2B-IT using the same ChatML-style JSONL
datasets as the Qwen pipeline. The datasets are model-agnostic
({"messages": [...]}), so no data changes are needed — the tokenizer's
chat template handles role formatting.

Differences from train.py:
  - Base model: unsloth/gemma-4-e2b-it
  - No forced EOS override (Gemma's tokenizer has the correct EOS already)
  - Response masking markers use Gemma's <|turn>user / <|turn>model delimiters
  - Supports --max-steps for short shakedown runs (overrides epochs)

Usage:
    .venv/bin/python3 -m forge.finetune.train_gemma4 \\
        --dataset medium \\
        --train-path forge/finetune/data/output/medium_train.jsonl \\
        --val-path forge/finetune/data/output/medium_val.jsonl \\
        --output-dir forge/finetune/output/ \\
        --adapter-suffix smoke \\
        --max-steps 50
"""

# ruff: noqa: I001 — import order matters: unsloth must patch before trl/transformers
from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from unsloth import FastLanguageModel  # MUST be first — patches trl/transformers/peft

import torch
from datasets import Dataset
from trl import SFTConfig, SFTTrainer

logger = logging.getLogger(__name__)

DEFAULT_BASE_MODEL = "unsloth/gemma-4-e2b-it"
MAX_SEQ_LENGTH = 4096
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LORA_TARGETS = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]


def _size_tag(base_model: str) -> str:
    """Extract a short size tag from a Gemma 4 HF model id. e2b / e4b / fallback."""
    low = base_model.lower()
    for tag in ("e2b", "e4b", "26b", "31b"):
        if tag in low:
            return tag
    return "unknown"

# Gemma 4's chat template uses these delimiters (probed: 'unsloth/gemma-4-e2b-it')
GEMMA4_INSTRUCTION_PART = "<|turn>user\n"
GEMMA4_RESPONSE_PART = "<|turn>model\n"


def load_chatml_dataset(path: Path, tokenizer) -> Dataset:
    records = []
    with open(path) as f:
        for line in f:
            rec = json.loads(line.strip())
            text = tokenizer.apply_chat_template(
                rec["messages"], tokenize=False, add_generation_prompt=False
            )
            records.append({"text": text})
    return Dataset.from_list(records)


def train_adapter(
    dataset_name: str,
    train_path: Path,
    val_path: Path,
    output_dir: Path,
    adapter_suffix: str,
    base_model: str = DEFAULT_BASE_MODEL,
    val_subset: int | None = None,
    eval_every: int | None = None,
    save_every: int | None = None,
    seed: int = 42,
    epochs: int = 3,
    max_steps: int | None = None,
    batch_size: int = 4,
    grad_accum: int = 4,
    lr: float = 2e-4,
):
    t0 = time.time()

    logger.info("Loading base model: %s", base_model)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    logger.info("Adding LoRA adapters (r=%d, alpha=%d)", LORA_R, LORA_ALPHA)
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,
        target_modules=LORA_TARGETS,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        use_gradient_checkpointing="unsloth",
    )

    logger.info("Loading training data from %s", train_path)
    train_dataset = load_chatml_dataset(train_path, tokenizer)
    logger.info("Loading validation data from %s", val_path)
    val_dataset = load_chatml_dataset(val_path, tokenizer)
    if val_subset and val_subset < len(val_dataset):
        val_dataset = val_dataset.select(range(val_subset))
        logger.info("Val set reduced to first %d samples (for faster eval)", val_subset)
    logger.info("Train: %d samples, Val: %d samples", len(train_dataset), len(val_dataset))

    size_tag = _size_tag(base_model)
    full_adapter_name = f"{dataset_name}_{adapter_suffix}" if adapter_suffix else dataset_name
    checkpoint_dir = output_dir / f"checkpoints_gemma4_{size_tag}_{full_adapter_name}"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # Eval/save cadence: explicit flags override; otherwise fall back to shakedown-aware defaults
    if eval_every is None:
        eval_every = max(10, max_steps // 5) if max_steps else 100
    if save_every is None:
        save_every = max(25, max_steps // 2) if max_steps else 200

    warmup = int(0.05 * (max_steps or (epochs * len(train_dataset) / (batch_size * grad_accum))))

    training_args = SFTConfig(
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=1,  # Gemma4 has a large vocab; logits blow up at >1
        gradient_accumulation_steps=grad_accum,
        eval_accumulation_steps=1,  # free GPU buffers between eval batches
        num_train_epochs=epochs if not max_steps else 1,
        max_steps=max_steps if max_steps else -1,
        learning_rate=lr,
        lr_scheduler_type="cosine",
        warmup_steps=max(5, warmup),
        fp16=False,
        bf16=True,
        logging_steps=5 if max_steps else 25,
        eval_strategy="steps",
        eval_steps=eval_every,
        save_strategy="steps",
        save_steps=save_every,
        save_total_limit=3,
        output_dir=str(checkpoint_dir),
        seed=seed,
        report_to="none",
        dataloader_num_workers=4,
        optim="adamw_8bit",
        dataset_text_field="text",
        packing=False,
        eos_token=tokenizer.eos_token,
    )

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        args=training_args,
    )

    from unsloth.chat_templates import train_on_responses_only
    trainer = train_on_responses_only(
        trainer,
        instruction_part=GEMMA4_INSTRUCTION_PART,
        response_part=GEMMA4_RESPONSE_PART,
    )

    logger.info("Starting training: max_steps=%s, epochs=%d, effective batch=%d, lr=%s",
                max_steps, epochs, batch_size * grad_accum, lr)

    train_result = trainer.train()

    train_loss = train_result.training_loss
    log_history = trainer.state.log_history
    val_losses = [(e["step"], e["eval_loss"]) for e in log_history if "eval_loss" in e]
    final_val_loss = val_losses[-1][1] if val_losses else None
    best_val = min(val_losses, key=lambda x: x[1]) if val_losses else (None, None)

    adapter_path = output_dir / f"adapter_gemma4_{size_tag}_{full_adapter_name}"
    adapter_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))
    logger.info("Adapter saved to %s", adapter_path)

    log_path = output_dir / f"training_log_gemma4_{size_tag}_{full_adapter_name}.json"
    with open(log_path, "w") as f:
        json.dump(log_history, f, indent=2, default=str)

    elapsed_min = (time.time() - t0) / 60
    peak_mem_gb = torch.cuda.max_memory_allocated() / 1e9

    metadata = {
        "dataset_name": dataset_name,
        "adapter_suffix": adapter_suffix,
        "base_model": base_model,
        "size_tag": size_tag,
        "val_subset": val_subset,
        "eval_every": eval_every,
        "save_every": save_every,
        "quantization": "4bit_nf4",
        "lora_rank": LORA_R,
        "lora_alpha": LORA_ALPHA,
        "lora_dropout": LORA_DROPOUT,
        "lora_targets": LORA_TARGETS,
        "learning_rate": lr,
        "epochs": epochs,
        "max_steps": max_steps,
        "effective_batch_size": batch_size * grad_accum,
        "max_seq_length": MAX_SEQ_LENGTH,
        "train_samples": len(train_dataset),
        "val_samples": len(val_dataset),
        "total_steps": trainer.state.global_step,
        "final_train_loss": round(train_loss, 6),
        "final_val_loss": round(final_val_loss, 6) if final_val_loss else None,
        "best_val_loss": round(best_val[1], 6) if best_val[1] else None,
        "best_val_step": best_val[0],
        "training_time_minutes": round(elapsed_min, 1),
        "peak_gpu_memory_gb": round(peak_mem_gb, 2),
        "gpu": torch.cuda.get_device_name(0),
        "seed": seed,
        "adapter_path": str(adapter_path),
        "timestamp": datetime.now(tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }

    meta_path = output_dir / f"training_metadata_gemma4_{size_tag}_{full_adapter_name}.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n{'='*60}")
    print(f"[gemma4_{size_tag}_{full_adapter_name}] Training complete")
    print(f"  Train loss: {train_loss:.4f}")
    if final_val_loss:
        print(f"  Val loss:   {final_val_loss:.4f}")
    if best_val[1]:
        print(f"  Best val:   {best_val[1]:.4f} at step {best_val[0]}")
    print(f"  Time:       {elapsed_min:.1f} min")
    print(f"  Peak VRAM:  {peak_mem_gb:.2f} GB")
    print(f"  Adapter:    {adapter_path}")
    print(f"  Metadata:   {meta_path}")
    print(f"{'='*60}\n")

    return metadata


def main():
    parser = argparse.ArgumentParser(description="QLoRA fine-tuning for Gemma 4 (Unsloth)")
    parser.add_argument("--dataset", required=True, choices=["medium", "hard"])
    parser.add_argument("--train-path", required=True, type=str)
    parser.add_argument("--val-path", required=True, type=str)
    parser.add_argument("--output-dir", required=True, type=str)
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL, type=str,
                        help="HF model id, e.g. unsloth/gemma-4-e2b-it or unsloth/gemma-4-e4b-it.")
    parser.add_argument("--adapter-suffix", default="", type=str,
                        help="Extra tag appended to adapter dir name, e.g. 'smoke' or 'v1'.")
    parser.add_argument("--val-subset", type=int, default=None,
                        help="Use only the first N samples from the val set (for faster eval).")
    parser.add_argument("--eval-every", type=int, default=None,
                        help="Run eval every N optimizer steps. Default: shakedown-aware.")
    parser.add_argument("--save-every", type=int, default=None,
                        help="Save checkpoint every N optimizer steps. Default: shakedown-aware.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--max-steps", type=int, default=None,
                        help="If set, overrides epochs and stops after this many optimizer steps.")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s - %(message)s",
    )

    train_adapter(
        dataset_name=args.dataset,
        train_path=Path(args.train_path),
        val_path=Path(args.val_path),
        output_dir=Path(args.output_dir),
        adapter_suffix=args.adapter_suffix,
        base_model=args.base_model,
        val_subset=args.val_subset,
        eval_every=args.eval_every,
        save_every=args.save_every,
        seed=args.seed,
        epochs=args.epochs,
        max_steps=args.max_steps,
        batch_size=args.batch_size,
        grad_accum=args.grad_accum,
        lr=args.lr,
    )


if __name__ == "__main__":
    main()

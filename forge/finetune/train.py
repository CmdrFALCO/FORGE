#!/usr/bin/env python3
"""
Stage 4: QLoRA Fine-Tuning with Unsloth.

Trains a LoRA adapter on Qwen 2.5 7B Instruct using ChatML-formatted
datasets from Stage 3.

Usage:
    python -m forge.finetune.train \
        --dataset medium \
        --train-path forge/finetune/data/output/medium_train.jsonl \
        --val-path forge/finetune/data/output/medium_val.jsonl \
        --output-dir forge/finetune/output/ \
        --seed 42
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

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_MODEL = "unsloth/Qwen2.5-7B-Instruct"
MAX_SEQ_LENGTH = 4096
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LORA_TARGETS = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def load_chatml_dataset(path: Path, tokenizer) -> Dataset:
    """Load ChatML JSONL and apply chat template."""
    records = []
    with open(path) as f:
        for line in f:
            rec = json.loads(line.strip())
            text = tokenizer.apply_chat_template(
                rec["messages"], tokenize=False, add_generation_prompt=False
            )
            records.append({"text": text})

    return Dataset.from_list(records)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_adapter(
    dataset_name: str,
    train_path: Path,
    val_path: Path,
    output_dir: Path,
    seed: int = 42,
    epochs: int = 3,
    batch_size: int = 4,
    grad_accum: int = 4,
    lr: float = 2e-4,
):
    """Train a QLoRA adapter and save it."""
    t0 = time.time()

    logger.info("Loading base model: %s", BASE_MODEL)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=True,
    )

    # Ensure tokenizer special tokens are correct for Qwen2.5
    if tokenizer.eos_token != "<|im_end|>":
        tokenizer.eos_token = "<|im_end|>"
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

    logger.info("Train: %d samples, Val: %d samples", len(train_dataset), len(val_dataset))

    checkpoint_dir = output_dir / f"checkpoints_{dataset_name}"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    training_args = SFTConfig(
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        num_train_epochs=epochs,
        learning_rate=lr,
        lr_scheduler_type="cosine",
        warmup_steps=int(0.05 * epochs * len(train_dataset) / (batch_size * grad_accum)),
        fp16=False,
        bf16=True,
        logging_steps=25,
        eval_strategy="steps",
        eval_steps=100,
        save_strategy="steps",
        save_steps=200,
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

    # Apply Unsloth's response-only masking: loss only on assistant turns
    from unsloth.chat_templates import train_on_responses_only
    trainer = train_on_responses_only(
        trainer,
        instruction_part="<|im_start|>user\n",
        response_part="<|im_start|>assistant\n",
    )

    logger.info("Starting training: %d epochs, effective batch %d, lr=%s",
                epochs, batch_size * grad_accum, lr)

    train_result = trainer.train()

    # Extract metrics
    train_loss = train_result.training_loss
    log_history = trainer.state.log_history

    # Find best and final val loss
    val_losses = [(entry["step"], entry["eval_loss"])
                  for entry in log_history if "eval_loss" in entry]
    final_val_loss = val_losses[-1][1] if val_losses else None
    best_val = min(val_losses, key=lambda x: x[1]) if val_losses else (None, None)

    # Save adapter
    adapter_path = output_dir / f"adapter_{dataset_name}"
    adapter_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))
    logger.info("Adapter saved to %s", adapter_path)

    # Save training log
    log_path = output_dir / f"training_log_{dataset_name}.json"
    with open(log_path, "w") as f:
        json.dump(log_history, f, indent=2, default=str)

    # Save metadata
    elapsed_min = (time.time() - t0) / 60
    peak_mem_gb = torch.cuda.max_memory_allocated() / 1e9

    metadata = {
        "dataset_name": dataset_name,
        "base_model": BASE_MODEL,
        "quantization": "4bit_nf4",
        "lora_rank": LORA_R,
        "lora_alpha": LORA_ALPHA,
        "lora_dropout": LORA_DROPOUT,
        "lora_targets": LORA_TARGETS,
        "learning_rate": lr,
        "epochs": epochs,
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
        "timestamp": datetime.now(tz=timezone.utc).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z"),
    }

    meta_path = output_dir / f"training_metadata_{dataset_name}.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n{'='*60}")
    print(f"[{dataset_name}] Training complete")
    print(f"  Train loss: {train_loss:.4f}")
    print(f"  Val loss:   {final_val_loss:.4f}" if final_val_loss else "  Val loss: N/A")
    print(f"  Best val:   {best_val[1]:.4f} at step {best_val[0]}" if best_val[1] else "")
    print(f"  Time:       {elapsed_min:.1f} min")
    print(f"  Peak VRAM:  {peak_mem_gb:.2f} GB")
    print(f"  Adapter:    {adapter_path}")
    print(f"  Metadata:   {meta_path}")
    print(f"{'='*60}\n")

    return metadata


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="QLoRA fine-tuning with Unsloth")
    parser.add_argument("--dataset", required=True, choices=["medium", "hard"])
    parser.add_argument("--train-path", required=True, type=str)
    parser.add_argument("--val-path", required=True, type=str)
    parser.add_argument("--output-dir", required=True, type=str)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=3)
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
        seed=args.seed,
        epochs=args.epochs,
        batch_size=args.batch_size,
        grad_accum=args.grad_accum,
        lr=args.lr,
    )


if __name__ == "__main__":
    main()

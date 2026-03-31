#!/usr/bin/env python3
"""
Corpus B Experiment Runner.

Runs one model × one condition (unsup or sup) over the full 250-prompt Corpus B.
Called by run_corpus_b.sh for each model/condition pair.

Usage:
    .venv/bin/python3 forge/experiments/corpus_b/run_corpus_b_experiments.py \
        --model llama3b --condition unsup
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import deque
from pathlib import Path

from forge.axiom.supervisor import driver as supervisor_driver
from forge.experiments.experiment_config import BackendConfig, ExperimentDefinition
from forge.experiments.run_experiments import (
    _build_backend,
    _load_completed_ids,
    _progress_line,
    _run_single_prompt,
    _status_line,
)

# ---------------------------------------------------------------------------
# Model configs — same as main experiments
# ---------------------------------------------------------------------------

MODELS = {
    "llama3b": BackendConfig(
        backend_type="ollama", model="llama3.2:3b",
        temperature=0.0, num_ctx=8192, num_predict=2000,
        host="http://localhost:11434",
    ),
    "llama8b": BackendConfig(
        backend_type="ollama", model="llama3.1:8b",
        temperature=0.0, num_ctx=8192, num_predict=2000,
        host="http://localhost:11434",
    ),
    "qwen9b": BackendConfig(
        backend_type="ollama", model="qwen3.5:9b",
        temperature=0.0, num_ctx=8192, num_predict=2000,
        host="http://localhost:11434",
    ),
    "mistral": BackendConfig(
        backend_type="ollama", model="mistral-small3.1",
        temperature=0.0, num_ctx=8192, num_predict=2000,
        host="http://localhost:11434",
    ),
    "qwen27b": BackendConfig(
        backend_type="ollama", model="qwen3.5:27b",
        temperature=0.0, num_ctx=8192, num_predict=2000,
        host="http://localhost:11434",
    ),
}

CORPUS_PATH = Path(__file__).resolve().parent / "prompt_corpus_b.json"
RESULTS_DIR = Path(__file__).resolve().parent / "results"


def _load_corpus(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["prompts"]


def main():
    parser = argparse.ArgumentParser(description="Corpus B experiment runner")
    parser.add_argument("--model", required=True, choices=list(MODELS.keys()))
    parser.add_argument("--condition", required=True, choices=["unsup", "sup"])
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s - %(message)s",
    )

    model_key = args.model
    condition = args.condition
    backend_cfg = MODELS[model_key]

    supervised = condition == "sup"
    max_retries = 4 if supervised else 1
    exp_id = f"corpusB_{model_key}_{condition}"
    output_filename = f"corpusB_{model_key}_{condition}.jsonl"

    experiment = ExperimentDefinition(
        experiment_id=exp_id,
        name=f"Corpus B — {model_key} {'supervised' if supervised else 'unsupervised'}",
        description=f"Corpus B evaluation: {backend_cfg.model}, {'supervised' if supervised else 'unsupervised'}",
        backend_config=backend_cfg,
        supervised=supervised,
        max_retries=max_retries,
        output_filename=output_filename,
        gpu_monitor=False,
    )

    # Load corpus
    corpus = _load_corpus(CORPUS_PATH)
    total = len(corpus)

    # Output path
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    jsonl_path = RESULTS_DIR / output_filename
    completed_ids = _load_completed_ids(jsonl_path)
    skip = sum(1 for p in corpus if p["prompt_id"] in completed_ids)

    # Build backend
    backend = _build_backend(backend_cfg)

    # Counters
    done = skip
    valid_count = 0
    rejected_count = 0
    error_count = 0
    recent: deque[float] = deque(maxlen=10)

    print(f"\n[{exp_id}] Starting — {total} prompts, "
          f"supervised={supervised}, max_retries={max_retries}")
    print(f"[{exp_id}] Model: {backend_cfg.model}")
    print(f"[{exp_id}] Output: {jsonl_path}")
    if skip:
        print(f"[{exp_id}] Resuming: {skip}/{total} already completed")
    print(flush=True)

    try:
        for prompt_entry in corpus:
            pid = prompt_entry["prompt_id"]
            if pid in completed_ids:
                continue

            record = _run_single_prompt(prompt_entry, experiment, backend)

            with open(jsonl_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, default=str) + "\n")

            done += 1
            wall_s = record["summary"]["total_wall_time_ms"] / 1000
            recent.append(wall_s)

            if record["errors"] is not None:
                error_count += 1
            elif record["summary"]["final_valid"]:
                valid_count += 1
            else:
                rejected_count += 1

            print(_status_line(exp_id, record, prompt_entry), flush=True)
            if done % 10 == 0 or done == total:
                print(
                    _progress_line(
                        exp_id, done, total,
                        valid_count, rejected_count, error_count, recent,
                    ),
                    flush=True,
                )

    except KeyboardInterrupt:
        print(f"\n[{exp_id}] Interrupted at {done}/{total}. Progress saved.")

    # Summary
    print(f"\n[{exp_id}] DONE: {done}/{total}")
    if done:
        print(f"  Valid:    {valid_count}/{done} ({valid_count / done * 100:.1f}%)")
        print(f"  Rejected: {rejected_count}/{done}")
        print(f"  Errors:   {error_count}/{done}")
    print(f"  Output:   {jsonl_path}\n")


if __name__ == "__main__":
    main()

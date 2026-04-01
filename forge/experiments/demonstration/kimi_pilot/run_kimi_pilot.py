#!/usr/bin/env python3
"""
Pilot: Kimi-VL-A3B-Thinking on the AXIOM battery cell design task.

Tests whether a vision-language MoE model (16B total, ~2.8B active per token)
with chain-of-thought reasoning can handle structured YAML generation and
supervision feedback at this parameter scale.

Comparison baseline: Llama 3.2 3B (74.2% unsup, 82.6% sup, 33% recovery).

Runs 50 prompts (stratified sample), supervised mode, original feedback format.
Does NOT modify any files in forge/experiments/results/.

Usage (from FORGE root):
    .venv/bin/python3 forge/experiments/demonstration/kimi_pilot/run_kimi_pilot.py
"""

from __future__ import annotations

import json
import logging
import random
from collections import deque
from pathlib import Path

# Import experiment infrastructure (no monkey-patching — original feedback format)
from forge.experiments.experiment_config import BackendConfig, ExperimentDefinition
from forge.experiments.run_experiments import (
    _build_backend,
    _load_completed_ids,
    _progress_line,
    _run_single_prompt,
    _status_line,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KIMI_VL_THINKING = BackendConfig(
    backend_type="ollama",
    model="richardyoung/kimi-vl-a3b-thinking:Q4_K_M",
    temperature=0.0,
    num_ctx=8192,
    num_predict=4000,  # Higher than usual to accommodate thinking tokens
    host="http://localhost:11434",
)

EXPERIMENTS = {
    "kimi_vl_think_sup": ExperimentDefinition(
        experiment_id="kimi_vl_think_sup",
        name="Kimi-VL-A3B-Thinking Supervised (Pilot)",
        description="50-prompt pilot: Kimi VL A3B Thinking, supervised, original feedback",
        backend_config=KIMI_VL_THINKING,
        supervised=True,
        max_retries=4,
        output_filename="kimi_vl_thinking_sup.jsonl",
        gpu_monitor=False,
    ),
    "kimi_vl_think_unsup": ExperimentDefinition(
        experiment_id="kimi_vl_think_unsup",
        name="Kimi-VL-A3B-Thinking Unsupervised (Pilot)",
        description="50-prompt pilot: Kimi VL A3B Thinking, unsupervised, single attempt",
        backend_config=KIMI_VL_THINKING,
        supervised=False,
        max_retries=1,
        output_filename="kimi_vl_thinking_unsup.jsonl",
        gpu_monitor=False,
    ),
}

CORPUS_PATH = Path(__file__).resolve().parent.parent.parent / "prompt_corpus_v1.json"
OUTPUT_DIR = Path(__file__).resolve().parent
PILOT_SIZE = 50
PILOT_SEED = 42


def _load_corpus(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data["prompts"]


def _select_pilot_subset(corpus: list[dict], n: int, seed: int) -> list[dict]:
    """Select a stratified subset of n prompts preserving cell_type balance."""
    rng = random.Random(seed)
    by_type: dict[str, list[dict]] = {}
    for p in corpus:
        by_type.setdefault(p["cell_type"], []).append(p)

    selected: list[dict] = []
    types = sorted(by_type.keys())
    per_type = n // len(types)
    remainder = n % len(types)

    for i, ct in enumerate(types):
        k = per_type + (1 if i < remainder else 0)
        pool = by_type[ct]
        rng.shuffle(pool)
        selected.extend(pool[:k])

    # Sort by prompt_id for deterministic order
    selected.sort(key=lambda p: p["prompt_id"])
    return selected


def _prewarm(model: str) -> None:
    import urllib.request

    print(f"[pilot] Pre-warming {model} ...", flush=True)
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "hello"}],
        "stream": False,
        "options": {"temperature": 0.0, "num_ctx": 8192, "num_predict": 10},
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())
            print(f"[pilot] Model loaded: {result.get('model', '?')}", flush=True)
    except Exception as e:
        print(f"[pilot] Pre-warm warning: {e}", flush=True)


def run_one_experiment(experiment: ExperimentDefinition, pilot_corpus: list[dict]) -> None:
    exp_id = experiment.experiment_id
    jsonl_path = OUTPUT_DIR / experiment.output_filename
    completed_ids = _load_completed_ids(jsonl_path)
    total = len(pilot_corpus)
    skip = sum(1 for p in pilot_corpus if p["prompt_id"] in completed_ids)

    backend = _build_backend(experiment.backend_config)

    done = skip
    valid_count = 0
    rejected_count = 0
    error_count = 0
    recent: deque[float] = deque(maxlen=10)

    print(f"\n[{exp_id}] Starting — {total} prompts, "
          f"supervised={experiment.supervised}, max_retries={experiment.max_retries}")
    print(f"[{exp_id}] Output: {jsonl_path}")
    if skip:
        print(f"[{exp_id}] Resuming: {skip}/{total} already completed")
    print(flush=True)

    try:
        for prompt_entry in pilot_corpus:
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

    print(f"\n[{exp_id}] DONE: {done}/{total}")
    if done:
        print(f"  Valid:    {valid_count}/{done} ({valid_count/done*100:.1f}%)")
        print(f"  Rejected: {rejected_count}/{done}")
        print(f"  Errors:   {error_count}/{done}")
    print(f"  Output:   {jsonl_path}\n")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s - %(message)s",
    )

    corpus = _load_corpus(CORPUS_PATH)
    pilot = _select_pilot_subset(corpus, PILOT_SIZE, PILOT_SEED)

    cell_types = {}
    for p in pilot:
        cell_types[p["cell_type"]] = cell_types.get(p["cell_type"], 0) + 1
    print(f"[pilot] Selected {len(pilot)} prompts: {cell_types}")

    _prewarm(KIMI_VL_THINKING.model)

    # Run unsupervised first (faster), then supervised
    print("=" * 60)
    print("KIMI-VL-A3B-THINKING PILOT — 50 prompts")
    print("=" * 60)

    run_one_experiment(EXPERIMENTS["kimi_vl_think_unsup"], pilot)
    run_one_experiment(EXPERIMENTS["kimi_vl_think_sup"], pilot)

    print("=" * 60)
    print("PILOT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()

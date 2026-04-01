#!/usr/bin/env python3
"""
Rerun: Kimi-VL-A3B-Thinking with num_predict=8000 (doubled token budget).

Tests whether the poor unsupervised performance (42%) was caused by
thinking tokens exhausting the output budget at num_predict=4000.

Same 50-prompt pilot subset, original feedback format.

Usage (from FORGE root):
    .venv/bin/python3 forge/experiments/demonstration/kimi_pilot/run_kimi_rerun.py
"""

from __future__ import annotations

import json
import logging
import random
from collections import deque
from pathlib import Path

from forge.experiments.experiment_config import BackendConfig, ExperimentDefinition
from forge.experiments.run_experiments import (
    _build_backend,
    _load_completed_ids,
    _progress_line,
    _run_single_prompt,
    _status_line,
)

KIMI_VL_8K = BackendConfig(
    backend_type="ollama",
    model="richardyoung/kimi-vl-a3b-thinking:Q4_K_M",
    temperature=0.0,
    num_ctx=8192,
    num_predict=8000,
    host="http://localhost:11434",
)

EXPERIMENTS = {
    "kimi_vl_8k_unsup": ExperimentDefinition(
        experiment_id="kimi_vl_8k_unsup",
        name="Kimi-VL-A3B-Thinking 8K Unsupervised",
        description="50-prompt pilot: Kimi VL, num_predict=8000, unsupervised",
        backend_config=KIMI_VL_8K,
        supervised=False,
        max_retries=1,
        output_filename="kimi_vl_thinking_8k_unsup.jsonl",
        gpu_monitor=False,
    ),
    "kimi_vl_8k_sup": ExperimentDefinition(
        experiment_id="kimi_vl_8k_sup",
        name="Kimi-VL-A3B-Thinking 8K Supervised",
        description="50-prompt pilot: Kimi VL, num_predict=8000, supervised",
        backend_config=KIMI_VL_8K,
        supervised=True,
        max_retries=4,
        output_filename="kimi_vl_thinking_8k_sup.jsonl",
        gpu_monitor=False,
    ),
}

CORPUS_PATH = Path(__file__).resolve().parent.parent.parent / "prompt_corpus_v1.json"
OUTPUT_DIR = Path(__file__).resolve().parent
PILOT_SIZE = 50
PILOT_SEED = 42


def _load_corpus(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["prompts"]


def _select_pilot_subset(corpus: list[dict], n: int, seed: int) -> list[dict]:
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
    selected.sort(key=lambda p: p["prompt_id"])
    return selected


def _prewarm(model: str) -> None:
    import urllib.request
    print(f"[rerun] Pre-warming {model} ...", flush=True)
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "hello"}],
        "stream": False,
        "options": {"temperature": 0.0, "num_ctx": 8192, "num_predict": 10},
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/chat", data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())
            print(f"[rerun] Model loaded: {result.get('model', '?')}", flush=True)
    except Exception as e:
        print(f"[rerun] Pre-warm warning: {e}", flush=True)


def run_one(experiment: ExperimentDefinition, pilot: list[dict]) -> None:
    exp_id = experiment.experiment_id
    jsonl_path = OUTPUT_DIR / experiment.output_filename
    completed_ids = _load_completed_ids(jsonl_path)
    total = len(pilot)
    skip = sum(1 for p in pilot if p["prompt_id"] in completed_ids)
    backend = _build_backend(experiment.backend_config)

    done, valid_count, rejected_count, error_count = skip, 0, 0, 0
    recent: deque[float] = deque(maxlen=10)

    print(f"\n[{exp_id}] Starting — {total} prompts, "
          f"supervised={experiment.supervised}, num_predict=8000")
    print(f"[{exp_id}] Output: {jsonl_path}")
    if skip:
        print(f"[{exp_id}] Resuming: {skip}/{total} already completed")
    print(flush=True)

    try:
        for p in pilot:
            if p["prompt_id"] in completed_ids:
                continue
            record = _run_single_prompt(p, experiment, backend)
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
            print(_status_line(exp_id, record, p), flush=True)
            if done % 10 == 0 or done == total:
                print(_progress_line(exp_id, done, total, valid_count,
                                     rejected_count, error_count, recent), flush=True)
    except KeyboardInterrupt:
        print(f"\n[{exp_id}] Interrupted at {done}/{total}. Progress saved.")

    print(f"\n[{exp_id}] DONE: {done}/{total}")
    if done:
        print(f"  Valid:    {valid_count}/{done} ({valid_count/done*100:.1f}%)")
        print(f"  Rejected: {rejected_count}/{done}")
        print(f"  Errors:   {error_count}/{done}")
    print(f"  Output:   {jsonl_path}\n")


def main() -> None:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s - %(message)s")
    corpus = _load_corpus(CORPUS_PATH)
    pilot = _select_pilot_subset(corpus, PILOT_SIZE, PILOT_SEED)
    ct = {}
    for p in pilot:
        ct[p["cell_type"]] = ct.get(p["cell_type"], 0) + 1
    print(f"[rerun] Selected {len(pilot)} prompts: {ct}")

    _prewarm(KIMI_VL_8K.model)

    print("=" * 60)
    print("KIMI-VL RERUN — num_predict=8000 (2x baseline)")
    print("=" * 60)

    run_one(EXPERIMENTS["kimi_vl_8k_unsup"], pilot)
    run_one(EXPERIMENTS["kimi_vl_8k_sup"], pilot)

    print("=" * 60)
    print("RERUN COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()

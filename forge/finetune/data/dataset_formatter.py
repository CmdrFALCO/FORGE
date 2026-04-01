#!/usr/bin/env python3
"""
Stage 3: ChatML Dataset Formatting & Train/Val Splits.

Converts Stage 2 outputs into ChatML-formatted training datasets:
- Medium: system + user prompt → assistant YAML (with YAML-only suffix)
- Hard: system + user prompt → assistant reasoning + YAML (no suffix)

Usage:
    python -m forge.finetune.data.dataset_formatter \
        --medium-input forge/finetune/data/output/configs_with_prompts.jsonl \
        --hard-input forge/finetune/data/output/configs_with_reasoning.jsonl \
        --corpus-a forge/experiments/prompt_corpus_v1.json \
        --corpus-b forge/experiments/corpus_b/prompt_corpus_b.json \
        --output-dir forge/finetune/data/output/ \
        --seed 42 --verbose
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

from forge.axiom.generator.prompt_builder import build_system_prompt

logger = logging.getLogger(__name__)

# The suffix appended by driver.py for Ollama models.
# Included in Medium training (pure YAML output), excluded from Hard (reasoning + YAML).
YAML_ONLY_SUFFIX = (
    "\n\nCRITICAL: Output ONLY the YAML specification. "
    "No explanations, no commentary, no text before or after the YAML block. "
    "Start your response with ```yaml and end with ```. Do not write anything else."
)


# ---------------------------------------------------------------------------
# Stratified splitting
# ---------------------------------------------------------------------------

def stratified_split(
    records: list[dict],
    train_ratio: float,
    seed: int,
) -> tuple[list[dict], list[dict], dict[str, str]]:
    """Split records into train/val stratified by cell_type × chemistry_bucket.

    Returns (train_records, val_records, assignment_map).
    assignment_map: config_id → "train" or "val".
    """
    rng = np.random.default_rng(seed)

    # Group by stratum
    strata: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        ct = rec["cell_type"]
        chem = rec.get("chemistry_bucket", rec.get("chemistry", "UNK"))
        key = f"{ct}_{chem}"
        strata[key] = strata.get(key, [])
        strata[key].append(rec)

    train, val = [], []
    assignment: dict[str, str] = {}

    for stratum_key in sorted(strata.keys()):
        items = strata[stratum_key]
        indices = rng.permutation(len(items))
        n_train = int(len(items) * train_ratio)

        for i, idx in enumerate(indices):
            rec = items[idx]
            cid = rec["config_id"]
            if i < n_train:
                train.append(rec)
                assignment[cid] = "train"
            else:
                val.append(rec)
                assignment[cid] = "val"

    logger.info("Split: %d train, %d val across %d strata",
                len(train), len(val), len(strata))
    return train, val, assignment


# ---------------------------------------------------------------------------
# ChatML formatting
# ---------------------------------------------------------------------------

def format_medium_chatml(record: dict) -> dict:
    """Format a Medium dataset record as ChatML conversation.

    System: build_system_prompt(cell_type) + YAML-only suffix
    User: prompt
    Assistant: ```yaml config ```
    """
    cell_type = record["config"]["_meta"]["cell_type"]
    system_msg = build_system_prompt(include_example=True, cell_type=cell_type)
    system_msg += YAML_ONLY_SUFFIX

    config_yaml = yaml.dump(
        record["config"], default_flow_style=False, sort_keys=False
    )
    assistant_msg = f"```yaml\n{config_yaml}```"

    return {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": record["prompt"]},
            {"role": "assistant", "content": assistant_msg},
        ]
    }


def format_hard_chatml(record: dict) -> dict:
    """Format a Hard dataset record as ChatML conversation.

    System: build_system_prompt(cell_type) — NO suffix (reasoning is expected)
    User: prompt
    Assistant: reasoning trace + ```yaml config ```
    """
    cell_type = record["config"]["_meta"]["cell_type"]
    system_msg = build_system_prompt(include_example=True, cell_type=cell_type)
    # No YAML-only suffix — model should reason then output YAML

    config_yaml = yaml.dump(
        record["config"], default_flow_style=False, sort_keys=False
    )
    reasoning = record.get("reasoning_trace", "")
    assistant_msg = f"{reasoning}\n\n```yaml\n{config_yaml}```"

    return {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": record["prompt"]},
            {"role": "assistant", "content": assistant_msg},
        ]
    }


# ---------------------------------------------------------------------------
# Decontamination
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> set[str]:
    return set(text.lower().split())


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def decontamination_check(
    train_records: list[dict],
    corpus_a_path: Path,
    corpus_b_path: Path,
    threshold: float = 0.6,
) -> dict:
    """Verify no training prompts are too similar to evaluation prompts."""
    eval_tokens: list[set[str]] = []
    for path in [corpus_a_path, corpus_b_path]:
        if not path.exists():
            continue
        with open(path) as f:
            data = json.load(f)
        for p in data.get("prompts", []):
            eval_tokens.append(_tokenize(p.get("prompt_text", "")))

    flagged = 0
    for rec in train_records:
        pt = _tokenize(rec["prompt"])
        max_sim = max((_jaccard(pt, et) for et in eval_tokens), default=0.0)
        if max_sim >= threshold:
            flagged += 1
            logger.warning("Decontamination flag: %s (Jaccard=%.3f)", rec["config_id"], max_sim)

    return {
        "checked_against_corpus_a": sum(1 for p in [corpus_a_path] if p.exists()) * 500,
        "checked_against_corpus_b": sum(1 for p in [corpus_b_path] if p.exists()) * 250,
        "flagged": flagged,
    }


# ---------------------------------------------------------------------------
# Token statistics
# ---------------------------------------------------------------------------

def compute_token_stats(records: list[dict]) -> dict:
    """Compute rough token stats using whitespace split."""
    sys_lens, user_lens, asst_lens, total_lens = [], [], [], []

    for rec in records:
        msgs = rec["messages"]
        s = len(msgs[0]["content"].split())
        u = len(msgs[1]["content"].split())
        a = len(msgs[2]["content"].split())
        sys_lens.append(s)
        user_lens.append(u)
        asst_lens.append(a)
        total_lens.append(s + u + a)

    def _stats(vals):
        return {
            "min": min(vals),
            "max": max(vals),
            "avg": round(sum(vals) / len(vals)),
            "p95": round(sorted(vals)[int(len(vals) * 0.95)]),
        }

    return {
        "system_tokens": _stats(sys_lens),
        "user_tokens": _stats(user_lens),
        "assistant_tokens": _stats(asst_lens),
        "total_tokens": _stats(total_lens),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def format_datasets(
    medium_input: Path,
    hard_input: Path,
    corpus_a: Path,
    corpus_b: Path,
    output_dir: Path,
    train_ratio: float = 0.8,
    seed: int = 42,
    verbose: bool = False,
) -> dict:
    """Format Medium and Hard datasets with identical train/val splits."""

    # Load Medium records
    medium_records: list[dict] = []
    with open(medium_input) as f:
        for line in f:
            medium_records.append(json.loads(line.strip()))
    logger.info("Loaded %d Medium records", len(medium_records))

    # Load Hard records indexed by config_id
    hard_by_id: dict[str, dict] = {}
    with open(hard_input) as f:
        for line in f:
            rec = json.loads(line.strip())
            hard_by_id[rec["config_id"]] = rec
    logger.info("Loaded %d Hard records", len(hard_by_id))

    # Step 1: Stratified split (using Medium records as source of truth)
    train_recs, val_recs, assignment = stratified_split(medium_records, train_ratio, seed)

    # Save split assignment
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "split_assignment.json", "w") as f:
        json.dump(assignment, f, indent=2)

    # Step 2: Format Medium dataset
    medium_train_chatml = [format_medium_chatml(r) for r in train_recs]
    medium_val_chatml = [format_medium_chatml(r) for r in val_recs]

    _write_jsonl(output_dir / "medium_train.jsonl", medium_train_chatml)
    _write_jsonl(output_dir / "medium_val.jsonl", medium_val_chatml)

    if verbose:
        print(f"Medium: {len(medium_train_chatml)} train, {len(medium_val_chatml)} val")

    # Step 3: Format Hard dataset (same split)
    hard_train_chatml, hard_val_chatml = [], []
    hard_missing = 0
    for rec in train_recs:
        hard_rec = hard_by_id.get(rec["config_id"])
        if hard_rec:
            hard_train_chatml.append(format_hard_chatml(hard_rec))
        else:
            hard_missing += 1
    for rec in val_recs:
        hard_rec = hard_by_id.get(rec["config_id"])
        if hard_rec:
            hard_val_chatml.append(format_hard_chatml(hard_rec))
        else:
            hard_missing += 1

    if hard_missing:
        logger.warning("%d records missing from Hard dataset", hard_missing)

    _write_jsonl(output_dir / "hard_train.jsonl", hard_train_chatml)
    _write_jsonl(output_dir / "hard_val.jsonl", hard_val_chatml)

    if verbose:
        print(f"Hard: {len(hard_train_chatml)} train, {len(hard_val_chatml)} val")

    # Step 4: Decontamination
    decon = decontamination_check(train_recs, corpus_a, corpus_b)
    if verbose:
        print(f"Decontamination: {decon['flagged']} flagged")

    # Compute stratification stats
    strat_train: dict[str, int] = defaultdict(int)
    strat_val: dict[str, int] = defaultdict(int)
    for rec in train_recs:
        key = f"{rec['cell_type']}_{rec.get('chemistry_bucket', rec.get('chemistry', 'UNK'))}"
        strat_train[key] += 1
    for rec in val_recs:
        key = f"{rec['cell_type']}_{rec.get('chemistry_bucket', rec.get('chemistry', 'UNK'))}"
        strat_val[key] += 1

    # Token stats
    med_train_stats = compute_token_stats(medium_train_chatml)
    med_val_stats = compute_token_stats(medium_val_chatml)
    hard_train_stats = compute_token_stats(hard_train_chatml)
    hard_val_stats = compute_token_stats(hard_val_chatml)

    if verbose:
        print("\nToken estimates (whitespace-split words):")
        print(f"  Medium train — total: avg {med_train_stats['total_tokens']['avg']}, "
              f"p95 {med_train_stats['total_tokens']['p95']}")
        print(f"  Hard train   — total: avg {hard_train_stats['total_tokens']['avg']}, "
              f"p95 {hard_train_stats['total_tokens']['p95']}")

    metadata = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "seed": seed,
        "train_ratio": train_ratio,
        "total_records": len(medium_records),
        "train_count": len(train_recs),
        "val_count": len(val_recs),
        "medium_train_file": "medium_train.jsonl",
        "medium_val_file": "medium_val.jsonl",
        "hard_train_file": "hard_train.jsonl",
        "hard_val_file": "hard_val.jsonl",
        "hard_missing": hard_missing,
        "stratification": {
            "train": dict(sorted(strat_train.items())),
            "val": dict(sorted(strat_val.items())),
        },
        "token_stats": {
            "medium_train": med_train_stats,
            "medium_val": med_val_stats,
            "hard_train": hard_train_stats,
            "hard_val": hard_val_stats,
        },
        "decontamination": decon,
        "notes": {
            "medium_system_prompt": "build_system_prompt(cell_type) + YAML-only suffix",
            "hard_system_prompt": "build_system_prompt(cell_type), no suffix",
            "stage5_note": "Hard model eval needs suppress_yaml_suffix flag in ExperimentDefinition",
        },
    }

    with open(output_dir / "dataset_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    if verbose:
        print(f"\nMetadata: {output_dir / 'dataset_metadata.json'}")
        print("=== Stage 3 complete ===")

    return metadata


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with open(path, "w") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    logger.info("Wrote %d records to %s", len(records), path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Format ChatML training datasets")
    parser.add_argument("--medium-input", required=True, type=str)
    parser.add_argument("--hard-input", required=True, type=str)
    parser.add_argument("--corpus-a", required=True, type=str)
    parser.add_argument("--corpus-b", required=True, type=str)
    parser.add_argument("--output-dir", required=True, type=str)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)-7s %(name)s - %(message)s",
    )

    format_datasets(
        medium_input=Path(args.medium_input),
        hard_input=Path(args.hard_input),
        corpus_a=Path(args.corpus_a),
        corpus_b=Path(args.corpus_b),
        output_dir=Path(args.output_dir),
        train_ratio=args.train_ratio,
        seed=args.seed,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()

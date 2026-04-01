#!/usr/bin/env python3
"""
Stage 2 Part B: Batch API Reasoning Trace Generator.

Sends (prompt, config) pairs to Claude Sonnet via Anthropic Batch API
to generate chain-of-thought reasoning traces for the Hard training dataset.

Three-step workflow:
  prepare  → build batch_requests.jsonl
  submit   → send to Anthropic Batch API
  collect  → download results, extract reasoning, write final output

Usage:
    python -m forge.finetune.data.reasoning_generator prepare \
        --input forge/finetune/data/output/configs_with_prompts.jsonl \
        --output forge/finetune/data/output/batch_requests.jsonl

    python -m forge.finetune.data.reasoning_generator submit \
        --requests forge/finetune/data/output/batch_requests.jsonl

    python -m forge.finetune.data.reasoning_generator collect \
        --batch-id <batch_id> \
        --input forge/finetune/data/output/configs_with_prompts.jsonl \
        --output forge/finetune/data/output/configs_with_reasoning.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

SYSTEM_MESSAGE = """You are an expert battery cell engineer explaining your design decisions.

Given a design request and a validated cell configuration, write a clear chain-of-thought explanation covering:

1. How you interpreted the requirements (cell type, chemistry, target specs)
2. Why you chose the specific dimensional parameters (referencing the constraints they must satisfy)
3. How electrode parameters (loading, thickness, porosity) were balanced for the target application
4. Any trade-offs considered (energy vs power, thermal vs capacity, cost vs performance)
5. Why the chosen values satisfy the validation constraints

Be specific and quantitative — reference actual parameter values and constraint ranges.
Keep the reasoning concise: 150–300 words. No filler, no preamble.

After the reasoning, output the exact cell configuration in YAML format."""

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1500


# ---------------------------------------------------------------------------
# prepare: Build batch request JSONL
# ---------------------------------------------------------------------------

def prepare_batch(input_path: Path, output_path: Path) -> int:
    """Build Anthropic Batch API request JSONL from configs_with_prompts."""
    count = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(input_path) as fin, open(output_path, "w") as fout:
        for line in fin:
            record = json.loads(line.strip())
            config_id = record["config_id"]
            prompt = record["prompt"]
            config = record["config"]

            # Convert config to YAML string
            config_yaml = yaml.dump(config, default_flow_style=False, sort_keys=False)

            user_message = (
                f'Design request: "{prompt}"\n\n'
                f"Validated configuration:\n```yaml\n{config_yaml}```\n\n"
                f"Explain your reasoning for this design, then output the configuration in YAML."
            )

            batch_request = {
                "custom_id": config_id,
                "params": {
                    "model": MODEL,
                    "max_tokens": MAX_TOKENS,
                    "system": SYSTEM_MESSAGE,
                    "messages": [
                        {"role": "user", "content": user_message},
                    ],
                },
            }

            fout.write(json.dumps(batch_request) + "\n")
            count += 1

    logger.info("Prepared %d batch requests -> %s", count, output_path)
    return count


# ---------------------------------------------------------------------------
# submit: Send batch to Anthropic API
# ---------------------------------------------------------------------------

def submit_batch(requests_path: Path) -> str:
    """Submit batch request file to Anthropic Batch API. Returns batch ID."""
    try:
        import anthropic
    except ImportError:
        logger.error("anthropic package required. Install with: pip install anthropic")
        sys.exit(1)

    client = anthropic.Anthropic()

    with open(requests_path) as f:
        requests = [json.loads(line) for line in f]

    logger.info("Submitting batch with %d requests...", len(requests))

    batch = client.messages.batches.create(requests=requests)

    print(f"Batch submitted successfully!")
    print(f"  Batch ID: {batch.id}")
    print(f"  Status: {batch.processing_status}")
    print(f"  Created: {batch.created_at}")
    print(f"\nUse this command to check status and collect results:")
    print(f"  python -m forge.finetune.data.reasoning_generator collect \\")
    print(f"      --batch-id {batch.id} \\")
    print(f"      --input forge/finetune/data/output/configs_with_prompts.jsonl \\")
    print(f"      --output forge/finetune/data/output/configs_with_reasoning.jsonl")

    return batch.id


# ---------------------------------------------------------------------------
# collect: Poll, download, and parse results
# ---------------------------------------------------------------------------

def collect_results(
    batch_id: str,
    input_path: Path,
    output_path: Path,
    raw_output_path: Path | None = None,
) -> dict:
    """Poll batch status, download results, extract reasoning traces."""
    try:
        import anthropic
    except ImportError:
        logger.error("anthropic package required.")
        sys.exit(1)

    client = anthropic.Anthropic()

    # Poll for completion
    print(f"Polling batch {batch_id}...")
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        print(f"  Status: {status} "
              f"(succeeded: {batch.request_counts.succeeded}, "
              f"failed: {batch.request_counts.errored})")

        if status == "ended":
            break
        if status in ("expired", "canceled"):
            logger.error("Batch %s: %s", batch_id, status)
            return {"status": status, "succeeded": 0, "failed": 0}

        print("  Waiting 60s...")
        time.sleep(60)

    # Load original records for merging
    originals: dict[str, dict] = {}
    with open(input_path) as f:
        for line in f:
            rec = json.loads(line.strip())
            originals[rec["config_id"]] = rec

    # Download and parse results
    succeeded = 0
    failed = 0
    reasoning_lengths: list[int] = []

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if raw_output_path is None:
        raw_output_path = output_path.parent / "batch_raw_results.jsonl"

    with open(output_path, "w") as fout, open(raw_output_path, "w") as fraw:
        for result in client.messages.batches.results(batch_id):
            fraw.write(json.dumps(result.model_dump(), default=str) + "\n")

            config_id = result.custom_id
            original = originals.get(config_id, {})

            if result.result.type == "succeeded":
                response_text = result.result.message.content[0].text
                reasoning, _ = _extract_reasoning(response_text)

                record = {
                    "config_id": config_id,
                    "cell_type": original.get("cell_type", ""),
                    "chemistry": original.get("chemistry", ""),
                    "prompt": original.get("prompt", ""),
                    "prompt_style": original.get("prompt_style", ""),
                    "reasoning_trace": reasoning,
                    "config": original.get("config", {}),
                    "batch_request_id": batch_id,
                    "reasoning_tokens": len(reasoning.split()),
                }
                fout.write(json.dumps(record, default=str) + "\n")
                succeeded += 1
                reasoning_lengths.append(record["reasoning_tokens"])
            else:
                logger.warning("Failed: %s — %s", config_id, result.result.type)
                failed += 1

    total = succeeded + failed
    avg_len = sum(reasoning_lengths) / len(reasoning_lengths) if reasoning_lengths else 0
    failure_rate = failed / total if total else 0

    stats = {
        "status": "complete",
        "batch_id": batch_id,
        "total": total,
        "succeeded": succeeded,
        "failed": failed,
        "failure_rate": round(failure_rate, 4),
        "avg_reasoning_words": round(avg_len, 1),
    }

    if failure_rate > 0.05:
        logger.warning(
            "Failure rate %.1f%% exceeds 5%% threshold. "
            "Consider resubmitting failed items.",
            failure_rate * 100,
        )

    print(f"\n=== Collection complete ===")
    print(f"  Succeeded: {succeeded}/{total}")
    print(f"  Failed: {failed}/{total}")
    print(f"  Avg reasoning: {avg_len:.0f} words")
    print(f"  Output: {output_path}")
    print(f"  Raw results: {raw_output_path}")

    return stats


def _extract_reasoning(response: str) -> tuple[str, str]:
    """Split response into reasoning trace and YAML config.

    Returns (reasoning, yaml_str). If no YAML block found,
    entire response is treated as reasoning.
    """
    # Look for ```yaml block
    yaml_start = response.find("```yaml")
    if yaml_start == -1:
        yaml_start = response.find("```")

    if yaml_start == -1:
        return response.strip(), ""

    reasoning = response[:yaml_start].strip()
    yaml_block = response[yaml_start:]

    # Extract content between ``` markers
    lines = yaml_block.split("\n")
    yaml_lines = []
    inside = False
    for line in lines:
        if line.strip().startswith("```") and not inside:
            inside = True
            continue
        if line.strip() == "```" and inside:
            break
        if inside:
            yaml_lines.append(line)

    return reasoning, "\n".join(yaml_lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Batch API reasoning trace generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # prepare
    prep = subparsers.add_parser("prepare", help="Build batch request JSONL")
    prep.add_argument("--input", required=True, type=str)
    prep.add_argument("--output", required=True, type=str)

    # submit
    sub = subparsers.add_parser("submit", help="Submit batch to Anthropic API")
    sub.add_argument("--requests", required=True, type=str)

    # collect
    col = subparsers.add_parser("collect", help="Download and parse batch results")
    col.add_argument("--batch-id", required=True, type=str)
    col.add_argument("--input", required=True, type=str)
    col.add_argument("--output", required=True, type=str)

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s - %(message)s",
    )

    if args.command == "prepare":
        count = prepare_batch(Path(args.input), Path(args.output))
        print(f"Prepared {count} batch requests.")

    elif args.command == "submit":
        submit_batch(Path(args.requests))

    elif args.command == "collect":
        collect_results(
            batch_id=args.batch_id,
            input_path=Path(args.input),
            output_path=Path(args.output),
        )


if __name__ == "__main__":
    main()

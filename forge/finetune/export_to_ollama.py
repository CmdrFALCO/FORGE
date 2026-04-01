#!/usr/bin/env python3
"""
Stage 4: Export fine-tuned adapter to Ollama via GGUF.

Merges QLoRA adapter into base model, saves as GGUF Q4_K_M,
creates an Ollama Modelfile, and registers the model.

Usage:
    python -m forge.finetune.export_to_ollama \
        --adapter-path forge/finetune/output/adapter_medium \
        --model-name qwen25-7b-forge-medium \
        --quantization Q4_K_M \
        --verbose
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def export_to_ollama(
    adapter_path: Path,
    model_name: str,
    quantization: str = "q4_k_m",
    output_dir: Path | None = None,
    verbose: bool = False,
):
    """Merge adapter, convert to GGUF, register with Ollama."""
    if output_dir is None:
        output_dir = adapter_path.parent

    # Step 1: Merge adapter into base model and save as GGUF
    logger.info("Merging adapter and saving as GGUF (%s)...", quantization)

    try:
        from unsloth import FastLanguageModel

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=str(adapter_path),
            max_seq_length=4096,
            load_in_4bit=True,
        )

        gguf_path = output_dir / f"{model_name}.gguf"

        # Unsloth has built-in GGUF export
        model.save_pretrained_gguf(
            str(output_dir / model_name),
            tokenizer,
            quantization_method=quantization,
        )

        # Unsloth may save with a different name pattern — find the GGUF
        possible_paths = [
            output_dir / f"{model_name}-unsloth.{quantization.upper()}.gguf",
            output_dir / f"{model_name}-unsloth-{quantization}.gguf",
            output_dir / f"{model_name}.gguf",
        ]
        gguf_path = None
        for p in possible_paths:
            if p.exists():
                gguf_path = p
                break

        if gguf_path is None:
            # Search for any GGUF in output dir
            ggufs = list(output_dir.glob(f"{model_name}*.gguf"))
            if ggufs:
                gguf_path = ggufs[0]
            else:
                logger.error("GGUF file not found after export. Check %s", output_dir)
                return None

        logger.info("GGUF saved: %s (%.1f MB)", gguf_path, gguf_path.stat().st_size / 1e6)

    except Exception as e:
        logger.error("Merge/export failed: %s", e)
        raise

    # Step 2: Create Ollama Modelfile
    modelfile_path = output_dir / f"Modelfile_{model_name}"
    modelfile_content = f"""FROM {gguf_path}

PARAMETER temperature 0.0
PARAMETER num_ctx 4096
PARAMETER num_predict 2000
PARAMETER stop <|im_end|>
PARAMETER stop <|endoftext|>
"""
    with open(modelfile_path, "w") as f:
        f.write(modelfile_content)
    logger.info("Modelfile written: %s", modelfile_path)

    # Step 3: Register with Ollama
    logger.info("Creating Ollama model: %s", model_name)
    result = subprocess.run(
        ["ollama", "create", model_name, "-f", str(modelfile_path)],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        logger.error("ollama create failed:\n%s\n%s", result.stdout, result.stderr)
        return None

    logger.info("Ollama model created: %s", model_name)

    # Step 4: Quick verification
    logger.info("Verifying model loads...")
    verify = subprocess.run(
        ["ollama", "run", model_name, "Say hello", "--nowordwrap"],
        capture_output=True, text=True, timeout=120,
    )
    if verify.returncode == 0:
        logger.info("Verification passed: %s", verify.stdout[:100].strip())
    else:
        logger.warning("Verification failed: %s", verify.stderr[:200])

    # Save export metadata
    meta = {
        "model_name": model_name,
        "adapter_path": str(adapter_path),
        "gguf_path": str(gguf_path),
        "gguf_size_mb": round(gguf_path.stat().st_size / 1e6, 1),
        "quantization": quantization,
        "modelfile_path": str(modelfile_path),
        "ollama_create_success": result.returncode == 0,
    }
    meta_path = output_dir / f"export_metadata_{model_name}.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    if verbose:
        print(f"\n=== Export complete: {model_name} ===")
        print(f"  GGUF: {gguf_path} ({meta['gguf_size_mb']} MB)")
        print(f"  Ollama: {model_name}")
        print(f"  Metadata: {meta_path}")

    return meta


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Export adapter to Ollama")
    parser.add_argument("--adapter-path", required=True, type=str)
    parser.add_argument("--model-name", required=True, type=str)
    parser.add_argument("--quantization", type=str, default="q4_k_m")
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)-7s %(name)s - %(message)s",
    )

    out_dir = Path(args.output_dir) if args.output_dir else None
    export_to_ollama(
        adapter_path=Path(args.adapter_path),
        model_name=args.model_name,
        quantization=args.quantization,
        output_dir=out_dir,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()

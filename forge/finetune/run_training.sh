#!/bin/bash
# =============================================================================
# FORGE QLoRA Fine-Tuning Pipeline
# =============================================================================
#
# Trains Medium and Hard adapters on Qwen 2.5 7B, then exports to Ollama.
# Expected runtime: ~6-8 hours on RTX 3090.
#
# Usage:
#   cd /home/cmdrfalco/Projects/CmdrFALCO/FORGE
#   nohup bash forge/finetune/run_training.sh > forge/finetune/output/training_run.log 2>&1 &
#
# =============================================================================

set -euo pipefail

PYTHON=".venv/bin/python3"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "=== FORGE QLoRA Fine-Tuning Pipeline ==="
log "GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader)"
echo ""

# --- Medium adapter ---
log "--- Training Medium adapter (direct mapping) ---"
${PYTHON} -m forge.finetune.train \
  --dataset medium \
  --train-path forge/finetune/data/output/medium_train.jsonl \
  --val-path forge/finetune/data/output/medium_val.jsonl \
  --output-dir forge/finetune/output/ \
  --seed 42

log "--- Medium training complete ---"
echo ""

# --- Hard adapter ---
log "--- Training Hard adapter (with reasoning) ---"
${PYTHON} -m forge.finetune.train \
  --dataset hard \
  --train-path forge/finetune/data/output/hard_train.jsonl \
  --val-path forge/finetune/data/output/hard_val.jsonl \
  --output-dir forge/finetune/output/ \
  --seed 42

log "--- Hard training complete ---"
echo ""

# --- Export to Ollama ---
log "--- Exporting Medium to Ollama ---"
${PYTHON} -m forge.finetune.export_to_ollama \
  --adapter-path forge/finetune/output/adapter_medium \
  --model-name qwen25-7b-forge-medium \
  --quantization q4_k_m \
  --verbose

echo ""

log "--- Exporting Hard to Ollama ---"
${PYTHON} -m forge.finetune.export_to_ollama \
  --adapter-path forge/finetune/output/adapter_hard \
  --model-name qwen25-7b-forge-hard \
  --quantization q4_k_m \
  --verbose

echo ""

# --- Verify ---
log "--- Verifying Ollama models ---"
ollama list | grep qwen25-7b-forge || echo "WARNING: Models not found in Ollama"

echo ""
log "=== Pipeline complete ==="

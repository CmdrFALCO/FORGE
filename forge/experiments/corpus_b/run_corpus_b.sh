#!/usr/bin/env bash
# =============================================================================
# Corpus B — Full local model run (5 models × unsupervised + supervised)
# =============================================================================
#
# Sequential execution, one model at a time. Each model: unsup then sup.
# Order: fastest first (Llama 3B → Llama 8B → Qwen 9B → Mistral → Qwen 27B)
#
# Usage:
#   cd /home/cmdrfalco/Projects/CmdrFALCO/FORGE
#   nohup bash forge/experiments/corpus_b/run_corpus_b.sh > forge/experiments/corpus_b/corpus_b_run.log 2>&1 &
#
# =============================================================================

set -euo pipefail

PYTHON=".venv/bin/python3"
RUNNER="forge/experiments/corpus_b/run_corpus_b_experiments.py"
OLLAMA="http://localhost:11434"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

prewarm() {
    local model=$1
    log "Pre-warming ${model}..."
    curl -sf "${OLLAMA}/api/chat" -d "{
        \"model\": \"${model}\",
        \"messages\": [{\"role\": \"user\", \"content\": \"hello\"}],
        \"stream\": false,
        \"options\": {\"temperature\": 0.0, \"num_ctx\": 8192, \"num_predict\": 5}
    }" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'  {d.get(\"model\")} loaded')"
}

unload() {
    local model=$1
    log "Unloading ${model}..."
    curl -sf "${OLLAMA}/api/generate" -d "{\"model\": \"${model}\", \"keep_alive\": 0}" > /dev/null 2>&1 || true
    sleep 3
}

run_pair() {
    local model_key=$1
    log "=========================================="
    log "Starting ${model_key} (unsupervised + supervised)"
    log "=========================================="
    ${PYTHON} -u ${RUNNER} --model "${model_key}" --condition unsup
    ${PYTHON} -u ${RUNNER} --model "${model_key}" --condition sup
    log "${model_key} DONE"
    echo
}

# =============================================================================
log "CORPUS B — Local Model Run Starting"
log "=========================================="

# --- Llama 3.2 3B ---
unload "qwen3.5:27b"
unload "qwen3.5:9b"
unload "mistral-small3.1"
unload "llama3.1:8b"
prewarm "llama3.2:3b"
log "--- Model 1/5: Llama 3.2 3B ---"
run_pair "llama3b"

# --- Llama 3.1 8B ---
unload "llama3.2:3b"
prewarm "llama3.1:8b"
log "--- Model 2/5: Llama 3.1 8B ---"
run_pair "llama8b"

# --- Qwen 3.5 9B ---
unload "llama3.1:8b"
prewarm "qwen3.5:9b"
log "--- Model 3/5: Qwen 3.5 9B ---"
run_pair "qwen9b"

# --- Mistral Small 3.1 ---
unload "qwen3.5:9b"
prewarm "mistral-small3.1"
log "--- Model 4/5: Mistral Small 3.1 ---"
run_pair "mistral"

# --- Qwen 3.5 27B ---
unload "mistral-small3.1"
prewarm "qwen3.5:27b"
log "--- Model 5/5: Qwen 3.5 27B ---"
run_pair "qwen27b"

# --- Done ---
unload "qwen3.5:27b"
log "=========================================="
log "ALL CORPUS B LOCAL EXPERIMENTS COMPLETE"
log "=========================================="

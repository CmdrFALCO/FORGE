#!/usr/bin/env bash
# =============================================================================
# AXIOM Multi-Model Full Run — Mistral Small 3.1, Llama 3.1 8B, Llama 3.2 3B
# =============================================================================
#
# Sequential execution, one model at a time.
# Order: Mistral (largest) → Llama 8B → Llama 3B (smallest)
#
# Usage:
#   cd /home/cmdrfalco/Projects/CmdrFALCO/FORGE
#   nohup bash forge/experiments/run_multimodel_full.sh > forge/experiments/results/multimodel_full_run.log 2>&1 &
#
# =============================================================================

set -euo pipefail

PYTHON=".venv/bin/python3"
CORPUS="forge/experiments/prompt_corpus_v1.json"
OLLAMA="http://localhost:11434"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

prewarm() {
    local model=$1
    log "Pre-warming ${model}..."
    curl -sf "${OLLAMA}/api/chat" -d "{
        \"model\": \"${model}\",
        \"messages\": [{\"role\": \"user\", \"content\": \"hello\"}],
        \"stream\": false, \"think\": false,
        \"options\": {\"temperature\": 0.0, \"num_ctx\": 8192, \"num_predict\": 5}
    }" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'  {d.get(\"model\")} loaded')"
}

unload() {
    local model=$1
    log "Unloading ${model}..."
    curl -sf "${OLLAMA}/api/generate" -d "{\"model\": \"${model}\", \"keep_alive\": 0}" > /dev/null 2>&1 || true
    sleep 3
}

run_experiment() {
    local exp_id=$1
    log "=========================================="
    log "Starting ${exp_id}"
    log "=========================================="
    ${PYTHON} -u -m forge.experiments.run_experiments \
        --experiment "${exp_id}" \
        --corpus "${CORPUS}"
    log "${exp_id} DONE"
    echo
}

# =============================================================================
log "AXIOM Multi-Model Full Run — Starting"
log "=========================================="

# --- Mistral Small 3.1 (24B) ---
unload "llama3.2:3b"
unload "llama3.1:8b"
prewarm "mistral-small3.1"

log "--- Model 1/3: Mistral Small 3.1 ---"
run_experiment "exp_mistral_unsup"
run_experiment "exp_mistral_sup"

# --- Llama 3.1 8B ---
unload "mistral-small3.1"
prewarm "llama3.1:8b"

log "--- Model 2/3: Llama 3.1 8B ---"
run_experiment "exp_llama8b_unsup"
run_experiment "exp_llama8b_sup"

# --- Llama 3.2 3B ---
unload "llama3.1:8b"
prewarm "llama3.2:3b"

log "--- Model 3/3: Llama 3.2 3B ---"
run_experiment "exp_llama3b_unsup"
run_experiment "exp_llama3b_sup"

# --- Done ---
unload "llama3.2:3b"
log "=========================================="
log "ALL MULTI-MODEL EXPERIMENTS COMPLETE"
log "=========================================="

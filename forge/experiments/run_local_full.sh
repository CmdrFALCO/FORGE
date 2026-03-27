#!/usr/bin/env bash
# =============================================================================
# AXIOM Local Model Full Run — Sequential Execution
# =============================================================================
#
# Runs all 4 local experiments (500 prompts each) sequentially:
#   1. exp3a_small  (9B unsupervised)   ~1.3 hours
#   2. exp3b_small  (9B supervised)     ~1.5-2 hours
#   3. exp3a        (27B unsupervised)  ~3.6 hours
#   4. exp3b        (27B supervised)    ~5-7 hours
#
# Total estimated: 12-14 hours GPU time
#
# Usage:
#   cd /home/cmdrfalco/Projects/CmdrFALCO/FORGE
#   bash forge/experiments/run_local_full.sh 2>&1 | tee forge/experiments/results/local_full_run.log
#
# Prerequisites:
#   - Ollama running with qwen3.5:9b and qwen3.5:27b available
#   - .venv activated or available at .venv/bin/python3
#   - No other models loaded on the GPU
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
    }" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'  {d.get(\"model\")} loaded, eval_count={d.get(\"eval_count\")}')"
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
log "AXIOM Local Full Run — Starting"
log "Estimated total time: 12-14 hours"
log "=========================================="

# --- Phase 1: 9B experiments ---

unload "qwen3.5:27b"  # ensure 27B not loaded
prewarm "qwen3.5:9b"

log "--- Phase 1/2: Qwen 3.5 9B ---"
run_experiment "exp3a_small"
run_experiment "exp3b_small"

# --- Phase 2: 27B experiments ---

unload "qwen3.5:9b"
prewarm "qwen3.5:27b"

log "--- Phase 2/2: Qwen 3.5 27B ---"
run_experiment "exp3a"
run_experiment "exp3b"

# --- Done ---
log "=========================================="
log "ALL LOCAL EXPERIMENTS COMPLETE"
log "=========================================="
log "Results:"
for f in forge/experiments/results/exp3{a,b}_*_local.jsonl forge/experiments/results/exp3{a,b}_baseline_local.jsonl forge/experiments/results/exp3{a,b}_supervised_local.jsonl; do
    if [ -f "$f" ]; then
        n=$(wc -l < "$f")
        valid=$(python3 -c "
import json
with open('$f') as fh:
    print(sum(1 for l in fh if json.loads(l)['summary']['final_valid']))
")
        echo "  $(basename $f): ${valid}/${n} valid"
    fi
done

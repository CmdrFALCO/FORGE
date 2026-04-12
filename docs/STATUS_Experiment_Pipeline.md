# AXIOM Experiment Pipeline — Current Status

**Last updated:** 2026-03-25 ~22:00 CET

---

## What's Built (all committed and pushed to main)

| Phase | Description | Commit | Status |
|-------|-------------|--------|--------|
| Phase 1 | Instrumentation: ConstraintResult, CONSTRAINT_REGISTRY, supervised mode, structured logging | `368ea63` | Done |
| Phase 1b | Backend instrumentation: LLMUsage, temperature, token counts on ClaudeBackend/OllamaBackend | `777f8c3` | Done |
| Phase 3 | Stratified prompt corpus: 500 prompts in `forge/experiments/prompt_corpus_v1.json` | `ed66225` | Done |
| Phase 4 | Experiment runner: `forge/experiments/run_experiments.py` with JSONL output, resume, GPU monitor | `581a42e` | Done |
| Phase 5 | Analysis script | — | Not started |

## What's NOT Run Yet

The experiment runner is built and dry-run tested, but no actual experiments have been executed.

### Four Experiments to Run

| ID | Name | Backend | Model | Supervised | MAX_RETRY | Est. Time | Cost |
|----|------|---------|-------|------------|-----------|-----------|------|
| exp1 | Baseline (Cloud) | Claude API | claude-sonnet-4-6-20250514 | False | 1 | ~4-8h | API tokens |
| exp2 | Supervised (Cloud) | Claude API | claude-sonnet-4-6-20250514 | True | 4 | ~8-17h | API tokens |
| exp3a | Baseline (Local) | Ollama | qwen2.5-coder:32b | False | 1 | ~17-42h | Electricity |
| exp3b | Supervised (Local) | Ollama | qwen2.5-coder:32b | True | 4 | ~33-83h | Electricity |

All use the same 500 prompts from `prompt_corpus_v1.json`. Temperature 0.0 for reproducibility.

### Execution Commands

```bash
cd ~/Projects/CmdrFALCO/FORGE

# Pilot first (5 prompts, verify end-to-end)
.venv311/bin/python -m forge.experiments.run_experiments \
    --experiment exp1 \
    --corpus forge/experiments/prompt_corpus_v1.json \
    --limit 5

# Full cloud experiments (need ANTHROPIC_API_KEY)
.venv311/bin/python -m forge.experiments.run_experiments \
    --experiment exp1 \
    --corpus forge/experiments/prompt_corpus_v1.json

.venv311/bin/python -m forge.experiments.run_experiments \
    --experiment exp2 \
    --corpus forge/experiments/prompt_corpus_v1.json

# Full local experiments (need Ollama + qwen2.5-coder:32b)
.venv311/bin/python -m forge.experiments.run_experiments \
    --experiment exp3a \
    --corpus forge/experiments/prompt_corpus_v1.json

.venv311/bin/python -m forge.experiments.run_experiments \
    --experiment exp3b \
    --corpus forge/experiments/prompt_corpus_v1.json

# Resume an interrupted run (auto-detects progress)
.venv311/bin/python -m forge.experiments.run_experiments \
    --experiment exp2 \
    --corpus forge/experiments/prompt_corpus_v1.json
```

### Prerequisites Before Running

1. **ANTHROPIC_API_KEY** must be set in environment for exp1/exp2
2. **Ollama** must be running with `qwen2.5-coder:32b` pulled for exp3a/exp3b
   - Check: `ollama list | grep qwen`
   - Pull if missing: `ollama pull qwen2.5-coder:32b`
3. **GPU** available for exp3a/exp3b (RTX 3060 on the rig)

### Output Files

Results go to `forge/experiments/results/`:
```
forge/experiments/results/
├── exp1_baseline_cloud.jsonl
├── exp2_supervised_cloud.jsonl
├── exp3a_baseline_local.jsonl
├── exp3b_supervised_local.jsonl
└── gpu_logs/
    ├── exp3a_gpu.csv
    └── exp3b_gpu.csv
```

These are JSONL (one JSON object per line, per prompt). Append-only and resume-safe.

Do NOT commit results to git — they're large and contain raw LLM output.

---

## Recommended Execution Order

1. **Pilot** exp1 with `--limit 5` — verify pipeline works end-to-end
2. **exp1** (cloud, unsupervised) — fastest, validates cloud path
3. **exp2** (cloud, supervised) — validates retry loop with real LLM
4. **exp3a** (local, unsupervised) — validates Ollama path
5. **exp3b** (local, supervised) — longest run, do last

exp1+exp2 can run overnight (~12-25h total). exp3a+exp3b need 2-5 days.

---

## Key Architecture Decisions (for context recovery)

- **Direct Python invocation** — the runner imports `forge.axiom.supervisor.driver.generate_cell_design()` directly. No HTTP, no FastAPI.
- **MAX_RETRIES control** — set via `supervisor_driver.MAX_RETRIES = N` before each call. Unsupervised=1, supervised=4.
- **Token tracking** — `backend.last_usage` (LLMUsage dataclass) populated after each `generate()` call. Limitation: only captures last call's tokens for multi-attempt runs.
- **Constraint results** — `GenerationResult.attempt_constraint_results` is a `list[list[ConstraintResult]]` from Phase 1 instrumentation. Each inner list is one attempt's full 14-constraint report card.
- **CONSTRAINT_REGISTRY** — IDs are C1-C7 (common), PR1-PR7 (prismatic), PO1-PO7 (pouch), CY1-CY8 (cylindrical). Defined in `forge/engine/validation/constraint_validator.py`.

---

## Known Gaps / Limitations

1. **Per-attempt token counts**: only last attempt's tokens captured (driver calls backend multiple times internally but we only read `last_usage` once after the driver returns)
2. **Per-attempt raw LLM output**: driver stores `yaml_content` (final) and `retry_reasons` (feedback strings) but not the full LLM response text per attempt
3. **Per-attempt inference vs simulation timing**: driver doesn't separate LLM inference time from validation/calculation time. Only total wall time is captured.
4. **API routing 404**: pre-existing nginx/root_path issue on the Docker deployment. Does NOT affect experiments (they use direct Python calls).

---

## File Reference

| File | Purpose |
|------|---------|
| `forge/experiments/run_experiments.py` | Main experiment runner |
| `forge/experiments/experiment_config.py` | Backend configs, experiment definitions |
| `forge/experiments/gpu_monitor.py` | nvidia-smi CSV logger |
| `forge/experiments/generate_corpus.py` | Phase 3 corpus generator |
| `forge/experiments/corpus_config.py` | Chemistry/application profiles |
| `forge/experiments/prompt_corpus_v1.json` | 500-prompt corpus |
| `forge/engine/validation/constraint_validator.py` | CONSTRAINT_REGISTRY, validate_physics() |
| `forge/engine/validation/schema_validator.py` | ConstraintResult, ValidationResult |
| `forge/axiom/supervisor/driver.py` | generate_cell_design() — the function experiments call |
| `forge/axiom/supervisor/result.py` | GenerationResult with attempt_constraint_results |
| `forge/axiom/backends/backends.py` | ClaudeBackend, OllamaBackend, LLMUsage |
| `forge/api/routes/pipeline.py` | Pipeline API route (supervised param, structured logging) |

---

## Other Active Work (parallel)

- **Opus CLI** was running Run 004 (Optuna comparison) on the autoresearch branch — check if complete
- **ML Dashboard** is live at `/app/ML_Autoresearch` with Runs 001-003, Surrogate Playground, prediction plots, Pareto front, calibration
- **Landing page** is live with EN/DE toggle at the Tailscale funnel URL
- **CI** should be green on main (last checked: 1457 tests pass, 1 pre-existing pybamm failure)

# FORGE OpenAI Build Week Guide

## 1. Project Mission

- FORGE is a neuro-symbolic engineering platform.
- An LLM generates engineering artefacts.
- Deterministic validators check structure, physical constraints, and consistency.
- AXIOM supervises the generate -> validate -> retry -> accept/reject loop.
- The Build Week extension adds OpenAI GPT-5.6 integration and a focused demonstration of formal supervision.

> FORGE Build Week demonstrates how AXIOM supervises GPT-5.6-generated battery-cell specifications, detects a coupled engineering constraint violation, returns structured corrective feedback, and accepts the corrected design with a complete audit trace.

## 2. Baseline and Provenance

- Baseline repository: `CmdrFALCO/FORGE`.
- Baseline commit: `25b738aa6b42b404723f7607954f4252fef5a1f3`.
- Baseline tag: `build-week-baseline-2026-07-19`.
- Build Week branch: `build-week/openai`.
- Active worktree: `D:\_Projects\2026_07_19_FORGE-v2\FORGE-BuildWeek`.
- The FORGE engine, AXIOM validator and supervisor, retry loop, FastAPI pipeline, Streamlit GUI,
  constraint registry, tests, experimental infrastructure, and battery-cell domain logic are pre-existing work.
- Keep every Build Week contribution clearly distinguishable from the baseline in Git history.

## 3. Repository Map

- `forge/engine/`: battery-cell models, calculations, conversion, geometry, CAD, cost, and validation logic.
- `forge/axiom/`: LLM generation, parsing, feedback, backend, validation, and supervision components.
- `forge/axiom/backends/`: the `LLMBackend` protocol, `LLMUsage`, and Claude, Ollama, and mock backends.
- `forge/axiom/supervisor/`: the generate-parse-validate-retry driver and `GenerationResult` model.
- `forge/api/`: FastAPI application, backend dependency factory, schemas, and HTTP routes.
- `forge/gui/`: Streamlit application, AXIOM pipeline tracking, pages, components, and visualizations.
- `tests/`: engine, AXIOM, API, GUI, materials, and ML test suites.
- `scripts/`: absent in the baseline; utility and launch scripts currently live at repository root.
- `demos/`: demonstration assets and integrations, currently including `demos/n8n/`.
- `docs/`: architecture, API, AXIOM, engine, experiment, status, and planning documentation.
- `experiments/`: AXIOM, data, ML, and notebook research infrastructure.

## 4. Files to Inspect First

- Read this `AGENTS.md` before changing Build Week files.
- Read `docs/BUILD_WEEK_SPEC.md` when it is added in a subsequent task.
- Read `docs/BUILD_WEEK_LOG.md` when it is added in a subsequent task.
- Inspect `forge/axiom/backends/backends.py` before extending backend behavior or telemetry.
- Inspect `forge/axiom/backends/__init__.py` before exporting a backend.
- Inspect `forge/axiom/supervisor/driver.py` and `forge/axiom/supervisor/result.py` before changing supervision.
- Inspect `forge/api/deps.py` before changing backend registration or dependency checks.
- Inspect `forge/api/routes/pipeline.py` and `forge/api/routes/generation.py` before changing API routing.
- Inspect `forge/api/schemas/models.py` before changing request, response, attempt, or constraint schemas.
- Inspect `forge/gui/pages/4_AXIOM_Designer.py` and `forge/gui/axiom_pipeline.py` before changing the demo UI.
- Inspect relevant tests in `tests/axiom/`, `tests/api/`, and `tests/gui/test_axiom_pipeline.py`.
- Treat `docs/BUILD_WEEK_SPEC.md` and `docs/BUILD_WEEK_LOG.md` as expected future files, not baseline files.

## 5. Build Week Scope

- Add an OpenAI GPT-5.6 backend through the existing backend abstraction.
- Register the OpenAI backend in the existing API backend factory.
- Map token usage and model metadata into the existing `LLMUsage` structure.
- Add tests for OpenAI backend behavior and API routing.
- Add a failure-discovery harness for genuine GPT-5.6 first-attempt engineering failures.
- Store real retry traces needed for verification and replay.
- Add one focused Build Week demonstration page.
- Provide clearly labelled live and verified-replay modes.
- Document which functionality was pre-existing and which was implemented during Build Week.

## 6. Non-Goals

- Do not redesign the CellCAD or FORGE calculation engine.
- Do not change engineering equations without an explicit reviewed task.
- Do not weaken, bypass, or manipulate constraints to manufacture a demonstration failure.
- Do not add MBSE support during Build Week.
- Do not build a generic constraint editor.
- Do not add a multi-agent architecture.
- Do not refactor unrelated ML, CAD, simulation, deployment, or experimental modules.
- Do not remove research infrastructure.
- Do not rename FORGE or AXIOM.
- Do not introduce a new validation architecture.
- Do not rewrite the existing retry loop unless a verified compatibility defect requires a minimal fix.
- Do not perform broad formatting-only changes.
- Do not add MCP integration before the core GPT-5.6 retry demonstration works.
- Do not commit secrets, API keys, private data, proprietary company data, or internal Mercedes-Benz information.

## 7. Architectural Invariants

- Preserve the existing `LLMBackend` abstraction.
- Preserve `generate(messages) -> str` unless an explicit task approves an interface change.
- Preserve the existing `LLMUsage` telemetry pattern.
- Preserve the AXIOM generate -> parse -> validate -> feedback -> retry flow.
- Keep the deterministic validator authoritative for acceptance or rejection.
- Preserve complete attempt records and per-attempt constraint results.
- Keep infrastructure failures distinct from validation rejections.
- Preserve compatibility with Claude, Ollama, and mock backends.
- Preserve backward compatibility for existing API users.
- Keep all core behavior testable without live API access.

## 8. Engineering Integrity

- Demonstration failures must originate from real GPT-5.6 outputs.
- Candidate prompts may be difficult, edge-case, underspecified, or multi-constraint.
- Prompts must not explicitly command the model to violate a known constraint.
- Constraints must not be modified solely to force a failure.
- Schema or prompt mismatches must not be presented as engineering failures.
- Prefer a schema-valid specification that fails a coupled physics or consistency rule.
- Every replay trace must preserve the real prompt and model identifier.
- Every replay trace must preserve attempt outputs, validator results, and corrective feedback.
- Preserve timestamps where available and the final accepted or rejected result.
- Clearly label recorded output as recorded or verified replay; never present replay as a live call.

## 9. Coding Conventions

- Maintain Python 3.11 compatibility; `pyproject.toml` requires Python `>=3.11`.
- Add type hints to new public interfaces.
- Use dataclasses or Pydantic models consistently with the surrounding module.
- Keep formatting and imports compatible with Ruff.
- Preserve the configured 120-character line length and existing lint selections.
- Do not add dependencies unless the bounded task requires them.
- Keep changes minimal and localized to the responsible modules.
- Write useful docstrings for public classes and functions.
- Raise clear, actionable errors for configuration, dependency, and service failures.
- Check optional SDK availability at import or initialization boundaries.
- Read secrets and runtime configuration from environment variables.
- Never hard-code API keys or secret values.

## 10. Testing Requirements

- Tests must not call the live OpenAI API by default.
- Mark live API tests with the existing `live` pytest marker.
- Mock successful OpenAI generation without network access.
- Mock SDK absence and missing API-key behavior.
- Mock and verify token-usage and model-metadata mapping.
- Mock and verify backend factory routing.
- Keep existing Claude, Ollama, and mock backend tests passing.
- Keep relevant API and AXIOM tests passing.
- Run targeted tests first, then the broader non-live suite where practical.
- Do not alter a test merely to hide a regression.
- Install development tooling when needed with `pip install -e ".[dev]"`.
- Run focused suites with `pytest tests/axiom tests/api`.
- Run the configured non-live suite with `pytest`; project addopts exclude `live` tests by default.
- Run live tests only when explicitly authorized, using `pytest -m live -v -s`.
- Run lint checks with `ruff check .`.
- Run static checks with `mypy forge/` where relevant.

## 11. Git and Commit Discipline

- Keep one bounded objective per commit.
- Include no unrelated file changes.
- Inspect `git diff` before committing.
- Do not amend or rewrite baseline history.
- Do not force-push.
- Do not push without explicit user instruction.
- Use clear commit prefixes such as `docs:`, `feat:`, `test:`, or `fix:`.
- Record major decisions and verified traces in `docs/BUILD_WEEK_LOG.md` after that file is introduced.
- Preserve clear provenance between baseline and Build Week contributions.

## 12. Security and Privacy

- Read `OPENAI_API_KEY` from the environment.
- Never commit a `.env` file containing secrets.
- An `.env.example` may contain variable names only, never secret values.
- Inspect logs and traces for sensitive content before committing them.
- Do not retain secret headers or private user data in raw API responses.
- Use only synthetic or public engineering prompts in the demonstration.

## 13. Definition of Done

- The requested bounded change is implemented.
- Relevant tests pass.
- No unrelated files changed.
- Documentation is updated where the task requires it.
- The complete `git diff` is reviewed.
- Limitations, skipped checks, and remaining risks are reported honestly.
- Stop and wait for user confirmation before beginning the next phase.

## 14. Required Working Behavior for Codex

- Inspect relevant repository files before editing.
- Propose a bounded plan before multi-file tasks.
- Prefer extending existing abstractions and local patterns.
- Stop and request clarification when engineering semantics are unclear.
- Never silently modify physical constraints or engineering equations.
- Report changed files, tests run, results, and remaining risks.
- Do not proceed to the next project phase without explicit user confirmation.

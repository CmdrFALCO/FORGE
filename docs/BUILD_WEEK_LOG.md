# FORGE OpenAI Build Week — Engineering Log

This is the append-only engineering and provenance log for the FORGE OpenAI Build Week extension.

- Add new entries chronologically.
- Do not silently rewrite historical entries.
- Add corrections as new dated entries that identify the entry being corrected.
- Base implementation claims on observed evidence.
- Record commands, test results, model identifiers, trace identifiers, and commit SHAs where relevant.
- Never record secrets, API keys, private prompts, proprietary information, or hidden chain-of-thought.

## Project Metadata

- **Project:** `FORGE — AXIOM Guard`
- **Baseline repository:** `CmdrFALCO/FORGE`
- **Baseline commit:** `25b738aa6b42b404723f7607954f4252fef5a1f3`
- **Baseline tag:** `build-week-baseline-2026-07-19`
- **Build Week branch:** `build-week/openai`
- **Baseline worktree:** `D:\_Projects\2026_07_19_FORGE-v2\FORGE-v1`
- **Active worktree:** `D:\_Projects\2026_07_19_FORGE-v2\FORGE-BuildWeek`
- **Project start date:** `2026-07-19`
- **Primary model target:** `GPT-5.6`
- **Status:** `Documentation and provenance preparation`

## 1. Log Conventions

Use this entry structure:

```markdown
## YYYY-MM-DD — Entry title

### Objective

### Actions

### Evidence

### Decisions

### Files changed

### Tests and checks

### Risks or open questions

### Next gate
```

- Omit an empty subsection only when it is genuinely irrelevant.
- Use exact repository paths, command names, model identifiers, and commit SHAs.
- Distinguish observed facts from plans, hypotheses, and intended work.
- Label failed or inconclusive experiments honestly.
- Record successful and unsuccessful GPT-5.6 failure-discovery attempts.
- Identify live API calls and recorded or verified replays clearly.
- Include model name, generation settings, prompt ID, and trace ID when applicable.
- Do not paste excessively large raw outputs when a committed trace file exists.
- Link to the committed trace path instead.
- Record skipped tests and the reason they were skipped.

## 2. Current Project State

Observed at log creation on 2026-07-19:

- The baseline workspace has been prepared.
- Baseline commit `25b738aa6b42b404723f7607954f4252fef5a1f3` has an annotated tag named
  `build-week-baseline-2026-07-19`.
- The Build Week worktree and branch have been created.
- `FORGE-v1` on `main` and `FORGE-BuildWeek` on `build-week/openai` initially point to the same baseline commit.
- Both worktrees are clean with respect to tracked files.
- No Build Week implementation code exists yet.
- `AGENTS.md` has been created and remains untracked.
- `docs/BUILD_WEEK_SPEC.md` has been created and remains untracked.
- `docs/BUILD_WEEK_LOG.md` is being created in this task.
- The existing AXIOM GUI page is `forge/gui/pages/4_AXIOM_Designer.py`.
- Existing recorded AXIOM demo data is stored under `data/demos/axiom/`.
- Actual candidate constraint identifiers include `C1` for computed N/P ratio and `CY5` for cylindrical
  jelly-roll fit.
- No root `scripts/` directory exists.
- Git reports a non-blocking, unresolved permission warning for
  `C:\Users\CmdrFALCO\.config\git\ignore`.
- No Build Week branch, tag, or documentation has been pushed during this preparation.

## 3. Confirmed Project Decisions

1. The original `FORGE-v1` worktree remains the frozen baseline.
2. Development occurs only in `FORGE-BuildWeek`.
3. The Build Week branch is `build-week/openai`.
4. The extension reuses the existing FORGE and AXIOM architecture rather than extracting or rewriting it.
5. GPT-5.6 will be added through the existing `LLMBackend` abstraction.
6. The existing validator and supervisor remain authoritative.
7. The primary demonstration must use a genuine GPT-5.6 first-attempt failure.
8. Constraints will not be weakened or manipulated to create the demonstration.
9. A schema-valid coupled engineering failure is preferred.
10. Computed N/P ratio and cylindrical jelly-roll fit are the leading candidates.
11. Live mode and verified-replay mode will be clearly distinguished.
12. Verified replay must contain a real captured GPT-5.6 trace.
13. No MBSE, multi-agent, generic rule authoring, model training, CAD redesign, or ML extension is included.
14. Codex work proceeds in bounded steps with user confirmation between phases.
15. No code implementation begins before documentation and provenance files are reviewed.

## 4. Build Week Contribution Boundary

| Area | Pre-existing baseline | Intended Build Week contribution | Current status |
| --- | --- | --- | --- |
| Deterministic battery engine | Models, calculations, conversion, and validation under `forge/engine/` | Reuse without equation or architecture changes | Pre-existing |
| AXIOM validator | Schema and engineering checks, including constraint registry | Reuse as deterministic acceptance authority | Pre-existing |
| AXIOM supervisor and retry loop | Generate, parse, validate, feedback, retry, convert, and calculate flow | Integrate GPT-5.6 through existing extension points | Pre-existing |
| Claude backend | `ClaudeBackend` and Anthropic dependency checks | Preserve compatibility | Pre-existing |
| Ollama backend | `OllamaBackend` and local HTTP integration | Preserve compatibility | Pre-existing |
| Mock backend | Sequenced test backend and usage approximation | Reuse and preserve compatibility | Pre-existing |
| FastAPI pipeline | `/api/v1/pipeline`, backend factory, supervised and unsupervised modes | Register OpenAI and retain API compatibility | Pre-existing |
| Attempt records | `GenerationResult`, `AttemptRecord`, and constraint-result records | Extend only where authentic trace evidence requires it | Pre-existing |
| Existing AXIOM GUI | AXIOM Designer, tracked pipeline steps, and recorded/live modes | Reuse components and conventions | Pre-existing |
| OpenAI backend | No OpenAI backend at baseline | Add GPT-5.6 through `LLMBackend` and `LLMUsage` | Not started |
| GPT-5.6 failure-discovery utility | No Build Week discovery utility | Find genuine first-attempt engineering failures | Not started |
| Authentic GPT-5.6 trace | No captured Build Week GPT-5.6 trace | Preserve a real failure, feedback, retry, and decision | Not started |
| Build Week demo page | Existing AXIOM Designer only | Add one focused Build Week story surface | Not started |
| Verified replay | Generic recorded AXIOM demos exist | Replay a clearly labelled authentic GPT-5.6 trace | Not started |
| Build Week documentation | Baseline documentation predates Build Week | Add operating guide, specification, and engineering log | Draft created |

## 5. Phase Gates

### Phase 0 — Documentation and Provenance

Completion requires:

- `AGENTS.md`;
- `docs/BUILD_WEEK_SPEC.md`;
- `docs/BUILD_WEEK_LOG.md`;
- user review; and
- one bounded documentation commit.

Current state: all three files have been drafted or are being drafted. User review, corrections, and the bounded
documentation commit remain outstanding.

### Phase 1 — OpenAI Backend

Completion requires:

- an OpenAI backend using the existing abstraction;
- one GPT-5.6 request completed through the existing pipeline;
- passing mocked tests; and
- passing existing backend regressions.

Current state: not started.

### Phase 2 — Failure Discovery

Completion requires:

- a real GPT-5.6 first-attempt engineering failure;
- a schema-valid failure where possible;
- structured AXIOM feedback;
- a later successful attempt; and
- a complete saved trace.

Current state: not started; no GPT-5.6 trace has been captured.

### Phase 3 — Demonstration Interface

Completion requires:

- one focused Build Week page;
- live mode;
- verified replay;
- understandable attempt progression; and
- exportable trace evidence.

Current state: not started.

### Phase 4 — Packaging

Completion requires:

- setup instructions;
- a README update;
- a successful relevant test run;
- a demo recording;
- a provenance statement;
- secret inspection; and
- a submission package.

Current state: not started.

## 6. Initial Chronological Entries

## 2026-07-19 — Baseline Frozen and Build Week Worktree Created

### Objective

Preserve the existing FORGE repository as an immutable baseline and create an isolated workspace for Build Week
development.

### Actions

- Inspected repository status.
- Confirmed a clean `main` branch.
- Synchronized with `origin/main` using fast-forward only.
- Created annotated tag `build-week-baseline-2026-07-19`.
- Created branch `build-week/openai`.
- Created worktree `D:\_Projects\2026_07_19_FORGE-v2\FORGE-BuildWeek`.
- Verified both worktrees initially point to the same commit.

### Evidence

- Baseline SHA: `25b738aa6b42b404723f7607954f4252fef5a1f3`.
- Baseline tag: `build-week-baseline-2026-07-19`.
- Build Week branch: `build-week/openai`.
- Baseline worktree: `D:\_Projects\2026_07_19_FORGE-v2\FORGE-v1`.
- Build Week worktree: `D:\_Projects\2026_07_19_FORGE-v2\FORGE-BuildWeek`.
- Both working trees were clean after preparation.
- No push was performed.

### Decisions

All Build Week work will occur in the new Build Week worktree.

### Files Changed

- No tracked repository files changed.

### Tests and Checks

- Git status, branch, SHA, tag, and worktree checks passed.
- No source tests were run because this was workspace preparation.

### Risks or Open Questions

- The global Git ignore permission warning is non-blocking but unresolved.

### Next Gate

Create and review repository instructions and the Build Week specification.

---

## 2026-07-19 — Repository Instructions Drafted

### Objective

Create a repository-level operating contract for subsequent Codex work.

### Actions

- Inspected the relevant repository structure.
- Created `AGENTS.md`.
- Documented scope, invariants, engineering integrity, testing, Git discipline, security, and completion behavior.

### Evidence

- Path: `AGENTS.md`.
- Line count: `181`.
- SHA-256: `94D8C12A73F8E55773E3C19EB1C5CDD13189B4BBE0DB23ACF25F8B36B556555F`.
- The file remains untracked.
- No commit was created.

### Decisions

- No root `scripts/` directory exists.
- Standalone utilities currently exist at repository root.
- Future utility placement must follow inspected repository conventions.

### Files Changed

- `AGENTS.md` created.

### Tests and Checks

- File content was reviewed using a no-index diff.
- No source tests were run.

### Risks or Open Questions

- `AGENTS.md` still requires user review and commit.

### Next Gate

Draft the bounded product and implementation specification.

---

## 2026-07-19 — Build Week Specification Drafted

### Objective

Define the bounded product, implementation scope, authentic failure requirements, architecture impact, phase gates,
and acceptance criteria.

### Actions

- Read `AGENTS.md` and relevant repository files.
- Created `docs/BUILD_WEEK_SPEC.md`.
- Adapted the specification to actual repository paths and constraints.

### Evidence

- Path: `docs/BUILD_WEEK_SPEC.md`.
- Line count: `440`.
- Existing AXIOM GUI path: `forge/gui/pages/4_AXIOM_Designer.py`.
- Existing recorded demo data path: `data/demos/axiom/`.
- Candidate constraint `C1`: computed N/P ratio.
- Candidate constraint `CY5`: cylindrical jelly-roll fit.
- The file remains untracked.
- No commit was created.

### Decisions

- The primary demo must use a real GPT-5.6 failure.
- Malformed output and schema errors are secondary scenarios.
- Coupled engineering failures are preferred.
- Verified replay is acceptable only when clearly labelled and based on a real captured run.

### Files Changed

- `docs/BUILD_WEEK_SPEC.md` created.

### Tests and Checks

- The `AGENTS.md` hash remained unchanged.
- No source tests were run.

### Risks or Open Questions

- The specification still requires user review.
- OpenAI backend implementation has not started.
- No GPT-5.6 trace has been captured.

### Next Gate

Create the engineering log, review all three documents, and commit Phase 0 documentation.

## 7. Open Questions Register

| ID | Question | Status | Resolution or next action |
| --- | --- | --- | --- |
| OQ-01 | Which exact OpenAI model identifier will be used at runtime? | Open | Resolve during Phase 1 planning. |
| OQ-02 | Which OpenAI SDK and Responses API integration pattern best fits the existing synchronous backend interface? | Open | Inspect current official SDK behavior during Phase 1. |
| OQ-03 | Where should the failure-discovery utility live given there is no root `scripts/` directory? | Open | Inspect utility conventions before Phase 2. |
| OQ-04 | Which candidate produces the strongest authentic demonstration: C1, CY5, or another coupled constraint? | Open | Compare authentic discovery results. |
| OQ-05 | How stable is the selected failure across repeated GPT-5.6 calls? | Open | Measure repeated live runs after selection. |
| OQ-06 | Does the existing pipeline expose enough raw attempt data for trace capture without modifying supervisor internals? | Open | Perform a bounded data-gap analysis. |
| OQ-07 | Can the existing AXIOM Designer be extended cleanly, or should a separate Build Week page be created? | Open | Decide after UI integration inspection. |
| OQ-08 | What trace redaction checks are needed before committing captured API results? | Open | Define an allowlist and review procedure. |
| OQ-09 | What is the smallest test set needed to validate OpenAI compatibility before the full suite? | Open | Select targeted backend and API tests in Phase 1. |
| OQ-10 | Should the Build Week branch later be pushed to the existing repository or published separately? | Open | Await explicit publication decision. |

## 8. Risk Register

| ID | Risk | Probability | Impact | Current mitigation | Status |
| --- | --- | --- | --- | --- | --- |
| R-01 | No authentic GPT-5.6 failure is found | Medium | High | Use a bounded set of legitimate edge-case and multi-constraint prompts. | Open |
| R-02 | Selected failure is not stable | High | Medium | Repeat the selected case, record settings, and retain verified replay. | Open |
| R-03 | Only schema failures are found | Medium | Medium | Classify honestly and refine prompts toward existing coupled constraints. | Open |
| R-04 | Retry does not recover | Medium | High | Bound retries, inspect feedback quality, and compare another authentic candidate. | Open |
| R-05 | API latency or outage affects the demo | Medium | Medium | Capture a genuine result and provide clearly labelled verified replay. | Open |
| R-06 | SDK behavior mismatches the synchronous backend interface | Medium | Medium | Isolate the optional SDK and test response extraction with mocks. | Open |
| R-07 | OpenAI changes regress existing backends | Low | High | Keep changes localized and run Claude, Ollama, mock, API, and AXIOM tests. | Open |
| R-08 | A secret or sensitive value enters a trace | Low | High | Use synthetic prompts, allowlist fields, redact, and inspect before commit. | Open |
| R-09 | Scope expands beyond the core demonstration | Medium | High | Enforce exclusions, bounded tasks, phase gates, and user confirmation. | Open |
| R-10 | UI work consumes too much time | Medium | Medium | Reuse existing Streamlit components and prioritize trace comprehension. | Open |
| R-11 | Documentation and provenance remain uncommitted | Medium | Medium | Complete user review and one bounded Phase 0 documentation commit. | Open |
| R-12 | Build Week deadline pressure reduces verification | High | High | Protect phase gates, prioritize the core trace, and report skipped work honestly. | Open |

## 9. Next Planned Action

The immediate next action is:

1. User review of `AGENTS.md`, `docs/BUILD_WEEK_SPEC.md`, and `docs/BUILD_WEEK_LOG.md`.
2. Corrections where required.
3. One bounded Phase 0 documentation commit.
4. Only then begin planning the OpenAI backend implementation.

Do not begin Phase 1 before explicit user confirmation.

## 2026-07-19 — Phase 0 documentation reviewed

### Objective

Review the repository instructions, product specification, and engineering log for consistency before beginning
implementation.

### Actions

- Read all three documents in full.
- Cross-checked provenance, scope, architecture, non-goals, phase gates, engineering integrity rules, paths, and
  constraint identifiers.
- Confirmed product identity and GPT-5.6 model naming are consistent.
- Confirmed the baseline and intended Build Week contribution remain clearly separated.
- No minor editorial corrections were required.
- No implementation files were touched.

### Evidence

- Reviewed `AGENTS.md`.
- Reviewed `docs/BUILD_WEEK_SPEC.md`.
- Reviewed `docs/BUILD_WEEK_LOG.md`.
- Current branch: `build-week/openai`.
- Baseline SHA: `25b738aa6b42b404723f7607954f4252fef5a1f3`.
- `git diff --check` and no-index whitespace checks reported no whitespace errors; line-ending normalization warnings
  remain informational.
- Final review outcome: no substantive contradiction found.

### Decisions

Phase 0 documentation is approved for one bounded documentation commit.

### Files changed

- `docs/BUILD_WEEK_LOG.md`: this review entry appended.
- `AGENTS.md`: reviewed and unchanged during this review.
- `docs/BUILD_WEEK_SPEC.md`: reviewed and unchanged during this review.

### Tests and checks

- No source tests were required because this review changed documentation only.
- Markdown content, complete file contents, Git state, and diff whitespace checks were reviewed.
- No source files changed.

### Risks or open questions

- Implementation questions `OQ-01` through `OQ-10` remain open.
- The unresolved global Git ignore permission warning remains non-blocking.

### Next gate

- Commit the Phase 0 documentation.
- Then plan the Phase 1 OpenAI backend implementation.
- Do not begin Phase 1 in this task.

## 2026-07-19 - Phase 1 live OpenAI smoke test passed

### Objective

Verify, with one explicitly authorized live request, that the committed OpenAI backend can complete the existing
FastAPI and AXIOM pipeline without changing the supervisor, validator, or engineering constraints.

### Actions

- Reconfirmed branch `build-week/openai`, HEAD `51717eaadc77911425c754f404642a56d5e8ff82`, and a clean working tree.
- Inspected the existing `live` pytest marker, credential guards, FastAPI pipeline schema, exception mapping, and
  supervisor attempt accounting.
- Installed the declared optional SDK dependency `openai>=2.45.0,<3` at Windows user scope; resolved version
  `2.46.0`.
- Confirmed `OPENAI_API_KEY` was available from the Windows user environment without printing its value.
- Obtained explicit approval to transmit the synthetic FORGE pipeline prompt and repository-derived AXIOM system
  prompt, schema, and example to the OpenAI API.
- Sent one in-process FastAPI `TestClient` request to `/api/v1/pipeline` with:
  - backend `openai`;
  - requested model `gpt-5.6`;
  - `supervised=false`;
  - `max_retries=1`;
  - the synthetic prompt `Design a 100 Ah LFP prismatic battery cell for stationary energy storage. Return a
    complete specification that follows the required schema.`
- Suppressed runtime logging during the call and emitted only a redacted status summary.

### Evidence

- HTTP status: `200`.
- Pipeline success envelope: returned.
- Deterministic final validity: `true`.
- Total generation attempts: `1`.
- Failed constraint identifiers: none.
- Redaction checks: passed for the secret value, authorization and bearer markers, raw SDK response fields, raw
  YAML fields, and YAML-content fields.
- Raw model output was not printed, written to disk, or retained as an artefact.
- Exactly one live OpenAI API request was made.
- A policy-approval rejection and a later PowerShell/Python quoting error both occurred before client execution and
  made no API request.
- The repository remained at HEAD `51717eaadc77911425c754f404642a56d5e8ff82` and was clean immediately after the
  smoke request, before this documentation entry was appended.

### Decisions

- The committed OpenAI backend and FastAPI pipeline are live-compatible for the bounded accepted case tested.
- An accepted smoke result is valid transport and integration evidence, but it is not the required authentic
  engineering-failure demonstration trace.
- This smoke result must not be represented as failure-discovery evidence or as verified replay because raw model
  output was intentionally not retained.
- Phase 2 remains gated on a separately reviewed discovery protocol and explicit authorization for each bounded set
  of live requests.

### Files changed

- `docs/BUILD_WEEK_LOG.md`: this append-only evidence entry.
- No source, configuration, dependency declaration, validator, supervisor, or engineering-equation file changed.
- The SDK installation changed only the local Windows user Python environment.

### Tests and checks

- OpenAI SDK import and version check: `2.46.0`.
- Live request path: in-process FastAPI `TestClient` to `/api/v1/pipeline`.
- Backend request timeout: `120` seconds.
- Backend output cap: `4096` tokens.
- Single-attempt assertion: passed.
- Response redaction checks: passed.
- Post-call `git status --short`: no output before this log entry was appended.
- No default non-live regression suite was rerun because no source code changed in this task.

### Risks or open questions

- The pipeline response does not expose the actual returned OpenAI model identifier or token usage, so this smoke
  evidence records the requested model `gpt-5.6` but does not independently prove the resolved model snapshot.
- No raw response was retained, so the accepted design cannot be independently replayed from this smoke run.
- The smoke check was an explicitly authorized ad hoc protocol, not a newly committed `live` pytest test.
- Authentic schema-valid engineering failure discovery has not started.
- The unresolved global Git ignore permission warning remains non-blocking.

### Next gate

- Review and commit this Phase 1 live-smoke evidence as one bounded documentation change.
- Then define the Phase 2 failure-discovery protocol, prompt candidates, retention policy, request budget, and
  approval boundary before making any further live API request.

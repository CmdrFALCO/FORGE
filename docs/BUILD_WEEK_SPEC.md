# FORGE OpenAI Build Week — Product and Implementation Specification

- **Status:** Draft
- **Date:** 2026-07-19
- **Baseline repository:** `CmdrFALCO/FORGE`
- **Baseline commit:** `25b738aa6b42b404723f7607954f4252fef5a1f3`
- **Baseline tag:** `build-week-baseline-2026-07-19`
- **Build Week branch:** `build-week/openai`
- **Primary model:** `GPT-5.6`
- **Working product name:** `FORGE — AXIOM Guard`
- **Target category:** Developer Tools

## 1. Executive Summary

> FORGE Build Week demonstrates how AXIOM supervises GPT-5.6-generated battery-cell specifications, detects a coupled engineering constraint violation, returns structured corrective feedback, and accepts the corrected design with a complete audit trace.

This work is a productisation and OpenAI integration layer built on the pre-existing FORGE and AXIOM research platform. It exposes an existing deterministic supervision loop through one focused, traceable demonstration. This specification describes intended work; it does not claim that Build Week implementation is complete.

## 2. Problem

- LLM-generated engineering outputs can be fluent and structurally plausible while violating coupled physical or mathematical constraints.
- The generating model must not be the final authority on validity.
- Requiring manual review of every generated field reduces the productivity advantage of generation.
- Engineering teams need declared deterministic checks, actionable corrective feedback, bounded termination rules, and an auditable decision trace.
- AXIOM evaluates only the schemas and constraints implemented in FORGE. Passing them is not proof of complete physical correctness, safety, manufacturability, or regulatory compliance.

## 3. Target User

The primary users are:

- an engineer or technical developer using an LLM to generate structured engineering artefacts;
- a developer integrating AI generation into an engineering workflow; and
- a reviewer who must understand why an artefact was accepted or rejected.

The immediate Build Week use case is generation and deterministic supervision of structured battery-cell specifications for the prismatic, pouch, or cylindrical domains already represented in FORGE.

## 4. Product Proposition

> Generate freely. Validate deterministically. Accept only after the declared constraints pass.

The product assigns explicit responsibilities:

- **GPT-5.6:** proposes a complete structured specification and acts as the correction agent after feedback.
- **FORGE validators:** perform deterministic structural and engineering checks over the proposal.
- **AXIOM supervisor:** orchestrates parsing, validation, retry logic, acceptance or rejection, and trace preservation.
- **User interface:** explains each attempt, failed constraint, feedback message, correction, and final decision.

The validator, not GPT-5.6, remains authoritative for the declared acceptance decision.

## 5. Pre-existing Baseline

The following capabilities existed at the tagged baseline and are not Build Week inventions:

- The deterministic battery-cell engine under `forge/engine/`, including calculations, calculators, conversion, geometry, CAD, cost, models, and validation.
- Battery-cell schemas and domain models for prismatic, pouch, and cylindrical cells.
- The AXIOM Generator-Validator-Supervisor architecture under `forge/axiom/`.
- The `LLMBackend` protocol, `LLMUsage`, `ClaudeBackend`, `OllamaBackend`, and `MockBackend` in `forge/axiom/backends/backends.py`.
- Generation, YAML parsing, validation feedback, retry, conversion, and calculation flow in `forge/axiom/supervisor/driver.py`.
- `GenerationResult`, retry reasons, and per-attempt constraint results in `forge/axiom/supervisor/result.py`.
- The constraint registry and deterministic checks in `forge/engine/validation/constraint_validator.py`.
- FastAPI backend construction in `forge/api/deps.py` and routes under `forge/api/routes/`.
- The `/api/v1/pipeline` flow, including supervised and single-attempt unsupervised modes.
- API `AttemptRecord`, `ConstraintResultSchema`, and pipeline request/response models in `forge/api/schemas/models.py`.
- The Streamlit GUI, the existing AXIOM Designer page at `forge/gui/pages/4_AXIOM_Designer.py`, and tracked `PipelineRun`/`PipelineStep` records in `forge/gui/axiom_pipeline.py`.
- Existing recorded demo loading from `data/demos/axiom/` and live Claude/Ollama GUI modes.
- Tests under `tests/`, experimental infrastructure under `experiments/`, and provenance material under `provenance_runs/`.
- Battery-cell domain knowledge, equations, schema rules, and physical constraints.

Build Week work must preserve and visibly credit this baseline.

## 6. New Build Week Contribution

The intended Build Week contribution is limited to:

1. An OpenAI GPT-5.6 backend using the existing `LLMBackend` abstraction.
2. OpenAI SDK dependency declaration and optional-dependency handling.
3. Registration of `openai` and justified, documented aliases in the backend factory.
4. Mapping OpenAI token usage and model metadata into the existing `LLMUsage` structure.
5. Mocked non-live tests for backend behavior and API routing.
6. A bounded failure-discovery utility for genuine first-attempt GPT-5.6 engineering failures.
7. Preservation of real prompts, outputs, validation results, feedback, retries, and final decisions.
8. One focused Build Week demonstration page.
9. A live execution mode.
10. A clearly labelled verified-replay mode based on a real captured GPT-5.6 trace.
11. Build Week documentation and Git provenance.

Only items that have been completed and verified may later be described as implemented.

## 7. Core User Flow

1. The user enters an engineering request.
2. GPT-5.6 generates a complete structured battery-cell specification.
3. FORGE extracts and parses the output.
4. Schema validation checks required structure and fields.
5. Deterministic engineering constraints run.
6. AXIOM decides to accept, retry with structured feedback, reject after the retry limit, or report an infrastructure failure separately.
7. On retry, GPT-5.6 receives the original request plus only the relevant corrective feedback and prior context required by the existing loop.
8. GPT-5.6 returns a corrected complete specification.
9. Parsing, schema validation, and engineering validation run again.
10. The interface shows the final accepted or rejected result and the complete available trace.

```text
Engineering request
        |
        v
 GPT-5.6 proposal
        |
        v
 Parse -> Schema checks -> Engineering constraints
        |                         |
        | pass                    | fail
        v                         v
     Accept             Structured AXIOM feedback
                                  |
                                  v
                            Retry GPT-5.6
                                  |
                         retry limit reached
                                  |
                                  v
                                Reject

Infrastructure error --------------------> Report separately
```

## 8. Demonstration Hypothesis

- Attempt 1 must be an authentic GPT-5.6 response.
- The preferred attempt parses and passes schema validation.
- It then fails at least one coupled physics, consistency, geometry, or calculated-value constraint.
- AXIOM returns specific feedback identifying the failed relationship and corrective direction.
- A later authentic attempt should pass the same unchanged validators.
- All attempts, feedback, validator outcomes, and the final decision must be retained.
- The failure must not be manufactured by weakening constraints or explicitly instructing GPT-5.6 to violate them.
- If no stable recovery case is found, that limitation must be reported rather than concealed.

## 9. Candidate Failure Scenarios

### Candidate A — Computed N/P Ratio
**Rank: 1. Preferred for audience clarity.**

- The existing `C1` `np_ratio` constraint computes N/P from anode and cathode loadings and specific capacities.
- The validator does not merely trust a declared scalar and also detects disagreement with a declared `np_ratio`.
- Each individual loading may appear plausible while the coupled computed ratio falls outside the accepted band.
- AXIOM can return actionable feedback directing correction of electrode loading or capacity relationships.
- This is the preferred primary case because the hidden coupling and deterministic recalculation are easy to explain.

### Candidate B — Cylindrical Jelly-roll Fit
**Rank: 2. Preferred for geometric coupling.**

- The existing `CY5` `jelly_roll_fits` constraint relates can diameter, wall thickness, mandrel diameter, and winding clearance.
- External can dimensions and individual winding values may look valid in isolation.
- The calculated usable winding space may nevertheless be insufficient.
- AXIOM can recommend increasing diameter or reducing mandrel or clearance values.

### Candidate C — Stack or Envelope Fit
**Rank: 3. Useful when the generated schema exposes a clear coupled fit error.**

- Individual sheet dimensions, wall values, stack counts, or layer counts may be valid independently.
- Their combined stack thickness or geometry may exceed the available internal envelope.
- Use this candidate only when the existing validator reports the coupled relationship deterministically.

### Candidate D — Material or Density Consistency
**Rank: 4. Conditional candidate.**

- Use only when an existing validator identifies a genuine multi-field engineering inconsistency.
- Do not present a spelling issue, unsupported label, simple lookup miss, or invented material rule as physics.

Malformed YAML, missing fields, and API errors remain useful robustness cases, but they are weaker primary
demonstrations because they do not show a non-obvious engineering constraint failure.

## 10. Failure-discovery Strategy

The discovery process is deliberately bounded:

1. Define a small, versioned set of candidate prompts.
2. Run GPT-5.6 in single-attempt mode with recorded generation settings.
3. Retain only responses that can be parsed.
4. Classify schema failures separately from engineering failures.
5. Retain schema-valid responses that fail deterministic engineering constraints.
6. Rerun retained prompts through AXIOM supervision without changing constraints.
7. Identify cases that recover within the configured retry count.
8. Save the complete authentic trace.
9. Repeat the selected case enough times to characterize stability.
10. Select the most understandable and defensible case for the demonstration.

The utility must report:

- prompt identifier and exact prompt;
- backend and model identifier;
- temperature and other relevant generation settings;
- attempt number and raw model output;
- parsed specification and parse result;
- schema result and deterministic constraint results;
- failed constraint IDs and exact corrective feedback;
- token usage and timing where available; and
- final decision and total attempt count.

The baseline has no root `scripts/` directory. The implementation task must inspect repository conventions and either choose an existing appropriate utility location or create one minimal, clearly named Build Week utility location.

## 11. Functional Requirements

- **FR-01:** The OpenAI backend implements the existing `LLMBackend` protocol.
- **FR-02:** The API key comes only from `OPENAI_API_KEY`.
- **FR-03:** The OpenAI model is runtime-configurable.
- **FR-04:** Generation returns response text in the format expected by the current AXIOM generator.
- **FR-05:** Token usage and model metadata populate the existing `LLMUsage` telemetry structure.
- **FR-06:** The OpenAI backend is selectable through the existing API backend factory.
- **FR-07:** Existing Claude, Ollama, and mock backends remain functional.
- **FR-08:** Existing supervised and unsupervised pipeline modes remain distinguishable.
- **FR-09:** Every retained attempt exposes its available parse, schema, and constraint validation results.
- **FR-10:** Infrastructure failures are not displayed as engineering rejections.
- **FR-11:** Live and verified-replay modes are visibly and consistently labelled.
- **FR-12:** Verified replay uses an authentic stored GPT-5.6 trace.
- **FR-13:** Trace export contains no secrets or private data.
- **FR-14:** The demonstration completes without CAD or ML optional dependencies.
- **FR-15:** The demo page tells the complete proposal-rejection-feedback-correction-acceptance story.
- **FR-16:** Retry limits remain bounded and visible in the trace.
- **FR-17:** Existing `/api/v1/pipeline` request behavior remains backward compatible.
- **FR-18:** The deterministic validator alone determines whether declared constraints pass.

## 12. Non-functional Requirements

- **NFR-01 — Backward compatibility:** Existing backend and API consumers continue to work.
- **NFR-02 — Determinism:** Given the same parsed specification, declared validators return deterministic decisions.
- **NFR-03 — Test isolation:** Default tests perform no live OpenAI calls.
- **NFR-04 — Diagnostics:** Missing key, missing SDK, malformed response, and service failures produce clear errors.
- **NFR-05 — Dependency restraint:** Add only the minimum OpenAI SDK dependency needed for the integration.
- **NFR-06 — Secret safety:** Keys, authorization headers, and private data never enter committed traces.
- **NFR-07 — Replayability:** A verified trace can reproduce the demonstrated decision sequence without network access.
- **NFR-08 — Locality:** Changes remain localized to existing extension points and the focused Build Week surface.
- **NFR-09 — Demo latency:** Live progress remains visible, bounded, and understandable during normal API latency.
- **NFR-10 — Traceability:** Attempts link prompts, outputs, validation evidence, feedback, usage, and final decisions.
- **NFR-11 — Honest labelling:** Recorded data is never represented as a live response.
- **NFR-12 — Compatibility:** New code remains compatible with Python 3.11 and project lint settings.

## 13. Architecture Impact

- **Backend implementation:** extend the backend layer while preserving `generate(messages) -> str` and `last_usage`.
- **Backend factory:** add OpenAI selection and dependency checks to the existing construction paths.
- **Optional dependencies:** expose the OpenAI SDK consistently with the repository's `llm` extras strategy.
- **API schemas:** change only if existing fields cannot represent required model, usage, attempt, or trace information; preserve current request defaults and response compatibility.
- **Failure discovery:** add a small utility around existing generation and validation entry points.
- **Trace storage:** reuse `PipelineRun`, `PipelineStep`, API schemas, or supervisor result structures where practical; extend rather than duplicate concepts.
- **Demo page:** add one focused Streamlit surface or a minimal extension aligned with existing GUI conventions.
- **Tests:** add mocked backend, factory, API, replay, and redaction coverage next to existing suites.
- **Documentation:** maintain this specification, a Build Week log, setup guidance, and provenance notes.

The AXIOM validator and supervisor should remain unchanged unless a verified compatibility defect requires a minimal, reviewed fix. Engineering equations and physical constraints are outside this integration task.

## 14. Data and Trace Format

A stored trace conceptually contains:

```yaml
trace_version:
trace_id:
created_at:
source: live_gpt56
prompt:
backend:
model:
generation_settings:
supervised:
max_attempts:
attempts:
  - attempt:
    raw_output:
    parsed_output:
    parse_result:
    schema_result:
    constraint_results:
    feedback:
    usage:
    duration_ms:
final_result:
final_valid:
total_attempts:
```

Implementation should reuse existing `LLMUsage`, `GenerationResult`, `AttemptRecord`, `ConstraintResultSchema`, `PipelineRun`, and `PipelineStep` concepts where practical. It must not create parallel structures without a concrete gap analysis.

A committed or exported trace must contain:

- no API key;
- no authorization header;
- no proprietary input;
- no hidden chain-of-thought; and
- no private user data.

The trace should retain model outputs and concise validator feedback, not internal model reasoning.

## 15. Build Week Demonstration Page

The Build Week interface is one focused page with:

- visible Build Week branding and a concise engineering problem statement;
- prompt input for live mode or selection of a verified case;
- backend and model labels;
- a persistent live or verified-replay indicator;
- an attempt timeline;
- raw or formatted specification content for each attempt;
- a per-attempt constraint report and failed-constraint explanation;
- the exact corrective feedback returned to GPT-5.6;
- final acceptance or rejection;
- a key calculated result when calculation succeeds;
- audit-trace export; and
- a disclaimer that passing declared constraints is not proof of total physical correctness.

The page must not add unrelated FORGE features or imply that the recorded mode is live.

## 16. Three-minute Demo Narrative

- **0:00-0:20 — Problem:** plausible generated specifications can hide coupled engineering violations.
- **0:20-0:45 — Request:** enter or select one battery-cell engineering request.
- **0:45-1:15 — Proposal:** show the authentic GPT-5.6 first attempt and its plausible fields.
- **1:15-1:45 — Detection:** reveal one deterministic hidden violation and the supporting values.
- **1:45-2:15 — Correction:** show AXIOM feedback and the complete corrected GPT-5.6 proposal.
- **2:15-2:35 — Acceptance:** show passing constraints, one key result, and the audit trace.
- **2:35-3:00 — Impact:** explain the generator-validator pattern without claiming complete correctness.

The narrative remains centered on one constraint failure.

## 17. Testing Strategy

Required coverage includes:

- mocked OpenAI SDK responses and successful text extraction;
- token usage and model metadata mapping;
- missing `OPENAI_API_KEY` handling;
- missing OpenAI SDK handling;
- backend factory routing and model override;
- compatibility with generation and `/api/v1/pipeline` routes;
- regressions for Claude, Ollama, and mock backends;
- verified-replay loading and authentic-source labelling; and
- trace redaction or safety checks.

Use the repository's configured commands:

```powershell
pytest tests/axiom tests/api
pytest
ruff check .
mypy forge/
```

The configured `pytest` addopts exclude the `live` marker. Run live tests only with explicit authorization:

```powershell
pytest -m live -v -s
```

Run targeted tests first and the broader non-live suite before final submission where practical.

## 18. Implementation Phases and Gates

### Phase 0 — Documentation and Provenance

Deliverables: `AGENTS.md`, `docs/BUILD_WEEK_SPEC.md`, `docs/BUILD_WEEK_LOG.md`, and baseline records.

**Gate:** documentation is reviewed and committed with baseline provenance intact.

### Phase 1 — OpenAI Backend

Deliverables include the backend, optional dependency handling, factory registration, and mocked tests.

**Gate:** GPT-5.6 completes one request through the existing AXIOM pipeline; mocked tests pass; and no existing backend regression is detected.

### Phase 2 — Failure Discovery

Deliverables include the bounded prompt set, discovery utility, and authentic trace.

**Gate:** at least one authentic schema-valid GPT-5.6 engineering failure is found; structured feedback is produced; a later attempt passes; and the full trace is saved and inspected.

### Phase 3 — Demonstration Interface

Deliverable: one focused demonstration page.

**Gate:** live mode works; verified replay works; and attempt progression is understandable without reading source code.

### Phase 4 — Packaging and Submission

**Gate:** README and setup instructions are complete; relevant tests pass; the demo video is recorded; provenance is clearly documented; and no secrets or proprietary data are committed.

No phase begins automatically; each gate requires review and explicit approval to continue.

## 19. Explicit Exclusions

- MBSE support.
- Generic rule authoring or a generic constraint editor.
- Multi-agent architecture.
- Model training or fine-tuning.
- New battery physics models or modified engineering equations.
- CAD redesign.
- PyBaMM research extension.
- ML surrogate work.
- Infrastructure redesign.
- Broad frontend redesign.
- Enterprise authentication.
- Regulatory certification claims.
- Complete formal proof of battery safety or physical correctness.
- Production deployment.

## 20. Risks and Mitigations

| Risk | Practical mitigation |
| --- | --- |
| GPT-5.6 passes every candidate on attempt 1 | Use a small set of legitimate edge-case and multi-constraint prompts; report the outcome honestly. |
| The selected GPT-5.6 failure is unstable | Repeat the case, record settings, measure recovery frequency, and keep a verified authentic replay. |
| Only schema failures are found | Classify them as robustness results and refine prompts toward existing coupled constraints without directing failure. |
| Correction fails repeatedly | Bound retries, inspect whether feedback is actionable, try another authentic candidate, and document non-recovery. |
| API latency or outage interrupts the demo | Show progress and timeouts; use verified replay for reliability after capturing a genuine live result. |
| Output format is incompatible | Preserve existing parser expectations, test response extraction, and classify format failure separately. |
| OpenAI SDK changes affect existing backends | Keep imports optional and localized; run Claude, Ollama, mock, AXIOM, and API regression tests. |
| A trace leaks sensitive information | Use synthetic prompts, allowlist stored fields, redact transport metadata, and inspect exports before commit. |
| Scope expands beyond the core story | Enforce phase gates, explicit exclusions, and one bounded objective per task. |
| UI work consumes too much time | Reuse existing Streamlit pipeline components and prioritize the attempt timeline and evidence over decoration. |

Verified replay mitigates API unreliability; it is not a substitute for capturing and preserving a genuine live GPT-5.6 result.

## 21. Acceptance Criteria

The Build Week product is acceptable only when:

1. GPT-5.6 is integrated through the existing backend abstraction.
2. Existing backends remain operational.
3. At least one real GPT-5.6 trace demonstrates a first-attempt engineering rejection.
4. The trace includes structured corrective feedback.
5. A later attempt is accepted, or the limitation is documented honestly if no recovery case can be found.
6. Live or recorded mode is always clearly identified.
7. The UI presents the retry loop clearly.
8. The final trace is exportable.
9. Relevant tests pass.
10. No secrets or proprietary information are present.
11. Baseline and Build Week contributions are clearly distinguishable.
12. Documentation avoids claiming complete engineering correctness.

## 22. Definition of Success

> The Build Week extension succeeds when a viewer can see GPT-5.6 produce a plausible engineering artefact, see AXIOM identify a non-obvious deterministic violation, see GPT-5.6 use the returned feedback to correct the artefact, and inspect the evidence for every decision.

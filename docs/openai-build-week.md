# OpenAI Build Week Demo and Provenance

## Product

**FORGE - AXIOM Guard** is a developer tool for supervising LLM-generated engineering specifications. The Build
Week demonstration uses GPT-5.6 to generate a cylindrical battery-cell definition while deterministic AXIOM checks
control whether that definition may enter the FORGE calculation engine.

The demonstration is intentionally narrow: it shows one authentic coupled-constraint failure, exact corrective
feedback, and a later accepted design. It does not claim complete physical correctness or production readiness.

## Judge Testing Path

The fastest test path is **Verified Replay**:

1. Install the project with `python -m pip install -e ".[gui,llm]"`.
2. Start it with `python -m streamlit run forge/gui/app.py`.
3. Open **OpenAI Build Week** from the sidebar.
4. Keep **Verified Replay** selected.
5. Inspect the two attempts, expand the YAML, and review the exact CY5 feedback.
6. Open **Colored Petri Net**, then use **Reset**, **Step by step**, or **Replay**.
7. Review **Trace provenance** and download the audit bundle.

This path is offline, uses bundled sample data, and requires no account, API key, or paid service.

Live OpenAI mode is optional. It requires `OPENAI_API_KEY`, makes at most two GPT-5.6 requests, may incur API
charges, and can produce a different valid or invalid design because generation is nondeterministic.

## Demonstrated Flow

```mermaid
sequenceDiagram
    participant User
    participant GPT as GPT-5.6
    participant AXIOM
    participant FORGE
    User->>GPT: P4 compact cylindrical-cell request
    GPT-->>AXIOM: Attempt 1 YAML
    AXIOM-->>AXIOM: Schema passes; CY5 fails
    AXIOM->>GPT: Exact deterministic corrective feedback
    GPT-->>AXIOM: Attempt 2 YAML
    AXIOM-->>AXIOM: All declared constraints pass
    AXIOM->>FORGE: Convert and calculate accepted design
```

## Canonical Evidence

The verified bundle is stored in `data/demos/axiom/openai_build_week_cy5/` and contains exactly:

- `trace.json`
- `manifest.json`
- `BUNDLE_SHA256.txt`

| Field | Value |
| --- | --- |
| Run ID | `20260719_174526Z_p4_gpt56` |
| Requested model | `gpt-5.6` |
| Returned model telemetry | `gpt-5.6-sol` |
| Attempts | `2` |
| Attempt 1 classification | Schema-valid engineering rejection |
| Isolated failed constraint | `CY5` |
| Attempt 2 classification | Accepted |
| Originating commit | `91f30ab88e0e10c733dceca805aa479de8bee3b8` |
| Promoted trace SHA-256 | `f12139e7566451df26ced03e659bd1fe7c08eb539d4a79480007043539c1fb59` |
| Bundle SHA-256 | `c1e3a0c7d09972de5b2f7ff836a30a2e20ada844a2197638d8ebac0157a5a6ca` |

Attempt 1 used a `10.0 mm` external diameter, `0.30 mm` wall, `7.5 mm` mandrel, and `0.10 mm` clearance. The
deterministic CY5 check calculated `1.70 mm` available winding space against a minimum of `2.0 mm`.

Attempt 2 changed only the external diameter to `10.5 mm`, producing `2.20 mm` available winding space. Every
declared constraint then passed. The accepted output was deterministically converted and recalculated by FORGE.

## Integrity and Redaction

Before Verified Replay is rendered or exported, the adapter checks:

- trace and manifest structure;
- trace and bundle hashes;
- per-attempt message and output hashes;
- model and token telemetry;
- ordered attempt history;
- the isolated attempt-1 CY5 rejection;
- exact feedback inclusion in the correction request;
- attempt-2 acceptance;
- absence of OpenAI response identifiers; and
- required deterministic result metrics.

The promoted trace contains the reviewed synthetic prompt and visible model outputs. It excludes credentials,
authorization headers, client state, transport details, personal paths, and OpenAI response identifiers.

## Pre-existing and Build Week Work

The baseline tag is `build-week-baseline-2026-07-19` at commit
`25b738aa6b42b404723f7607954f4252fef5a1f3`.

Pre-existing FORGE supplied the battery-cell domain models, calculators, engineering validators, AXIOM supervision
architecture, FastAPI service, Streamlit application, attempt tracking, and visualization components.

The Build Week extension added the OpenAI Responses API backend, API registration, mocked compatibility coverage,
bounded failure-discovery tooling, authentic GPT-5.6 evidence capture and promotion, verified-replay adapter,
focused demonstration page, audit export, live execution mode, and related tests and documentation.

The complete distinction is reviewable with:

```bash
git log --oneline build-week-baseline-2026-07-19..build-week/openai
git diff --stat build-week-baseline-2026-07-19..build-week/openai
```

## Codex Collaboration

Codex accelerated repository analysis, implementation, test construction, trace tooling, interface development,
debugging, and verification. Work was divided into bounded phases with explicit human review gates. The human
maintainer selected the product scope, preserved engineering constraints, authorized each live request, reviewed
candidate evidence, directed interface corrections, and approved each commit and push.

GPT-5.6 supplied engineering candidates. Codex helped build the integration and demonstration. Neither model is the
acceptance authority: deterministic AXIOM validation controls the result.

## Limitations

- Live generation is nondeterministic; Verified Replay is the reproducible evidence path.
- The captured scenario demonstrates one declared coupled constraint, not comprehensive battery qualification.
- Deterministic calculation metrics are FORGE outputs, not OpenAI telemetry.
- Live outputs are browser-session data and disappear when the Streamlit server stops.
- No API key is bundled, persisted, or required for Verified Replay.

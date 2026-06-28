"""Tests for the AXIOM Designer pipeline wrapper and renderers."""

from forge.axiom import MockBackend
from forge.gui.axiom_pipeline import (
    DEMO_DIR,
    FLOW_STEPS,
    PipelineRun,
    PipelineStep,
    StepStatus,
    load_pipeline_run,
    run_pipeline_with_tracking,
)
from forge.gui.components.axiom_cpn import compute_cpn_sequence, render_cpn_graph
from forge.gui.components.axiom_flow import render_pipeline_flow

VALID_POUCH_RESPONSE = """
```yaml
_meta:
  cell_type: pouch
  design_intent: "10Ah NMC811 pouch cell for EV application"

geometry:
  cathode_height_mm: 100.0
  cathode_width_mm: 80.0
  anode_offset_mm: 2.0
  separator_offset_mm: 2.5

stack_config:
  num_stacks: 1
  electrode_pairs_per_stack: 20
  end_electrode_config: "BothNegative"
  separator_overwraps: 1

electrochemistry:
  cathode:
    material_name: "NMC811"
    loading_mg_cm2: 20.0
    rev_spec_capacity_mahg: 195.0
    collector_thickness_um: 12.0
    coating_thickness_0pct_um: 55.0
    coating_thickness_100pct_um: 57.0
    porosity_pct: 25.0
  anode:
    material_name: "Graphite"
    loading_mg_cm2: 12.359
    rev_spec_capacity_mahg: 355.0
    collector_thickness_um: 6.0
    coating_thickness_0pct_um: 75.0
    coating_thickness_100pct_um: 80.0
    porosity_pct: 35.0
    np_ratio: 1.15
  separator:
    material_name: "Ceramic-coated PE"
    thickness_um: 14.0
    porosity_pct: 42.0
    areal_weight_mgcm2: 1.2
  electrolyte:
    material_name: "LiPF6 in EC:EMC"
    density_g_cm3: 1.22
    excess_factor: 1.1

tabs:
  cathode:
    material: "Aluminum"
    height_mm: 25.0
    width_mm: 30.0
    thickness_mm: 0.3
  anode:
    material: "Nickel-plated Copper"
    height_mm: 25.0
    width_mm: 25.0
    thickness_mm: 0.2

packaging:
  pouch_thickness_mm: 0.113
  offset_top_mm: 8.0
  offset_bottom_mm: 4.0
  offset_sides_mm: 5.0
```
"""

INVALID_POUCH_RESPONSE = """
```yaml
_meta:
  cell_type: pouch
  design_intent: "Invalid pouch"

geometry:
  cathode_height_mm: 100.0
  cathode_width_mm: 80.0
  anode_offset_mm: 2.0
  separator_offset_mm: 2.5

stack_config:
  num_stacks: 1
  electrode_pairs_per_stack: 20
  end_electrode_config: "BothNegative"

electrochemistry:
  cathode:
    material_name: "NMC811"
    loading_mg_cm2: 20.0
    rev_spec_capacity_mahg: 195.0
    collector_thickness_um: 12.0
    coating_thickness_0pct_um: 55.0
    coating_thickness_100pct_um: 57.0
    porosity_pct: 25.0
  anode:
    material_name: "Graphite"
    loading_mg_cm2: 11.0
    rev_spec_capacity_mahg: 355.0
    collector_thickness_um: 6.0
    coating_thickness_0pct_um: 75.0
    coating_thickness_100pct_um: 80.0
    porosity_pct: 35.0
    np_ratio: 1.35
  separator:
    material_name: "Ceramic-coated PE"
    thickness_um: 14.0
    porosity_pct: 42.0
    areal_weight_mgcm2: 1.2
  electrolyte:
    material_name: "LiPF6 in EC:EMC"
    density_g_cm3: 1.22
    excess_factor: 1.1

tabs:
  cathode:
    material: "Aluminum"
    height_mm: 25.0
    width_mm: 30.0
    thickness_mm: 0.3
  anode:
    material: "Nickel-plated Copper"
    height_mm: 25.0
    width_mm: 25.0
    thickness_mm: 0.2

packaging:
  pouch_thickness_mm: 0.113
  offset_top_mm: 8.0
  offset_bottom_mm: 4.0
  offset_sides_mm: 5.0
```
"""


class FailingBackend:
    """Backend that always fails."""

    def generate(self, messages):
        raise RuntimeError("Backend unavailable")


def test_pipeline_step_and_run_dataclasses() -> None:
    step = PipelineStep(name="LLM Generate", status=StepStatus.ACTIVE, attempt=2)
    run = PipelineRun(prompt="Design a cell", backend_name="Mock", steps=[step], attempt=2)

    assert step.name == "LLM Generate"
    assert step.status == StepStatus.ACTIVE
    assert run.steps[0].attempt == 2
    assert run.max_attempts == 3


def test_render_pipeline_flow_pending_html() -> None:
    run = PipelineRun(
        prompt="",
        backend_name="Recorded Demo",
        steps=[PipelineStep(name=name) for name in FLOW_STEPS],
    )

    html = render_pipeline_flow(run)

    assert "<style>" in html
    assert "Attempt 1 of 3" in html
    assert "Build Prompt" in html
    assert "pending" in html


def test_render_pipeline_flow_completed_with_retry() -> None:
    run = PipelineRun(
        prompt="Design a cell",
        backend_name="Recorded Demo",
        attempt=2,
        success=True,
        steps=[
            PipelineStep(name="Build Prompt", status=StepStatus.PASSED, attempt=1),
            PipelineStep(name="LLM Generate", status=StepStatus.PASSED, attempt=1),
            PipelineStep(name="Parse YAML", status=StepStatus.PASSED, attempt=1),
            PipelineStep(name="Schema Validate", status=StepStatus.PASSED, attempt=1),
            PipelineStep(
                name="Physics Validate",
                status=StepStatus.FAILED,
                detail="N/P ratio out of range",
                attempt=1,
            ),
            PipelineStep(
                name="Retry Feedback",
                status=StepStatus.PASSED,
                detail="Retry with corrected N/P ratio",
                raw_data={"feedback": "N/P ratio out of range"},
                attempt=1,
            ),
            PipelineStep(name="LLM Generate", status=StepStatus.PASSED, attempt=2),
            PipelineStep(name="Parse YAML", status=StepStatus.PASSED, attempt=2),
            PipelineStep(name="Schema Validate", status=StepStatus.PASSED, attempt=2),
            PipelineStep(name="Physics Validate", status=StepStatus.PASSED, attempt=2),
            PipelineStep(name="Convert", status=StepStatus.PASSED, attempt=2),
            PipelineStep(name="Calculate", status=StepStatus.PASSED, attempt=2),
        ],
    )

    html = render_pipeline_flow(run)

    assert "Attempt 2 of 3" in html
    assert "Retry Loop" in html
    assert "N/P ratio out of range" in html


def test_recorded_demo_files_load() -> None:
    success_demo = load_pipeline_run(DEMO_DIR / "successful_first_try.json")
    retry_demo = load_pipeline_run(DEMO_DIR / "retry_success.json")

    assert success_demo.success is True
    assert retry_demo.success is True
    assert retry_demo.attempt == 2
    assert len(success_demo.steps) >= 7
    assert any(step.name == "Retry Feedback" for step in retry_demo.steps)


def test_run_pipeline_with_tracking_mock_backend_success() -> None:
    run = run_pipeline_with_tracking(
        prompt="Design a 10Ah pouch cell",
        backend=MockBackend([VALID_POUCH_RESPONSE]),
        cell_type="pouch",
        max_attempts=1,
    )

    assert run.success is True
    assert run.calculation_summary is not None
    assert run.calculation_summary["capacity_ah"] > 0
    assert any(step.name == "Calculate" and step.status == StepStatus.PASSED for step in run.steps)


def test_run_pipeline_with_tracking_missing_backend_graceful() -> None:
    run = run_pipeline_with_tracking(
        prompt="Design a cell",
        backend=FailingBackend(),
        cell_type="pouch",
        max_attempts=1,
    )

    llm_step = next(step for step in run.steps if step.name == "LLM Generate")

    assert run.success is False
    assert llm_step.status == StepStatus.FAILED
    assert "Backend unavailable" in llm_step.detail


def test_run_pipeline_with_tracking_retry_success() -> None:
    run = run_pipeline_with_tracking(
        prompt="Design a 10Ah pouch cell",
        backend=MockBackend([INVALID_POUCH_RESPONSE, VALID_POUCH_RESPONSE]),
        cell_type="pouch",
        max_attempts=2,
    )

    assert run.success is True
    assert run.attempt == 2
    assert any(step.name == "Retry Feedback" for step in run.steps)
    assert any(
        step.name == "Physics Validate" and step.status == StepStatus.FAILED for step in run.steps
    )


def test_render_cpn_graph_returns_svg() -> None:
    run = load_pipeline_run(DEMO_DIR / "successful_first_try.json")

    svg = render_cpn_graph(run)

    assert svg.lstrip().startswith("<svg")
    assert 'id="P_prompt"' in svg
    assert 'id="T_calculate"' in svg
    assert "AXIOM Colored Petri Net" in svg


def test_compute_cpn_sequence_success_run_ends_at_result() -> None:
    run = load_pipeline_run(DEMO_DIR / "successful_first_try.json")

    sequence = compute_cpn_sequence(run)

    assert sequence[0]["token_place"] == "P_prompt"
    assert sequence[-1]["token_place"] == "P_result"
    assert sequence[-1]["transition_id"] == "T_calculate"
    assert "T_accept" in sequence[-1]["fired_transitions"]


def test_compute_cpn_sequence_retry_run_includes_loop() -> None:
    run = load_pipeline_run(DEMO_DIR / "retry_success.json")

    sequence = compute_cpn_sequence(run)
    transition_ids = [snapshot["transition_id"] for snapshot in sequence]

    assert "T_retry" in transition_ids
    assert "T_regenerate" in transition_ids
    assert sequence[-1]["token_place"] == "P_result"
    assert sequence[-1]["attempt"] == 2


def test_compute_cpn_sequence_handles_empty_run() -> None:
    run = PipelineRun(prompt="", backend_name="AXIOM")

    sequence = compute_cpn_sequence(run)

    assert len(sequence) == 1
    assert sequence[0]["token_place"] == "P_prompt"
    assert sequence[0]["transition_id"] is None

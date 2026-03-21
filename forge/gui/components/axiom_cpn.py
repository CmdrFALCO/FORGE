"""SVG CPN renderer for the AXIOM Designer page."""

from __future__ import annotations

from collections.abc import Iterable
from math import hypot

from forge.gui.axiom_pipeline import RETRY_STEP, PipelineRun, PipelineStep, StepStatus

SVG_VIEWBOX = "0 0 1180 520"

PLACE_LAYOUT: dict[str, dict[str, object]] = {
    "P_prompt": {"label": "Prompt", "x": 70.0, "y": 130.0, "radius": 22.0, "kind": "source"},
    "P_raw_output": {
        "label": "Raw Output",
        "x": 250.0,
        "y": 130.0,
        "radius": 20.0,
        "kind": "normal",
    },
    "P_parsed": {"label": "Parsed", "x": 430.0, "y": 130.0, "radius": 20.0, "kind": "normal"},
    "P_schema_ok": {
        "label": "Schema OK",
        "x": 610.0,
        "y": 130.0,
        "radius": 20.0,
        "kind": "normal",
    },
    "P_deciding": {
        "label": "Deciding",
        "x": 790.0,
        "y": 130.0,
        "radius": 24.0,
        "kind": "hub",
    },
    "P_feedback": {
        "label": "Feedback",
        "x": 800.0,
        "y": 320.0,
        "radius": 20.0,
        "kind": "normal",
    },
    "P_valid": {"label": "Valid", "x": 1020.0, "y": 75.0, "radius": 20.0, "kind": "normal"},
    "P_input": {
        "label": "Cell Input",
        "x": 1020.0,
        "y": 235.0,
        "radius": 20.0,
        "kind": "normal",
    },
    "P_result": {
        "label": "Result",
        "x": 1020.0,
        "y": 395.0,
        "radius": 22.0,
        "kind": "success",
    },
    "P_rejected": {
        "label": "Rejected",
        "x": 1090.0,
        "y": 305.0,
        "radius": 22.0,
        "kind": "failure",
    },
}

TRANSITION_LAYOUT: dict[str, dict[str, object]] = {
    "T_generate": {
        "label": "Generate",
        "x": 160.0,
        "y": 130.0,
        "width": 64.0,
        "height": 28.0,
        "from": "P_prompt",
        "to": "P_raw_output",
    },
    "T_parse": {
        "label": "Parse",
        "x": 340.0,
        "y": 130.0,
        "width": 60.0,
        "height": 28.0,
        "from": "P_raw_output",
        "to": "P_parsed",
    },
    "T_schema": {
        "label": "Schema Check",
        "x": 520.0,
        "y": 130.0,
        "width": 82.0,
        "height": 28.0,
        "from": "P_parsed",
        "to": "P_schema_ok",
    },
    "T_physics": {
        "label": "Physics Check",
        "x": 700.0,
        "y": 130.0,
        "width": 86.0,
        "height": 28.0,
        "from": "P_schema_ok",
        "to": "P_deciding",
    },
    "T_accept": {
        "label": "Accept",
        "x": 900.0,
        "y": 75.0,
        "width": 58.0,
        "height": 28.0,
        "from": "P_deciding",
        "to": "P_valid",
    },
    "T_retry": {
        "label": "Retry",
        "x": 905.0,
        "y": 210.0,
        "width": 54.0,
        "height": 28.0,
        "from": "P_deciding",
        "to": "P_feedback",
    },
    "T_reject": {
        "label": "Reject",
        "x": 1000.0,
        "y": 210.0,
        "width": 58.0,
        "height": 28.0,
        "from": "P_deciding",
        "to": "P_rejected",
    },
    "T_regenerate": {
        "label": "Regenerate",
        "x": 610.0,
        "y": 320.0,
        "width": 88.0,
        "height": 28.0,
        "from": "P_feedback",
        "to": "P_prompt",
    },
    "T_convert": {
        "label": "Convert",
        "x": 1020.0,
        "y": 155.0,
        "width": 64.0,
        "height": 28.0,
        "from": "P_valid",
        "to": "P_input",
    },
    "T_calculate": {
        "label": "Calculate",
        "x": 1020.0,
        "y": 315.0,
        "width": 72.0,
        "height": 28.0,
        "from": "P_input",
        "to": "P_result",
    },
}


def compute_cpn_sequence(run: PipelineRun) -> list[dict[str, object]]:
    """Convert a PipelineRun into cumulative CPN state snapshots."""
    fired: set[str] = set()
    visited: set[str] = {"P_prompt"}
    snapshots = [
        _snapshot(
            transition_id=None,
            token_place="P_prompt",
            fired_transitions=fired,
            visited_places=visited,
            step_label="Prompt ready",
            attempt=1,
        )
    ]

    steps_by_attempt: dict[int, list[PipelineStep]] = {}
    for step in run.steps:
        if step.name == "Build Prompt":
            continue
        steps_by_attempt.setdefault(step.attempt, []).append(step)

    if not steps_by_attempt:
        return snapshots

    sorted_attempts = sorted(steps_by_attempt)
    for attempt in sorted_attempts:
        attempt_steps = steps_by_attempt[attempt]
        retry_step = _find_step(attempt_steps, RETRY_STEP)
        for step in attempt_steps:
            if step.name == RETRY_STEP:
                continue

            if step.name == "LLM Generate":
                _append_transition(
                    snapshots,
                    fired,
                    visited,
                    "T_generate",
                    "P_raw_output" if step.status != StepStatus.FAILED else "P_prompt",
                    attempt,
                    step.detail or "LLM backend call",
                )
                if step.status == StepStatus.FAILED:
                    _append_failure_exit(snapshots, fired, visited, retry_step, attempt, run)
                    break
                continue

            if step.name == "Parse YAML":
                _append_transition(
                    snapshots,
                    fired,
                    visited,
                    "T_parse",
                    "P_parsed" if step.status != StepStatus.FAILED else "P_raw_output",
                    attempt,
                    step.detail or "YAML extraction",
                )
                if step.status == StepStatus.FAILED:
                    _append_failure_exit(snapshots, fired, visited, retry_step, attempt, run)
                    break
                continue

            if step.name == "Schema Validate":
                _append_transition(
                    snapshots,
                    fired,
                    visited,
                    "T_schema",
                    "P_schema_ok" if step.status != StepStatus.FAILED else "P_parsed",
                    attempt,
                    step.detail or "Schema validation",
                )
                if step.status == StepStatus.FAILED:
                    _append_failure_exit(snapshots, fired, visited, retry_step, attempt, run)
                    break
                continue

            if step.name == "Physics Validate":
                _append_transition(
                    snapshots,
                    fired,
                    visited,
                    "T_physics",
                    "P_deciding",
                    attempt,
                    step.detail or "Physics validation",
                )
                if step.status in {StepStatus.PASSED, StepStatus.SKIPPED}:
                    _append_transition(
                        snapshots,
                        fired,
                        visited,
                        "T_accept",
                        "P_valid",
                        attempt,
                        "No blocking constraint errors",
                    )
                else:
                    _append_failure_exit(snapshots, fired, visited, retry_step, attempt, run)
                    break
                continue

            if step.name == "Convert":
                _append_transition(
                    snapshots,
                    fired,
                    visited,
                    "T_convert",
                    "P_input",
                    attempt,
                    step.detail or "Template converted to engine input",
                )
                if step.status == StepStatus.FAILED:
                    _append_transition(
                        snapshots,
                        fired,
                        visited,
                        "T_reject",
                        "P_rejected",
                        attempt,
                        step.detail or "Conversion failed",
                    )
                    break
                continue

            if step.name == "Calculate":
                destination = "P_result" if step.status != StepStatus.FAILED else "P_input"
                _append_transition(
                    snapshots,
                    fired,
                    visited,
                    "T_calculate",
                    destination,
                    attempt,
                    step.detail or "Engine calculation",
                )
                if step.status == StepStatus.FAILED:
                    _append_transition(
                        snapshots,
                        fired,
                        visited,
                        "T_reject",
                        "P_rejected",
                        attempt,
                        step.detail or "Calculation failed",
                    )
                break

    return snapshots


def render_cpn_graph(run: PipelineRun, current_step_index: int = -1) -> str:
    """Render the AXIOM CPN graph as an inline SVG string."""
    sequence = compute_cpn_sequence(run)
    if not sequence:
        sequence = compute_cpn_sequence(PipelineRun(prompt="", backend_name="AXIOM"))

    final_view = current_step_index < 0
    index = len(sequence) - 1 if final_view else max(0, min(current_step_index, len(sequence) - 1))
    snapshot = sequence[index]
    active_transition = None if final_view else snapshot["transition_id"]
    fired_transitions = set(snapshot["fired_transitions"])
    traversed_transitions = fired_transitions - ({active_transition} if active_transition else set())
    visited_places = set(snapshot["visited_places"])
    token_place = str(snapshot["token_place"])
    step_label = str(snapshot["step_label"])
    attempt = int(snapshot["attempt"])

    edges_svg = "\n".join(
        _render_transition_edges(transition_id, active_transition, traversed_transitions)
        for transition_id in TRANSITION_LAYOUT
    )
    places_svg = "\n".join(
        _render_place(place_id, token_place, visited_places, final_view)
        for place_id in PLACE_LAYOUT
    )
    transitions_svg = "\n".join(
        _render_transition(transition_id, active_transition, traversed_transitions)
        for transition_id in TRANSITION_LAYOUT
    )
    token_svg = _render_token(token_place, final_view)

    total_steps = len(sequence)
    step_text = f"Steps: {total_steps}/{total_steps}" if final_view else f"Steps: {index + 1}/{total_steps}"
    subtitle = f"Attempt {attempt} - {step_label}"

    return f"""
<svg
  viewBox="{SVG_VIEWBOX}"
  width="100%"
  height="520"
  preserveAspectRatio="xMidYMid meet"
  xmlns="http://www.w3.org/2000/svg"
  role="img"
  aria-label="AXIOM Colored Petri Net"
>
  <defs>
    <marker id="axiom-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
      <path d="M 0 0 L 8 4 L 0 8 z" fill="context-stroke" />
    </marker>
  </defs>
  <style>
    .axiom-cpn {{
      font-family: "Segoe UI", sans-serif;
      color: #ccc;
    }}
    .axiom-edge {{
      fill: none;
      stroke: #555;
      stroke-width: 2;
      marker-end: url(#axiom-arrow);
    }}
    .axiom-edge.traversed {{ stroke: #4CAF50; }}
    .axiom-edge.active {{ stroke: #4A9EFF; stroke-width: 3; }}
    .axiom-edge.active.retry {{ stroke: #FFA726; }}
    .axiom-edge.active.reject {{ stroke: #FF5252; }}
    .axiom-place {{
      fill: transparent;
      stroke: #888;
      stroke-width: 2;
    }}
    .axiom-place.visited {{ stroke: #4CAF50; }}
    .axiom-place.active {{
      stroke: #4A9EFF;
      fill: rgba(74, 158, 255, 0.15);
    }}
    .axiom-place.active.success,
    .axiom-place.success {{
      stroke: #4CAF50;
      fill: rgba(76, 175, 80, 0.14);
    }}
    .axiom-place.active.failure,
    .axiom-place.failure {{
      stroke: #FF5252;
      fill: rgba(255, 82, 82, 0.14);
    }}
    .axiom-transition {{
      fill: #333;
      stroke: #666;
      stroke-width: 1.5;
      rx: 6;
      ry: 6;
    }}
    .axiom-transition.fired {{ stroke: #4CAF50; fill: #3a3a3a; }}
    .axiom-transition.active {{ stroke: #4A9EFF; fill: #4A9EFF; }}
    .axiom-transition.active.retry {{ stroke: #FFA726; fill: #FFA726; }}
    .axiom-transition.active.reject {{ stroke: #FF5252; fill: #FF5252; }}
    .axiom-label {{
      fill: #ccc;
      font-size: 11px;
      text-anchor: middle;
    }}
    .axiom-transition-label {{
      fill: #ddd;
      font-size: 9px;
      text-anchor: middle;
      dominant-baseline: middle;
    }}
    .axiom-meta {{
      fill: #b7bdc3;
      font-size: 13px;
      text-anchor: start;
    }}
    .axiom-token {{
      fill: #4A9EFF;
      stroke: rgba(255, 255, 255, 0.2);
      stroke-width: 1.5;
    }}
    .axiom-token.success {{ fill: #4CAF50; }}
    .axiom-token.failure {{ fill: #FF5252; }}
    .pulse {{
      animation: axiomTokenPulse 1.1s ease-in-out infinite;
      transform-origin: center;
      transform-box: fill-box;
    }}
    @keyframes axiomTokenPulse {{
      0% {{ opacity: 0.85; transform: scale(1.0); }}
      50% {{ opacity: 1.0; transform: scale(1.1); }}
      100% {{ opacity: 0.85; transform: scale(1.0); }}
    }}
  </style>
  <g class="axiom-cpn">
    <text x="24" y="26" class="axiom-meta">{step_text}</text>
    <text x="24" y="48" class="axiom-meta">{_escape_xml(subtitle)}</text>
    {edges_svg}
    {places_svg}
    {transitions_svg}
    {token_svg}
  </g>
</svg>
"""


def _append_failure_exit(
    snapshots: list[dict[str, object]],
    fired: set[str],
    visited: set[str],
    retry_step: PipelineStep | None,
    attempt: int,
    run: PipelineRun,
) -> None:
    if retry_step is not None:
        _append_transition(
            snapshots,
            fired,
            visited,
            "T_retry",
            "P_feedback",
            attempt,
            retry_step.detail or "Retry requested",
        )
        _append_transition(
            snapshots,
            fired,
            visited,
            "T_regenerate",
            "P_prompt",
            attempt,
            "Feedback loop to next attempt",
        )
        return

    label = run.last_error or "Retries exhausted"
    _append_transition(
        snapshots,
        fired,
        visited,
        "T_reject",
        "P_rejected",
        attempt,
        label,
    )


def _append_transition(
    snapshots: list[dict[str, object]],
    fired: set[str],
    visited: set[str],
    transition_id: str,
    token_place: str,
    attempt: int,
    label: str,
) -> None:
    fired.add(transition_id)
    visited.add(token_place)
    snapshots.append(
        _snapshot(
            transition_id=transition_id,
            token_place=token_place,
            fired_transitions=fired,
            visited_places=visited,
            step_label=label,
            attempt=attempt,
        )
    )


def _snapshot(
    *,
    transition_id: str | None,
    token_place: str,
    fired_transitions: Iterable[str],
    visited_places: Iterable[str],
    step_label: str,
    attempt: int,
) -> dict[str, object]:
    return {
        "transition_id": transition_id,
        "token_place": token_place,
        "fired_transitions": set(fired_transitions),
        "visited_places": set(visited_places),
        "step_label": step_label,
        "attempt": attempt,
    }


def _find_step(steps: list[PipelineStep], name: str) -> PipelineStep | None:
    matches = [step for step in steps if step.name == name]
    return matches[-1] if matches else None


def _render_transition_edges(
    transition_id: str,
    active_transition: object,
    traversed_transitions: set[str],
) -> str:
    transition = TRANSITION_LAYOUT[transition_id]
    source = str(transition["from"])
    target = str(transition["to"])
    classes = ["axiom-edge"]
    if transition_id == active_transition:
        classes.append("active")
        if transition_id in {"T_retry", "T_regenerate"}:
            classes.append("retry")
        if transition_id == "T_reject":
            classes.append("reject")
    elif transition_id in traversed_transitions:
        classes.append("traversed")

    edge_class = " ".join(classes)
    source_path = _edge_path(source, transition_id, forward=True)
    target_path = _edge_path(transition_id, target, forward=True)
    return f'<path class="{edge_class}" d="{source_path}" />\n<path class="{edge_class}" d="{target_path}" />'


def _render_place(
    place_id: str,
    token_place: str,
    visited_places: set[str],
    final_view: bool,
) -> str:
    place = PLACE_LAYOUT[place_id]
    x = float(place["x"])
    y = float(place["y"])
    radius = float(place["radius"])
    kind = str(place["kind"])

    classes = ["axiom-place"]
    if place_id in visited_places:
        classes.append("visited")
    if place_id == token_place:
        classes.append("active")
        if final_view and place_id == "P_result":
            classes.append("success")
        if final_view and place_id == "P_rejected":
            classes.append("failure")
    elif kind == "success":
        classes.append("success")
    elif kind == "failure":
        classes.append("failure")

    label_y = y + radius + 22
    outer_circle = ""
    if kind in {"source", "success", "failure"}:
        outer_circle = (
            f'<circle class="{" ".join(classes)}" cx="{x:.1f}" cy="{y:.1f}" r="{radius + 6:.1f}" />'
        )

    return (
        f'{outer_circle}'
        f'<circle id="{place_id}" class="{" ".join(classes)}" cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" />'
        f'<text x="{x:.1f}" y="{label_y:.1f}" class="axiom-label">{_escape_xml(str(place["label"]))}</text>'
    )


def _render_transition(
    transition_id: str,
    active_transition: object,
    traversed_transitions: set[str],
) -> str:
    transition = TRANSITION_LAYOUT[transition_id]
    x = float(transition["x"])
    y = float(transition["y"])
    width = float(transition["width"])
    height = float(transition["height"])

    classes = ["axiom-transition"]
    if transition_id in traversed_transitions:
        classes.append("fired")
    if transition_id == active_transition:
        classes.append("active")
        if transition_id in {"T_retry", "T_regenerate"}:
            classes.append("retry")
        if transition_id == "T_reject":
            classes.append("reject")

    return (
        f'<rect id="{transition_id}" class="{" ".join(classes)}" '
        f'x="{x - width / 2:.1f}" y="{y - height / 2:.1f}" width="{width:.1f}" height="{height:.1f}" />'
        f'<text x="{x:.1f}" y="{y:.1f}" class="axiom-transition-label">{_escape_xml(str(transition["label"]))}</text>'
    )


def _render_token(token_place: str, final_view: bool) -> str:
    place = PLACE_LAYOUT[token_place]
    x = float(place["x"])
    y = float(place["y"])
    classes = ["axiom-token"]
    if final_view and token_place == "P_result":
        classes.append("success")
    elif final_view and token_place == "P_rejected":
        classes.append("failure")
    else:
        classes.append("pulse")
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" class="{" ".join(classes)}" />'


def _edge_path(source_id: str, target_id: str, *, forward: bool) -> str:
    if source_id == "T_regenerate" and target_id == "P_prompt":
        start_x, start_y = _node_boundary_point("T_regenerate", "P_prompt")
        end_x, end_y = _node_boundary_point("P_prompt", "T_regenerate")
        return (
            f"M {start_x:.1f},{start_y:.1f} "
            f"C {start_x - 150:.1f},{start_y + 120:.1f} {end_x + 120:.1f},{end_y + 160:.1f} {end_x:.1f},{end_y:.1f}"
        )

    if not forward:
        source_id, target_id = target_id, source_id
    start_x, start_y = _node_boundary_point(source_id, target_id)
    end_x, end_y = _node_boundary_point(target_id, source_id)
    return f"M {start_x:.1f},{start_y:.1f} L {end_x:.1f},{end_y:.1f}"


def _node_boundary_point(node_id: str, toward_id: str) -> tuple[float, float]:
    node = _node_layout(node_id)
    toward = _node_layout(toward_id)
    x = float(node["x"])
    y = float(node["y"])
    tx = float(toward["x"])
    ty = float(toward["y"])
    dx = tx - x
    dy = ty - y

    if node["type"] == "place":
        distance = max(hypot(dx, dy), 1.0)
        radius = float(node["radius"])
        return x + dx / distance * radius, y + dy / distance * radius

    width = float(node["width"]) / 2
    height = float(node["height"]) / 2
    scale_x = width / abs(dx) if dx else float("inf")
    scale_y = height / abs(dy) if dy else float("inf")
    scale = min(scale_x, scale_y)
    if scale == float("inf"):
        return x, y
    return x + dx * scale, y + dy * scale


def _node_layout(node_id: str) -> dict[str, object]:
    if node_id in PLACE_LAYOUT:
        place = PLACE_LAYOUT[node_id]
        return {
            "type": "place",
            "x": place["x"],
            "y": place["y"],
            "radius": place["radius"],
        }
    transition = TRANSITION_LAYOUT[node_id]
    return {
        "type": "transition",
        "x": transition["x"],
        "y": transition["y"],
        "width": transition["width"],
        "height": transition["height"],
    }


def _escape_xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

"""ML Autoresearch dashboard — visualizes autonomous surrogate optimization results."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

from forge.ml.autoresearch.constants import (
    MAX_ERROR_RATE,
    MAX_ERROR_TEMP,
    NUM_EPOCHS,
    NUM_PARAMS,
    PRIMARY_SCORE,
    RMSE_RATE,
    RMSE_RATE_NORM,
    RMSE_TEMP,
    RMSE_TEMP_NORM,
    TOTAL_SECONDS,
    TRAINING_SECONDS,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


RESULTS_PATH = _repo_root() / "experiments" / "ml" / "autoresearch" / "results.tsv"

ACCENT_GREEN = "#4ade80"
ACCENT_RED = "#f87171"


def load_results(path: Path) -> pd.DataFrame | None:
    """Load autoresearch results TSV into a DataFrame.

    Returns None if the file doesn't exist or contains no data rows.
    """
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, sep="\t")
    except Exception:
        return None
    if df.empty:
        return None
    return df


# =============================================================================
# Page
# =============================================================================

st.title("ML Autoresearch")

df = load_results(RESULTS_PATH)

if df is None:
    st.info(
        "No autoresearch results found.\n\n"
        "Run the autoresearch loop to generate results:\n"
        "```\n"
        "cd experiments/ml/autoresearch\n"
        "python prepare.py          # generate dataset\n"
        "python run.py --budget 300 # run optimization loop\n"
        "```"
    )
    st.stop()

if go is None:
    st.error("Plotly is required for the ML Autoresearch dashboard but could not be imported.")
    st.stop()

# Parse accepted column
df["accepted"] = df["accepted"].astype(str).str.strip().str.lower().isin({"true", "1", "yes"})

tab_journey, tab_best, tab_playground = st.tabs(
    ["Optimization Journey", "Best Model", "Surrogate Playground"]
)

# =============================================================================
# Tab 1 — Optimization Journey
# =============================================================================
with tab_journey:
    # --- Trend Plot ---
    accepted_df = df[df["accepted"]]
    rejected_df = df[~df["accepted"]]

    fig = go.Figure()

    # Accepted markers + trajectory line
    if not accepted_df.empty:
        fig.add_trace(
            go.Scatter(
                x=accepted_df["experiment_id"],
                y=accepted_df[PRIMARY_SCORE],
                mode="lines+markers",
                name="Accepted",
                marker=dict(color=ACCENT_GREEN, size=8),
                line=dict(color=ACCENT_GREEN, width=1),
                hovertemplate=(
                    "Experiment %{x}<br>"
                    "Score: %{y:.4f}<br>"
                    "<extra>Accepted</extra>"
                ),
            )
        )

    # Rejected markers (no line)
    if not rejected_df.empty:
        fig.add_trace(
            go.Scatter(
                x=rejected_df["experiment_id"],
                y=rejected_df[PRIMARY_SCORE],
                mode="markers",
                name="Rejected",
                marker=dict(color=ACCENT_RED, size=6, symbol="x"),
                hovertemplate=(
                    "Experiment %{x}<br>"
                    "Score: %{y:.4f}<br>"
                    "<extra>Rejected</extra>"
                ),
            )
        )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Experiment",
        yaxis_title="Primary Score (lower is better)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=40, b=40),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True, key="journey_chart")

    # --- Summary Stats ---
    st.markdown("#### Summary")
    total = len(df)
    n_accepted = int(df["accepted"].sum())
    n_rejected = total - n_accepted
    acceptance_rate = n_accepted / total if total > 0 else 0

    best_score = accepted_df[PRIMARY_SCORE].min() if not accepted_df.empty else None
    baseline_score = df.loc[df["experiment_id"].idxmin(), PRIMARY_SCORE] if not df.empty else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Experiments", total)
    c2.metric("Accepted / Rejected", f"{n_accepted} / {n_rejected}")
    c3.metric("Acceptance Rate", f"{acceptance_rate:.0%}")

    if TRAINING_SECONDS in df.columns:
        total_time = df[TRAINING_SECONDS].sum()
        hours = total_time / 3600
        c4.metric("Training Time", f"{hours:.1f}h" if hours >= 1 else f"{total_time:.0f}s")

    if best_score is not None and baseline_score is not None:
        c5, c6, c7, _ = st.columns(4)
        improvement = baseline_score - best_score
        pct = (improvement / baseline_score * 100) if baseline_score != 0 else 0
        c5.metric("Best Score", f"{best_score:.4f}")
        c6.metric("Baseline", f"{baseline_score:.4f}")
        c7.metric("Improvement", f"{improvement:.4f}", delta=f"{pct:.1f}%")

    # --- Leaderboard ---
    st.markdown("#### Top 5 Experiments")
    leaderboard_cols = ["experiment_id", PRIMARY_SCORE, RMSE_RATE_NORM, RMSE_TEMP_NORM, NUM_PARAMS, TRAINING_SECONDS]
    available_cols = [c for c in leaderboard_cols if c in df.columns]

    top5 = accepted_df.nsmallest(5, PRIMARY_SCORE)[available_cols].reset_index(drop=True)
    top5.index = top5.index + 1  # 1-based ranking
    st.dataframe(top5, use_container_width=True)

# =============================================================================
# Tab 2 — Best Model
# =============================================================================
with tab_best:
    if accepted_df.empty:
        st.warning("No accepted experiments yet.")
    else:
        best_row = accepted_df.loc[accepted_df[PRIMARY_SCORE].idxmin()]
        exp_id = int(best_row["experiment_id"])

        st.markdown(f"#### Experiment {exp_id}")

        # Per-target metrics (left) | Training/architecture metrics (right)
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("**Per-Target Metrics**")
            metric_pairs: list[tuple[str, str]] = [
                (RMSE_RATE, "RMSE Rate"),
                (RMSE_RATE_NORM, "RMSE Rate (norm)"),
                (MAX_ERROR_RATE, "Max Error Rate"),
                (RMSE_TEMP, "RMSE Temp"),
                (RMSE_TEMP_NORM, "RMSE Temp (norm)"),
                (MAX_ERROR_TEMP, "Max Error Temp"),
            ]
            for key, label in metric_pairs:
                if key in best_row.index and pd.notna(best_row[key]):
                    val = best_row[key]
                    # Delta from baseline if available
                    delta = None
                    if baseline_score is not None and key == PRIMARY_SCORE:
                        delta = f"{baseline_score - val:.4f}"
                    st.metric(label, f"{val:.6f}", delta=delta)

        with col_right:
            st.markdown("**Training & Architecture**")
            st.metric(PRIMARY_SCORE, f"{best_row[PRIMARY_SCORE]:.6f}")
            arch_pairs: list[tuple[str, str]] = [
                (NUM_PARAMS, "Parameters"),
                (NUM_EPOCHS, "Epochs"),
                (TRAINING_SECONDS, "Training (s)"),
                (TOTAL_SECONDS, "Total (s)"),
            ]
            for key, label in arch_pairs:
                if key in best_row.index and pd.notna(best_row[key]):
                    val = best_row[key]
                    fmt = f"{int(val):,}" if key in (NUM_PARAMS, NUM_EPOCHS) else f"{val:.1f}"
                    st.metric(label, fmt)

        # Architecture descriptor
        if "architecture" in best_row.index and pd.notna(best_row.get("architecture")):
            st.markdown("**Architecture**")
            st.code(str(best_row["architecture"]))
        else:
            st.info(
                "Architecture descriptor not available — "
                "will be added in a future autoresearch run."
            )

# =============================================================================
# Tab 3 — Surrogate Playground
# =============================================================================
with tab_playground:
    st.info(
        "The Surrogate Playground allows interactive prediction using the trained model.\n\n"
        "This feature requires a saved model checkpoint, which will be available "
        "after implementing checkpoint saving in the autoresearch pipeline."
    )

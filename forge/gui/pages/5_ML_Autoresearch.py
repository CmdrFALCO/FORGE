"""ML Autoresearch dashboard — visualizes autonomous surrogate optimization results."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

try:
    from forge.ml.surrogate_inference import SurrogatePredictor

    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False

try:
    from sklearn.ensemble import GradientBoostingRegressor

    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False

try:
    from scipy.stats import spearmanr as _spearmanr

    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

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
CHECKPOINT_PATH = _repo_root() / "experiments" / "ml" / "autoresearch" / "checkpoint.pt"
_DATASET_DIR = _repo_root() / "experiments" / "ml" / "autoresearch" / "dataset"
TEST_PATH = _DATASET_DIR / "test.npz"
TRAIN_PATH = _DATASET_DIR / "train.npz"

ACCENT_GREEN = "#4ade80"
ACCENT_RED = "#f87171"
ACCENT_BLUE = "#60a5fa"


@st.cache_resource
def _load_predictor() -> "SurrogatePredictor":
    return SurrogatePredictor(CHECKPOINT_PATH)


@st.cache_data
def _batch_predict_test() -> (
    tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None
):
    """Run ensemble over the test set. Returns (X_test, y_test, means, stds)."""
    if not (_HAS_TORCH and CHECKPOINT_PATH.exists() and TEST_PATH.exists()):
        return None
    predictor = _load_predictor()
    data = np.load(TEST_PATH)
    x_test, y_test = data["X"].astype(np.float32), data["y"].astype(np.float32)
    means, stds = predictor.predict_batch(x_test)
    return x_test, y_test, means, stds


@st.cache_data
def _train_gbr() -> tuple[np.ndarray, np.ndarray] | None:
    """Train two GBR models on the training set, return test predictions."""
    if not (_HAS_SKLEARN and TRAIN_PATH.exists() and TEST_PATH.exists()):
        return None
    train = np.load(TRAIN_PATH)
    test = np.load(TEST_PATH)
    x_tr, y_tr = train["X"].astype(np.float32), train["y"].astype(np.float32)
    x_te = test["X"].astype(np.float32)
    preds = np.zeros((x_te.shape[0], 2), dtype=np.float64)
    for col in range(2):
        gbr = GradientBoostingRegressor(
            n_estimators=200, max_depth=4, learning_rate=0.1, random_state=42,
        )
        gbr.fit(x_tr, y_tr[:, col])
        preds[:, col] = gbr.predict(x_te)
    return preds, test["y"].astype(np.float32)


def _pareto_mask(points: np.ndarray) -> np.ndarray:
    """Return boolean mask of Pareto-optimal points (lower is better)."""
    n = len(points)
    is_pareto = np.ones(n, dtype=bool)
    for i in range(n):
        if is_pareto[i]:
            dominated = np.all(points[i] <= points, axis=1) & np.any(
                points[i] < points, axis=1
            )
            is_pareto[dominated] = False
    return is_pareto


def _categorize_reason(reason: str) -> str:
    r = str(reason).lower()
    if any(k in r for k in ["log_", "feature", "bruggeman", "remove", "drop", "add "]):
        return "Feature Engineering"
    if any(k in r for k in ["ensemble", "hidden", "lr=", "batch", "learning"]):
        return "Hyperparameter Tuning"
    if any(k in r for k in ["gelu", "batchnorm", "skip", "activation", "layer"]):
        return "Architecture"
    if any(k in r for k in ["cuda", "target norm", "adamw", "weight_decay"]):
        return "Training Strategy"
    return "Other"


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

    # Total experiments attempted (including rejected, not in git history)
    TOTAL_ATTEMPTED = 200

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Experiments Attempted", TOTAL_ATTEMPTED)
    c2.metric("Accepted / Rejected", f"{n_accepted} / {TOTAL_ATTEMPTED - n_accepted}")
    c3.metric("Acceptance Rate", f"{n_accepted / TOTAL_ATTEMPTED:.0%}")

    if TRAINING_SECONDS in df.columns and df[TRAINING_SECONDS].notna().any():
        total_time = df[TRAINING_SECONDS].dropna().sum()
        hours = total_time / 3600
        c4.metric("Training Time", f"{hours:.1f}h" if hours >= 1 else f"{total_time:.0f}s")
    else:
        c4.metric("Training Time", "—")

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

    # --- Enhancement 4: Pareto Front ---
    if RMSE_RATE_NORM in df.columns and RMSE_TEMP_NORM in df.columns:
        pareto_df = df[[RMSE_RATE_NORM, RMSE_TEMP_NORM]].dropna()
        if len(pareto_df) > 1:
            st.markdown("#### Rate vs Temperature Tradeoff (Pareto Front)")
            pts = pareto_df.values
            mask = _pareto_mask(pts)
            pareto_pts = pts[mask]
            order = np.argsort(pareto_pts[:, 0])
            pareto_pts = pareto_pts[order]

            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(
                x=pts[:, 0], y=pts[:, 1], mode="markers",
                name="All experiments",
                marker=dict(color="grey", size=5, opacity=0.5),
                hovertemplate="Rate: %{x:.4f}<br>Temp: %{y:.4f}<extra></extra>",
            ))
            fig_p.add_trace(go.Scatter(
                x=pareto_pts[:, 0], y=pareto_pts[:, 1],
                mode="lines+markers", name="Pareto front",
                marker=dict(color=ACCENT_GREEN, size=8),
                line=dict(color=ACCENT_GREEN, width=2),
                hovertemplate="Rate: %{x:.4f}<br>Temp: %{y:.4f}<extra>Pareto</extra>",
            ))
            fig_p.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="RMSE Rate (normalized)",
                yaxis_title="RMSE Temp (normalized)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02,
                            xanchor="right", x=1),
                margin=dict(l=40, r=20, t=40, b=40),
                height=400,
            )
            st.plotly_chart(fig_p, use_container_width=True, key="pareto_chart")

    # --- Enhancement 3: Hyperparameter Landscape ---
    if "reason" in df.columns:
        st.markdown("#### Experiment Categories")
        cat_df = df.copy()
        cat_df["category"] = cat_df["reason"].apply(_categorize_reason)
        cat_colors = {
            "Architecture": "#a78bfa",
            "Feature Engineering": ACCENT_BLUE,
            "Hyperparameter Tuning": ACCENT_GREEN,
            "Training Strategy": "#fbbf24",
            "Other": "grey",
        }
        fig_cat = go.Figure()
        for cat, color in cat_colors.items():
            sub = cat_df[cat_df["category"] == cat]
            if sub.empty:
                continue
            fig_cat.add_trace(go.Scatter(
                x=sub["experiment_id"], y=sub[PRIMARY_SCORE],
                mode="markers", name=cat,
                marker=dict(color=color, size=7),
                hovertemplate=(
                    "Exp %{x}<br>Score: %{y:.4f}<br>"
                    "%{text}<extra>" + cat + "</extra>"
                ),
                text=sub["reason"],
            ))
        fig_cat.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Experiment",
            yaxis_title="Primary Score",
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1),
            margin=dict(l=40, r=20, t=40, b=40),
            height=400,
        )
        st.plotly_chart(fig_cat, use_container_width=True, key="category_chart")

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
            st.markdown("**Architecture**")
            st.code(
                "2-layer MLP, BatchNorm, input skip connection\n"
                "HIDDEN_SIZE=80, BATCH_SIZE=32, LR=5e-3\n"
                "WEIGHT_DECAY=1e-4, ACTIVATION=GELU, LOSS=MSE\n"
                "ENSEMBLE_SIZE=30, Device=CUDA (RTX 3060)\n"
                "\n"
                "Features (22 total): 11 raw inputs (can_inner_diameter zeroed)\n"
                "+ et×por, ntabs×height, log_diff, log_cond, log_stv,\n"
                "  log_por, log_cond_diff, et², por^1.5 (Bruggeman),\n"
                "  et/por^1.5 (corrected diffusion), log(et)",
                language=None,
            )

        # --- Enhancement 1: Prediction vs Actual ---
        batch_result = _batch_predict_test()
        if batch_result is not None:
            _, y_test, means, stds = batch_result

            st.markdown("#### Prediction vs Actual (Test Set)")

            r2_vals = []
            for idx, (tgt_name, unit) in enumerate(
                [("Rate Capability", ""), ("Max Temperature", "\u00b0C")]
            ):
                actual = y_test[:, idx]
                predicted = means[:, idx]
                ss_res = np.sum((actual - predicted) ** 2)
                ss_tot = np.sum((actual - actual.mean()) ** 2)
                r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
                r2_vals.append(r2)

            rc1, rc2 = st.columns(2)
            rc1.metric("R\u00b2 Rate", f"{r2_vals[0]:.4f}")
            rc2.metric("R\u00b2 Temp", f"{r2_vals[1]:.4f}")

            pva_left, pva_right = st.columns(2)
            for idx, (col_c, tgt_name, unit) in enumerate([
                (pva_left, "Rate Capability", ""),
                (pva_right, "Max Temperature", "\u00b0C"),
            ]):
                actual = y_test[:, idx]
                predicted = means[:, idx]
                unc = stds[:, idx]
                lo_v, hi_v = actual.min(), actual.max()

                fig_pva = go.Figure()
                fig_pva.add_trace(go.Scatter(
                    x=[lo_v, hi_v], y=[lo_v, hi_v], mode="lines",
                    name="Perfect", line=dict(color="white", dash="dash", width=1),
                    showlegend=False,
                ))
                fig_pva.add_trace(go.Scatter(
                    x=actual, y=predicted, mode="markers",
                    marker=dict(color=unc, colorscale="Viridis", size=5,
                                colorbar=dict(title="\u03c3")),
                    hovertemplate=(
                        "Actual: %{x:.4f}<br>Predicted: %{y:.4f}<br>"
                        "Error: %{customdata[0]:.4f}<br>"
                        "\u03c3: %{customdata[1]:.4f}<extra></extra>"
                    ),
                    customdata=np.column_stack([predicted - actual, unc]),
                    showlegend=False,
                ))
                fig_pva.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis_title=f"Actual {unit}",
                    yaxis_title=f"Predicted {unit}",
                    title=tgt_name,
                    margin=dict(l=40, r=20, t=40, b=40),
                    height=400,
                )
                col_c.plotly_chart(fig_pva, use_container_width=True,
                                   key=f"pva_{idx}")

            # --- Enhancement 5: Uncertainty Calibration ---
            st.markdown("#### Uncertainty Calibration")
            errors_abs = np.abs(means - y_test)
            cal_left, cal_right = st.columns(2)
            for idx, (col_c, tgt_name) in enumerate([
                (cal_left, "Rate"), (cal_right, "Temperature"),
            ]):
                pred_std = stds[:, idx]
                act_err = errors_abs[:, idx]
                lo_v = 0
                hi_v = max(pred_std.max(), act_err.max()) * 1.1

                fig_cal = go.Figure()
                fig_cal.add_trace(go.Scatter(
                    x=[lo_v, hi_v], y=[lo_v, hi_v], mode="lines",
                    line=dict(color="white", dash="dash", width=1),
                    showlegend=False,
                ))
                fig_cal.add_trace(go.Scatter(
                    x=pred_std, y=act_err, mode="markers",
                    marker=dict(color=ACCENT_BLUE, size=5, opacity=0.6),
                    showlegend=False,
                    hovertemplate="\u03c3: %{x:.4f}<br>|error|: %{y:.4f}<extra></extra>",
                ))
                title_text = f"{tgt_name}"
                if _HAS_SCIPY:
                    rho, _ = _spearmanr(pred_std, act_err)
                    title_text += f" (\u03c1 = {rho:.3f})"
                fig_cal.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis_title="Ensemble \u03c3",
                    yaxis_title="|Prediction Error|",
                    title=title_text,
                    margin=dict(l=40, r=20, t=40, b=40),
                    height=350,
                )
                col_c.plotly_chart(fig_cal, use_container_width=True,
                                   key=f"cal_{idx}")
            st.caption(
                "Points near the diagonal indicate well-calibrated uncertainty. "
                "The ensemble\u2019s disagreement (\u03c3 across 30 models) should "
                "correlate with actual prediction error."
            )

        # --- Enhancement 2: Model Comparison ---
        gbr_result = _train_gbr()
        if gbr_result is not None and batch_result is not None:
            gbr_preds, y_test_gbr = gbr_result
            _, y_test_mlp, mlp_means, _ = batch_result

            st.markdown("#### Model Comparison")
            rmse_mlp = np.sqrt(np.mean((mlp_means - y_test_mlp) ** 2, axis=0))
            rmse_gbr = np.sqrt(np.mean((gbr_preds - y_test_gbr) ** 2, axis=0))

            comp_data = {
                "Metric": [
                    "RMSE (rate)", "RMSE (temp)",
                    "R\u00b2 (rate)", "R\u00b2 (temp)",
                ],
                "MLP Ensemble (30)": [
                    f"{rmse_mlp[0]:.4f}", f"{rmse_mlp[1]:.2f}",
                    f"{1 - np.sum((mlp_means[:,0]-y_test_mlp[:,0])**2)/np.sum((y_test_mlp[:,0]-y_test_mlp[:,0].mean())**2):.4f}",
                    f"{1 - np.sum((mlp_means[:,1]-y_test_mlp[:,1])**2)/np.sum((y_test_mlp[:,1]-y_test_mlp[:,1].mean())**2):.4f}",
                ],
                "Gradient Boosting": [
                    f"{rmse_gbr[0]:.4f}", f"{rmse_gbr[1]:.2f}",
                    f"{1 - np.sum((gbr_preds[:,0]-y_test_gbr[:,0])**2)/np.sum((y_test_gbr[:,0]-y_test_gbr[:,0].mean())**2):.4f}",
                    f"{1 - np.sum((gbr_preds[:,1]-y_test_gbr[:,1])**2)/np.sum((y_test_gbr[:,1]-y_test_gbr[:,1].mean())**2):.4f}",
                ],
            }
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True,
                         hide_index=True)

# =============================================================================
# Tab 3 — Surrogate Playground
# =============================================================================
with tab_playground:
    if not _HAS_TORCH:
        st.warning(
            "PyTorch is not installed in this environment. "
            "The Surrogate Playground requires `torch` for model inference."
        )
    elif not CHECKPOINT_PATH.exists():
        st.info(
            "No model checkpoint found.\n\n"
            "Train the surrogate and export a checkpoint:\n"
            "```\n"
            "python surrogate.py --dataset dataset --seed 42 "
            "--budget-seconds 300 --save-checkpoint checkpoint.pt\n"
            "```"
        )
    else:
        predictor = _load_predictor()
        ranges = predictor.feature_ranges

        col_sliders, col_results = st.columns([1, 1])

        with col_sliders:
            st.markdown("#### Cell Design Parameters")
            inputs: dict[str, float] = {}
            for name, (lo, hi) in ranges.items():
                mid = (lo + hi) / 2
                # Integer slider for n_tabs
                if name == "n_tabs":
                    inputs[name] = float(
                        st.slider(name, min_value=int(lo), max_value=int(hi),
                                  value=int(mid), step=1)
                    )
                else:
                    step = (hi - lo) / 200
                    inputs[name] = st.slider(
                        name, min_value=lo, max_value=hi,
                        value=mid, step=step, format="%.3f",
                    )

        result = predictor.predict(inputs)

        with col_results:
            st.markdown("#### Predicted Performance")
            rate_mean, rate_std = result["rate"]
            temp_mean, temp_std = result["temp"]

            st.metric(
                "Rate Capability",
                f"{rate_mean:.4f}",
                delta=f"\u00b1 {rate_std:.4f}",
                delta_color="off",
            )
            st.metric(
                "Max Temperature",
                f"{temp_mean:.1f} \u00b0C",
                delta=f"\u00b1 {temp_std:.1f} \u00b0C",
                delta_color="off",
            )

            # --- Sensitivity bar chart ---
            st.markdown("#### Feature Sensitivity")
            if go is not None:
                sens_rate: dict[str, float] = {}
                sens_temp: dict[str, float] = {}
                for feat, (lo, hi) in ranges.items():
                    delta = (hi - lo) * 0.01
                    inp_lo = {**inputs, feat: inputs[feat] - delta}
                    inp_hi = {**inputs, feat: inputs[feat] + delta}
                    r_lo = predictor.predict(inp_lo)
                    r_hi = predictor.predict(inp_hi)
                    sens_rate[feat] = (r_hi["rate"][0] - r_lo["rate"][0]) / (2 * delta)
                    sens_temp[feat] = (r_hi["temp"][0] - r_lo["temp"][0]) / (2 * delta)

                feats = list(sens_rate.keys())
                rate_vals = [sens_rate[f] for f in feats]
                temp_vals = [sens_temp[f] for f in feats]

                fig_s = go.Figure()
                fig_s.add_trace(go.Bar(
                    y=feats, x=rate_vals, orientation="h",
                    name="Rate", marker_color=ACCENT_GREEN,
                ))
                fig_s.add_trace(go.Bar(
                    y=feats, x=temp_vals, orientation="h",
                    name="Temp", marker_color=ACCENT_RED,
                ))
                fig_s.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    barmode="group",
                    xaxis_title="d(output) / d(feature)",
                    margin=dict(l=20, r=20, t=20, b=40),
                    height=300,
                    legend=dict(orientation="h", yanchor="bottom",
                                y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_s, use_container_width=True,
                                key="sensitivity_chart")

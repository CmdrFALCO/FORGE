"""Inference module for the trained battery cell surrogate ensemble.

Loads a checkpoint produced by ``surrogate.py --save-checkpoint`` and exposes
a high-level :class:`SurrogatePredictor` API for interactive prediction.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from torch import nn

# ---------------------------------------------------------------------------
# Model architecture (must match surrogate.py exactly)
# ---------------------------------------------------------------------------

def _activation_layer(name: str) -> nn.Module:
    key = name.lower()
    if key == "relu":
        return nn.ReLU()
    if key == "gelu":
        return nn.GELU()
    if key == "tanh":
        return nn.Tanh()
    raise ValueError(f"Unsupported activation: {name}")


class _SkipNet(nn.Module):
    """MLP with input skip connection and BatchNorm."""

    def __init__(self, input_dim: int, hidden_size: int, activation: str) -> None:
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_size)
        self.bn1 = nn.BatchNorm1d(hidden_size)
        self.act1 = _activation_layer(activation)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.bn2 = nn.BatchNorm1d(hidden_size)
        self.act2 = _activation_layer(activation)
        self.fc_out = nn.Linear(hidden_size + input_dim, 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.act1(self.bn1(self.fc1(x)))
        h = self.act2(self.bn2(self.fc2(h)))
        h = torch.cat([h, x], dim=1)
        return self.fc_out(h)


class _PlainNet(nn.Module):
    """Simple 2-layer MLP without BatchNorm or skip connection."""

    def __init__(self, input_dim: int, hidden_size: int, activation: str) -> None:
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_size)
        self.act1 = _activation_layer(activation)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.act2 = _activation_layer(activation)
        self.fc_out = nn.Linear(hidden_size, 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.act1(self.fc1(x))
        h = self.act2(self.fc2(h))
        return self.fc_out(h)


# ---------------------------------------------------------------------------
# Feature engineering (must match surrogate.py _add_features exactly)
# ---------------------------------------------------------------------------

def _compute_feature(x: np.ndarray, name: str) -> np.ndarray:
    """Compute a single engineered feature by name."""
    if name == "et_x_por":
        return (x[:, 0] * x[:, 1]).reshape(-1, 1)
    if name == "ntabs_x_h":
        return (x[:, 3] * x[:, 7]).reshape(-1, 1)
    if name == "log_diff":
        return np.log(np.maximum(x[:, 10], 1e-6)).reshape(-1, 1)
    if name == "log_cond":
        return np.log(np.maximum(x[:, 9], 1e-6)).reshape(-1, 1)
    if name == "log_stv":
        return np.log(np.maximum(x[:, 8], 1e-6)).reshape(-1, 1)
    if name == "log_por":
        return np.log(np.maximum(x[:, 1], 1e-6)).reshape(-1, 1)
    if name == "log_cond_diff":
        log_cond = np.log(np.maximum(x[:, 9], 1e-6)).reshape(-1, 1)
        log_diff = np.log(np.maximum(x[:, 10], 1e-6)).reshape(-1, 1)
        return log_cond - log_diff
    if name == "et_sq":
        return (x[:, 0] ** 2).reshape(-1, 1)
    if name == "bruggeman":
        return (x[:, 1] ** 1.5).reshape(-1, 1)
    if name == "diff_brugg":
        return (x[:, 0] / np.maximum(x[:, 1] ** 1.5, 1e-6)).reshape(-1, 1)
    if name == "log_et":
        return np.log(np.maximum(x[:, 0], 1e-6)).reshape(-1, 1)
    raise ValueError(f"Unknown engineered feature: {name}")


def _add_features(x: np.ndarray, feature_names: list[str]) -> np.ndarray:
    """Apply engineered features specified in the checkpoint config."""
    cols = [x]
    for name in feature_names:
        cols.append(_compute_feature(x, name))
    return np.concatenate(cols, axis=1)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class SurrogatePredictor:
    """Load a trained ensemble checkpoint and predict battery cell performance."""

    def __init__(self, checkpoint_path: str | Path) -> None:
        ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)

        hp = ckpt["hyperparameters"]
        norm = ckpt["normalization"]

        self._x_mean = np.asarray(norm["x_mean"], dtype=np.float32)
        self._x_std = np.asarray(norm["x_std"], dtype=np.float32)
        self._y_mean = np.asarray(norm["y_mean"], dtype=np.float32)
        self._y_std = np.asarray(norm["y_std"], dtype=np.float32)

        self._metadata = ckpt["metadata"]
        self._feature_config = ckpt["feature_config"]
        self._feature_names: list[str] = self._metadata["feature_names"]
        self._engineered_features: list[str] = self._feature_config.get(
            "engineered_features", []
        )

        # Detect architecture from state dict keys
        first_sd = ckpt["ensemble_state_dicts"][0]
        has_batchnorm = any("bn1" in k for k in first_sd)
        model_cls = _SkipNet if has_batchnorm else _PlainNet

        # Reconstruct ensemble on CPU
        self._models: list[nn.Module] = []
        for sd in ckpt["ensemble_state_dicts"]:
            model = model_cls(
                input_dim=hp["input_dim"],
                hidden_size=hp["hidden_size"],
                activation=hp["activation"],
            )
            model.load_state_dict(sd)
            model.eval()
            self._models.append(model)

    # ---- public interface ------------------------------------------------

    @property
    def feature_ranges(self) -> dict[str, tuple[float, float]]:
        """Physical ranges for each input feature (for slider bounds).

        Excludes ``can_inner_diameter`` which is zeroed during training.
        """
        ranges = self._metadata["feature_ranges"]
        return {
            k: (float(v[0]), float(v[1]))
            for k, v in ranges.items()
            if k != "can_inner_diameter"
        }

    def predict(self, inputs: dict[str, float]) -> dict[str, tuple[float, float]]:
        """Predict rate capability and max temperature from physical inputs.

        Args:
            inputs: Feature name → value, e.g.
                ``{"electrode_thickness": 120.0, "porosity": 0.35, ...}``

        Returns:
            ``{"rate": (mean, std), "temp": (mean, std)}`` in physical units.
        """
        # 1. Build raw 11-feature vector in the correct order
        raw = np.zeros((1, len(self._feature_names)), dtype=np.float32)
        for i, name in enumerate(self._feature_names):
            if name in inputs:
                raw[0, i] = inputs[name]

        # can_inner_diameter is excluded from sliders — use midpoint for derived calcs
        can_id = inputs.get("can_inner_diameter", 45.0)
        raw[0, 5] = can_id

        # 2. Compute derived features (must match prepare.py formulas exactly)
        et = raw[0, 0]   # electrode_thickness
        por = raw[0, 1]  # porosity
        n_tabs = raw[0, 3]
        tab_w = raw[0, 4]
        h = raw[0, 7]    # cell_height

        raw[0, 8] = 2.0 / (can_id / 2.0) + 2.0 / max(h, 1e-9)  # surface_to_volume
        raw[0, 9] = n_tabs * tab_w                                 # tab_conductance_proxy
        raw[0, 10] = et / max(por, 1e-9)                           # diffusion_path_proxy

        # 3. Zero out can_inner_diameter (matching training)
        for col in self._feature_config["zeroed_columns"]:
            raw[0, col] = 0.0

        # 4. Feature engineering
        x = _add_features(raw, self._engineered_features)

        # 5. Normalize
        x_n = (x - self._x_mean) / self._x_std
        x_t = torch.from_numpy(x_n)

        # 6. Ensemble forward pass
        preds = []
        with torch.no_grad():
            for model in self._models:
                preds.append(model(x_t).numpy())
        preds_arr = np.array(preds).squeeze(axis=1)  # (n_models, 2)

        # 7. Denormalize
        preds_phys = preds_arr * self._y_std.flatten() + self._y_mean.flatten()

        mean = preds_phys.mean(axis=0)
        std = preds_phys.std(axis=0)
        return {
            "rate": (float(mean[0]), float(std[0])),
            "temp": (float(mean[1]), float(std[1])),
        }

    def predict_batch(
        self, x_raw: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Predict on a batch of raw feature vectors.

        Args:
            x_raw: shape ``(n_samples, 11)`` — raw features as stored in the
                ``.npz`` dataset (derived features already present).

        Returns:
            ``(means, stds)`` each of shape ``(n_samples, 2)``.
        """
        x = x_raw.astype(np.float32).copy()
        for col in self._feature_config["zeroed_columns"]:
            x[:, col] = 0.0
        x = _add_features(x, self._engineered_features)
        x_n = (x - self._x_mean) / self._x_std
        x_t = torch.from_numpy(x_n)

        all_preds = []
        with torch.no_grad():
            for model in self._models:
                all_preds.append(model(x_t).numpy())
        # (n_models, n_samples, 2)
        stack = np.array(all_preds)
        stack = stack * self._y_std.flatten() + self._y_mean.flatten()
        means = stack.mean(axis=0)
        stds = stack.std(axis=0)
        return means, stds

    def sensitivity(
        self,
        base_inputs: dict[str, float],
        feature: str,
        n_points: int = 50,
    ) -> dict[str, np.ndarray]:
        """Sweep one feature across its range to measure output sensitivity.

        Returns:
            ``{"values": array, "rate_mean": array, "rate_std": array,
               "temp_mean": array, "temp_std": array}``
        """
        lo, hi = self.feature_ranges[feature]
        values = np.linspace(lo, hi, n_points)
        rate_mean, rate_std, temp_mean, temp_std = [], [], [], []

        for v in values:
            inp = {**base_inputs, feature: float(v)}
            result = self.predict(inp)
            rate_mean.append(result["rate"][0])
            rate_std.append(result["rate"][1])
            temp_mean.append(result["temp"][0])
            temp_std.append(result["temp"][1])

        return {
            "values": values,
            "rate_mean": np.array(rate_mean),
            "rate_std": np.array(rate_std),
            "temp_mean": np.array(temp_mean),
            "temp_std": np.array(temp_std),
        }

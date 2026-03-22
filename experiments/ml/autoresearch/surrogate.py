import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

# Ensure forge package is importable when running from experiments/ directory.
_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from forge.ml.autoresearch.constants import (  # noqa: E402
    MAX_ERROR_RATE,
    MAX_ERROR_TEMP,
    NUM_EPOCHS,
    NUM_PARAMS,
    RMSE_RATE,
    RMSE_RATE_NORM,
    RMSE_TEMP,
    RMSE_TEMP_NORM,
    TOTAL_SECONDS,
    TRAINING_SECONDS,
)

# === HYPERPARAMETERS ===
HIDDEN_SIZE = 96
NUM_LAYERS = 2
LEARNING_RATE = 5e-3
BATCH_SIZE = 64
ACTIVATION = "gelu"
LOSS_FN = "mse"
WEIGHT_DECAY = 0.0
ENSEMBLE_SIZE = 10


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train baseline surrogate model")
    parser.add_argument("--dataset", required=True, help="Path to dataset directory")
    parser.add_argument("--seed", required=True, type=int, help="Random seed")
    parser.add_argument("--budget-seconds", required=True, type=int, help="Training budget in seconds")
    return parser


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_npz(path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.load(path)
    return data["X"].astype(np.float32), data["y"].astype(np.float32)


def _activation_layer(name: str) -> nn.Module:
    key = name.lower()
    if key == "relu":
        return nn.ReLU()
    if key == "gelu":
        return nn.GELU()
    if key == "tanh":
        return nn.Tanh()
    raise ValueError(f"Unsupported activation: {name}")


def _loss_fn(name: str) -> nn.Module:
    key = name.lower()
    if key == "mse":
        return nn.MSELoss()
    if key == "huber":
        return nn.HuberLoss()
    raise ValueError(f"Unsupported loss function: {name}")


class _SkipNet(nn.Module):
    """MLP with input skip connection and BatchNorm."""

    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.fc1 = nn.Linear(input_dim, HIDDEN_SIZE)
        self.bn1 = nn.BatchNorm1d(HIDDEN_SIZE)
        self.act1 = _activation_layer(ACTIVATION)
        self.fc2 = nn.Linear(HIDDEN_SIZE, HIDDEN_SIZE)
        self.bn2 = nn.BatchNorm1d(HIDDEN_SIZE)
        self.act2 = _activation_layer(ACTIVATION)
        self.fc_out = nn.Linear(HIDDEN_SIZE + input_dim, 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.act1(self.bn1(self.fc1(x)))
        h = self.act2(self.bn2(self.fc2(h)))
        h = torch.cat([h, x], dim=1)
        return self.fc_out(h)


def _build_model(input_dim: int) -> nn.Module:
    return _SkipNet(input_dim)


def main() -> int:
    args = _build_parser().parse_args()
    if args.budget_seconds <= 0:
        print("--budget-seconds must be > 0", file=sys.stderr)
        return 1

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    total_start = time.time()

    dataset_dir = Path(args.dataset).resolve()
    train_path = dataset_dir / "train.npz"
    val_path = dataset_dir / "val.npz"
    test_path = dataset_dir / "test.npz"
    metadata_path = dataset_dir / "metadata.json"

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    expected_train_hash = metadata["hashes"]["train"]
    actual_train_hash = _sha256_file(train_path)
    if actual_train_hash != expected_train_hash:
        print(
            f"train.npz hash mismatch: {actual_train_hash} != {expected_train_hash}",
            file=sys.stderr,
        )
        return 1

    X_train, y_train = _load_npz(train_path)
    X_val, y_val = _load_npz(val_path)
    X_test, y_test = _load_npz(test_path)

    def _add_features(X: np.ndarray) -> np.ndarray:
        # Indices: 0=electrode_thickness, 1=porosity, 3=n_tabs, 6=can_wall_thickness,
        #          7=cell_height, 10=diffusion_path_proxy
        et_x_por = (X[:, 0] * X[:, 1]).reshape(-1, 1)          # interaction
        ntabs_x_h = (X[:, 3] * X[:, 7]).reshape(-1, 1)          # interaction
        et_sq = (X[:, 0] ** 2).reshape(-1, 1)                   # threshold behavior
        log_diff = np.log(np.maximum(X[:, 10], 1e-6)).reshape(-1, 1)  # compress range
        return np.concatenate([X, et_x_por, ntabs_x_h, et_sq, log_diff], axis=1)

    X_train = _add_features(X_train)
    X_val = _add_features(X_val)
    X_test = _add_features(X_test)

    x_mean = X_train.mean(axis=0, keepdims=True)
    x_std = X_train.std(axis=0, keepdims=True)
    x_std[x_std == 0.0] = 1.0

    X_train_n = (X_train - x_mean) / x_std
    X_val_n = (X_val - x_mean) / x_std
    X_test_n = (X_test - x_mean) / x_std

    criterion = _loss_fn(LOSS_FN)

    X_train_t = torch.from_numpy(X_train_n)
    y_train_t = torch.from_numpy(y_train)
    X_val_t = torch.from_numpy(X_val_n)
    y_val_t = torch.from_numpy(y_val)
    X_test_t = torch.from_numpy(X_test_n)

    input_dim = X_train_n.shape[1]
    per_model_budget = args.budget_seconds / ENSEMBLE_SIZE
    all_test_preds: list[np.ndarray] = []
    num_epochs = 0
    num_params = 0

    train_start = time.time()
    for member_idx in range(ENSEMBLE_SIZE):
        member_seed = args.seed + member_idx
        torch.manual_seed(member_seed)
        rng = np.random.default_rng(member_seed)

        model = _build_model(input_dim=input_dim)
        if member_idx == 0:
            num_params = sum(param.numel() for param in model.parameters())
        optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)

        best_val_loss = float("inf")
        best_state: dict[str, torch.Tensor] | None = None
        member_start = time.time()
        member_epochs = 0

        while True:
            if time.time() - member_start >= per_model_budget:
                break

            model.train()
            permutation = rng.permutation(X_train_t.shape[0])
            train_loss_acc = 0.0

            for start_idx in range(0, X_train_t.shape[0], BATCH_SIZE):
                batch_idx = permutation[start_idx : start_idx + BATCH_SIZE]
                batch_x = X_train_t[batch_idx]
                batch_y = y_train_t[batch_idx]

                optimizer.zero_grad()
                pred = model(batch_x)
                loss = criterion(pred, batch_y)
                loss.backward()
                optimizer.step()

                train_loss_acc += float(loss.item()) * batch_x.shape[0]

            member_epochs += 1
            train_loss = train_loss_acc / X_train_t.shape[0]

            model.eval()
            with torch.no_grad():
                val_pred = model(X_val_t)
                val_loss = float(criterion(val_pred, y_val_t).item())

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}

            print(f"member={member_idx} epoch={member_epochs} train_loss={train_loss:.6f} val_loss={val_loss:.6f}")

        num_epochs += member_epochs
        if best_state is not None:
            model.load_state_dict(best_state)
        model.eval()
        with torch.no_grad():
            all_test_preds.append(model(X_test_t).cpu().numpy())

    training_seconds = time.time() - train_start
    test_pred = np.mean(all_test_preds, axis=0)

    errors = test_pred - y_test
    rmse = np.sqrt(np.mean(np.square(errors), axis=0))
    max_errors = np.max(np.abs(errors), axis=0)

    rate_std = float(metadata["target_stds"]["rate_capability_proxy"])
    temp_std = float(metadata["target_stds"]["max_temp_proxy"])
    if rate_std <= 0 or temp_std <= 0:
        print("Target stds in metadata must be > 0", file=sys.stderr)
        return 1

    rmse_norm = np.array([rmse[0] / rate_std, rmse[1] / temp_std], dtype=np.float64)
    total_seconds = time.time() - total_start

    print("---")
    print(f"{RMSE_RATE}: {rmse[0]:.6f}")
    print(f"{RMSE_TEMP}: {rmse[1]:.6f}")
    print(f"{RMSE_RATE_NORM}: {rmse_norm[0]:.6f}")
    print(f"{RMSE_TEMP_NORM}: {rmse_norm[1]:.6f}")
    print(f"{MAX_ERROR_RATE}: {max_errors[0]:.6f}")
    print(f"{MAX_ERROR_TEMP}: {max_errors[1]:.6f}")
    print(f"{TRAINING_SECONDS}: {training_seconds:.3f}")
    print(f"{TOTAL_SECONDS}: {total_seconds:.3f}")
    print(f"{NUM_PARAMS}: {num_params}")
    print(f"{NUM_EPOCHS}: {num_epochs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


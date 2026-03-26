"""Optuna hyperparameter search for surrogate model.

Fair comparison against LLM-driven autoresearch: Optuna tunes numbers
(hyperparameters), the LLM invents ideas (features, architecture choices).
Optuna uses the 11 raw input features with no engineering or selection.
"""

import argparse
import hashlib
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import optuna
import torch
from torch import nn

# Ensure forge package is importable when running from experiments/ directory.
_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_npz(path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.load(path)
    return data["X"].astype(np.float32), data["y"].astype(np.float32)


def _activation_layer(name: str) -> nn.Module:
    return {
        "relu": nn.ReLU,
        "gelu": nn.GELU,
        "tanh": nn.Tanh,
        "silu": nn.SiLU,
    }[name.lower()]()


def _loss_fn(name: str) -> nn.Module:
    return {"mse": nn.MSELoss, "huber": nn.HuberLoss}[name.lower()]()


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


class _Net(nn.Module):
    """Parameterized MLP for hyperparameter search."""

    def __init__(
        self,
        input_dim: int,
        hidden_size: int,
        num_layers: int,
        activation: str,
        use_batchnorm: bool,
        use_skip: bool,
        dropout: float,
    ) -> None:
        super().__init__()
        self.use_skip = use_skip
        self.blocks = nn.ModuleList()

        in_dim = input_dim
        for i in range(num_layers):
            parts: list[nn.Module] = [nn.Linear(in_dim, hidden_size)]
            if use_batchnorm:
                parts.append(nn.BatchNorm1d(hidden_size))
            parts.append(_activation_layer(activation))
            if dropout > 0:
                parts.append(nn.Dropout(dropout))
            self.blocks.append(nn.Sequential(*parts))
            in_dim = hidden_size

        self.fc_out = nn.Linear(hidden_size, 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = x
        for i, block in enumerate(self.blocks):
            out = block(h)
            # Skip connection only when dims match (layers after the first)
            if self.use_skip and i > 0:
                out = out + h
            h = out
        return self.fc_out(h)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Optuna hyperparameter search for surrogate model"
    )
    parser.add_argument(
        "--dataset", type=str, required=True, help="Path to dataset directory"
    )
    parser.add_argument(
        "--n-trials", type=int, default=200, help="Number of Optuna trials"
    )
    parser.add_argument(
        "--budget-seconds",
        type=int,
        default=300,
        help="Time budget per trial (seconds)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--output", type=str, default="optuna_results", help="Output directory"
    )
    parser.add_argument(
        "--study-name",
        type=str,
        default="surrogate_hpo",
        help="Optuna study name",
    )
    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    args = _build_parser().parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    dataset_dir = Path(args.dataset).resolve()
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Load dataset once (shared across all trials) ---
    metadata = json.loads(
        (dataset_dir / "metadata.json").read_text(encoding="utf-8")
    )

    expected_hash = metadata["hashes"]["train"]
    actual_hash = _sha256_file(dataset_dir / "train.npz")
    if actual_hash != expected_hash:
        logger.error(
            "train.npz hash mismatch: %s != %s", actual_hash, expected_hash
        )
        return 1

    X_train, y_train = _load_npz(dataset_dir / "train.npz")
    X_val, y_val = _load_npz(dataset_dir / "val.npz")
    X_test, y_test = _load_npz(dataset_dir / "test.npz")

    # Normalize inputs (zero mean, unit variance from training set)
    x_mean = X_train.mean(axis=0, keepdims=True)
    x_std = X_train.std(axis=0, keepdims=True)
    x_std[x_std == 0.0] = 1.0
    X_train_n = (X_train - x_mean) / x_std
    X_val_n = (X_val - x_mean) / x_std
    X_test_n = (X_test - x_mean) / x_std

    # Normalize targets for stable training
    y_mean = y_train.mean(axis=0, keepdims=True)
    y_std_arr = y_train.std(axis=0, keepdims=True)
    y_std_arr[y_std_arr == 0.0] = 1.0
    y_train_n = (y_train - y_mean) / y_std_arr
    y_val_n = (y_val - y_mean) / y_std_arr

    X_train_t = torch.from_numpy(X_train_n)
    y_train_t = torch.from_numpy(y_train_n)
    X_val_t = torch.from_numpy(X_val_n)
    y_val_t = torch.from_numpy(y_val_n)
    X_test_t = torch.from_numpy(X_test_n)

    input_dim = X_train_n.shape[1]
    rate_std = float(metadata["target_stds"]["rate_capability_proxy"])
    temp_std = float(metadata["target_stds"]["max_temp_proxy"])

    logger.info(
        "Dataset: %s | %d train, %d val, %d test | %d features",
        dataset_dir.name,
        len(X_train),
        len(X_val),
        len(X_test),
        input_dim,
    )

    # --- Objective (closure over pre-loaded data) ---
    def objective(trial: optuna.Trial) -> float:
        trial_start = time.time()

        # Architecture
        hidden_size = trial.suggest_int("hidden_size", 32, 256, step=32)
        num_layers = trial.suggest_int("num_layers", 1, 4)
        activation = trial.suggest_categorical(
            "activation", ["relu", "gelu", "tanh", "silu"]
        )

        # Training
        learning_rate = trial.suggest_float(
            "learning_rate", 1e-4, 1e-2, log=True
        )
        batch_size = trial.suggest_categorical("batch_size", [16, 32, 64, 128])
        weight_decay = trial.suggest_float(
            "weight_decay", 1e-6, 1e-2, log=True
        )
        optimizer_name = trial.suggest_categorical(
            "optimizer", ["adam", "adamw"]
        )
        loss_name = trial.suggest_categorical("loss", ["mse", "huber"])

        # Regularization
        use_batchnorm = trial.suggest_categorical("batchnorm", [True, False])
        use_skip = trial.suggest_categorical("skip_connection", [True, False])
        dropout = trial.suggest_float("dropout", 0.0, 0.3, step=0.05)

        # Ensemble
        ensemble_size = trial.suggest_int("ensemble_size", 1, 10)

        criterion = _loss_fn(loss_name)
        per_model_budget = args.budget_seconds / ensemble_size

        all_test_preds: list[np.ndarray] = []
        total_epochs = 0
        num_params = 0
        train_start = time.time()

        for member_idx in range(ensemble_size):
            member_seed = args.seed + member_idx
            torch.manual_seed(member_seed)
            rng = np.random.default_rng(member_seed)

            model = _Net(
                input_dim,
                hidden_size,
                num_layers,
                activation,
                use_batchnorm,
                use_skip,
                dropout,
            )
            if member_idx == 0:
                num_params = sum(p.numel() for p in model.parameters())

            if optimizer_name == "adamw":
                opt = torch.optim.AdamW(
                    model.parameters(),
                    lr=learning_rate,
                    weight_decay=weight_decay,
                )
            else:
                opt = torch.optim.Adam(
                    model.parameters(),
                    lr=learning_rate,
                    weight_decay=weight_decay,
                )

            best_val_loss = float("inf")
            best_state: dict[str, torch.Tensor] | None = None
            member_start = time.time()
            member_epochs = 0

            while time.time() - member_start < per_model_budget:
                model.train()
                perm = rng.permutation(X_train_t.shape[0])

                for start in range(0, X_train_t.shape[0], batch_size):
                    batch_idx = perm[start : start + batch_size]
                    opt.zero_grad()
                    loss = criterion(
                        model(X_train_t[batch_idx]), y_train_t[batch_idx]
                    )
                    loss.backward()
                    opt.step()

                member_epochs += 1

                model.eval()
                with torch.no_grad():
                    val_loss = float(
                        criterion(model(X_val_t), y_val_t).item()
                    )

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_state = {
                        k: v.detach().cpu().clone()
                        for k, v in model.state_dict().items()
                    }

                # Report to Optuna for pruning (first member only)
                if member_idx == 0 and member_epochs % 50 == 0:
                    trial.report(val_loss, member_epochs)
                    if trial.should_prune():
                        raise optuna.TrialPruned()

            total_epochs += member_epochs
            if best_state is not None:
                model.load_state_dict(best_state)
            model.eval()
            with torch.no_grad():
                all_test_preds.append(model(X_test_t).cpu().numpy())

        training_seconds = time.time() - train_start

        # Denormalize predictions and compute RMSE
        test_pred_n = np.mean(all_test_preds, axis=0)
        test_pred = test_pred_n * y_std_arr + y_mean

        errors = test_pred - y_test
        rmse = np.sqrt(np.mean(np.square(errors), axis=0))
        max_errors = np.max(np.abs(errors), axis=0)

        rmse_rate_norm = float(rmse[0] / rate_std)
        rmse_temp_norm = float(rmse[1] / temp_std)
        primary_score = rmse_rate_norm + rmse_temp_norm
        total_seconds = time.time() - trial_start

        # Store detailed metrics as trial user attributes
        trial.set_user_attr("rmse_rate", float(rmse[0]))
        trial.set_user_attr("rmse_temp", float(rmse[1]))
        trial.set_user_attr("rmse_rate_norm", rmse_rate_norm)
        trial.set_user_attr("rmse_temp_norm", rmse_temp_norm)
        trial.set_user_attr("max_error_rate", float(max_errors[0]))
        trial.set_user_attr("max_error_temp", float(max_errors[1]))
        trial.set_user_attr("training_seconds", training_seconds)
        trial.set_user_attr("total_seconds", total_seconds)
        trial.set_user_attr("num_params", num_params)
        trial.set_user_attr("num_epochs", total_epochs)

        try:
            best_so_far = min(trial.study.best_value, primary_score)
        except ValueError:
            best_so_far = primary_score

        logger.info(
            "Trial %d/%d | score=%.4f | best=%.4f | "
            "params: h=%d, lr=%.1e, act=%s, ens=%d",
            trial.number + 1,
            args.n_trials,
            primary_score,
            best_so_far,
            hidden_size,
            learning_rate,
            activation,
            ensemble_size,
        )

        return primary_score

    # --- Create study and optimize ---
    storage = f"sqlite:///{output_dir / 'optuna_study.db'}"
    study = optuna.create_study(
        study_name=args.study_name,
        storage=storage,
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=args.seed),
        pruner=optuna.pruners.MedianPruner(
            n_startup_trials=10, n_warmup_steps=100
        ),
        load_if_exists=True,
    )

    logger.info(
        "Starting Optuna search: %d trials, %ds budget/trial",
        args.n_trials,
        args.budget_seconds,
    )
    study.optimize(objective, n_trials=args.n_trials)

    # --- Save results ---
    completed = [
        t
        for t in study.trials
        if t.state == optuna.trial.TrialState.COMPLETE
    ]
    pruned = [
        t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED
    ]
    failed = [
        t for t in study.trials if t.state == optuna.trial.TrialState.FAIL
    ]

    logger.info(
        "Done: %d completed, %d pruned, %d failed | best=%.4f",
        len(completed),
        len(pruned),
        len(failed),
        study.best_value,
    )

    # results.tsv — one row per completed trial, sorted by trial number
    columns = [
        "experiment_id",
        "primary_score",
        "accepted",
        "rmse_rate",
        "rmse_temp",
        "rmse_rate_norm",
        "rmse_temp_norm",
        "max_error_rate",
        "max_error_temp",
        "training_seconds",
        "total_seconds",
        "num_params",
        "num_epochs",
    ]
    best_so_far = float("inf")
    rows: list[str] = ["\t".join(columns)]
    for trial in sorted(completed, key=lambda t: t.number):
        score = trial.value
        accepted = 1 if score < best_so_far else 0
        if accepted:
            best_so_far = score
        ua = trial.user_attrs
        row = [
            str(trial.number),
            f"{score:.6f}",
            str(accepted),
            f"{ua['rmse_rate']:.6f}",
            f"{ua['rmse_temp']:.6f}",
            f"{ua['rmse_rate_norm']:.6f}",
            f"{ua['rmse_temp_norm']:.6f}",
            f"{ua['max_error_rate']:.6f}",
            f"{ua['max_error_temp']:.6f}",
            f"{ua['training_seconds']:.3f}",
            f"{ua['total_seconds']:.3f}",
            str(ua["num_params"]),
            str(ua["num_epochs"]),
        ]
        rows.append("\t".join(row))
    tsv_path = output_dir / "results.tsv"
    tsv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    # best_params.json
    best = study.best_trial
    best_params = {
        "trial_number": best.number,
        "primary_score": best.value,
        "params": best.params,
        "metrics": best.user_attrs,
    }
    (output_dir / "best_params.json").write_text(
        json.dumps(best_params, indent=2) + "\n", encoding="utf-8"
    )

    # run_config.json
    run_config = {
        "optimizer_type": "optuna_tpe",
        "study_name": args.study_name,
        "n_trials": args.n_trials,
        "n_completed": len(completed),
        "n_pruned": len(pruned),
        "budget_seconds_per_trial": args.budget_seconds,
        "seed": args.seed,
        "dataset": str(dataset_dir),
        "dataset_name": dataset_dir.name,
        "n_train": len(X_train),
        "n_val": len(X_val),
        "n_test": len(X_test),
        "n_features": input_dim,
        "search_space": {
            "hidden_size": {"low": 32, "high": 256, "step": 32},
            "num_layers": {"low": 1, "high": 4},
            "activation": ["relu", "gelu", "tanh", "silu"],
            "learning_rate": {"low": 1e-4, "high": 1e-2, "log": True},
            "batch_size": [16, 32, 64, 128],
            "weight_decay": {"low": 1e-6, "high": 1e-2, "log": True},
            "optimizer": ["adam", "adamw"],
            "loss": ["mse", "huber"],
            "batchnorm": [True, False],
            "skip_connection": [True, False],
            "dropout": {"low": 0.0, "high": 0.3, "step": 0.05},
            "ensemble_size": {"low": 1, "high": 10},
        },
        "fixed_features": "11 raw (no engineering, no selection)",
        "comparison_note": (
            "Fair comparison — Optuna tunes numbers, LLM invents ideas"
        ),
        "best_score": study.best_value,
        "best_params": study.best_params,
    }
    (output_dir / "run_config.json").write_text(
        json.dumps(run_config, indent=2) + "\n", encoding="utf-8"
    )

    logger.info("Results saved to %s", output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

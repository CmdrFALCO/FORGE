"""Generate checkpoint.pt for Optuna runs from their best_params.json.

Usage:
    .venv311/bin/python experiments/ml/autoresearch/generate_optuna_checkpoints.py
"""

import json
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

RUNS = [
    ("run-004a-optuna-500", "experiments/ml/autoresearch/dataset_pybamm", 300),
    ("run-004b-optuna-3k", "experiments/ml/autoresearch/dataset_pybamm_3k", 300),
]

ACTIVATIONS = {"relu": nn.ReLU, "gelu": nn.GELU, "tanh": nn.Tanh, "silu": nn.SiLU}


class _FlexNet(nn.Module):
    def __init__(self, input_dim, hidden, act_name, use_skip, use_bn, dropout):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden)
        self.bn1 = nn.BatchNorm1d(hidden) if use_bn else nn.Identity()
        self.act1 = ACTIVATIONS[act_name]()
        self.drop1 = nn.Dropout(dropout) if dropout > 0 else nn.Identity()
        self.fc2 = nn.Linear(hidden, hidden)
        self.bn2 = nn.BatchNorm1d(hidden) if use_bn else nn.Identity()
        self.act2 = ACTIVATIONS[act_name]()
        self.drop2 = nn.Dropout(dropout) if dropout > 0 else nn.Identity()
        self.fc_out = nn.Linear(hidden + input_dim if use_skip else hidden, 2)
        self.use_skip = use_skip

    def forward(self, x):
        h = self.drop1(self.act1(self.bn1(self.fc1(x))))
        h = self.drop2(self.act2(self.bn2(self.fc2(h))))
        if self.use_skip:
            h = torch.cat([h, x], dim=1)
        return self.fc_out(h)


def main():
    for run_name, dataset_dir, budget in RUNS:
        print(f"=== {run_name} ===")
        bp = json.loads(
            Path(f"experiments/ml/autoresearch/runs/{run_name}/best_params.json").read_text()
        )
        params = bp["params"]
        ds_path = Path(dataset_dir)
        metadata = json.loads((ds_path / "metadata.json").read_text())

        train = np.load(ds_path / "train.npz")
        X_train = train["X"].astype(np.float32)
        y_train = train["y"].astype(np.float32)

        x_mean = X_train.mean(axis=0, keepdims=True)
        x_std = X_train.std(axis=0, keepdims=True)
        x_std[x_std == 0] = 1.0
        X_n = (X_train - x_mean) / x_std

        y_mean = y_train.mean(axis=0, keepdims=True)
        y_std = y_train.std(axis=0, keepdims=True)
        y_std[y_std == 0] = 1.0
        y_n = (y_train - y_mean) / y_std

        input_dim = X_n.shape[1]
        hidden = params["hidden_size"]
        act = params["activation"]
        use_skip = params["skip_connection"]
        use_bn = params["batchnorm"]
        dropout = params["dropout"]
        ensemble_size = params["ensemble_size"]
        lr = params["learning_rate"]
        wd = params["weight_decay"]
        bs = params["batch_size"]
        criterion = nn.HuberLoss() if params["loss"] == "huber" else nn.MSELoss()

        X_t = torch.from_numpy(X_n)
        y_t = torch.from_numpy(y_n)
        per_budget = budget / ensemble_size
        all_states = []

        for m in range(ensemble_size):
            torch.manual_seed(42 + m)
            model = _FlexNet(input_dim, hidden, act, use_skip, use_bn, dropout)
            opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
            best_loss = float("inf")
            best_state = None
            t0 = time.time()
            epochs = 0
            rng = np.random.default_rng(42 + m)

            while time.time() - t0 < per_budget:
                model.train()
                perm = rng.permutation(len(X_t))
                for i in range(0, len(X_t), bs):
                    idx = perm[i : i + bs]
                    loss = criterion(model(X_t[idx]), y_t[idx])
                    opt.zero_grad()
                    loss.backward()
                    opt.step()
                epochs += 1
                model.eval()
                with torch.no_grad():
                    val_loss = criterion(model(X_t), y_t).item()
                if val_loss < best_loss:
                    best_loss = val_loss
                    best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

            all_states.append(best_state)
            print(f"  member {m}: {epochs} epochs, loss={best_loss:.6f}")

        ckpt = {
            "ensemble_state_dicts": all_states,
            "hyperparameters": {
                "hidden_size": hidden,
                "ensemble_size": ensemble_size,
                "input_dim": input_dim,
                "activation": act,
                "num_layers": 2,
                "use_skip": use_skip,
                "use_batchnorm": use_bn,
                "dropout": dropout,
            },
            "normalization": {
                "x_mean": x_mean.tolist(),
                "x_std": x_std.tolist(),
                "y_mean": y_mean.tolist(),
                "y_std": y_std.tolist(),
            },
            "feature_config": {
                "zeroed_columns": [],
                "engineered_features": [],
            },
            "metadata": metadata,
        }

        out_path = Path(f"experiments/ml/autoresearch/runs/{run_name}/checkpoint.pt")
        torch.save(ckpt, out_path)
        print(f"  Saved {out_path} ({out_path.stat().st_size / 1024:.0f} KB)\n")


if __name__ == "__main__":
    main()

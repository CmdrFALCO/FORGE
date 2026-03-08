"""Output format key constants for autoresearch metrics.

Both the surrogate script (producer) and the metrics parser (consumer)
import these constants to prevent key-name drift.
"""

RMSE_RATE = "rmse_rate"
RMSE_TEMP = "rmse_temp"

RMSE_RATE_NORM = "rmse_rate_norm"
RMSE_TEMP_NORM = "rmse_temp_norm"

MAX_ERROR_RATE = "max_error_rate"
MAX_ERROR_TEMP = "max_error_temp"

TRAINING_SECONDS = "training_seconds"
TOTAL_SECONDS = "total_seconds"

NUM_PARAMS = "num_params"
NUM_EPOCHS = "num_epochs"

# Composite score -- optional in surrogate output.
# The engine always computes this from rmse_rate_norm + rmse_temp_norm.
PRIMARY_SCORE = "primary_score"

REQUIRED_KEYS = frozenset(
    {
        RMSE_RATE,
        RMSE_TEMP,
        RMSE_RATE_NORM,
        RMSE_TEMP_NORM,
        MAX_ERROR_RATE,
        MAX_ERROR_TEMP,
        TRAINING_SECONDS,
        TOTAL_SECONDS,
        NUM_PARAMS,
        NUM_EPOCHS,
    }
)


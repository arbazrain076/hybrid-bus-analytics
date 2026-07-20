"""Target-leakage guard: post-outcome columns must never enter the model feature vector.

Required by PROJECT_RULES section 6 and the testing skill. delay_min is the target; ping_sec (actual
time) and dist_m (a match artifact) are only known after the outcome. None may be a model input.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ml.features import (  # noqa: E402
    CATEGORICAL_COLS,
    LEAKAGE_COLS,
    NUMERIC_COLS,
    TARGET,
)


def test_target_not_in_features():
    assert TARGET not in CATEGORICAL_COLS + NUMERIC_COLS


def test_no_leakage_columns_in_features():
    feature_inputs = set(CATEGORICAL_COLS + NUMERIC_COLS)
    for leaky in LEAKAGE_COLS:
        assert leaky not in feature_inputs, f"{leaky} is a post-outcome column and must not be a feature"


def test_assembler_inputs_exclude_leakage():
    # The VectorAssembler consumes the numeric cols directly and one-hot versions of the categoricals;
    # confirm none of the raw assembler inputs is a leakage column (raw or one-hot encoded).
    from ml.features import assembler_input_names

    assembler_inputs = set(assembler_input_names())
    encoded_leakage = set(LEAKAGE_COLS) | {f"{c}_oh" for c in LEAKAGE_COLS}
    assert assembler_inputs.isdisjoint(encoded_leakage)

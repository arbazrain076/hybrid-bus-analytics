"""Feature engineering for the delay-regression models.

Target: delay_min (continuous minutes late). Every feature below is known *before* the trip runs, so none
leaks the outcome. The columns produced from the actual observation - ping_sec (actual time), dist_m
(match distance), and delay_min itself - are the target/artifacts and are explicitly excluded from the
feature vector; `LEAKAGE_COLS` exists so a test can assert they never enter it.

Feature rationale (why each plausibly relates to delay):
- operator: operators differ in fleet, scheduling slack and reliability.
- line: some routes are structurally delay-prone (congestion corridors, long routes).
- direction_id: inbound vs outbound hit peak-direction congestion differently.
- stop_sequence: delay tends to accumulate along a journey, so position matters.
- sched_hour: peak vs off-peak scheduled time is the dominant delay driver.
- stop_lat / stop_lon: location proxies for local congestion (city centre vs suburb).
"""

from pyspark.ml import Pipeline
from pyspark.ml.feature import OneHotEncoder, StringIndexer, VectorAssembler
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

TARGET = "delay_min"

CATEGORICAL_COLS = ["operator", "line"]
NUMERIC_COLS = ["direction_id", "stop_sequence", "sched_hour", "stop_lat", "stop_lon"]

# Post-outcome columns that must never be used as model inputs (leakage guard checks this).
LEAKAGE_COLS = ["ping_sec", "delay_min", "dist_m"]


def add_derived_features(df: DataFrame) -> DataFrame:
    """Adds pre-trip-known derived columns (scheduled hour-of-day from the scheduled seconds)."""
    return df.withColumn("sched_hour", (F.col("sched_sec") / 3600).cast("int") % 24)


def assembler_input_names() -> list:
    """Column names fed into the VectorAssembler (one-hot categoricals + raw numerics).

    Exposed as plain Python (no Spark objects) so the leakage-guard test can inspect it without a
    SparkContext.
    """
    return [f"{c}_oh" for c in CATEGORICAL_COLS] + NUMERIC_COLS


def feature_pipeline_stages() -> list:
    """StringIndexer -> OneHotEncoder for categoricals, then VectorAssembler into 'features'.

    handleInvalid='keep' so operators/lines present only in the test day don't crash the transform.
    """
    indexers = [
        StringIndexer(inputCol=c, outputCol=f"{c}_idx", handleInvalid="keep")
        for c in CATEGORICAL_COLS
    ]
    encoders = [
        OneHotEncoder(inputCol=f"{c}_idx", outputCol=f"{c}_oh", handleInvalid="keep")
        for c in CATEGORICAL_COLS
    ]
    assembler = VectorAssembler(
        inputCols=assembler_input_names(),
        outputCol="features",
        handleInvalid="keep",
    )
    return indexers + encoders + [assembler]


def build_feature_pipeline() -> Pipeline:
    return Pipeline(stages=feature_pipeline_stages())

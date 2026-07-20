"""Trains and compares delay-regression models against a trivial baseline.

Single category (regression), 3 MLlib models + a mean-predicting baseline, on a time-based split
(train = 2026-06-30, test = 2026-07-01). All stochastic steps use SEED for reproducibility. Reports
RMSE / MAE / R2, training time, and Model Efficiency for every model, plus a domain anchor (test-set
Service Reliability = % of arrivals within +/-2 min of schedule). See ADR-004 and
`.project/skills/evaluation/SKILL.md`.
"""

import time
from pathlib import Path

from pyspark.ml import Pipeline
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.regression import GBTRegressor, LinearRegression, RandomForestRegressor
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from ml.features import TARGET, add_derived_features, feature_pipeline_stages

SEED = 42
TRAIN_DATE = "20260630"
TEST_DATE = "20260701"
DELAY_EVENTS = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "silver" / "delay_events"
RESULTS_CSV = Path(__file__).resolve().parent.parent.parent / "outputs" / "model_comparison.csv"

# Service Reliability (urban): within +/-2 min of schedule (see evaluation skill).
ON_TIME_TOL_MIN = 2.0


def load_split(spark: SparkSession):
    df = add_derived_features(spark.read.parquet(str(DELAY_EVENTS)))
    train = df.filter(F.col("service_date") == TRAIN_DATE).cache()
    test = df.filter(F.col("service_date") == TEST_DATE).cache()
    return train, test


def _metrics(predictions: DataFrame) -> dict:
    out = {}
    for name, metric in [("rmse", "rmse"), ("mae", "mae"), ("r2", "r2")]:
        out[name] = RegressionEvaluator(
            labelCol=TARGET, predictionCol="prediction", metricName=metric
        ).evaluate(predictions)
    return out


def evaluate_baseline(train: DataFrame, test: DataFrame) -> dict:
    t0 = time.perf_counter()
    mean_delay = train.select(F.mean(TARGET)).first()[0]
    train_time = time.perf_counter() - t0

    preds = test.withColumn("prediction", F.lit(mean_delay))
    m = _metrics(preds)
    return _row("Baseline (mean)", m, train_time)


def evaluate_model(name: str, estimator, param_grid, train: DataFrame, test: DataFrame) -> dict:
    pipeline = Pipeline(stages=feature_pipeline_stages() + [estimator])
    cv = CrossValidator(
        estimator=pipeline,
        estimatorParamMaps=param_grid,
        evaluator=RegressionEvaluator(labelCol=TARGET, predictionCol="prediction", metricName="rmse"),
        numFolds=3,
        seed=SEED,
        parallelism=2,
    )
    t0 = time.perf_counter()
    model = cv.fit(train)
    train_time = time.perf_counter() - t0

    preds = model.transform(test)
    m = _metrics(preds)
    return _row(name, m, train_time)


def _row(name: str, m: dict, train_time: float) -> dict:
    # Model Efficiency: inverted RMSE per second - (1/RMSE)/training_time. Higher is better (lower RMSE
    # and shorter training both raise it). Convention stated once and applied to every model + baseline.
    efficiency = 1.0 / (m["rmse"] * train_time) if train_time > 0 else float("nan")
    return {
        "model": name,
        "rmse": round(m["rmse"], 4),
        "mae": round(m["mae"], 4),
        "r2": round(m["r2"], 4),
        "train_time_s": round(train_time, 2),
        "model_efficiency": round(efficiency, 5),
    }


def service_reliability(df: DataFrame) -> float:
    """Actual test-set Service Reliability: fraction of arrivals within +/-2 min of schedule."""
    total = df.count()
    on_time = df.filter(F.abs(F.col(TARGET)) <= ON_TIME_TOL_MIN).count()
    return round(100 * on_time / total, 1)


def run(spark: SparkSession) -> list[dict]:
    train, test = load_split(spark)
    print(f"Train rows ({TRAIN_DATE}): {train.count()}  |  Test rows ({TEST_DATE}): {test.count()}")
    print(f"Test-set actual Service Reliability (within +/-{ON_TIME_TOL_MIN} min): "
          f"{service_reliability(test)}%")

    lr_grid = ParamGridBuilder().addGrid(LinearRegression.regParam, [0.0, 0.1]).build()
    rf_grid = ParamGridBuilder().addGrid(RandomForestRegressor.maxDepth, [5, 8]).build()
    gbt_grid = ParamGridBuilder().addGrid(GBTRegressor.maxDepth, [5]).build()

    results = [
        evaluate_baseline(train, test),
        evaluate_model(
            "LinearRegression",
            LinearRegression(labelCol=TARGET, featuresCol="features"),
            lr_grid, train, test,
        ),
        evaluate_model(
            "RandomForest",
            RandomForestRegressor(labelCol=TARGET, featuresCol="features", numTrees=30, seed=SEED),
            rf_grid, train, test,
        ),
        evaluate_model(
            "GBTRegressor",
            GBTRegressor(labelCol=TARGET, featuresCol="features", maxIter=30, seed=SEED),
            gbt_grid, train, test,
        ),
    ]
    return results

"""End-to-end smoke test over a sample of the silver data.

Required by PROJECT_RULES section 6. This exercises the real path a modelling run takes -- read the
delay-event table, derive features, fit the pipeline, predict -- on a small sample, so a breaking change
anywhere along that chain fails fast without waiting for a full training run.

Skipped automatically when the silver layer has not been built, so the suite still passes on a clean
checkout with no data.
"""

import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))

DELAY_EVENTS = BASE / "data" / "processed" / "silver" / "delay_events"
pytestmark = pytest.mark.skipif(
    not DELAY_EVENTS.exists(),
    reason="silver delay_events not built; run scripts/run_compute_delay.py first",
)

SAMPLE_ROWS = 2000


@pytest.fixture(scope="module")
def spark():
    from config.spark_session import get_spark_session

    session = get_spark_session("pipeline-smoke-test")
    yield session
    session.stop()


@pytest.fixture(scope="module")
def sample(spark):
    from ml.features import add_derived_features

    df = add_derived_features(spark.read.parquet(str(DELAY_EVENTS)).limit(SAMPLE_ROWS))
    return df.cache()


def test_sample_has_expected_schema(sample):
    from ml.features import CATEGORICAL_COLS, NUMERIC_COLS, TARGET

    for column in [TARGET, *CATEGORICAL_COLS, *NUMERIC_COLS]:
        assert column in sample.columns, f"{column} missing from the delay-event table"
    assert sample.count() > 0


def test_target_has_no_nulls(sample):
    from pyspark.sql import functions as F

    from ml.features import TARGET

    assert sample.filter(F.col(TARGET).isNull()).count() == 0


def test_feature_pipeline_produces_a_dense_feature_vector(sample):
    from ml.features import build_feature_pipeline

    out = build_feature_pipeline().fit(sample).transform(sample)
    assert "features" in out.columns
    first = out.select("features").head()[0]
    assert first.size > 0, "assembled feature vector is empty"


def test_end_to_end_train_and_predict(sample):
    """Fits a small model on the sample and predicts, exercising the full modelling path."""
    from pyspark.ml import Pipeline
    from pyspark.ml.evaluation import RegressionEvaluator
    from pyspark.ml.regression import LinearRegression

    from ml.features import TARGET, feature_pipeline_stages
    from ml.train import SEED

    train, test = sample.randomSplit([0.7, 0.3], seed=SEED)
    model = Pipeline(
        stages=feature_pipeline_stages() + [LinearRegression(labelCol=TARGET, featuresCol="features")]
    ).fit(train)

    predictions = model.transform(test)
    assert "prediction" in predictions.columns
    assert predictions.count() > 0

    rmse = RegressionEvaluator(labelCol=TARGET, predictionCol="prediction",
                               metricName="rmse").evaluate(predictions)
    assert rmse == pytest.approx(rmse)  # not NaN
    assert rmse > 0

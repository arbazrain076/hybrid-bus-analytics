"""Trains and compares the delay-regression models, printing and saving the comparison table."""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.spark_session import get_spark_session  # noqa: E402
from ml.train import RESULTS_CSV, run  # noqa: E402


def main() -> None:
    spark = get_spark_session()
    results = run(spark)

    cols = ["model", "rmse", "mae", "r2", "train_time_s", "model_efficiency"]
    print("\n=== Model comparison (test = 2026-07-01) ===")
    print(" | ".join(cols))
    for r in results:
        print(" | ".join(str(r[c]) for c in cols))

    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(results)
    print(f"\nSaved: {RESULTS_CSV}")

    spark.stop()


if __name__ == "__main__":
    main()

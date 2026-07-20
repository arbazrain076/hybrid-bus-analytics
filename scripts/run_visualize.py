"""Generates the delay-analysis figures under outputs/figures/."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.spark_session import get_spark_session  # noqa: E402
from eda.visualize import run  # noqa: E402


def main() -> None:
    spark = get_spark_session()
    figures = run(spark)
    print("Figures written:", figures)
    spark.stop()


if __name__ == "__main__":
    main()

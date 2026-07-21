"""Generates the extended EDA and model-evaluation charts, printing the descriptive profile."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.spark_session import get_spark_session  # noqa: E402
from eda.extended_charts import run  # noqa: E402


def main() -> None:
    spark = get_spark_session()
    stats = run(spark)
    print(json.dumps(stats, indent=2))
    spark.stop()


if __name__ == "__main__":
    main()

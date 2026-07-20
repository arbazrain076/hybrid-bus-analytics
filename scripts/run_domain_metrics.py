"""Computes and prints the transport-domain reliability metrics."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.spark_session import get_spark_session  # noqa: E402
from evaluation.domain_metrics import run  # noqa: E402


def main() -> None:
    spark = get_spark_session()
    result = run(spark)
    print(json.dumps(result, indent=2))
    spark.stop()


if __name__ == "__main__":
    main()

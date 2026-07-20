"""Centralised SparkSession configuration for the project."""

from pyspark.sql import SparkSession

# >=4 partitions is a project requirement, not a Spark default — set explicitly rather than
# relying on the machine's core count.
MIN_PARTITIONS = 8


def get_spark_session(app_name: str = "hybrid-bus-analytics") -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", MIN_PARTITIONS)
        .config("spark.default.parallelism", MIN_PARTITIONS)
        .getOrCreate()
    )

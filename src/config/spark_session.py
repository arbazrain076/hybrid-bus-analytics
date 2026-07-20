"""Centralised SparkSession configuration for the project."""

import os

from pyspark.sql import SparkSession

# >=4 partitions is a project requirement, not a Spark default — set explicitly rather than
# relying on the machine's core count. 8 satisfies the floor while keeping small-job overhead low.
MIN_PARTITIONS = 8

# Heavier stages (the spatial-temporal delay join) shuffle tens of millions of rows; the default local
# driver heap (~1g) OOMs on them. Raise driver memory and use more shuffle partitions so each task stays
# small. Driver memory must be set before the JVM launches, so it goes through PYSPARK_SUBMIT_ARGS at
# import time rather than the SparkSession builder (which runs after the JVM is already up in local mode).
DRIVER_MEMORY = "4g"
SHUFFLE_PARTITIONS = 64

os.environ.setdefault("PYSPARK_SUBMIT_ARGS", f"--driver-memory {DRIVER_MEMORY} pyspark-shell")


def get_spark_session(app_name: str = "hybrid-bus-analytics") -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", SHUFFLE_PARTITIONS)
        .config("spark.default.parallelism", MIN_PARTITIONS)
        .config("spark.driver.memory", DRIVER_MEMORY)
        .getOrCreate()
    )

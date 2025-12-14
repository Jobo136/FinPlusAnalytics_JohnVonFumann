"""I/O helpers."""

from __future__ import annotations #Permite usar las nuevas anotaciones de tipo (type hints) de forma diferida

from pyspark.sql import DataFrame, SparkSession


def read_parquet(spark: SparkSession, path: str) -> DataFrame:
    return spark.read.parquet(path)


def write_parquet(df: DataFrame, path: str, mode: str = "overwrite") -> None:
    df.write.mode(mode).parquet(path)


def to_csv_via_pandas(df: DataFrame, path: str, index: bool = False) -> None:
    """Collect to pandas and write CSV (use only if dataset fits in memory)."""
    pdf = df.toPandas()
    pdf.to_csv(path, index=index)

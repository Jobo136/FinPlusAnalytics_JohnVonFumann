"""Lightweight EDA/profiling for Spark DataFrames."""

from __future__ import annotations

from typing import Dict, List, Optional

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.utils import print_header, shape


def show_head_and_schema(df: DataFrame, name: str, n: int = 5, truncate: bool = False) -> None:
    print_header(f"{name} - head({n})")
    df.show(n, truncate=truncate)
    print_header(f"{name} - schema")
    df.printSchema()


def describe_df(df: DataFrame, name: str) -> None:
    r, c = shape(df)
    print_header(f"{name} - describe")
    print(f"Shape: ({r}, {c})")
    df.describe().show(truncate=False)


def report_missing(df: DataFrame, name: str, total_rows: Optional[int] = None) -> Dict[str, int]:
    """Counts nulls per column in one aggregation."""
    if total_rows is None:
        total_rows = df.count()

    exprs = [F.sum(F.when(F.col(c).isNull(), 1).otherwise(0)).alias(c) for c in df.columns]
    row = df.agg(*exprs).collect()[0].asDict()

    print_header(f"{name} - missing values")
    found = False
    for c in df.columns:
        m = int(row.get(c, 0) or 0)
        if m > 0:
            found = True
            pct = (m / total_rows * 100) if total_rows else 0.0
            print(f"  {c}: {m} nulos ({pct:.2f}%)")
    if not found:
        print("No hay valores nulos.")
    return {k: int(v or 0) for k, v in row.items()}


def count_row_duplicates(df: DataFrame, name: str) -> int:
    """Equivalent to pandas duplicated().sum() for full-row duplicates."""
    conteos = df.groupBy(df.columns).agg(F.count("*").alias("count"))
    dup = conteos.withColumn("duplicated_count", F.col("count") - 1)
    num = dup.agg(F.sum("duplicated_count")).collect()[0][0]
    num = int(num or 0)

    print_header(f"{name} - row duplicates")
    print(f"Filas duplicadas: {num}")
    return num


def count_missing_or_nan(df: DataFrame, name: str) -> Dict[str, int]:
    """Counts nulls; kept to match your notebook's second missing-values block."""
    row = df.select([F.count(F.when(F.col(c).isNull(), c)).alias(c) for c in df.columns]).collect()[0].asDict()
    total = df.count()

    print_header(f"{name} - missing (alt)")
    for c, m in row.items():
        m = int(m or 0)
        pct = (m / total * 100) if total else 0.0
        print(f"{c}: {m} missing ({pct:.2f}%)")
    return {k: int(v or 0) for k, v in row.items()}


def count_zeros(df: DataFrame, name: str) -> Dict[str, int]:
    row = (
        df.select([F.count(F.when(F.col(c) == 0, c)).alias(c) for c in df.columns])
        .collect()[0]
        .asDict()
    )

    print_header(f"{name} - zeros")
    for c, z in row.items():
        print(f"{c}: {int(z or 0)} ceros")
    return {k: int(v or 0) for k, v in row.items()}


def count_distinct_row_duplicates(df: DataFrame, name: str) -> int:
    total = df.count()
    unique = df.dropDuplicates().count()
    dup = total - unique

    print_header(f"{name} - duplicates (dropDuplicates)")
    print(f"Filas duplicadas: {dup}")
    return int(dup)

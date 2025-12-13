"""Outlier utilities (Spark-friendly)."""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import NumericType


def numeric_columns(df: DataFrame) -> List[str]:
    return [f.name for f in df.schema.fields if isinstance(f.dataType, NumericType)]


def mad_outlier_report(
    df: DataFrame,
    cols: Optional[Sequence[str]] = None,
    threshold: float = 3.5,
    ignore_zeros: bool = True,
    scale_factor: float = 1.482602218505602,  # for normal dist
) -> Dict[str, Dict[str, float]]:
    """Robust Z-score using MAD.

    Returns a dict per column with median, mad, outlier_count, outlier_pct.
    """
    if cols is None:
        cols = numeric_columns(df)

    results: Dict[str, Dict[str, float]] = {}
    for colname in cols:
        base = df
        if ignore_zeros:
            base = base.filter(F.col(colname) != 0)

        n = base.count()
        if n == 0:
            results[colname] = {"outlier_count": 0, "outlier_pct": 0.0, "median": None, "mad": None}
            continue

        median = base.select(F.expr(f"percentile_approx({colname}, 0.5)").alias("m")).collect()[0]["m"]

        # MAD = median(|x - median(x)|)
        abs_dev = base.select(F.abs(F.col(colname) - F.lit(median)).alias("abs_dev"))
        mad_raw = abs_dev.select(F.expr("percentile_approx(abs_dev, 0.5)").alias("mad")).collect()[0]["mad"]

        if mad_raw is None or mad_raw == 0:
            results[colname] = {"outlier_count": 0, "outlier_pct": 0.0, "median": float(median), "mad": float(mad_raw or 0.0)}
            continue

        mad_scaled = float(mad_raw) * float(scale_factor)
        robust_z = F.abs((F.col(colname) - F.lit(median)) / F.lit(mad_scaled))

        out_count = base.filter(robust_z > F.lit(threshold)).count()
        out_pct = out_count / n * 100

        results[colname] = {
            "median": float(median),
            "mad": float(mad_scaled),
            "outlier_count": float(out_count),
            "outlier_pct": float(out_pct),
        }

    return results


def iqr_outlier_report(
    df: DataFrame,
    cols: Optional[Sequence[str]] = None,
    factor: float = 1.5,
) -> Dict[str, Dict[str, float]]:
    """IQR outliers (Tukey). Returns per-column dict with bounds & counts."""
    if cols is None:
        cols = numeric_columns(df)

    n_total = df.count()
    results: Dict[str, Dict[str, float]] = {}
    for colname in cols:
        q1 = df.select(F.expr(f"percentile_approx({colname}, 0.25)").alias("q1")).collect()[0]["q1"]
        q3 = df.select(F.expr(f"percentile_approx({colname}, 0.75)").alias("q3")).collect()[0]["q3"]
        iqr = q3 - q1
        lower = q1 - factor * iqr
        upper = q3 + factor * iqr

        out_df = df.filter((F.col(colname) < F.lit(lower)) | (F.col(colname) > F.lit(upper)))
        out_count = out_df.count()
        out_pct = (out_count / n_total * 100) if n_total else 0.0

        results[colname] = {
            "q1": float(q1),
            "q3": float(q3),
            "iqr": float(iqr),
            "lower": float(lower),
            "upper": float(upper),
            "outlier_count": float(out_count),
            "outlier_pct": float(out_pct),
        }

    return results

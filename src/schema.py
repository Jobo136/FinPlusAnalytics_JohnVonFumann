"""Schema helpers (optional)."""

from __future__ import annotations

from typing import Dict, List

from pyspark.sql import DataFrame


def assert_has_columns(df: DataFrame, required: List[str]) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def columns_summary(df: DataFrame) -> Dict[str, str]:
    return {f.name: f.dataType.simpleString() for f in df.schema.fields}

"""Quality checks and simple reporting wrappers."""

from __future__ import annotations

from typing import Dict

from pyspark.sql import DataFrame

from src.profiling import report_missing, count_row_duplicates
from .utils import print_header


def quick_quality_report(df: DataFrame, name: str) -> Dict[str, int]:
    """Returns a minimal set of quality KPIs."""
    print_header(f"{name} - quality report")
    miss = report_missing(df, name)
    dups = count_row_duplicates(df, name)
    return {"duplicate_rows": int(dups), "columns": len(df.columns), "rows": df.count(), "missing_cells": sum(miss.values())}

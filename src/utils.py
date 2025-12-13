"""Small utilities."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from pyspark.sql import DataFrame


def shape(df: DataFrame) -> tuple[int, int]:
    return (df.count(), len(df.columns))


def print_header(title: str) -> None:
    bar = "=" * max(10, len(title))
    print(f"\n{bar}\n{title}\n{bar}")

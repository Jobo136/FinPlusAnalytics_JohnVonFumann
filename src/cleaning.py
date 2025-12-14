from __future__ import annotations #Permite usar las nuevas anotaciones de tipo (type hints) de forma diferida

from typing import Iterable, List, Optional

from pyspark.sql import DataFrame


def drop_columns(df: DataFrame, cols: Iterable[str]) -> DataFrame:
    cols = [c for c in cols if c in df.columns]
    return df.drop(*cols) if cols else df


def dropna_subset(df: DataFrame, subset: List[str]) -> DataFrame:
    subset = [c for c in subset if c in df.columns]
    return df.dropna(subset=subset) if subset else df

from __future__ import annotations #Permite usar las nuevas anotaciones de tipo (type hints) de forma diferida

from typing import Dict, Optional
from pyspark.sql import SparkSession


def get_spark(app_name: str, master: Optional[str] = None, configs: Optional[Dict[str, str]] = None) -> SparkSession:
    """Create (or retrieve) a SparkSession.

    Args:
        app_name: Spark application name.
        master: Optional Spark master (e.g., "local[*]").
        configs: Optional spark configs dict.

    Returns:
        SparkSession
    """
    builder = SparkSession.builder.appName(app_name)
    if master:
        builder = builder.master(master)
    if configs:
        for k, v in configs.items():
            builder = builder.config(k, v)
    return builder.getOrCreate()

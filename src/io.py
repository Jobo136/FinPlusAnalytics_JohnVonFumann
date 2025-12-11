"""
Módulo de entrada/salida de datos para Spark.
"""

from pathlib import Path
from pyspark.sql import SparkSession, DataFrame


def read_parquet(spark: SparkSession, path: str | Path) -> DataFrame:
    """
    Lee un dataset Parquet y devuelve un DataFrame de Spark.
    """
    return spark.read.parquet(str(path))


def write_parquet(df: DataFrame, path: str | Path, mode: str = "overwrite") -> None:
    """
    Escribe un DataFrame de Spark en formato Parquet.
    """
    df.write.mode(mode).parquet(str(path))


def spark_to_csv(df: DataFrame, path: str | Path, mode: str = "overwrite") -> None:
    """
    Exporta un DataFrame de Spark a CSV mediante toPandas().
    Úsalo solo para tamaños que quepan en memoria.
    """
    import pandas as pd  # Import local para que no sea obligatorio en todo el proyecto

    pdf = df.toPandas()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.to_csv(path, index=False)

"""
Funciones de EDA básica: info, describe, nulos, duplicados, etc.
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def basic_info(df: DataFrame, name: str, n_rows: int = 5) -> None:
    """
    Muestra información básica del DataFrame:
    shape, primeras filas y esquema.
    """
    n_rows_df = df.count()
    n_cols = len(df.columns)

    print(f"\n=== {name} ===")
    print(f"Shape: ({n_rows_df}, {n_cols})")

    print("\nPrimeras filas:")
    df.show(n_rows, truncate=False)

    print("\nEsquema:")
    df.printSchema()


def describe_df(df: DataFrame, name: str) -> None:
    """
    Muestra estadísticas descriptivas básicas (describe()).
    """
    print(f"\nEstadísticas descriptivas para {name}:")
    df.describe().show(truncate=False)


def report_missing(df: DataFrame, name: str) -> None:
    """
    Reporta el número y porcentaje de valores nulos por columna.
    """
    n_rows = df.count()

    nulos_expr = [
        F.sum(F.when(F.col(c).isNull(), 1).otherwise(0)).alias(c)
        for c in df.columns
    ]

    missing_values = df.agg(*nulos_expr).collect()[0]

    print(f"\nValores nulos por columna en {name}:")
    found_missing = False
    for column in df.columns:
        missing_count = missing_values[column]
        if missing_count > 0:
            porcentaje = (missing_count / n_rows) * 100 if n_rows > 0 else 0
            print(f"  {column}: {missing_count} nulos ({porcentaje:.2f}%)")
            found_missing = True

    if not found_missing:
        print(f"No hay valores nulos en el dataset {name}.")


def count_row_duplicates(df: DataFrame, name: str) -> int:
    """
    Cuenta filas duplicadas a nivel de registro completo (todas las columnas).
    """
    conteos = df.groupBy(df.columns).agg(F.count("*").alias("count"))
    duplicados_totales = conteos.withColumn("duplicated_count", F.col("count") - 1)
    num_duplicados = duplicados_totales.agg(F.sum("duplicated_count")).collect()[0][0]
    num_duplicados = num_duplicados if num_duplicados is not None else 0

    print(f"Filas duplicadas en {name}: {num_duplicados}")
    return num_duplicados

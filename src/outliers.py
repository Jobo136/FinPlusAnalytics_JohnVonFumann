"""
Detección de outliers con MAD e IQR en Spark.
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def mad_outliers_report(
    df: DataFrame,
    cols: list[str],
    name: str,
    threshold: float = 3.5,
    scale_factor: float = 1.482602218505602,
    ignore_zeros: bool = True,
) -> None:
    """
    Reporta outliers columna a columna usando MAD robusto.
    - threshold: umbral del z-score robusto.
    - ignore_zeros: si True, ignora filas con valor 0 en la columna.
    """
    df_cached = df.cache()
    print(f"\n=== Outliers MAD para {name} ===")

    for colname in cols:
        df_col = df_cached
        if ignore_zeros:
            df_col = df_col.filter(F.col(colname) != 0)

        total_col_rows = df_col.count()
        if total_col_rows == 0:
            print(f"\n⚠️ Columna {colname}: todas las filas filtradas (0 o null).")
            continue

        # Mediana
        median = df_col.select(
            F.expr(f"percentile_approx({colname}, 0.5)").alias("median")
        ).collect()[0]["median"]

        # MAD "crudo"
        mad_raw = df_col.select(
            F.expr(f"percentile_approx(ABS({colname} - {median}), 0.5)").alias("mad")
        ).collect()[0]["mad"]

        if mad_raw is None or mad_raw == 0:
            print(f"\nColumna {colname}: MAD = {mad_raw} (no se puede aplicar MAD robusto).")
            continue

        mad_scaled = mad_raw * scale_factor

        robust_z = F.abs((F.col(colname) - median) / mad_scaled)
        count_outliers = df_col.filter(robust_z > threshold).count()
        perc_outliers = (count_outliers / total_col_rows) * 100

        print(f"\n📌 Columna: {colname}")
        print(f"   - Outliers (MAD): {count_outliers} ({perc_outliers:.2f}%)")
        print(f"   - Mediana = {median}")
        print(f"   - MAD crudo = {mad_raw}")
        print(f"   - MAD escalado = {mad_scaled}")

    df_cached.unpersist()


def iqr_outliers_report(
    df: DataFrame,
    cols: list[str],
    name: str,
    factor: float = 1.5,
    sample_values: int = 50,
) -> None:
    """
    Reporta outliers columna a columna usando el criterio IQR.
    - factor: multiplicador de IQR (típico 1.5).
    - sample_values: nº de valores outliers a mostrar como ejemplo (máx).
    """
    df_cached = df.cache()
    n_rows = df_cached.count()

    print(f"\n=== Outliers IQR para {name} ===")

    for colname in cols:
        q1 = df_cached.select(F.expr(f"percentile_approx({colname}, 0.25)")).collect()[0][0]
        q3 = df_cached.select(F.expr(f"percentile_approx({colname}, 0.75)")).collect()[0][0]
        iqr = q3 - q1

        lower = q1 - factor * iqr
        upper = q3 + factor * iqr

        outliers_df = df_cached.filter(
            (F.col(colname) < lower) | (F.col(colname) > upper)
        )

        count_outliers = outliers_df.count()
        percentage_outliers = (count_outliers / n_rows) * 100 if n_rows > 0 else 0

        # Muestra solo algunos ejemplos de valores outliers
        valores = (
            outliers_df.select(colname)
            .limit(sample_values)
            .toPandas()[colname]
            .values
            if count_outliers > 0
            else []
        )

        print(f"\n📌 Columna: {colname}")
        print(f"   - Nº de outliers: {count_outliers}")
        print(f"   - Porcentaje: {percentage_outliers:.2f}%")
        print(f"   - Rango permitido: [{lower}, {upper}]")
        print(f"   - Ejemplos de valores outliers: {valores}")

    df_cached.unpersist()

"""
Funciones de limpieza específicas de datasets (CLIENTS, BEHAVIOURAL, etc.).
Ajusta columnas concretas a tus datasets reales.
"""

from pyspark.sql import DataFrame


def clean_clients(df: DataFrame) -> DataFrame:
    """
    Aplica las reglas de limpieza específicas al dataset CLIENTS:
    - Elimina filas con NA en un conjunto de columnas críticas.
    - Elimina columnas poco útiles o con demasiados nulos (ejemplo: CAR_AGE, REACTIVE_SCORING, CURRENCY).
    Ajusta la lista según las reglas que definiste en el notebook.
    """
    columnas_a_filtrar = [
        "NUM_PREVIOUS_LOAN_APP",
        "LOAN_ANNUITY_PAYMENT_MAX",
        "LOAN_ANNUITY_PAYMENT_MIN",
        "LOAN_ANNUITY_PAYMENT_SUM",
        "LOAN_APPLICATION_AMOUNT_MAX",
        "LOAN_APPLICATION_AMOUNT_MIN",
        "LOAN_APPLICATION_AMOUNT_SUM",
        "LOAN_CREDIT_GRANTED_MAX",
        "LOAN_CREDIT_GRANTED_MIN",
        "LOAN_CREDIT_GRANTED_SUM",
        "LOAN_VARIABLE_RATE_MAX",
        "LOAN_VARIABLE_RATE_MIN",
        "NUM_STATUS_ANNULLED",
        "NUM_STATUS_AUTHORIZED",
        "NUM_STATUS_DENIED",
        "NUM_STATUS_NOT_USED",
        "NUM_FLAG_INSURED",
    ]

    columnas_drop = ["CAR_AGE", "REACTIVE_SCORING", "CURRENCY"]

    before_rows = df.count()
    df_clean = df.dropna(subset=columnas_a_filtrar).drop(*columnas_drop)
    after_rows = df_clean.count()

    print("\n=== Limpieza CLIENTS ===")
    print(f"Filas iniciales: {before_rows}")
    print(f"Filas eliminadas por NA en columnas críticas: {before_rows - after_rows}")
    print(f"Filas finales: {after_rows}")
    print(f"Nº columnas finales: {len(df_clean.columns)}")

    return df_clean


def clean_behavioural(df: DataFrame) -> DataFrame:
    """
    Punto de extensión para reglas específicas de BEHAVIOURAL.
    De momento se devuelve el DF tal cual; aquí puedes meter:
    - filtros de fechas
    - eliminación de columnas redundantes
    - imputaciones, etc.
    """
    # Ejemplo: si sabes que cierta columna es completamente nula o irrelevante:
    # df = df.drop("SOME_USELESS_COLUMN")

    print("\n=== Limpieza BEHAVIOURAL (actualmente sin reglas específicas) ===")
    print(f"Filas: {df.count()}, Columnas: {len(df.columns)}")
    return df

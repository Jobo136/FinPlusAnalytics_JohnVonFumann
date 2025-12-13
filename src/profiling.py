"""Lightweight EDA/profiling for Spark DataFrames."""

from __future__ import annotations

from typing import Dict, List, Optional

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.stat import Correlation
from pyspark.sql.types import StringType, NumericType

from src.utils import print_header, shape


def show_head_and_schema(df: DataFrame, name: str, n: int = 5, truncate: bool = False) -> None:
    print_header(f"{name} - head({n})")
    df.show(n, truncate=truncate)
    print_header(f"{name} - schema")
    df.printSchema()


def describe_df(df: DataFrame, name: str) -> None:
    r, c = shape(df)
    print_header(f"{name} - describe")
    print(f"Shape: ({r}, {c})")
    df.describe().show(truncate=False)


def report_missing(df: DataFrame, name: str, total_rows: Optional[int] = None) -> Dict[str, int]:
    """Counts nulls per column in one aggregation."""
    if total_rows is None:
        total_rows = df.count()

    exprs = [F.sum(F.when(F.col(c).isNull(), 1).otherwise(0)).alias(c) for c in df.columns]
    row = df.agg(*exprs).collect()[0].asDict()

    print_header(f"{name} - missing values")
    found = False
    for c in df.columns:
        m = int(row.get(c, 0) or 0)
        if m > 0:
            found = True
            pct = (m / total_rows * 100) if total_rows else 0.0
            print(f"  {c}: {m} nulos ({pct:.2f}%)")
    if not found:
        print("No hay valores nulos.")
    return {k: int(v or 0) for k, v in row.items()}


def count_row_duplicates(df: DataFrame, name: str) -> int:
    """Equivalent to pandas duplicated().sum() for full-row duplicates."""
    conteos = df.groupBy(df.columns).agg(F.count("*").alias("count"))
    dup = conteos.withColumn("duplicated_count", F.col("count") - 1)
    num = dup.agg(F.sum("duplicated_count")).collect()[0][0]
    num = int(num or 0)

    print_header(f"{name} - row duplicates")
    print(f"Filas duplicadas: {num}")
    return num


def count_missing_or_nan(df: DataFrame, name: str) -> Dict[str, int]:
    """Counts nulls; kept to match your notebook's second missing-values block."""
    row = df.select([F.count(F.when(F.col(c).isNull(), c)).alias(c) for c in df.columns]).collect()[0].asDict()
    total = df.count()

    print_header(f"{name} - missing (alt)")
    for c, m in row.items():
        m = int(m or 0)
        pct = (m / total * 100) if total else 0.0
        print(f"{c}: {m} missing ({pct:.2f}%)")
    return {k: int(v or 0) for k, v in row.items()}


def count_zeros(df: DataFrame, name: str) -> Dict[str, int]:
    row = (
        df.select([F.count(F.when(F.col(c) == 0, c)).alias(c) for c in df.columns])
        .collect()[0]
        .asDict()
    )

    print_header(f"{name} - zeros")
    for c, z in row.items():
        print(f"{c}: {int(z or 0)} ceros")
    return {k: int(v or 0) for k, v in row.items()}


def count_distinct_row_duplicates(df: DataFrame, name: str) -> int:
    total = df.count()
    unique = df.dropDuplicates().count()
    dup = total - unique

    print_header(f"{name} - duplicates (dropDuplicates)")
    print(f"Filas duplicadas: {dup}")
    return int(dup)

# Asumo que tienes una función para obtener columnas numéricas,
# por ejemplo, de tu módulo 'outliers.py'
# from src.outliers import numeric_columns 
# from src.utils import print_header 

def get_numeric_columns(df: DataFrame) -> list[str]:
    # Placeholder si no tienes src/outliers.py
    return [f.name for f in df.schema.fields if isinstance(f.dataType, NumericType)]

def calculate_spark_stats(df: DataFrame, name: str) -> DataFrame:
    """
    Calcula estadísticas descriptivas detalladas para todas las columnas numéricas.
    (Lógica extraída de PERFILADO_SPARK.ipynb)
    """
    spark = df.sparkSession
    numeric_cols = get_numeric_columns(df) # Usar tu función real
    
    stats_list = []
    
    # describe() de Spark da min, max, mean, stddev. Se complementa con moda y mediana
    spark_stats = df.describe(*numeric_cols).collect()
    
    for c in numeric_cols:
        col_stats = {row['summary']: row[c] for row in spark_stats}
        
        # Mediana (Q50)
        # Usar approxQuantile por ser distribuido
        try:
            mediana = df.approxQuantile(c, [0.5], 0.01)[0]
        except Exception:
            mediana = None
        
        # Moda (usando groupBy para obtener el valor más frecuente)
        moda_result = df.groupBy(c).count().orderBy(F.desc('count')).limit(1).collect()
        moda = moda_result[0][c] if moda_result else None
        
        # Coeficiente de Variación (CV) = DesvStd / Media
        stddev = float(col_stats['stddev']) if 'stddev' in col_stats else 0
        mean = float(col_stats['mean']) if 'mean' in col_stats else 0
        cv = stddev / mean if mean != 0 else float('nan')
        
        # Range
        min_val = float(col_stats['min']) if 'min' in col_stats else 0
        max_val = float(col_stats['max']) if 'max' in col_stats else 0
        rango = max_val - min_val

        stats_list.append({
            "Columna": c,
            "Media": mean,
            "Mediana": mediana,
            "Moda": moda,
            "DesvStd": stddev,
            "CoefVar": cv,
            "Rango": rango,
            "Min": min_val,
            "Max": max_val,
        })

    # El esquema debe ser definido para asegurar el tipo de dato, simplificado aquí:
    # print_header(f"{name} - Estadísticas Detalladas") # Usar tu función real
    resumen_df = spark.createDataFrame(stats_list)
    resumen_df.show(truncate=False)
    return resumen_df


def report_categorical_freq(df: DataFrame, name: str, max_categories: int = 20) -> None:
    """
    Filtra y muestra la frecuencia de las columnas categóricas con N o menos categorías únicas.
    (Lógica extraída de PERFILADO_SPARK.ipynb)
    """
    string_cols = [f.name for f in df.schema.fields if isinstance(f.dataType, StringType) and f.name != 'CLIENT_ID']
    
    columnas_validas = []
    for c in string_cols:
        n_cat = df.select(F.countDistinct(c)).first()[0]
        if n_cat <= max_categories:
            columnas_validas.append(c)

    # print_header(f"{name} - Frecuencias Categóricas (<= {max_categories})") # Usar tu función real
    for c in columnas_validas:
        print(f"\n===== Frecuencia de {c} =====")
        frecuencias = (
            df.groupBy(c)
            .count()
            .orderBy(F.desc("count"))
        )
        frecuencias.show(truncate=False)

def compute_corr_matrix_and_report(df: DataFrame, df_name: str, threshold: float = 0.4) -> DataFrame:
    """
    Calcula la matriz de correlación de Pearson y reporta los pares con una correlación (|r|) 
    superior a un umbral.
    (Lógica extraída de PERFILADO_SPARK.ipynb)
    """
    spark = df.sparkSession
    numeric_cols = get_numeric_columns(df) # Usar tu función real
    
    # 1. Ensamblar el vector de features
    assembler = VectorAssembler(inputCols=numeric_cols, outputCol="features")
    vector_df = assembler.transform(df).select("features")
    
    # 2. Calcular la matriz de correlación (Pearson)
    # Correlation.corr requiere que el DF no esté vacío
    if vector_df.count() == 0:
        print(f"Advertencia: DataFrame {df_name} está vacío. No se puede calcular la correlación.")
        return spark.createDataFrame([], "Variable_A STRING, Variable_B STRING, Correlacion DOUBLE, Abs_Correlacion DOUBLE")

    matrix = Correlation.corr(vector_df, "features", "pearson").collect()[0][0]
    corr_array = matrix.toArray()
    
    # 3. Extraer pares de alta correlación
    correlacion_data = []
    for i, col1 in enumerate(numeric_cols):
        for j, col2 in enumerate(numeric_cols):
            if i < j: 
                corr_val = corr_array[i][j]
                if abs(corr_val) >= threshold:
                    correlacion_data.append(
                        (col1, col2, corr_val, abs(corr_val))
                    )
                    
    # 4. Crear un DataFrame de Spark con los resultados
    schema = ["Variable_A", "Variable_B", "Correlacion", "Abs_Correlacion"]
    correlacion_df = spark.createDataFrame(correlacion_data, schema=schema)
    
    # 5. Reportar resultados
    comb_pairs_df = correlacion_df.orderBy(F.desc("Abs_Correlacion"))
    
    # print_header(f"Correlaciones |r| >= {threshold} en {df_name}") # Usar tu función real
    comb_pairs_df.show(comb_pairs_df.count(), truncate=False)
    
    return correlacion_df

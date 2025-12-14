"""Lightweight EDA/profiling for Spark DataFrames."""

from __future__ import annotations

from typing import Dict, List, Optional

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.stat import Correlation
from pyspark.sql.types import StringType, StructType, StructField, DoubleType
from typing import List

# Importa las funciones necesarias de otros módulos
from src.outliers import numeric_columns # Para obtener la lista de columnas numéricas
from src.utils import print_header # Para formato de reporte

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
    NOTA: Se asegura que todos los valores estadísticos sean float para evitar 
    PySparkTypeError al crear el DataFrame de resumen.
    """
    spark = df.sparkSession
    numeric_cols = numeric_columns(df)
    
    if not numeric_cols:
        print_header(f"{name} - Estadísticas Detalladas")
        print("No se encontraron columnas numéricas.")
        return spark.createDataFrame([], "Columna STRING, Media DOUBLE")
        
    spark_stats = df.describe(*numeric_cols).collect()
    stats_list = []
    
    for c in numeric_cols:
        col_stats = {row['summary']: row[c] for row in spark_stats}
        
        # Mediana (Q50)
        try:
            # Resultado es float
            mediana = df.approxQuantile(c, [0.5], 0.01)[0]
        except Exception:
            mediana = None
        
        # Moda (valor más frecuente)
        moda_result = df.groupBy(c).count().orderBy(F.desc('count')).limit(1).collect()
        
        moda = None
        if moda_result:
            moda_val = moda_result[0][c]
            try:
                # FIX: Forzar a float para consistencia de tipos en el DF final
                moda = float(moda_val) 
            except (ValueError, TypeError):
                # Si es un ID muy grande o un string que se coló, se pone None
                moda = None
        
        # Los demás valores son float de describe()
        mean = float(col_stats.get('mean', 0))
        stddev = float(col_stats.get('stddev', 0))
        cv = stddev / mean if mean != 0 else float('nan')
        
        stats_list.append({
            "Columna": c,
            "Media": mean, 
            "Mediana": mediana, 
            "Moda": moda, 
            "DesvStd": stddev, 
            "CoefVar": cv, 
            "Min": float(col_stats.get('min', 0)), 
            "Max": float(col_stats.get('max', 0)), 
        })

    return spark.createDataFrame(stats_list)

def report_categorical_freq(df: DataFrame, name: str, max_categories: int = 20) -> None:
    """
    Filtra y muestra la frecuencia de las columnas categóricas con N o menos categorías únicas.
    """
    string_cols = [f.name for f in df.schema.fields if isinstance(f.dataType, StringType) and f.name != 'CLIENT_ID']
    
    columnas_validas = []
    for c in string_cols:
        n_cat = df.select(F.approx_count_distinct(c)).first()[0] 
        if n_cat <= max_categories:
            columnas_validas.append(c)

    print_header(f"{name} - Frecuencias Categóricas (<= {max_categories})")
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
    """
    spark = df.sparkSession
    numeric_cols = numeric_columns(df)
    
    # 4. Crear un esquema explícito (CORRECCIÓN CLAVE)
    # Define el esquema para que PySpark no tenga que inferir el tipo de float
    schema = StructType([
        StructField("Variable_A", StringType(), True),
        StructField("Variable_B", StringType(), True),
        StructField("Correlacion", DoubleType(), True),
        StructField("Abs_Correlacion", DoubleType(), True),
    ])

    if not numeric_cols:
        print("ADVERTENCIA: No hay columnas numéricas para calcular la correlación.")
        return spark.createDataFrame([], schema)

    # 1. Ensamblar el vector de features (rellenar nulos con 0)
    assembler = VectorAssembler(inputCols=numeric_cols, outputCol="features")
    vector_df = assembler.transform(df.na.fill(0)).select("features") 
    
    # 2. Calcular la matriz de correlación
    try:
        matrix = Correlation.corr(vector_df, "features", "pearson").collect()[0][0]
        corr_array = matrix.toArray()
    except Exception as e:
        print(f"Error al calcular la correlación: {e}")
        return spark.createDataFrame([], schema)
    
    # 3. Extraer pares de alta correlación
    correlacion_data = []
    for i, col1 in enumerate(numeric_cols):
        for j, col2 in enumerate(numeric_cols):
            if i < j: 
                corr_val = corr_array[i][j]
                if abs(corr_val) >= threshold:
                    correlacion_data.append(
                        (col1, col2, float(corr_val), float(abs(corr_val)))
                    )
                    
    # 4. Crear el DataFrame de Spark usando el esquema explícito
    correlacion_df = spark.createDataFrame(correlacion_data, schema=schema)
    
    comb_pairs_df = correlacion_df.orderBy(F.desc("Abs_Correlacion"))
    
    print_header(f"Correlaciones |r| >= {threshold} en {df_name}")
    comb_pairs_df.show(comb_pairs_df.count(), truncate=False)
    
    return correlacion_df
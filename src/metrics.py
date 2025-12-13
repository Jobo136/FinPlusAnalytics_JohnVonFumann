# src/metrics.py (NUEVO ARCHIVO)
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from typing import List

def calculate_payment_ratio(df: DataFrame) -> DataFrame:
    """
    Calcula el PAYMENT_RATIO (Pago / Balance) y maneja la división por cero/nulls.
    (Extracción de metricas.ipynb - Cell 7)
    """
    df_features = df.withColumn(
        "PAYMENT_RATIO",
        F.col("CREDIT_CARD_PAYMENT") / F.col("CREDICT_CARD_BALANCE")
    )
    
    # Si el balance es 0, el pago fue 100% sobre 0 deuda, se asume 1.0 (pago total)
    df_features = df_features.withColumn(
        "PAYMENT_RATIO",
        F.when(
            (F.col("PAYMENT_RATIO").isNull()) | (F.col("CREDICT_CARD_BALANCE") == 0), 1.0
        ).otherwise(F.col("PAYMENT_RATIO"))
    ).na.fill(0.0, subset=["PAYMENT_RATIO"])

    return df_features

def apply_cap_and_binning(df: DataFrame, num_prods_cap: int = 10) -> DataFrame:
    """
    Aplica capping a NUM_OF_PRODUCTS y crea bins para AMOUNT_PRODUCT.
    (Extracción de metricas.ipynb - Celdas 11-14)
    """
    # 1. Capping para NUM_OF_PRODUCTS
    df = df.withColumn(
        "NUMPROD_CAP",
        F.when(F.col("NUMBER_OF_PRODUCTS") > num_prods_cap, num_prods_cap)
         .otherwise(F.col("NUMBER_OF_PRODUCTS"))
    )

    # 2. Binning para AMOUNT_PRODUCT
    df = df.withColumn(
        "AMOUNT_BIN",
        F.when((F.col("AMOUNT_PRODUCT") >= 0) & (F.col("AMOUNT_PRODUCT") < 100), "0-100")
         .when((F.col("AMOUNT_PRODUCT") >= 100) & (F.col("AMOUNT_PRODUCT") < 500), "100-500")
         .when(F.col("AMOUNT_PRODUCT") >= 500, "500+")
         .otherwise("MISSING")
    )
    return df

def calculate_caq_segment(df: DataFrame, metric_cols: List[str]) -> DataFrame:
    """
    Asigna una etiqueta de segmentación CAQ (Customer Acquisition Quality) 
    basada en cuantiles (Q75) de métricas clave.
    (Extracción de metricas.ipynb - Celdas 8-10)
    """
    
    # 1. Calcular cuantiles (Q75)
    quantile_list = [0.75]
    quantiles = df.approxQuantile(metric_cols, quantile_list, 0.01)
    
    thresholds = {
        "TOTAL_INCOME": quantiles[0][0],
        "CREDIT_CARD_LIMIT": quantiles[1][0],
        "PAYMENT_RATIO": quantiles[2][0]
    }
    
    # 2. Aplicar la lógica de segmentación (CAQ Alto)
    df = df.withColumn(
        "CAQ_SEGMENT",
        F.when(
            (F.col("TOTAL_INCOME") >= thresholds["TOTAL_INCOME"]) &
            (F.col("CREDIT_CARD_LIMIT") >= thresholds["CREDIT_CARD_LIMIT"]) &
            (F.col("PAYMENT_RATIO") >= 1.0), 
            "CAQ_Alto"
        )
        .otherwise("CAQ_Normal")
    )
    
    return df
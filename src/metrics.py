# =============================================================================
# src/metrics.py (CÓDIGO FINAL CON TODAS LAS MÉTRICAS)
# =============================================================================
from pyspark.sql import DataFrame
from pyspark.sql import functions as F, Window
from typing import List

# --- PASO 1: RATIOS BÁSICOS Y UTILIZACIÓN DE CRÉDITO ---

def calculate_credit_ratios_and_utilization(df: DataFrame) -> DataFrame:
    """
    Calcula PAYMENT_RATIO (Pago/Balance), TASA PAY/DRAW (Pago/Drawings) y CUR.
    """
    # 1. PAYMENT_RATIO (Pago / Balance)
    df = df.withColumn(
        "PAYMENT_RATIO",
        F.col("CREDIT_CARD_PAYMENT") / F.col("CREDICT_CARD_BALANCE")
    ).withColumn(
        "PAYMENT_RATIO",
        F.when(
            (F.col("PAYMENT_RATIO").isNull()) | (F.col("CREDICT_CARD_BALANCE") == 0), 1.0
        ).otherwise(F.col("PAYMENT_RATIO"))
    ).na.fill(0.0, subset=["PAYMENT_RATIO"])
    
    # 2. Tasa PAY/DRAW (Pago / Drawings)
    df = df.withColumn(
        "PAY_DRAW_RATE", 
        F.when(
            (F.col("CREDIT_CARD_DRAWINGS").isNotNull()) & (F.col("CREDIT_CARD_DRAWINGS") != 0),
            F.col("CREDIT_CARD_PAYMENT") / F.col("CREDIT_CARD_DRAWINGS")
        ).otherwise(None)
    )

    # 3. CUR (Credit Utilization Ratio)
    df = df.withColumn(
        "CUR", 
        F.when(
            (F.col("CREDIT_CARD_LIMIT").isNotNull()) & (F.col("CREDIT_CARD_LIMIT") > 0),
            F.col("CREDICT_CARD_BALANCE") / F.col("CREDIT_CARD_LIMIT")
        ).otherwise(None)
    )
    return df


def calculate_risk(df: DataFrame) -> DataFrame:
    """
    Calcula el Score de Riesgo de Moroso (RM_SCORE) y el Engagement Score (SCORE_VARIEDAD).
    """
    # 1. RM Score (Riesgo de Moroso) - Fórmula de 6 banderas
    # Nota: Utiliza la columna CUR calculada en la función anterior.
    df = df.withColumn(
        "RM_SCORE",
        (
            # Punto 1: CUR ≥ 80%
            F.when(F.col("CUR") >= 0.8, 1).otherwise(0) +
            
            # Punto 2: Pago ≤ 10% del balance
            F.when(
                (F.col("CREDICT_CARD_BALANCE") > 0) &
                (F.col("CREDIT_CARD_PAYMENT") / F.col("CREDICT_CARD_BALANCE") <= 0.1), 1
            ).otherwise(0) +
            
            # Punto 3: ≥10 retiros en cajeros
            F.when(F.col("NUMBER_DRAWINGS_ATM") >= 10, 1).otherwise(0) +
            
            # Punto 4: ≥3 préstamos denegados
            F.when(F.col("NUM_STATUS_DENIED") >= 3, 1).otherwise(0) +
            
            # Punto 5: Incumplimiento de contrato
            F.when(F.col("NON_COMPLIANT_CONTRACT") == 1, 1).otherwise(0) +
            
            # Punto 6: Endeudamiento INSTALLMENT ≥ 50% de ingresos
            F.when(
                (F.col("TOTAL_INCOME") > 0) &
                (F.col("INSTALLMENT") / F.col("TOTAL_INCOME") >= 0.5), 1
            ).otherwise(0)
        )
    )
    
    
    return df


def calculate_debt_and_net_income(df: DataFrame) -> DataFrame:
    """
    Calcula Ingreso Neto después de Deuda, Tasa Debt-to-Income (DTI), y RISK_BUCKET.
    Asume que DEBT_CUMULED (deuda acumulada) existe en el DataFrame.
    """
    w = Window.partitionBy("CLIENT_ID").orderBy(F.to_date("DATE", "dd/MM/yyyy"))\
            .rowsBetween(Window.unboundedPreceding, Window.currentRow)
    
    df = df \
        .withColumn("DATE", F.to_date("DATE", "dd/MM/yyyy")) \
        .withColumn("DEBT",F.col("CREDIT_CARD_DRAWINGS")-F.col("CREDIT_CARD_PAYMENT")) \
        .withColumn("DEBT_CUMULED", F.sum("DEBT").over(w))
        

    # 1. Ingreso Neto después de Deuda
    df = df.withColumn(
        "NET_INCOME_AFTER_DEBT",
        F.col("TOTAL_INCOME") - F.col("DEBT_CUMULED")
    )
    
    # 2. Debt-to-Income (DTI)
    df = df.withColumn(
        "DEBT_TO_INCOME",
        F.when(
            (F.col("TOTAL_INCOME").isNull()) | (F.col("TOTAL_INCOME") == 0),
            None
        ).otherwise(F.col("DEBT_CUMULED") / F.col("TOTAL_INCOME"))
    )
    
    # 3. RISK_BUCKET
    df = df.withColumn(
        "RISK_BUCKET",
        F.when(F.col("DEBT_TO_INCOME").isNull(), "UNKNOWN")
         .when(F.col("DEBT_TO_INCOME") <= 0.5, "LOW")
         .when((F.col("DEBT_TO_INCOME") > 0.5) & (F.col("DEBT_TO_INCOME") <= 1.0), "MEDIUM")
         .when(F.col("DEBT_TO_INCOME") > 1.0, "HIGH")
         .otherwise("UNKNOWN")
    )
    return df


# --- FUNCIONES DE TRANSFORMACIÓN Y REPORTE (Anexadas) ---

def apply_cap_and_binning(df: DataFrame, num_prods_cap: int = 10) -> DataFrame:
    """Aplica capping a NUM_OF_PRODUCTS y crea bins para AMOUNT_PRODUCT."""
    df = df.withColumn(
        "NUMPROD_CAP",
        F.when(F.col("NUMBER_OF_PRODUCTS") > num_prods_cap, num_prods_cap)
         .otherwise(F.col("NUMBER_OF_PRODUCTS"))
    )
    df = df.withColumn(
        "AMOUNT_BIN",
        F.when((F.col("AMOUNT_PRODUCT") >= 0) & (F.col("AMOUNT_PRODUCT") < 100), "0-100")
         .when((F.col("AMOUNT_PRODUCT") >= 100) & (F.col("AMOUNT_PRODUCT") < 500), "100-500")
         .when(F.col("AMOUNT_PRODUCT") >= 500, "500+")
         .otherwise("MISSING")
    )
    return df

def calculate_caq_segment(df: DataFrame, metric_cols: List[str]) -> DataFrame:
    """Asigna una etiqueta de segmentación CAQ basada en cuantiles (Q75)."""
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

def calculate_grouped_compliance_rates(df: DataFrame, group_col: str) -> DataFrame:
    """Calcula las tasas de incumplimiento y métricas por grupo (para reporte tabular)."""
    df_report = (
        df.groupBy(group_col)
        .agg(
            F.count("*").alias("n_clients"),
            F.mean("NON_COMPLIANT_CONTRACT").alias("non_compliant_rate"),
            F.mean("AMOUNT_PRODUCT").alias("amount_mean"),
            F.approx_quantile("AMOUNT_PRODUCT", [0.5], 0.01)[0].alias("amount_median")
        )
        .orderBy(F.col("non_compliant_rate").desc())
    )
    return df_report
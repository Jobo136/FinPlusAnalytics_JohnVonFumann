from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def verify_engagement_data(df: DataFrame) -> None:
    """Verifica columnas necesarias para el análisis de engagement."""
    required = [
        "CLIENT_ID", "CREDIT_CARD_DRAWINGS_ATM", "CREDIT_CARD_DRAWINGS_POS", 
        "CREDIT_CARD_DRAWINGS_OTHER", "CREDIT_CARD_DRAWINGS", "CREDIT_CARD_PAYMENT",
        "CREDICT_CARD_BALANCE", "CREDIT_CARD_LIMIT", "NUMBER_INSTALMENTS"
    ]
    missing = [c for c in required if c not in df.columns]
    
    print("\n1. VERIFICACIÓN DE DATOS DISPONIBLES (ENGAGEMENT)")
    print("-" * 60)
    if missing:
        print(f" ADVERTENCIA: Faltan columnas: {missing}")
    else:
        print(" Todas las columnas necesarias están disponibles")
    print(f" Total registros: {df.count():,}")


def calculate_dimension_variety(df: DataFrame) -> DataFrame:
    """Calcula Dimensión 1: Variedad de Uso."""
    # Agregación por cliente
    df_var = df.groupBy("CLIENT_ID").agg(
        F.countDistinct("CREDIT_CARD_DRAWINGS_ATM", "CREDIT_CARD_DRAWINGS_POS", "CREDIT_CARD_DRAWINGS_OTHER").alias("VARIEDAD_TIPO_TRANSACCION"),
        F.when(F.sum("CREDIT_CARD_DRAWINGS_ATM") > 0, 1).otherwise(0).alias("USA_ATM"),
        F.when(F.sum("CREDIT_CARD_DRAWINGS_POS") > 0, 1).otherwise(0).alias("USA_POS"),
        F.when(F.sum("CREDIT_CARD_DRAWINGS_OTHER") > 0, 1).otherwise(0).alias("USA_OTHER"),
        F.avg("CREDIT_CARD_DRAWINGS").alias("MONTO_PROMEDIO_TRANSACCION"),
        F.when(F.sum("CREDICT_CARD_BALANCE") > 0, F.sum("CREDIT_CARD_PAYMENT") / F.sum("CREDICT_CARD_BALANCE")).otherwise(0).alias("RATIO_PAGO_VS_BALANCE")
    )
    
    # Score Variedad
    df_var = df_var.withColumn(
        "SCORE_VARIEDAD",
        (F.col("VARIEDAD_TIPO_TRANSACCION") / 3 * 25) + 
        ((F.col("USA_ATM") + F.col("USA_POS") + F.col("USA_OTHER")) * 25) + 
        (F.when(F.col("MONTO_PROMEDIO_TRANSACCION") > 100, 25).when(F.col("MONTO_PROMEDIO_TRANSACCION") > 50, 15).when(F.col("MONTO_PROMEDIO_TRANSACCION") > 10, 5).otherwise(0)) + 
        (F.when(F.col("RATIO_PAGO_VS_BALANCE") >= 0.8, 25).when(F.col("RATIO_PAGO_VS_BALANCE") >= 0.5, 15).when(F.col("RATIO_PAGO_VS_BALANCE") > 0, 5).otherwise(0))
    ).withColumn(
        "NIVEL_VARIEDAD",
        F.when(F.col("SCORE_VARIEDAD") >= 75, "ALTA VARIEDAD").when(F.col("SCORE_VARIEDAD") >= 50, "MEDIA VARIEDAD").when(F.col("SCORE_VARIEDAD") >= 25, "BAJA VARIEDAD").otherwise("SIN VARIEDAD")
    )
    return df_var


def calculate_dimension_intensity(df: DataFrame) -> DataFrame:
    """Calcula Dimensión 2: Intensidad de Uso."""
    df_int = df.groupBy("CLIENT_ID").agg(
        F.when(F.avg("CREDIT_CARD_LIMIT") > 0, F.avg("CREDICT_CARD_BALANCE") / F.avg("CREDIT_CARD_LIMIT")).otherwise(0).alias("UTILIZACION_PROMEDIO"),
        F.avg("CREDIT_CARD_DRAWINGS").alias("MONTO_PROMEDIO_USO"),
        F.when(F.sum("CREDICT_CARD_BALANCE") > 0, F.sum("CREDIT_CARD_PAYMENT") / F.sum("CREDICT_CARD_BALANCE")).otherwise(0).alias("RATIO_PAGO"),
        F.when(F.count("*") > 0, F.sum("NUMBER_INSTALMENTS") / F.count("*")).otherwise(0).alias("FRACCION_PAGOS_FRACCIONADOS")
    )
    
    # Score Intensidad
    df_int = df_int.withColumn(
        "SCORE_INTENSIDAD",
        F.when((F.col("UTILIZACION_PROMEDIO") >= 0.3) & (F.col("UTILIZACION_PROMEDIO") <= 0.7), 30).when(F.col("UTILIZACION_PROMEDIO") > 0, 15).otherwise(0) +
        F.when(F.col("MONTO_PROMEDIO_USO") >= 500, 30).when(F.col("MONTO_PROMEDIO_USO") >= 200, 20).when(F.col("MONTO_PROMEDIO_USO") >= 50, 10).otherwise(5) +
        F.when(F.col("RATIO_PAGO") >= 0.8, 40).when(F.col("RATIO_PAGO") >= 0.5, 25).when(F.col("RATIO_PAGO") > 0, 10).otherwise(0)
    ).withColumn(
        "NIVEL_INTENSIDAD",
        F.when(F.col("SCORE_INTENSIDAD") >= 80, "USO INTENSO").when(F.col("SCORE_INTENSIDAD") >= 50, "USO MODERADO").when(F.col("SCORE_INTENSIDAD") >= 20, "USO OCASIONAL").otherwise("USO MÍNIMO")
    )
    return df_int


def calculate_dimension_habits(df: DataFrame) -> DataFrame:
    """Calcula Dimensión 3: Hábitos Saludables."""
    df_hab = df.groupBy("CLIENT_ID").agg(
        F.when(F.avg("CREDICT_CARD_BALANCE") > 0, F.avg("CREDIT_CARD_PAYMENT") / F.avg("CREDICT_CARD_BALANCE")).otherwise(0).alias("RATIO_PAGO_SOBRE_BALANCE"),
        F.when(F.sum("CREDIT_CARD_DRAWINGS") > 0, F.sum("CREDIT_CARD_DRAWINGS_ATM") / F.sum("CREDIT_CARD_DRAWINGS")).otherwise(0).alias("PORCENTAJE_USO_ATM"),
        F.when(F.sum("CREDIT_CARD_DRAWINGS") > 0, F.sum("CREDIT_CARD_DRAWINGS_POS") / F.sum("CREDIT_CARD_DRAWINGS")).otherwise(0).alias("PORCENTAJE_USO_POS"),
        F.when(F.avg("CREDIT_CARD_LIMIT") > 0, F.avg("CREDICT_CARD_BALANCE") / F.avg("CREDIT_CARD_LIMIT")).otherwise(0).alias("UTILIZACION_CREDITO"),
        F.avg("NUMBER_INSTALMENTS").alias("PROMEDIO_INSTALMENTS")
    )
    
    # Score Hábitos
    df_hab = df_hab.withColumn(
        "SCORE_HABITOS_SALUDABLES",
        F.when(F.col("RATIO_PAGO_SOBRE_BALANCE") >= 0.8, 30).when(F.col("RATIO_PAGO_SOBRE_BALANCE") >= 0.5, 20).when(F.col("RATIO_PAGO_SOBRE_BALANCE") > 0.2, 10).otherwise(0) +
        F.when(F.col("PORCENTAJE_USO_ATM") < 0.3, 20).when(F.col("PORCENTAJE_USO_ATM") < 0.6, 10).otherwise(0) +
        F.when(F.col("PORCENTAJE_USO_POS") > 0.5, 20).when(F.col("PORCENTAJE_USO_POS") > 0.2, 10).otherwise(0) +
        F.when((F.col("UTILIZACION_CREDITO") >= 0.3) & (F.col("UTILIZACION_CREDITO") <= 0.7), 20).when(F.col("UTILIZACION_CREDITO") < 0.9, 10).otherwise(0) +
        F.when(F.col("PROMEDIO_INSTALMENTS") < 2, 10).when(F.col("PROMEDIO_INSTALMENTS") < 4, 5).otherwise(0)
    ).withColumn(
        "NIVEL_HABITOS",
        F.when(F.col("SCORE_HABITOS_SALUDABLES") >= 80, "HÁBITOS EXCELENTES").when(F.col("SCORE_HABITOS_SALUDABLES") >= 60, "HÁBITOS BUENOS").when(F.col("SCORE_HABITOS_SALUDABLES") >= 40, "HÁBITOS REGULARES").otherwise("HÁBITOS A MEJORAR")
    )
    return df_hab


def calculate_full_engagement_analysis(df: DataFrame) -> DataFrame:
    """Orquestador que calcula las 3 dimensiones y el score total."""
    print("="*80 + "\nANÁLISIS DE ENGAGEMENT (3 DIMENSIONES)\n" + "="*80)
    
    verify_engagement_data(df)
    
    # Calcular Dimensiones
    df_var = calculate_dimension_variety(df)
    df_int = calculate_dimension_intensity(df)
    df_hab = calculate_dimension_habits(df)
    
    # Unir resultados
    df_full = df_var.join(df_int, "CLIENT_ID", "inner").join(df_hab, "CLIENT_ID", "inner")
    
    # Score Total Ponderado
    df_full = df_full.withColumn(
        "ENGAGEMENT_SCORE_TOTAL",
        (F.col("SCORE_VARIEDAD") * 0.3) + (F.col("SCORE_INTENSIDAD") * 0.4) + (F.col("SCORE_HABITOS_SALUDABLES") * 0.3)
    ).withColumn(
        "NIVEL_ENGAGEMENT_TOTAL",
        F.when(F.col("ENGAGEMENT_SCORE_TOTAL") >= 80, "ENGAGEMENT ALTO")
         .when(F.col("ENGAGEMENT_SCORE_TOTAL") >= 60, "ENGAGEMENT MEDIO-ALTO")
         .when(F.col("ENGAGEMENT_SCORE_TOTAL") >= 40, "ENGAGEMENT MEDIO")
         .when(F.col("ENGAGEMENT_SCORE_TOTAL") >= 20, "ENGAGEMENT BAJO")
         .otherwise("ENGAGEMENT MUY BAJO")
    )
    return df_full


def join_product_info(df_final: DataFrame, df_clients: DataFrame) -> DataFrame:
    """Añade información de producto al dataframe final."""
    return df_final.join(
        df_clients.select("CLIENT_ID", F.col("NAME_PRODUCT_TYPE").alias("PRODUCT_TYPE")),
        on="CLIENT_ID", how="left"
    )


def print_engagement_report(df_eng: DataFrame) -> None:
    """Genera el reporte de texto detallado con distribuciones y top clientes."""
    total = df_eng.count()
    print(f"\n--- REPORTE DE RESULTADOS ({total:,} clientes) ---")
    
    # 1. Distribución Total
    print("\n1. DISTRIBUCIÓN ENGAGEMENT TOTAL:")
    for nivel in ["ENGAGEMENT ALTO", "ENGAGEMENT MEDIO-ALTO", "ENGAGEMENT MEDIO", "ENGAGEMENT BAJO", "ENGAGEMENT MUY BAJO"]:
        cnt = df_eng.filter(F.col("NIVEL_ENGAGEMENT_TOTAL") == nivel).count()
        print(f"   • {nivel}: {cnt:,} ({cnt/total*100:.1f}%)")
        
    # 2. Promedios
    stats = df_eng.agg(
        F.avg("ENGAGEMENT_SCORE_TOTAL").alias("TOT"),
        F.avg("SCORE_VARIEDAD").alias("VAR"),
        F.avg("SCORE_INTENSIDAD").alias("INT"),
        F.avg("SCORE_HABITOS_SALUDABLES").alias("HAB")
    ).collect()[0]
    print(f"\n2. PROMEDIOS: Total {stats['TOT']:.1f} | Var {stats['VAR']:.1f} | Int {stats['INT']:.1f} | Hab {stats['HAB']:.1f}")
    
    # 3. Top Clientes
    print("\n3. TOP 3 CLIENTES (ENGAGEMENT TOTAL):")
    df_eng.select("CLIENT_ID", "NIVEL_ENGAGEMENT_TOTAL", F.round("ENGAGEMENT_SCORE_TOTAL", 1).alias("SCORE")) \
          .orderBy(F.desc("ENGAGEMENT_SCORE_TOTAL")).limit(3).show(truncate=False)
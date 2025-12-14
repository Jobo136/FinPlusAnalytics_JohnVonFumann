# =============================================================================
# src/ml_utils.py (VERSIÓN ROBUSTA)
# =============================================================================
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.ml import Pipeline
from pyspark.ml.feature import (
    StringIndexer, 
    OneHotEncoder, 
    VectorAssembler, 
    StandardScaler
)
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.sql.types import NumericType, StringType
from typing import List, Dict, Tuple

def get_feature_columns(df: DataFrame) -> Tuple[List[str], List[str]]:
    """Identifica columnas categóricas y numéricas para el ML."""
    cat_cols = [f.name for f in df.schema.fields if isinstance(f.dataType, StringType) and f.name != 'CLIENT_ID']
    num_cols = [f.name for f in df.schema.fields if isinstance(f.dataType, NumericType) and f.name != 'CLIENT_ID']
    return cat_cols, num_cols

def create_clustering_pipeline(
    df: DataFrame, 
    k_clusters: int, 
    output_feature_col: str = "features_scaled", 
    output_prediction_col: str = "prediction" 
) -> Pipeline:
    """
    Crea el pipeline completo de preprocesamiento y KMeans.
    """
    cat_cols, num_cols = get_feature_columns(df)

    stages = []

    # 1. Preprocesamiento Categórico (solo si hay columnas)
    encoded_cat_cols = []
    if cat_cols:
        for c in cat_cols:
            indexer = StringIndexer(inputCol=c, outputCol=c + "_idx", handleInvalid="keep")
            encoder = OneHotEncoder(inputCol=c + "_idx", outputCol=c + "_vec")
            stages.extend([indexer, encoder])
            encoded_cat_cols.append(c + "_vec")

    # 2. Ensamblar Features
    assembler_inputs = encoded_cat_cols + num_cols
    assembler = VectorAssembler(
        inputCols=assembler_inputs, 
        outputCol="features_raw"
    )
    stages.append(assembler)

    # 3. Escalar Features
    scaler = StandardScaler(
        inputCol="features_raw", 
        outputCol=output_feature_col, 
        withStd=True, 
        withMean=False
    )
    stages.append(scaler)

    # 4. Modelo KMeans
    kmeans = KMeans(
        featuresCol=output_feature_col, 
        predictionCol=output_prediction_col, 
        k=k_clusters, 
        seed=42
    )
    stages.append(kmeans)

    return Pipeline(stages=stages)

def find_optimal_k(df: DataFrame, k_range: range, features_col: str = "features_scaled") -> Dict[int, float]:
    """
    Entrena el pipeline para un rango de K y calcula el Silhouette Score.
    """
    # El Evaluator busca por defecto la columna 'prediction'
    evaluator = ClusteringEvaluator(featuresCol=features_col, predictionCol="prediction")
    scores = {}
    
    for k in k_range:
        try:
            pipeline = create_clustering_pipeline(df, k)
            model = pipeline.fit(df)
            predictions = model.transform(df)
            silhouette = evaluator.evaluate(predictions)
            scores[k] = silhouette
        except Exception as e:
            print(f"Advertencia: Error calculando K={k}: {e}")
            scores[k] = -1.0
        
    return scores

def profile_clusters(df: DataFrame, segment_col: str) -> Tuple[DataFrame, DataFrame]:
    """
    Perfila los clusters. Maneja casos donde no hay columnas de un tipo específico.
    """
    cat_cols, num_cols = get_feature_columns(df)
    
    # --- 1. Perfilado Numérico (Media) ---
    valid_num_cols = [c for c in num_cols if c in df.columns and c != segment_col]
    
    if valid_num_cols:
        num_agg_exprs = [F.mean(c).alias(f"MEAN_{c}") for c in valid_num_cols]
        df_perfil_numerico = df.groupBy(segment_col).agg(*num_agg_exprs).orderBy(segment_col)
    else:
        # Si no hay numéricas, devolvemos solo los IDs de segmento
        df_perfil_numerico = df.select(segment_col).distinct().orderBy(segment_col)
    
    # --- 2. Perfilado Categórico (Moda) ---
    valid_cat_cols = [c for c in cat_cols if c in df.columns and c != segment_col]
    
    # Si no hay categóricas (tu caso actual), devolvemos un DF vacío o con solo el segmento
    if not valid_cat_cols:
        df_perfil_categorico = df.select(segment_col).distinct().orderBy(segment_col)
    else:
        try:
            # Intenta usar F.mode (Spark 3.4+)
            cat_agg_exprs = [F.mode(c).alias(f"MODE_{c}") for c in valid_cat_cols]
            df_perfil_categorico = df.groupBy(segment_col).agg(*cat_agg_exprs).orderBy(segment_col)
        except (AttributeError, Exception):
            # Fallback si falla F.mode o versión antigua de Spark
            print("Aviso: No se pudo calcular la moda categórica (F.mode no disponible).")
            df_perfil_categorico = df.select(segment_col).distinct().orderBy(segment_col)

    return df_perfil_numerico, df_perfil_categorico
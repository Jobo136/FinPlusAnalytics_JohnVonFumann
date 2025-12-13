# src/ml_utils.py (NUEVO ARCHIVO)
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.feature import (
    StringIndexer, 
    OneHotEncoder, 
    VectorAssembler, 
    StandardScaler
)
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.sql.types import NumericType, StringType
from pyspark.sql.window import Window
from typing import List, Dict

def get_feature_columns(df: DataFrame) -> tuple[List[str], List[str]]:
    """Identifica columnas categóricas y numéricas para el ML."""
    cat_cols = [f.name for f in df.schema.fields if isinstance(f.dataType, StringType) and f.name != 'CLIENT_ID']
    num_cols = [f.name for f in df.schema.fields if isinstance(f.dataType, NumericType)]
    return cat_cols, num_cols

def create_clustering_pipeline(
    df: DataFrame, 
    k_clusters: int, 
    output_feature_col: str = "features_scaled", 
    output_prediction_col: str = "cluster"
) -> Pipeline:
    """
    Crea el pipeline completo de preprocesamiento y KMeans.
    (Lógica extraída de embedding_ml.ipynb)
    """
    cat_cols, num_cols = get_feature_columns(df)

    # 1. Preprocesamiento Categórico
    indexers = [
        StringIndexer(inputCol=c, outputCol=c + "_idx", handleInvalid="keep")
        for c in cat_cols
    ]
    encoders = [
        OneHotEncoder(inputCol=c + "_idx", outputCol=c + "_vec") 
        for c in cat_cols
    ]

    # 2. Ensamblar Features
    assembler_inputs = [c + "_vec" for c in cat_cols] + num_cols
    assembler = VectorAssembler(
        inputCols=assembler_inputs, 
        outputCol="features_raw"
    )

    # 3. Escalar Features
    scaler = StandardScaler(
        inputCol="features_raw", 
        outputCol=output_feature_col, 
        withStd=True, 
        withMean=False
    )

    # 4. Modelo KMeans
    kmeans = KMeans(
        featuresCol=output_feature_col, 
        predictionCol=output_prediction_col, 
        k=k_clusters, 
        seed=42
    )

    # 5. Crear Pipeline
    pipeline_stages = indexers + encoders + [assembler, scaler, kmeans]
    pipeline = Pipeline(stages=pipeline_stages)
    
    return pipeline

def find_optimal_k(df: DataFrame, k_range: range, features_col: str = "features_scaled") -> Dict[int, float]:
    """
    Entrena el pipeline para un rango de K y calcula el Silhouette Score.
    (Lógica extraída de embedding_ml.ipynb)
    """
    evaluator = ClusteringEvaluator(featuresCol=features_col)
    scores = {}
    
    for k in k_range:
        pipeline = create_clustering_pipeline(df, k)
        model = pipeline.fit(df)
        predictions = model.transform(df)
        silhouette = evaluator.evaluate(predictions)
        scores[k] = silhouette
        
    return scores

def profile_clusters(df: DataFrame, segment_col: str) -> tuple[DataFrame, DataFrame]:
    """
    Perfila los clusters calculando la media de las variables numéricas y la moda 
    de las categóricas por segmento.
    (Lógica extraída de embedding_ml.ipynb)
    """
    cat_cols, num_cols = get_feature_columns(df)
    
    # 1. Perfilado Numérico (Media)
    num_agg_exprs = [F.mean(c).alias(f"MEAN_{c}") for c in num_cols]
    df_perfil_numerico = (
        df.groupBy(segment_col)
        .agg(*num_agg_exprs)
        .orderBy(segment_col)
    )
    
    # 2. Perfilado Categórico (Moda: usando la función F.mode de PySpark 3.4+ o el enfoque de ventana)
    
    # Usando F.mode() (si tu versión de PySpark lo soporta)
    cat_agg_exprs = [F.mode(c).alias(f"MODE_{c}") for c in cat_cols]
    df_perfil_categorico = (
        df.groupBy(segment_col)
        .agg(*cat_agg_exprs)
        .orderBy(segment_col)
    )

    # Si tu versión de PySpark no tiene F.mode(), reemplaza con la lógica de ventana o el join.

    return df_perfil_numerico, df_perfil_categorico
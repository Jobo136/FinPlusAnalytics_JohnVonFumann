# src/reporting.py (NUEVO ARCHIVO)
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
# from src.utils import print_header # Asumo que existe

def generate_pivot_and_heatmap(
    df: DataFrame, 
    index_col: str, 
    columns_col: str, 
    value_col: str, 
    title: str
) -> None:
    """
    Agrupa un DF, crea una tabla pivote en Pandas, y genera un heatmap.
    (Extracción de metricas.ipynb - Celdas 16-17)
    """
    # print_header(f"Generando Heatmap: {title}") # Usar tu función real
    
    # 1. Agrupar en Spark
    pdf_pivot = df.groupBy(index_col, columns_col).agg(
        F.mean(value_col).alias("rate")
    ).toPandas() # CUIDADO: Cargar a Pandas.

    if not pdf_pivot.empty:
        # 2. Pivotar en Pandas
        pivot_table = pdf_pivot.pivot(
            index=index_col, 
            columns=columns_col, 
            values="rate"
        ).fillna(0)
        
        # 3. Generar Heatmap con Matplotlib
        plt.figure(figsize=(12,6))
        plt.imshow(pivot_table.values, aspect="auto", interpolation='nearest', cmap='viridis')
        plt.title(title)
        plt.xlabel(columns_col)
        plt.ylabel(index_col)
        
        # Configurar ticks
        plt.xticks(ticks=np.arange(pivot_table.shape[1]), labels=pivot_table.columns, rotation=60, ha="right")
        plt.yticks(ticks=np.arange(pivot_table.shape[0]), labels=pivot_table.index)
        
        plt.colorbar(label=value_col.replace('_', ' ').upper())
        
        plt.tight_layout()
        plt.show()
    else:
        print("Advertencia: El DataFrame pivotado está vacío. No se generó el Heatmap.")
# src/data_split.py (NUEVO ARCHIVO)
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from typing import Dict

def get_client_id_sets(df_beh: DataFrame, df_cli: DataFrame) -> Dict[str, DataFrame]:
    """
    Calcula y retorna los conjuntos de CLIENT_ID comunes, solo en clientes, y solo en behavioural.
    (Extracción de Separación_datasets.ipynb)
    """
    ids_beh = df_beh.select("CLIENT_ID").distinct()
    ids_cli = df_cli.select("CLIENT_ID").distinct()
    
    ids_comunes = ids_beh.intersect(ids_cli)
    ids_solo_cli = ids_cli.join(ids_beh, "CLIENT_ID", "left_anti")
    ids_solo_beh = ids_beh.join(ids_cli, "CLIENT_ID", "left_anti")
    
    print(f"IDs Clientes (únicos): {ids_cli.count()}")
    print(f"IDs Behavioral (únicos): {ids_beh.count()}")
    print(f"IDs Comunes: {ids_comunes.count()}")
    
    return {
        "comunes": ids_comunes,
        "solo_cli": ids_solo_cli,
        "solo_beh": ids_solo_beh
    }

def align_and_join_datasets(df_beh: DataFrame, df_cli: DataFrame) -> DataFrame:
    """
    Realiza un INNER JOIN de los datasets clientes y behavioural por CLIENT_ID.
    Asume que en df_beh hay columnas que deben ser dropeadas para evitar duplicados en el join (ej. 'CONTRACT_ID', 'DATE').
    (Lógica central de Separación_datasets.ipynb)
    """
    # Se dropean columnas en df_beh que probablemente causen problemas o son redundantes con df_cli
    df_beh_dropped = df_beh.drop('CONTRACT_ID') 
    
    # Join
    df_comunes_final = df_cli.join(
        df_beh_dropped, 
        on="CLIENT_ID", 
        how="inner"
    )

    return df_comunes_final


def get_solo_datasets(df_beh: DataFrame, df_cli: DataFrame) -> list[DataFrame, DataFrame]:
    """
    Retorna los DataFrames completos que representan:
    1. df_cli filtrado por IDs sin actividad (Solo Clientes).
    2. df_beh filtrado por IDs sin datos de cliente (Solo Behavioral).
    """
    solo_ids = get_client_id_sets(df_beh, df_cli)
    
    # Clientes Solos (DF CLIENTS completo filtrado por IDs únicos)
    df_solo_cli = df_cli.join(solo_ids['solo_cli'], "CLIENT_ID", "inner")
    
    # Behavioral Solo (DF BEHAVIORAL completo filtrado por IDs únicos)
    df_solo_beh = df_beh.join(solo_ids['solo_beh'], "CLIENT_ID", "inner")
    
    return df_solo_cli, df_solo_beh
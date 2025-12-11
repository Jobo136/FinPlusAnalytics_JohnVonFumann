"""
Utilidades genéricas de apoyo (no específicas de EDA).
"""

from pyspark.sql import DataFrame
from pyspark.sql.types import NumericType


def get_numeric_columns(df: DataFrame) -> list[str]:
    """
    Devuelve una lista con los nombres de las columnas numéricas de un DataFrame de Spark.
    """
    return [
        field.name
        for field in df.schema.fields
        if isinstance(field.dataType, NumericType)
    ]

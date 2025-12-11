from pathlib import Path
from pyspark.sql import SparkSession


# Ruta base del proyecto (ajusta según tu entorno)
PROJECT_ROOT = Path("/home/jovyan/work")
DATA_DIR = PROJECT_ROOT / "data"

# Rutas de datos (ajusta nombres de carpetas/archivos si hace falta)
BEHAVIOURAL_PATH = DATA_DIR / "BEHAVIOURAL"
CLIENTS_PATH = DATA_DIR / "CLIENTS"

# Rutas de salida recomendadas
OUTPUT_DIR = DATA_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_spark_session(app_name: str = "FinPlus EDA") -> SparkSession:
    """
    Crea y devuelve una SparkSession básica.
    Ajusta aquí configuración de memoria, shuffle partitions, etc., si lo necesitas.
    """
    spark = (
        SparkSession.builder
        .appName(app_name)
        .getOrCreate()
    )
    return spark

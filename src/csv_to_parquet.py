from pathlib import Path
from pyspark.sql import SparkSession

def convert_csv_to_parquet_spark(
        spark: SparkSession,
        input_csv: str | Path,
        output_parquet: str | Path | None = None,
        header: bool = True,
        infer_schema: bool = True,
        repartition: int | None = None,
        single_file: bool = False,
        data_dir: str | Path = "/home/jovyan/work/data/",
) -> str:

    """
    Convierte un CSV a Parquet usando PySpark sin cargar todo en memoria.

    - spark: SparkSession ya creada
    - input_csv: nombre o ruta del CSV (relativa a data_dir si no es absoluta)
    - output_parquet: nombre o ruta de la carpeta Parquet (por defecto, mismo nombre con .parquet)
    - header: si la primera fila es cabecera
    - infer_schema: si Spark debe inferir los tipos
    - repartition: nº de particiones para el Parquet (opcional)
    - data_dir: carpeta base donde están los datos (por defecto /data en Docker)
    """
    data_dir = Path(data_dir)

    csv_path = Path(input_csv)
    if not csv_path.is_absolute():
        csv_path = data_dir / csv_path

    if output_parquet is None:
        parquet_path = csv_path.with_suffix(".parquet")
    else:
        parquet_path = Path(output_parquet)
        if not parquet_path.is_absolute():
            parquet_path = data_dir / parquet_path

    print(f"📥 CSV de entrada : {csv_path}")
    print(f"📤 Parquet salida: {parquet_path}")

    if not csv_path.exists():
        raise FileNotFoundError(f"No encuentro el archivo CSV: {csv_path}")

    # Leer CSV con Spark
    df = (
        spark.read
        .option("header", "true" if header else "false")
        .option("inferSchema", "true" if infer_schema else "false")
        .csv(str(csv_path))
    )

    print(f"🔹 DataFrame leído con {df.count()} filas y {len(df.columns)} columnas")

    if repartition is not None:
        print(f"🔹 Reparticionando a {repartition} particiones")
        df = df.repartition(repartition)

    if single_file:
        print("🔹 Uniendo la salida en un único archivo Parquet con coalesce(1)")
        df = df.coalesce(1)
        
    # Escribir a Parquet
    (
        df.write
        .mode("overwrite")
        .parquet(str(parquet_path))
    )

    print("✅ Conversión a Parquet terminada.")
    return str(parquet_path)

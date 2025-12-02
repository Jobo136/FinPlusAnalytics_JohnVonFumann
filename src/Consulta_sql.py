def create_temp_views(spark_session, df_clients, df_behaviour):
    """Crea vistas SQL temporales para que Spark SQL pueda consultarlas."""
    # Las mayúsculas son clave: las vistas son 'clients' y 'behaviour'
    df_clients.createOrReplaceTempView("clients")
    df_behaviour.createOrReplaceTempView("behaviour")
    print("Vistas SQL 'clients' y 'behaviour' creadas.")


def get_dynamic_segmentation_query(requested_columns: list):
    """
    Retorna una consulta SQL dinámica, uniendo 'clients' y 'behaviour',
    incluyendo solo las columnas solicitadas.
    """
    # 1. Mapeo de columnas a su origen (para resolver ambigüedades)
    # Debes saber qué columna pertenece a qué vista (tabla).
    COLUMN_MAP = {
        "CLIENT_ID": "c.CLIENT_ID",
    }
    
    # 2. Construir la cláusula SELECT
    select_parts = []
    
    # El CLIENT_ID es obligatorio para el JOIN, pero también puede ser solicitado
    if "CLIENT_ID" not in requested_columns:
        # Si no se pide, se incluye solo para el join (no se selecciona al final)
        pass # En este caso, lo incluiremos siempre al inicio para simplificar el ejemplo.

    for col_name in requested_columns:
        if col_name in COLUMN_MAP:
            # Añadir la columna con su alias de tabla (ej: 'c.AGE_IN_YEARS')
            select_parts.append(COLUMN_MAP[col_name])
        else:
            print(f"ADVERTENCIA: Columna '{col_name}' no encontrada en el mapeo.")

    # Si no se solicitó ninguna columna válida, se selecciona * por defecto
    if not select_parts:
        return "SELECT * FROM clients c LEFT JOIN behaviour b ON c.CLIENT_ID = b.CLIENT_ID LIMIT 10"

    # Unir las partes con coma para la cláusula SELECT
    select_clause = ",\n        ".join(select_parts)
    
    # 3. Construir la consulta final
    query = f"""
    SELECT 
        {select_clause}
    FROM clients c        
    LEFT JOIN behaviour b
    ON c.CLIENT_ID = b.CLIENT_ID
    LIMIT 20
    """
    return query
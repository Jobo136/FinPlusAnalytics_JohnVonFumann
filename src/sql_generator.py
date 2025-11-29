# /src/sql_generator.py

def create_temp_views(spark_session, df_clients, df_behaviour):
    """Crea vistas SQL temporales para que Spark SQL pueda consultarlas."""
    df_clients.createOrReplaceTempView("clients")
    df_behaviour.createOrReplaceTempView("behaviour")
    print("Vistas SQL 'clients' y 'behaviour' creadas.")

# /src/sql_generator.py - ¡CORRECCIÓN CON MAYÚSCULAS EXACTAS!

def get_base_segmentation_query():
    """Retorna la consulta SQL limpia."""
    query = """
    SELECT 
        c.CLIENT_ID,        
        c.AGE_IN_YEARS,     
        b.CREDICT_CARD_BALANCE,  
        b.CREDIT_CARD_PAYMENT  
    FROM clients c        
    LEFT JOIN behaviour b
    ON c.CLIENT_ID = b.CLIENT_ID
    LIMIT 10
    """
    return query
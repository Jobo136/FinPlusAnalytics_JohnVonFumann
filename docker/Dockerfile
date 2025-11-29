# /docker/Dockerfile
# Usamos tu imagen base, que ya tiene Java, Spark y Jupyter
FROM jupyter/pyspark-notebook:latest

# Instalar dependencias adicionales si lo necesitas
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# =========================================================
# MODIFICACIÓN CLAVE: Iniciar Jupyter sin token/contraseña
# Esto elimina el error '403 Forbidden' y permite acceso directo
# Nota: La imagen base ya define SPARK_HOME, no necesitamos ajustarlo
# =========================================================
# Reemplazar el comando por defecto (CMD) por uno sin token/password
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--ServerApp.token=''", "--ServerApp.password=''"]
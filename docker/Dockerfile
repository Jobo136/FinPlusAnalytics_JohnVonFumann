# Imagen base con Python
FROM python:3.11-slim

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    wget \
    curl \
    && apt-get clean

# Configurar JAVA para PySpark
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:${PATH}"

# Crear directorios
WORKDIR /app

# Copiar dependencias
COPY requirements.txt /app/requirements.txt

# Instalar Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Crear carpeta de trabajo conectada al host
RUN mkdir /workspace
WORKDIR /workspace

# Exponer puertos
EXPOSE 8888 4040

# Comando por defecto: lanzar jupyter
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]

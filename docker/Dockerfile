# Usamos una imagen base que incluye Python y Java JRE/JDK,
# y usamos la variante "slim" que es más ligera y menos propensa
# a problemas de manejo de paquetes del sistema.
FROM eclipse-temurin:17-jdk-jammy

# Instalar las dependencias esenciales de Python
# La imagen base ya trae una versión de Python, pero nos aseguramos de tener pip.
RUN apt-get update && \
    apt-get install -y python3-pip python3-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copiar requirements y crear el directorio de la aplicación
WORKDIR /app
COPY requirements.txt .

# Instalar dependencias Python (incluye PySpark).
# Usamos --no-cache-dir para mantener la imagen pequeña.
RUN pip3 install --no-cache-dir -r requirements.txt

# Configurar el directorio de trabajo para tus scripts/notebooks
WORKDIR /workspace

# Puertos
EXPOSE 8888 4040

# Comando para iniciar Jupyter Lab
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
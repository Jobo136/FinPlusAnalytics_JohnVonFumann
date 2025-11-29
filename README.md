# Entorno Docker del proyecto FinPlus

## Requisitos
- Docker >= 20
- docker-compose >= 1.29

## Construcción del entorno
cd docker
docker-compose build

## Ejecución
docker-compose up

El entorno lanza:
- JupyterLab en http://localhost:8888
- Spark UI en http://localhost:4040

Los notebooks se guardan en `notebooks/`
Los datos en `data/`
El código ETL en `src/`

Todo el pipeline ETL debe ejecutarse dentro de Docker.
╔══════════════════════════════════╗
║   █████╗ ██╗   ██╗ ███████╗      ║
║       ██║ ██║   ██║ ██╔════╝     ║
║       ██║ ██║   ██║ █████╗       ║
║ ██╗   ██║ ╚██╗ ██╔╝ ██╔══╝       ║
║ ╚█████╔╝    ╚████╔╝  ██║         ║ Jhon Von Fumann. SL
║  ╚════╝      ╚═══╝   ╚═╝         ║ © 2025 Aritz (Co-founder), Ángela (Co-founder), Javier (Co-founder) y Andrés(Co-founder).
╚══════════════════════════════════╝ All Rights Reserved





# FinPlus Analytics Challenge: Evaluación de Riesgos y Scoring de Engagement

## Resumen del Proyecto

Este proyecto implementa un pipeline de Big Data *end-to-end* diseñado para el sector bancario. Su objetivo principal es procesar grandes volúmenes de datos transaccionales y demográficos para generar *insights* accionables sobre el Riesgo Crediticio y la Vinculación (Engagement) del cliente.

El sistema utiliza **Apache Spark** para el procesamiento distribuido de datos, abarcando todo el ciclo de vida de la ingeniería de datos: desde la ingesta y limpieza hasta la ingeniería de características (*feature engineering*) y el aprendizaje automático no supervisado (*Clustering*).

Los puntos centrales de este framework son:
1.  **Motor de Riesgo:** Un sistema de puntuación calculado para identificar posibles morosos y perfiles de alto riesgo basado en la utilización del crédito y comportamientos de pago.
2.  **Scoring de Engagement:** Un análisis multidimensional (Variedad, Intensidad, Hábitos) para cuantificar la lealtad del cliente y sus patrones de uso.
3.  **Segmentación de Clientes:** Un modelo de agrupamiento automatizado (K-Means) para identificar perfiles de comportamiento distintos para la toma de decisiones estratégicas.

## Arquitectura del Proyecto y Flujo de Datos

El flujo de procesamiento de datos se organiza secuencialmente a través de una serie de etapas orquestadas. La estructura del pipeline se define de la siguiente manera:

1.  **Ingesta y Optimización:** Conversión de conjuntos de datos CSV crudos a formato columnar Parquet para optimizar el almacenamiento y el rendimiento de Entrada/Salida.
2.  **Análisis Exploratorio de Datos (EDA) y Calidad:** Perfilado automatizado, detección de valores atípicos (utilizando métodos MAD e IQR) y verificaciones de integridad de datos.
3.  **Integración de Datos:** Lógica para la fusión y separación del conjuntos de datos heterogéneos (Demográficos y Comportamentales).
4.  **Ingeniería de Características (Feature Engineering):**
    * Cálculo de ratios financieros (Ratio de Pago, Ratio de Utilización de Crédito, Deuda-Ingreso).
    * Generación de indicadores de negocio sintéticos (Segmentación CAQ, Buckets de Riesgo).
5.  **Machine Learning:** Implementación de un Pipeline de Clustering utilizando PySpark MLlib para segmentar la base de clientes basándose en las características generadas.

## Estructura del Repositorio

El repositorio está organizado en los siguientes directorios:

* **`dashboards/`**: Contiene archivos de configuración y definiciones para paneles de visualización.
* **`data/`**: Almacenamiento local para conjuntos de datos.
* **`docker/`**: Lógica de contenedorización, incluyendo `Dockerfile` y `docker-compose.yml` para configurar el entorno de Spark y Jupyter.
* **`docs/`**: PDFs con los tres primero entregables. En estos documentos entra en profundida en el ánalisis del negocio, diseño del proyecto y el historial de commits de GIT.
* **`notebooks/`**: Cuadernos Jupyter secuenciales correspondientes a las etapas del pipeline (01 a 06).
* **`src/`**: Biblioteca de código fuente principal que contiene módulos reutilizables para el pipeline. En su interior contiene `00_diccionario_funciones.txt` donde contiene un rapida guía para encontrar y entender cada función.


## Prerrequisitos e Instalación

Para desplegar y ejecutar este proyecto, se requieren las siguientes dependencias:

* **Docker Desktop**
* **Python 3.8+**
* **Apache Spark 3.x**

### Instrucciones de Configuración

1.  Clonar el repositorio:
    ```bash
    git clone [https://github.com/Jobo136/FinPlusAnalytics_JohnVonFumann.git](https://github.com/Jobo136/FinPlusAnalytics_JohnVonFumann.git)
    cd FinPlusAnalytics_JohnVonFumann
    ```

2.  Construir y ejecutar el entorno Docker (si aplica):
    ```bash
    cd docker
    docker-compose up -d
    ```

3.  Alternativamente, instalar dependencias locales:
    ```bash
    pip install -r requirements.txt
    ```

4.  Configuración:
    Revise `src/config.py` para asegurar que las rutas de datos locales coincidan con la estructura de su entorno. En principio todas las rutas son las de los volumenes de docker solo cambiar las rutas en caso de querer ejecutar el programa localmente.

## Orden de Ejecución

El pipeline está diseñado para ejecutarse secuencialmente a través de los cuadernos ubicados en el directorio `notebooks/`:

1.  `01_INGESTA_PIPELINE.ipynb`
2.  `02_EDA_PIPELINE.ipynb`
3.  `03_SEPARACIÓN_DATASETS_PIPELINE.ipynb`
4.  `04_PERFILADO_AVANZADO_PIPELINE.ipynb`
5.  `05_MÉTRICAS_PIPELINE.ipynb`
6.  `06_ANÁLISIS_AVANZADO_PIPELINE.ipynb`
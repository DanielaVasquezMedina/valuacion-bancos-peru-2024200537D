# Nombres y apellidos: Daniela Andrea Vasquez Medina
# Código de matrícula: 2024200537D
# Tema N.º 47: Valuación relativa de los bancos peruanos listados en bolsa
# Fecha de extracción: 2026-09-24

"""
01_extraccion_api.py

Este script se encarga de extraer datos históricos de precios y splits de acciones
de bancos peruanos listados en la Bolsa de Valores de Lima (BVL) utilizando
la API de Yahoo Finance a través de la librería `yfinance`. Los datos son
guardados en formato CSV, tal como se reciben de la API, en la carpeta
`datos_crudos` para su posterior procesamiento.

Fuente: Yahoo Finance (vía `yfinance`)
Método: `Ticker.history`
Contenido: Precios diarios (apertura, máximo, mínimo, cierre), volumen y splits.
"""

# ---------- BLOQUE 1: librerías ----------
# Importa las librerías necesarias para la ejecución del script.
import os            # Para interactuar con el sistema operativo (e.g., manejo de rutas y directorios).
import time          # Para introducir pausas en la ejecución y evitar saturar la API.
from datetime import datetime  # Para trabajar con fechas y horas.
from zoneinfo import ZoneInfo  # Para manejar zonas horarias, asegurando consistencia en los registros de tiempo.

import pandas as pd  # Para manipulación y análisis de datos, especialmente con DataFrames.
import yfinance as yf  # Librería para descargar datos financieros de Yahoo Finance.

# ---------- BLOQUE 2: parámetros congelados (no usar fechas dinámicas) ----------
# Define las constantes y parámetros clave para la extracción de datos.
CODIGO = "2024200537D"  # Código de matrícula o identificador del usuario/proyecto.
FECHA_INICIO = "2010-01-01"  # Fecha de inicio del período de extracción de datos históricos (incluida).
FECHA_CORTE = "2025-12-31"            # Fecha de corte (último día incluido) para la extracción de datos de precios.
TICKERS = {  # Diccionario de tickers de las acciones de los bancos y sus nombres.
    "BBVAC1.LM": "BBVA Perú",
    "CREDITC1.LM": "BCP",
    "SCOTIAC1.LM": "Scotiabank Perú",
    "INTERBC1.LM": "Interbank",
}
PAUSA_SEGUNDOS = 1                    # Duración de la pausa en segundos entre cada solicitud a la API para evitar bloqueos.

# ---------- BLOQUE 3: rutas relativas ----------
# Define las rutas de las carpetas y archivos donde se guardarán los datos crudos y el log.
CARPETA_CRUDOS = "datos_crudos"  # Nombre de la carpeta principal para almacenar los datos brutos.
# Rutas completas a los archivos CSV donde se guardarán los precios y los splits.
ARCHIVO_PRECIOS = os.path.join(CARPETA_CRUDOS, f"datos_crudos_yahoo_{CODIGO}.csv")
ARCHIVO_SPLITS = os.path.join(CARPETA_CRUDOS, f"splits_yahoo_{CODIGO}.csv")
ARCHIVO_LOG = "log_ejecucion.txt"  # Nombre del archivo de log para registrar el progreso y errores.
# Crea la carpeta de datos crudos si no existe, asegurando que el script pueda escribir en ella.
os.makedirs(CARPETA_CRUDOS, exist_ok=True)

# ---------- BLOQUE 4: registro de la ejecución (log) ----------
def registrar(mensaje):
    """Escribe el mensaje con fecha y hora en pantalla y en log_ejecucion.txt.

    Registra un mensaje, añadiendo la fecha y hora actual (zona horaria de Lima)
    tanto a la consola como a un archivo de log (`log_ejecucion.txt`).
    Esto es útil para depuración y seguimiento del proceso.
    """
    ahora = datetime.now(ZoneInfo("America/Lima")).strftime('%Y-%m-%d %H:%M:%S')
    linea = f"[{ahora} hora de Lima] [01_API] {mensaje}"
    print(linea)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
        f.write(linea + "\n")

# ---------- BLOQUE 5: extracción desde la API ----------
# Prepara y ejecuta la extracción de datos históricos de precios y splits para cada ticker.
# yfinance excluye la fecha 'end', por eso se suma un día a FECHA_CORTE para incluirla.
fin_exclusivo = (pd.Timestamp(FECHA_CORTE) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
registrar(f"Inicio | yfinance {yf.__version__} | periodo {FECHA_INICIO} a {FECHA_CORTE}")

tablas_precios = []  # Lista para almacenar los DataFrames de precios de cada ticker.
tablas_splits = []   # Lista para almacenar los DataFrames de splits de cada ticker.

for ticker, banco in TICKERS.items():
    try:
        accion = yf.Ticker(ticker)  # Crea un objeto Ticker para el símbolo de la acción actual.
        # Descarga el historial de precios. auto_adjust=False mantiene los precios tal cual,
        # sin ajustes automáticos por dividendos, y actions=True incluye eventos como splits y dividendos.
        hist = accion.history(start=FECHA_INICIO, end=fin_exclusivo,
                              auto_adjust=False, actions=True)
        if hist.empty:
            registrar(f"{ticker}: ERROR - la API no devolvió datos")
        else:
            hist = hist.reset_index()  # Convierte el índice de fecha en una columna regular.
            hist.insert(0, "ticker", ticker)  # Añade la columna 'ticker' al inicio del DataFrame.
            hist.insert(1, "banco", banco)    # Añade la columna 'banco' al inicio del DataFrame.
            tablas_precios.append(hist)        # Añade el DataFrame de historial a la lista.
            registrar(f"{ticker}: OK - {len(hist)} filas "
                      f"({hist['Date'].min().date()} a {hist['Date'].max().date()})")

        # Extrae la lista COMPLETA de splits para el ticker, hasta el día de la extracción.
        splits = accion.splits.reset_index()
        splits.columns = ["fecha", "factor"]  # Renombra las columnas para mayor claridad.
        splits.insert(0, "ticker", ticker)    # Añade la columna 'ticker' al inicio del DataFrame.
        tablas_splits.append(splits)          # Añade el DataFrame de splits a la lista.
        registrar(f"{ticker}: {len(splits)} splits registrados en total")
    except Exception as error:
        registrar(f"{ticker}: ERROR - {error}") # Registra cualquier error que ocurra durante la extracción.
    time.sleep(PAUSA_SEGUNDOS)  # Pausa para respetar los límites de la API.

# ---------- BLOQUE 6: guardar los datos crudos sin modificar ----------
# Concatena y guarda todos los datos extraídos en archivos CSV separados.
if tablas_precios:
    # Concatena todos los DataFrames de precios y los guarda en un CSV.
    pd.concat(tablas_precios, ignore_index=True).to_csv(ARCHIVO_PRECIOS, index=False)
    registrar(f"Guardado: {ARCHIVO_PRECIOS}")
if tablas_splits:
    # Concatena todos los DataFrames de splits y los guarda en un CSV.
    pd.concat(tablas_splits, ignore_index=True).to_csv(ARCHIVO_SPLITS, index=False)
    registrar(f"Guardado: {ARCHIVO_SPLITS}")
registrar("Fin del script 01")

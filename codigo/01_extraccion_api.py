# Nombres y apellidos: Daniela Andrea Vasquez Medina
# Código de matrícula: 2024200537D
# Tema N.º 47: Valuación relativa de los bancos peruanos listados en bolsa (S06 Valuación de acciones)
# Fecha de extracción: 2026-09-24

"""
01_extraccion_api.py
Fuente: Yahoo Finance, consultada como API mediante la librería yfinance
(método Ticker.history). Extrae precios diarios, volumen y splits de las
acciones de cuatro bancos peruanos listados en la BVL y los guarda tal como
llegan, sin modificarlos, en la carpeta datos_crudos.
"""

# ---------- BLOQUE 1: librerías ----------
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

# ---------- BLOQUE 2: parámetros congelados (no usar fechas dinámicas) ----------
CODIGO = "2024200537D"
FECHA_INICIO = "2010-01-01"
FECHA_CORTE = "2025-12-31"            # último día incluido en la consulta
TICKERS = {
    "BBVAC1.LM": "BBVA Perú",
    "CREDITC1.LM": "BCP",
    "SCOTIAC1.LM": "Scotiabank Perú",
    "INTERBC1.LM": "Interbank",
}
PAUSA_SEGUNDOS = 1                    # pausa entre solicitudes

# ---------- BLOQUE 3: rutas relativas ----------
CARPETA_CRUDOS = "datos_crudos"
ARCHIVO_PRECIOS = os.path.join(CARPETA_CRUDOS, f"datos_crudos_yahoo_{CODIGO}.csv")
ARCHIVO_SPLITS = os.path.join(CARPETA_CRUDOS, f"splits_yahoo_{CODIGO}.csv")
ARCHIVO_LOG = "log_ejecucion.txt"
os.makedirs(CARPETA_CRUDOS, exist_ok=True)

# ---------- BLOQUE 4: registro de la ejecución (log) ----------
def registrar(mensaje):
    """Escribe el mensaje con fecha y hora en pantalla y en log_ejecucion.txt."""
    ahora = datetime.now(ZoneInfo("America/Lima")).strftime('%Y-%m-%d %H:%M:%S')
    linea = f"[{ahora} hora de Lima] [01_API] {mensaje}"
    print(linea)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
        f.write(linea + "\n")

# ---------- BLOQUE 5: extracción desde la API ----------
# yfinance excluye la fecha 'end', por eso se suma un día a FECHA_CORTE
fin_exclusivo = (pd.Timestamp(FECHA_CORTE) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
registrar(f"Inicio | yfinance {yf.__version__} | periodo {FECHA_INICIO} a {FECHA_CORTE}")

tablas_precios = []
tablas_splits = []

for ticker, banco in TICKERS.items():
    try:
        accion = yf.Ticker(ticker)
        # precios sin ajuste por dividendos (auto_adjust=False) e incluyendo eventos
        hist = accion.history(start=FECHA_INICIO, end=fin_exclusivo,
                              auto_adjust=False, actions=True)
        if hist.empty:
            registrar(f"{ticker}: ERROR - la API no devolvió datos")
        else:
            hist = hist.reset_index()
            hist.insert(0, "ticker", ticker)
            hist.insert(1, "banco", banco)
            tablas_precios.append(hist)
            registrar(f"{ticker}: OK - {len(hist)} filas "
                      f"({hist['Date'].min().date()} a {hist['Date'].max().date()})")

        # lista COMPLETA de splits hasta el día de la extracción (incluye 2026)
        splits = accion.splits.reset_index()
        splits.columns = ["fecha", "factor"]
        splits.insert(0, "ticker", ticker)
        tablas_splits.append(splits)
        registrar(f"{ticker}: {len(splits)} splits registrados en total")
    except Exception as error:
        registrar(f"{ticker}: ERROR - {error}")
    time.sleep(PAUSA_SEGUNDOS)

# ---------- BLOQUE 6: guardar los datos crudos sin modificar ----------
if tablas_precios:
    pd.concat(tablas_precios, ignore_index=True).to_csv(ARCHIVO_PRECIOS, index=False)
    registrar(f"Guardado: {ARCHIVO_PRECIOS}")
if tablas_splits:
    pd.concat(tablas_splits, ignore_index=True).to_csv(ARCHIVO_SPLITS, index=False)
    registrar(f"Guardado: {ARCHIVO_SPLITS}")
registrar("Fin del script 01")

# Nombres y apellidos: Daniela Andrea Vasquez Medina
# Código de matrícula: 2024200537D
# Tema N.º 47: Valuación relativa de los bancos peruanos listados en bolsa (S06 Valuación de acciones)
# Fecha de extracción: 2026-09-24

"""
02_scraping_web.py
Fuente: Superintendencia de Banca, Seguros y AFP (SBS),
Información Estadística de Banca Múltiple. Cuadros mensuales:
  B-2201 Balance General y Estado de Ganancias y Pérdidas
  B-2401 Indicadores Financieros
  B-2402 Requerimiento de Patrimonio Efectivo y Ratio de Capital Global
Patrón de URL:
  https://intranet2.sbs.gob.pe/estadistica/financiera/{AÑO}/{Mes}/{CÓDIGO}-{abrev}{AÑO}.XLS
Parte A: descarga programática; los archivos originales quedan intactos en datos_crudos/sbs/.
Parte B: lectura (parseo) de los archivos con pandas/xlrd, buscando bancos y variables por texto.
"""

# ---------- BLOQUE 1: librerías ----------
import os
import re
import time
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib import robotparser

import pandas as pd
import requests

# ---------- BLOQUE 2: parámetros congelados ----------
CODIGO = "2024200537D"
PERIODO_INICIO = "2009-12"     # un mes antes de 2010 (cada día usará el balance del mes anterior)
PERIODO_CORTE = "2025-12"
CUADROS = ["B-2201", "B-2401", "B-2402"]
BASE_URL = "https://intranet2.sbs.gob.pe/estadistica/financiera"
USER_AGENT = "Daniela Vasquez Medina - UNCP Economia - Finanzas I (uso academico)"
PAUSA_SEGUNDOS = 1
MESES = {1: ("Enero", "en"), 2: ("Febrero", "fe"), 3: ("Marzo", "ma"), 4: ("Abril", "ab"),
         5: ("Mayo", "my"), 6: ("Junio", "jn"), 7: ("Julio", "jl"), 8: ("Agosto", "ag"),
         9: ("Setiembre", "se"), 10: ("Octubre", "oc"), 11: ("Noviembre", "no"),
         12: ("Diciembre", "di")}

# ---------- BLOQUE 3: rutas relativas ----------
CARPETA_SBS = os.path.join("datos_crudos", "sbs")
ARCHIVO_INVENTARIO = os.path.join("datos_crudos", f"inventario_descargas_sbs_{CODIGO}.csv")
ARCHIVO_SBS = os.path.join("datos_crudos", f"datos_crudos_sbs_{CODIGO}.csv")
ARCHIVO_LOG = "log_ejecucion.txt"
os.makedirs(CARPETA_SBS, exist_ok=True)

# ---------- BLOQUE 4: registro de la ejecución (log) ----------
def registrar(mensaje):
    """Escribe el mensaje con fecha y hora de Lima en pantalla y en log_ejecucion.txt."""
    ahora = datetime.now(ZoneInfo("America/Lima")).strftime('%Y-%m-%d %H:%M:%S')
    linea = f"[{ahora} hora de Lima] [02_SBS] {mensaje}"
    print(linea)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
        f.write(linea + "\n")

# ================= PARTE A: DESCARGA =================

# ---------- BLOQUE 5: revisar robots.txt ----------
robots = robotparser.RobotFileParser()
robots.set_url("https://intranet2.sbs.gob.pe/robots.txt")
robots.read()   # si robots.txt no existe (404), por convención no hay restricciones

# ---------- BLOQUE 6: descarga mes por mes y cuadro por cuadro ----------
periodos = pd.period_range(PERIODO_INICIO, PERIODO_CORTE, freq="M")
registrar(f"Inicio | {len(periodos)} meses x {len(CUADROS)} cuadros = "
          f"{len(periodos) * len(CUADROS)} archivos")

sesion = requests.Session()
sesion.headers.update({"User-Agent": USER_AGENT})
inventario = []

for p in periodos:
    carpeta_mes, abrev = MESES[p.month]
    for cuadro in CUADROS:
        nombre = f"{cuadro}-{abrev}{p.year}.XLS"
        url = f"{BASE_URL}/{p.year}/{carpeta_mes}/{nombre}"
        destino = os.path.join(CARPETA_SBS, nombre)
        fila = {"periodo": str(p), "cuadro": cuadro, "url": url, "archivo": destino}

        if os.path.exists(destino):
            fila["estado"] = "YA_EXISTIA"      # no se vuelve a pedir al portal
        elif not robots.can_fetch(USER_AGENT, url):
            fila["estado"] = "BLOQUEADO_POR_ROBOTS"
            registrar(f"{nombre}: bloqueado por robots.txt")
        else:
            try:
                r = sesion.get(url, timeout=60)
                fila["http"] = r.status_code
                es_excel = r.content[:4] in (b"\xd0\xcf\x11\xe0", b"PK\x03\x04")
                if r.status_code == 200 and es_excel:
                    with open(destino, "wb") as f:
                        f.write(r.content)          # archivo original, sin cambios
                    fila["estado"] = "OK"
                    fila["bytes"] = len(r.content)
                elif r.status_code == 200:
                    fila["estado"] = "NO_ES_EXCEL"
                else:
                    fila["estado"] = "ERROR_HTTP"
                registrar(f"{nombre}: HTTP {r.status_code} | {fila['estado']} | {len(r.content)} bytes")
            except Exception as error:
                fila["estado"] = "ERROR"
                registrar(f"{nombre}: ERROR - {error}")
            time.sleep(PAUSA_SEGUNDOS)

        fila["fecha_hora"] = datetime.now(ZoneInfo("America/Lima")).strftime('%Y-%m-%d %H:%M:%S')
        inventario.append(fila)

# ---------- BLOQUE 7: inventario de descargas ----------
tabla = pd.DataFrame(inventario)
tabla.to_csv(ARCHIVO_INVENTARIO, index=False)
registrar(f"Inventario guardado: {ARCHIVO_INVENTARIO}")
registrar(f"Resumen de estados: {tabla['estado'].value_counts().to_dict()}")

# ================= PARTE B: LECTURA DE LOS ARCHIVOS =================

# ---------- BLOQUE 8: funciones auxiliares ----------
def normalizar(texto):
    """Quita tildes, espacios repetidos y mayúsculas, para comparar textos."""
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", texto).strip().lower()

def identificar_banco(nombre):
    """Reconoce a los 4 bancos del estudio por palabras clave (sus nombres cambian con los años)."""
    n = normalizar(nombre)
    if n == "nan" or "total" in n or len(n) > 70:
        return None
    if "bbva" in n or "continental" in n:
        return "BBVA Perú"
    if "credito" in n:
        return "BCP"
    if "scotiabank" in n:
        return "Scotiabank Perú"
    if "interbank" in n:
        return "Interbank"
    return None

def elegir(candidatos):
    """Si un banco aparece dos veces, prefiere la versión 'con sucursales en el exterior'."""
    con_sucursales = [c for c in candidatos if "sucursales" in normalizar(c[0])]
    return (con_sucursales or candidatos)[0]

def fila_con(hoja, palabra):
    """Devuelve la primera fila que contiene la palabra (se usa para hallar la fila de bancos)."""
    for f in range(len(hoja)):
        if any(palabra in normalizar(v) for v in hoja.iloc[f] if pd.notna(v)):
            return f
    return None

def es_morosidad(e):
    """Fila de morosidad total: 'Créditos Atrasados (criterio SBS)* / Créditos Directos'
    o 'Cartera Atrasada / Créditos Directos'; excluye las versiones M.N., M.E. y 90 días."""
    return "atrasad" in e and e.endswith("/ creditos directos") and "90" not in e

def bancos_en_fila(hoja, f):
    """Agrupa las columnas de la fila f que corresponden a cada banco del estudio."""
    candidatos = {}
    for col in hoja.columns:
        banco = identificar_banco(hoja.iat[f, col])
        if banco:
            candidatos.setdefault(banco, []).append((hoja.iat[f, col], col))
    return candidatos

# ---------- BLOQUE 9: lectores de cada cuadro ----------
def leer_b2201(ruta):
    """Balance: patrimonio y capital social (columna TOTAL de cada banco)."""
    hoja = pd.read_excel(ruta, sheet_name=0, header=None)
    f_bancos = fila_con(hoja, "interbank")
    etiquetas = [normalizar(v) for v in hoja[0]]
    f_pat = etiquetas.index("patrimonio")
    f_cap = next(i for i in range(f_pat, len(etiquetas)) if etiquetas[i] == "capital social")
    resultado = {}
    for banco, cands in bancos_en_fila(hoja, f_bancos).items():
        nombre, col = elegir(cands)
        limite = min(col + 4, hoja.shape[1])
        col_total = next(c for c in range(col, limite)
                         if any(normalizar(hoja.iat[f, c]) == "total"
                                for f in (f_bancos + 1, f_bancos + 2)))
        resultado[banco] = {"nombre_b2201": normalizar(nombre),
                            "patrimonio": hoja.iat[f_pat, col_total],
                            "capital_social": hoja.iat[f_cap, col_total]}
    return resultado

def leer_b2401(ruta):
    """Indicadores: ROE y morosidad (bancos en columnas)."""
    hoja = pd.read_excel(ruta, sheet_name=0, header=None)
    f_bancos = fila_con(hoja, "interbank")
    etiquetas = [normalizar(v) for v in hoja[0]]
    f_roe = next(i for i, e in enumerate(etiquetas)
                 if e.startswith("utilidad neta anualizada / patrimonio promedio"))
    f_mor = next(i for i, e in enumerate(etiquetas) if es_morosidad(e))
    resultado = {}
    for banco, cands in bancos_en_fila(hoja, f_bancos).items():
        nombre, col = elegir(cands)
        resultado[banco] = {"nombre_b2401": normalizar(nombre),
                            "roe": hoja.iat[f_roe, col],
                            "morosidad": hoja.iat[f_mor, col]}
    return resultado

def leer_b2402(ruta):
    """Capital: ratio de capital global (bancos en filas)."""
    hoja = pd.read_excel(ruta, sheet_name=0, header=None)
    encabezados = {c: " ".join(normalizar(v) for v in hoja.iloc[:12, c] if pd.notna(v))
                   for c in hoja.columns}
    col_ratio = [c for c, t in encabezados.items()
                 if "ratio de capital" in t and "global" in t][-1]
    candidatos = {}
    for f in range(len(hoja)):
        banco = identificar_banco(hoja.iat[f, 0])
        if banco:
            candidatos.setdefault(banco, []).append((hoja.iat[f, 0], f))
    resultado = {}
    for banco, cands in candidatos.items():
        nombre, f = elegir(cands)
        resultado[banco] = {"nombre_b2402": normalizar(nombre),
                            "ratio_capital": hoja.iat[f, col_ratio]}
    return resultado

# ---------- BLOQUE 10: leer todos los archivos y guardar la tabla SBS ----------
registrar("Parte B: lectura de los archivos descargados")
lectores = {"B-2201": leer_b2201, "B-2401": leer_b2401, "B-2402": leer_b2402}
datos = {}
errores = 0
for _, fila in tabla.iterrows():
    if not os.path.exists(fila["archivo"]):
        continue
    try:
        for banco, valores in lectores[fila["cuadro"]](fila["archivo"]).items():
            datos.setdefault((fila["periodo"], banco), {}).update(valores)
    except Exception as error:
        errores += 1
        registrar(f"No se pudo leer {fila['archivo']}: {type(error).__name__} {error}")

sbs = pd.DataFrame([{"periodo": p, "banco": b, **v} for (p, b), v in datos.items()])
sbs = sbs.sort_values(["banco", "periodo"]).reset_index(drop=True)
sbs.to_csv(ARCHIVO_SBS, index=False)
registrar(f"Guardado {ARCHIVO_SBS}: {len(sbs)} filas | archivos con error de lectura: {errores}")
registrar(f"Valores encontrados por variable: {sbs.notna().sum().to_dict()}")
registrar("Fin del script 02")

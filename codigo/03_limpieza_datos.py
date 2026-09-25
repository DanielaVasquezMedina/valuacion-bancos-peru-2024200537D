# Nombres y apellidos: Daniela Andrea Vasquez Medina
# Código de matrícula: 2024200537D
# Tema N.º 47: Valuación relativa de los bancos peruanos listados en bolsa (S06 Valuación de acciones)
# Fecha de extracción: 2026-09-24

"""
03_limpieza_datos.py
Entradas (datos crudos; este script NO los modifica):
  - datos_crudos/datos_crudos_yahoo_2024200537D.csv  -> precios diarios (script 01)
  - datos_crudos/splits_yahoo_2024200537D.csv         -> splits de Yahoo (script 01)
  - datos_crudos/datos_crudos_sbs_2024200537D.csv     -> indicadores SBS (script 02)
Proceso:
  depuración, reconstrucción del precio real, unión con la SBS del mes anterior,
  corrección del número de acciones (regla SBS-Yahoo), cálculo del P/B,
  validaciones automáticas y armonización a frecuencia mensual.
Salidas:
  - datos_procesados/datos_procesados_2024200537D.csv -> base DIARIA (evidencia)
  - datos_procesados/datos_mensuales_2024200537D.csv  -> base MENSUAL (análisis)
  - datos_procesados/eventos_acciones_2024200537D.csv -> trazabilidad de acciones
"""

# =============================================================================
# BLOQUE 1: librerías
# =============================================================================
import os                          # manejo de carpetas y rutas
import hashlib                     # cálculo del hash SHA-256 (huella digital del archivo)
from datetime import datetime      # fecha y hora para el log
from zoneinfo import ZoneInfo      # zona horaria de Lima

import pandas as pd                # tablas de datos

# =============================================================================
# BLOQUE 2: parámetros congelados (no se usan fechas dinámicas como "hoy")
# =============================================================================
CODIGO = "2024200537D"
FECHA_INICIO = "2010-01-01"        # primer día del periodo de estudio
FECHA_CORTE = "2025-12-31"         # último día del periodo de estudio

# Valor nominal por acción de cada banco (verificado en memorias oficiales).
VALOR_NOMINAL = {"BBVA Perú": 1.0, "BCP": 1.0, "Scotiabank Perú": 10.0, "Interbank": 1.0}

# Correspondencia entre ticker de Yahoo y nombre del banco en la SBS.
TICKER_A_BANCO = {"BBVAC1.LM": "BBVA Perú", "CREDITC1.LM": "BCP",
                  "SCOTIAC1.LM": "Scotiabank Perú", "INTERBC1.LM": "Interbank"}

TOLERANCIA_FACTOR = 0.01   # diferencia máxima entre factores SBS y Yahoo (1 %)
VENTANA_MESES = 12         # la SBS puede adelantarse hasta 12 meses a Yahoo
UMBRAL_CAMBIO = 0.001      # cambios de acciones menores a 0.1 % se ignoran
UMBRAL_SALTO_PB = 0.20     # un cambio diario del P/B mayor a 20 % se marca como alerta
MINIMO_OBSERVACIONES = 1000

# =============================================================================
# BLOQUE 3: rutas relativas
# =============================================================================
ENTRADA_PRECIOS = os.path.join("datos_crudos", f"datos_crudos_yahoo_{CODIGO}.csv")
ENTRADA_SPLITS = os.path.join("datos_crudos", f"splits_yahoo_{CODIGO}.csv")
ENTRADA_SBS = os.path.join("datos_crudos", f"datos_crudos_sbs_{CODIGO}.csv")
CARPETA_PROCESADOS = "datos_procesados"
SALIDA_DIARIA = os.path.join(CARPETA_PROCESADOS, f"datos_procesados_{CODIGO}.csv")
SALIDA_MENSUAL = os.path.join(CARPETA_PROCESADOS, f"datos_mensuales_{CODIGO}.csv")
SALIDA_EVENTOS = os.path.join(CARPETA_PROCESADOS, f"eventos_acciones_{CODIGO}.csv")
ARCHIVO_LOG = "log_ejecucion.txt"
os.makedirs(CARPETA_PROCESADOS, exist_ok=True)   # crea la carpeta si no existe

# =============================================================================
# BLOQUE 4: funciones de apoyo
# =============================================================================
def registrar(mensaje):
    """Escribe el mensaje con fecha y hora de Lima en pantalla y en log_ejecucion.txt."""
    ahora = datetime.now(ZoneInfo("America/Lima")).strftime('%Y-%m-%d %H:%M:%S')
    linea = f"[{ahora} hora de Lima] [03_LIMPIEZA] {mensaje}"
    print(linea)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:
        f.write(linea + "\n")

def validacion(nombre, condicion, detalle):
    """Registra el resultado de una validación automática como OK o ALERTA."""
    estado = "OK" if condicion else "ALERTA"
    registrar(f"VALIDACIÓN {nombre}: {estado} | {detalle}")

def fecha_de_yahoo(serie):
    """Toma el día tal como lo escribe Yahoo (primeros 10 caracteres: AAAA-MM-DD),
    SIN convertir la zona horaria. Yahoo registra las fechas a medianoche en hora de
    Nueva York (-05:00, o -04:00 en su horario de verano); convertirlas a hora de Lima
    corría esas fechas un día hacia atrás y generaba días domingo inexistentes."""
    return pd.to_datetime(serie.astype(str).str[:10])

def sha256(ruta):
    """Calcula la huella digital SHA-256 de un archivo (cambia si se altera un solo byte)."""
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):   # leer el archivo por partes
            h.update(bloque)
    return h.hexdigest()

registrar(f"Inicio | periodo {FECHA_INICIO} a {FECHA_CORTE}")

# =============================================================================
# BLOQUE 5: leer los datos crudos (verificando que existan)
# =============================================================================
for ruta in (ENTRADA_PRECIOS, ENTRADA_SPLITS, ENTRADA_SBS):
    if not os.path.exists(ruta):
        registrar(f"ERROR: no existe {ruta}. Ejecute primero los scripts 01 y 02.")
        raise SystemExit(1)       # detiene el script de forma controlada

precios = pd.read_csv(ENTRADA_PRECIOS)
splits = pd.read_csv(ENTRADA_SPLITS)
sbs = pd.read_csv(ENTRADA_SBS)
registrar(f"Leídos: precios {len(precios)} filas | splits {len(splits)} | SBS {len(sbs)} filas")

# =============================================================================
# BLOQUE 6: depurar precios (solo días con negociación y dentro del periodo)
# =============================================================================
precios["fecha"] = fecha_de_yahoo(precios["Date"])               # día escrito por Yahoo
precios["banco"] = precios["ticker"].map(TICKER_A_BANCO)         # nombre del banco
precios = precios.rename(columns={"Close": "precio_yahoo", "Volume": "volumen"})

en_periodo = precios["fecha"].between(FECHA_INICIO, FECHA_CORTE)  # dentro del periodo
con_negociacion = precios["volumen"] > 0                          # hubo operaciones
registrar(f"Días sin negociación excluidos: {int((en_periodo & ~con_negociacion).sum())}")
precios = precios[en_periodo & con_negociacion].copy()
registrar(f"Días con negociación en el periodo: {len(precios)}")

# =============================================================================
# BLOQUE 7: reconstruir el precio real (deshacer los splits posteriores)
# =============================================================================
splits["fecha"] = fecha_de_yahoo(splits["fecha"])
splits["banco"] = splits["ticker"].map(TICKER_A_BANCO)

precios["factor_split"] = 1.0                    # 1 = sin corrección
for _, s in splits.iterrows():
    # filas del mismo ticker ANTERIORES al split: su precio fue reducido por Yahoo
    mask = (precios["ticker"] == s["ticker"]) & (precios["fecha"] < s["fecha"])
    precios.loc[mask, "factor_split"] *= s["factor"]
precios["precio_real"] = precios["precio_yahoo"] * precios["factor_split"]

# =============================================================================
# BLOQUE 8: unir cada día con la SBS del MES ANTERIOR (Decisión 1)
# =============================================================================
sbs["periodo"] = pd.PeriodIndex(sbs["periodo"], freq="M")
sbs["valor_nominal"] = sbs["banco"].map(VALOR_NOMINAL)
sbs["acciones_sbs"] = sbs["capital_social"] * 1000 / sbs["valor_nominal"]

precios["periodo_sbs"] = precios["fecha"].dt.to_period("M") - 1   # mes anterior
base = precios.merge(
    sbs[["banco", "periodo", "patrimonio", "capital_social", "valor_nominal",
         "acciones_sbs", "roe", "morosidad", "ratio_capital"]],
    left_on=["banco", "periodo_sbs"], right_on=["banco", "periodo"], how="left"
).drop(columns="periodo")          # la columna 'periodo' repite a 'periodo_sbs'

# =============================================================================
# BLOQUE 9: número de acciones (regla: la SBS dice CUÁNTAS; Yahoo, DESDE CUÁNDO)
# =============================================================================
sbs = sbs.sort_values(["banco", "periodo"])
# factor de cambio de acciones respecto al mes anterior del mismo banco
sbs["factor_sbs"] = sbs.groupby("banco")["acciones_sbs"].transform(lambda s: s / s.shift(1))
aumentos = sbs[sbs["factor_sbs"] > 1 + UMBRAL_CAMBIO][["banco", "periodo", "factor_sbs"]]
reducciones = sbs[sbs["factor_sbs"] < 1 - UMBRAL_CAMBIO][["banco", "periodo", "factor_sbs"]]
spl = splits[splits["fecha"].between(FECHA_INICIO, FECHA_CORTE)]

eventos, usados = [], set()
for _, s in spl.iterrows():
    mes_split = s["fecha"].to_period("M")
    # candidatos: mismo banco, entre 0 y 12 meses antes, factor casi igual, no usados
    cand = aumentos[(aumentos["banco"] == s["banco"]) &
                    (aumentos["periodo"] <= mes_split) &
                    (aumentos["periodo"] >= mes_split - VENTANA_MESES) &
                    ((aumentos["factor_sbs"] - s["factor"]).abs() < TOLERANCIA_FACTOR) &
                    (~aumentos.index.isin(usados))]
    if len(cand):
        i = (cand["factor_sbs"] - s["factor"]).abs().idxmin()   # el factor más parecido
        usados.add(i)
        eventos.append({"banco": s["banco"], "tipo": "confirmado",
                        "mes_sbs": aumentos.loc[i, "periodo"], "fecha_entrega": s["fecha"],
                        "factor_sbs": aumentos.loc[i, "factor_sbs"], "factor_yahoo": s["factor"],
                        "tratamiento": "acciones anteriores hasta la fecha de entrega"})
    else:
        eventos.append({"banco": s["banco"], "tipo": "split_sin_aumento_sbs",
                        "mes_sbs": None, "fecha_entrega": s["fecha"],
                        "factor_sbs": None, "factor_yahoo": s["factor"],
                        "tratamiento": "12 meses previos marcados como no confirmados"})

conf = [e for e in eventos if e["tipo"] == "confirmado"]
# rezago de cada evento confirmado = meses entre el registro SBS y la entrega en bolsa
for e in conf:
    e["rezago_meses"] = (e["fecha_entrega"].to_period("M") - e["mes_sbs"]).n
rezago_max = pd.DataFrame(conf).groupby("banco")["rezago_meses"].max().to_dict()

for _, a in aumentos[~aumentos.index.isin(usados)].iterrows():
    eventos.append({"banco": a["banco"], "tipo": "aumento_sbs_sin_split",
                    "mes_sbs": a["periodo"], "fecha_entrega": None,
                    "factor_sbs": a["factor_sbs"], "factor_yahoo": None,
                    "tratamiento": f"{rezago_max.get(a['banco'], VENTANA_MESES)} meses marcados como no confirmados"})
for _, r in reducciones.iterrows():
    eventos.append({"banco": r["banco"], "tipo": "reduccion_sbs",
                    "mes_sbs": r["periodo"], "fecha_entrega": None,
                    "factor_sbs": r["factor_sbs"], "factor_yahoo": None,
                    "tratamiento": "se aplica en el mes SBS (sin ajuste de precio)"})

base["acciones"] = base["acciones_sbs"]      # punto de partida: acciones de la SBS
base["acciones_confirmadas"] = True
for e in eventos:
    if e["tipo"] == "confirmado":
        # antes de la entrega, el mercado negociaba con el número ANTERIOR de acciones
        mask = ((base["banco"] == e["banco"]) & (base["periodo_sbs"] >= e["mes_sbs"]) &
                (base["fecha"] < e["fecha_entrega"]))
        base.loc[mask, "acciones"] /= e["factor_sbs"]
    elif e["tipo"] == "aumento_sbs_sin_split":
        # fecha de entrega desconocida: se marcan los meses del rezago máximo del banco
        L = rezago_max.get(e["banco"], VENTANA_MESES)
        mask = ((base["banco"] == e["banco"]) & (base["periodo_sbs"] >= e["mes_sbs"]) &
                (base["periodo_sbs"] <= e["mes_sbs"] + L))
        base.loc[mask, "acciones_confirmadas"] = False
    elif e["tipo"] == "split_sin_aumento_sbs":
        # número previo de acciones desconocido: se marcan los 12 meses anteriores al split
        mask = ((base["banco"] == e["banco"]) & (base["fecha"] < e["fecha_entrega"]) &
                (base["fecha"] >= e["fecha_entrega"] - pd.DateOffset(months=VENTANA_MESES)))
        base.loc[mask, "acciones_confirmadas"] = False

tabla_eventos = pd.DataFrame(eventos)
registrar(f"Eventos de acciones: {tabla_eventos['tipo'].value_counts().to_dict()}")
registrar(f"Rezago máximo SBS-Yahoo por banco (meses): {rezago_max}")

# =============================================================================
# BLOQUE 10: valor contable por acción, P/B y validez de cada observación
# =============================================================================
base["vpa"] = base["patrimonio"] * 1000 / base["acciones"]    # soles por acción
base["pb"] = base["precio_real"] / base["vpa"]                # múltiplo P/B
variables_necesarias = ["precio_real", "patrimonio", "acciones", "roe", "morosidad", "ratio_capital"]
completa = base[variables_necesarias].notna().all(axis=1)     # ninguna variable vacía
base["observacion_valida"] = completa & base["acciones_confirmadas"]

# marca informativa (no excluye): cambio del P/B mayor al umbral respecto al día previo
base = base.sort_values(["banco", "fecha"]).reset_index(drop=True)
cambio = base.groupby("banco")["pb"].pct_change().abs()
base["alerta_salto_pb"] = cambio > UMBRAL_SALTO_PB

# =============================================================================
# BLOQUE 11: validaciones automáticas (resultado OK o ALERTA en el log)
# =============================================================================
validas = base[base["observacion_valida"]]

# V1: ninguna fila con datos faltantes
validacion("V1 datos completos", completa.all(),
           f"{int((~completa).sum())} filas con algún dato faltante")
# V2: tamaño mínimo exigido por la consigna
validacion("V2 tamaño mínimo", len(validas) >= MINIMO_OBSERVACIONES,
           f"{len(validas)} observaciones válidas (mínimo {MINIMO_OBSERVACIONES})")
# V3: P/B positivo y dentro de un rango plausible (0 a 10)
fuera = validas[(validas["pb"] <= 0) | (validas["pb"] > 10)]
validacion("V3 rango del P/B", len(fuera) == 0, f"{len(fuera)} valores fuera de 0-10")
# V4: todos los bancos tienen datos válidos en todos los años
anios = validas.groupby("banco")["fecha"].apply(lambda f: f.dt.year.nunique())
esperados = pd.Timestamp(FECHA_CORTE).year - pd.Timestamp(FECHA_INICIO).year + 1
validacion("V4 cobertura anual", (anios == esperados).all(), f"años con datos por banco: {anios.to_dict()}")
# V5: saltos bruscos del P/B (se informan, no se eliminan)
saltos = base[base["alerta_salto_pb"]]
validacion("V5 saltos del P/B", len(saltos) == 0,
           f"{len(saltos)} cambios diarios mayores a {UMBRAL_SALTO_PB:.0%}")
for _, f in saltos.head(15).iterrows():
    registrar(f"    salto: {f['banco']} {f['fecha'].date()} P/B={f['pb']:.2f} válida={f['observacion_valida']}")
# V6: fechas de los valores extremos del P/B por banco
for banco, g in validas.groupby("banco"):
    fmin, fmax = g.loc[g["pb"].idxmin()], g.loc[g["pb"].idxmax()]
    registrar(f"    extremos {banco}: mín {fmin['pb']:.2f} ({fmin['fecha'].date()}) | "
              f"máx {fmax['pb']:.2f} ({fmax['fecha'].date()})")

# =============================================================================
# BLOQUE 12: guardar la base DIARIA y la tabla de eventos
# =============================================================================
columnas = ["banco", "ticker", "fecha", "periodo_sbs", "volumen", "precio_yahoo",
            "factor_split", "precio_real", "patrimonio", "capital_social", "valor_nominal",
            "acciones_sbs", "acciones", "acciones_confirmadas", "vpa", "pb",
            "roe", "morosidad", "ratio_capital", "observacion_valida", "alerta_salto_pb"]
base[columnas].to_csv(SALIDA_DIARIA, index=False)
tabla_eventos.to_csv(SALIDA_EVENTOS, index=False)
registrar(f"Guardado {SALIDA_DIARIA}: {len(base)} filas, {len(columnas)} columnas "
          f"({len(validas)} válidas)")
registrar(f"Guardado {SALIDA_EVENTOS}: {len(tabla_eventos)} eventos")

# =============================================================================
# BLOQUE 13: base MENSUAL para el análisis (solo observaciones válidas)
# =============================================================================
validas = validas.assign(mes=validas["fecha"].dt.to_period("M"))
mensual = (validas.groupby(["banco", "mes"])
           .agg(periodo_sbs=("periodo_sbs", "first"),     # mes SBS usado (mes anterior)
                pb_promedio=("pb", "mean"),              # P/B promedio del mes
                pb_fin_mes=("pb", "last"),               # P/B del último día válido del mes
                dias_validos=("pb", "size"),             # días válidos que forman el promedio
                roe=("roe", "first"),                    # iguales todo el mes (mes anterior)
                morosidad=("morosidad", "first"),
                ratio_capital=("ratio_capital", "first"))
           .reset_index())
mensual.to_csv(SALIDA_MENSUAL, index=False)
registrar(f"Guardado {SALIDA_MENSUAL}: {len(mensual)} banco-mes")

# =============================================================================
# BLOQUE 14: huella digital SHA-256 (para el README y la verificación del docente)
# =============================================================================
registrar(f"SHA-256 {SALIDA_DIARIA}: {sha256(SALIDA_DIARIA)}")
registrar(f"SHA-256 {SALIDA_MENSUAL}: {sha256(SALIDA_MENSUAL)}")
registrar("Fin del script 03")

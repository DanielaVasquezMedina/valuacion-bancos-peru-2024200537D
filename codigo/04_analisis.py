# Nombres y apellidos: Daniela Andrea Vasquez Medina
# Código de matrícula: 2024200537D
# Tema N.º 47: Valuación relativa de los bancos peruanos listados en bolsa
# Fecha de extracción: 2026-09-24

"""
04_analisis.py
Entradas (generadas por 03_limpieza_datos.py; este script NO las modifica):
  - datos_procesados/datos_procesados_2024200537D.csv -> base diaria (P/B diario)
  - datos_procesados/datos_mensuales_2024200537D.csv  -> base mensual (análisis)
Proceso, según los objetivos del artículo:
  - OE1: estadística descriptiva y evolución del P/B por banco.
  - Paso previo: matriz de correlaciones de Pearson.
  - OE2, OE3, OE4 y objetivo general: regresión lineal múltiple por MCO agrupado.
  - Validez: pruebas de Durbin-Watson, Breusch-Pagan, Jarque-Bera y VIF.
  - Robustez: misma regresión con el P/B de fin de mes.
Salidas (carpeta salidas/): tablas en .csv y .tex, figuras en .png y resumen .txt.
"""

# =============================================================================
# BLOQUE 1: LIBRERÍAS
# -----------------------------------------------------------------------------
# QUÉ SE BUSCA: cargar las herramientas que Python necesita para el análisis.
#   Python por sí solo no sabe hacer regresiones ni gráficos; estas librerías
#   agregan esas capacidades.
# QUÉ HACE: importa (carga en memoria) cada librería y le da un nombre corto.
#   - pandas: manejar tablas de datos (como hojas de Excel).
#   - matplotlib: dibujar gráficos.
#   - statsmodels: estimar la regresión por MCO y las pruebas de supuestos.
#   - scipy: calcular la correlación de Pearson con su p-valor.
# RESULTADO: ninguno visible; deja las herramientas listas para los demás bloques.
# =============================================================================
import os                                   # manejar carpetas y rutas de archivos
from datetime import datetime               # obtener la fecha y hora actual
from zoneinfo import ZoneInfo               # expresar la hora en zona horaria de Lima

import matplotlib
matplotlib.use("Agg")                       # dibujar sin pantalla (necesario al ejecutar con !python)
import matplotlib.pyplot as plt             # funciones para crear gráficos
import pandas as pd                         # tablas de datos
import statsmodels.api as sm                # regresión lineal por MCO
from scipy import stats                     # correlación de Pearson y su p-valor
from statsmodels.stats.diagnostic import het_breuschpagan                 # prueba de heterocedasticidad
from statsmodels.stats.outliers_influence import variance_inflation_factor  # prueba de multicolinealidad
from statsmodels.stats.stattools import durbin_watson, jarque_bera        # autocorrelación y normalidad

# =============================================================================
# BLOQUE 2: PARÁMETROS DEL ANÁLISIS
# -----------------------------------------------------------------------------
# QUÉ SE BUSCA: fijar en un solo lugar todas las decisiones metodológicas, para
#   que sean visibles, fáciles de explicar y fáciles de cambiar si fuera necesario.
# QUÉ HACE: guarda en variables:
#   - ALFA = 0.05: nivel de significancia (95 % de confianza), como en el material
#     del curso ("ritual de significancia").
#   - MAXLAGS_NW = 12: cuántos meses hacia atrás considera la corrección de
#     Newey-West; 12 meses = 1 año, por el ciclo anual de dividendos que
#     encontramos en los datos (saltos del P/B cada abril).
#   - VARIABLES_X: las tres variables independientes de las hipótesis.
#   - ORDEN_BANCOS y ETIQUETAS: nombres ordenados y legibles para tablas y gráficos.
# RESULTADO: ninguno visible; los demás bloques usan estos valores.
# =============================================================================
CODIGO = "2024200537D"
ALFA = 0.05
MAXLAGS_NW = 12
VARIABLES_X = ["roe", "morosidad", "ratio_capital"]
ORDEN_BANCOS = ["BBVA Perú", "BCP", "Interbank", "Scotiabank Perú"]
ETIQUETAS = {"pb_promedio": "P/B (promedio mensual)", "pb_fin_mes": "P/B (fin de mes)",
             "roe": "ROE (%)", "morosidad": "Morosidad (%)",
             "ratio_capital": "Ratio de capital global (%)"}

# =============================================================================
# BLOQUE 3: RUTAS RELATIVAS
# -----------------------------------------------------------------------------
# QUÉ SE BUSCA: indicar dónde están los datos de entrada y dónde guardar los
#   resultados, usando rutas relativas (exigencia de la consigna, numeral 2.4.4),
#   para que el script funcione igual en la computadora del docente.
# QUÉ HACE: arma los nombres de los archivos con tu código de matrícula y crea
#   la carpeta "salidas" si todavía no existe.
# RESULTADO: la carpeta salidas/ lista para recibir tablas y figuras.
# =============================================================================
ENTRADA_DIARIA = os.path.join("datos_procesados", f"datos_procesados_{CODIGO}.csv")
ENTRADA_MENSUAL = os.path.join("datos_procesados", f"datos_mensuales_{CODIGO}.csv")
CARPETA_SALIDAS = "salidas"
ARCHIVO_LOG = "log_ejecucion.txt"
os.makedirs(CARPETA_SALIDAS, exist_ok=True)     # crea la carpeta; si ya existe, no hace nada

# =============================================================================
# BLOQUE 4: FUNCIONES DE APOYO
# -----------------------------------------------------------------------------
# QUÉ SE BUSCA: evitar repetir el mismo código muchas veces. Una "función" es un
#   bloque con nombre que se escribe una vez y se usa cuantas veces se necesite.
# QUÉ HACE: define cuatro funciones:
#   - registrar(): escribe cada paso con fecha y hora de Lima en pantalla y en
#     log_ejecucion.txt (evidencia de la ejecución).
#   - guardar_tabla(): guarda una tabla en .csv (para revisarla) y en .tex (para
#     insertarla directamente en el artículo de LaTeX).
#   - guardar_figura(): guarda el gráfico en .png de alta resolución (300 dpi).
#   - estrellas(): convierte un p-valor en asteriscos (*** p<0.01, ** p<0.05,
#     * p<0.10), la convención usual en tablas de artículos científicos.
# RESULTADO: ninguno todavía; estas funciones se usan en los bloques 6 a 10.
# =============================================================================
def registrar(mensaje):
    """Escribe el mensaje con fecha y hora de Lima en pantalla y en log_ejecucion.txt."""
    ahora = datetime.now(ZoneInfo("America/Lima")).strftime('%Y-%m-%d %H:%M:%S')
    linea = f"[{ahora} hora de Lima] [04_ANALISIS] {mensaje}"
    print(linea)
    with open(ARCHIVO_LOG, "a", encoding="utf-8") as f:   # "a" = agregar al final sin borrar
        f.write(linea + "\n")

def guardar_tabla(tabla, nombre, decimales=3):
    """Guarda una tabla en .csv y en .tex, redondeada al número de decimales indicado."""
    ruta_csv = os.path.join(CARPETA_SALIDAS, f"{nombre}.csv")
    tabla.round(decimales).to_csv(ruta_csv)
    try:
        ruta_tex = os.path.join(CARPETA_SALIDAS, f"{nombre}.tex")
        tabla.round(decimales).to_latex(ruta_tex, float_format=f"%.{decimales}f")
    except Exception as error:      # si falla el .tex, el .csv igual queda guardado
        registrar(f"Aviso: no se pudo crear {nombre}.tex ({error})")
    registrar(f"Tabla guardada: {ruta_csv}")

def guardar_figura(nombre):
    """Guarda el gráfico actual como .png de alta resolución y lo cierra."""
    ruta = os.path.join(CARPETA_SALIDAS, f"{nombre}.png")
    plt.tight_layout()                  # ajusta márgenes para que no se corten etiquetas
    plt.savefig(ruta, dpi=300)          # 300 puntos por pulgada: calidad de publicación
    plt.close()                         # libera la memoria del gráfico
    registrar(f"Figura guardada: {ruta}")

def estrellas(p):
    """Devuelve asteriscos según el p-valor."""
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""

registrar("Inicio del análisis")

# =============================================================================
# BLOQUE 5: LECTURA DE LAS BASES PROCESADAS
# -----------------------------------------------------------------------------
# QUÉ SE BUSCA: cargar los datos que generó el script 03 y confirmar que están
#   completos antes de analizarlos (si faltara algo, los resultados no servirían).
# QUÉ HACE:
#   1. Verifica que existan los dos archivos; si falta uno, se detiene con un
#      mensaje claro (manejo de errores).
#   2. Lee la base diaria y se queda solo con las observaciones válidas
#      (observacion_valida = True: completas y con acciones confirmadas).
#   3. Lee la base mensual (la que se usa en la regresión) y crea una columna de
#      fecha para poder graficar.
#   4. Cuenta si hay valores faltantes en las variables del modelo.
# RESULTADO: las tablas "diaria_valida" y "mensual" en memoria, y en el log el
#   número de filas y de faltantes.
# =============================================================================
for ruta in (ENTRADA_DIARIA, ENTRADA_MENSUAL):
    if not os.path.exists(ruta):
        registrar(f"ERROR: no existe {ruta}. Ejecute primero el script 03.")
        raise SystemExit(1)

diaria = pd.read_csv(ENTRADA_DIARIA, parse_dates=["fecha"])
diaria_valida = diaria[diaria["observacion_valida"]]
mensual = pd.read_csv(ENTRADA_MENSUAL)
mensual["fecha_mes"] = pd.PeriodIndex(mensual["mes"], freq="M").to_timestamp()
registrar(f"Base diaria: {len(diaria)} filas ({len(diaria_valida)} válidas) | "
          f"base mensual: {len(mensual)} banco-mes")

variables_modelo = ["pb_promedio"] + VARIABLES_X
faltantes = int(mensual[variables_modelo].isna().sum().sum())
registrar(f"Valores faltantes en las variables del modelo: {faltantes}")

# =============================================================================
# BLOQUE 6: OBJETIVO ESPECÍFICO 1 - DESCRIBIR LA EVOLUCIÓN DEL P/B
# -----------------------------------------------------------------------------
# QUÉ SE BUSCA: responder el OE1: "Describir la evolución del P/B de cada banco
#   durante 2010-2025". Es la parte descriptiva: muestra CÓMO son los datos
#   antes de buscar explicaciones.
# QUÉ HACE:
#   - Tabla 1: para cada variable (P/B, ROE, morosidad, capital) calcula n,
#     media, desviación estándar, mínimo, percentiles 25 y 75, mediana y máximo.
#   - Tabla 1b: promedio de cada variable por banco, con cuántos meses y días
#     válidos aporta cada uno (muestra que el panel no está balanceado).
#   - Figura 1: línea del P/B de cada banco mes a mes; incluye una línea en
#     P/B = 1 (el mercado paga exactamente el valor contable).
#   - Figura 2: diagrama de cajas: compara nivel y dispersión del P/B entre bancos.
#   - Figura 3: puntos ROE vs P/B: primera mirada visual a la relación del OE2.
# RESULTADO: tabla1, tabla1b, figura1, figura2 y figura3 en salidas/.
# =============================================================================
tabla1 = mensual[variables_modelo].describe().T
tabla1 = tabla1[["count", "mean", "std", "min", "25%", "50%", "75%", "max"]]
tabla1.columns = ["n", "Media", "Desv. estándar", "Mínimo", "P25", "Mediana", "P75", "Máximo"]
tabla1.index = [ETIQUETAS[v] for v in tabla1.index]
guardar_tabla(tabla1, "tabla1_descriptivos_generales", 2)

tabla1b = mensual.groupby("banco")[variables_modelo].mean().reindex(ORDEN_BANCOS)
tabla1b["Meses válidos"] = mensual.groupby("banco").size()
tabla1b["Días válidos"] = diaria_valida.groupby("banco").size()
tabla1b = tabla1b.rename(columns=ETIQUETAS)
guardar_tabla(tabla1b, "tabla1b_promedios_por_banco", 2)

# pivot: una columna por banco; asfreq("MS") agrega como vacíos los meses sin
# datos, para que la línea se corte en esos meses y no una puntos lejanos
serie = mensual.pivot(index="fecha_mes", columns="banco", values="pb_promedio").asfreq("MS")
fig, ax = plt.subplots(figsize=(10, 5))
for banco in ORDEN_BANCOS:
    ax.plot(serie.index, serie[banco], label=banco, linewidth=1.3)
ax.axhline(1, color="gray", linestyle="--", linewidth=0.8)   # referencia: P/B = 1
ax.set_xlabel("Mes")
ax.set_ylabel("P/B (promedio mensual)")
ax.legend()
ax.grid(alpha=0.3)
guardar_figura("figura1_evolucion_pb")

datos_caja = [mensual.loc[mensual["banco"] == b, "pb_promedio"] for b in ORDEN_BANCOS]
fig, ax = plt.subplots(figsize=(8, 5))
ax.boxplot(datos_caja)                  # caja: 50 % central de los datos; línea: mediana
ax.set_xticks(range(1, len(ORDEN_BANCOS) + 1), ORDEN_BANCOS)
ax.set_ylabel("P/B (promedio mensual)")
ax.grid(alpha=0.3, axis="y")
guardar_figura("figura2_pb_por_banco")

fig, ax = plt.subplots(figsize=(7, 5))
for banco in ORDEN_BANCOS:
    g = mensual[mensual["banco"] == banco]
    ax.scatter(g["roe"], g["pb_promedio"], s=12, alpha=0.6, label=banco)   # un punto por banco-mes
ax.set_xlabel("ROE (%) del mes anterior")
ax.set_ylabel("P/B (promedio mensual)")
ax.legend()
ax.grid(alpha=0.3)
guardar_figura("figura3_pb_vs_roe")

# =============================================================================
# BLOQUE 7: PASO PREVIO - MATRIZ DE CORRELACIONES DE PEARSON
# -----------------------------------------------------------------------------
# QUÉ SE BUSCA: dos cosas antes de la regresión:
#   1. Ver si el P/B se mueve junto con cada variable (análisis bivariado, nivel
#      relacional según el material del docente).
#   2. Detectar si las variables independientes están muy relacionadas entre sí
#      (multicolinealidad), lo que dificultaría separar su efecto en la regresión.
# QUÉ HACE: para cada par de variables calcula el coeficiente r de Pearson
#   (entre -1 y 1) y su p-valor, y los muestra juntos con asteriscos de
#   significancia (ej. "0.452***").
# RESULTADO: tabla2_correlaciones en salidas/.
# =============================================================================
tabla2 = pd.DataFrame(index=[ETIQUETAS[v] for v in variables_modelo],
                      columns=[ETIQUETAS[v] for v in variables_modelo])
for a in variables_modelo:
    for b in variables_modelo:
        r, p = stats.pearsonr(mensual[a], mensual[b])      # coeficiente r y su p-valor
        tabla2.loc[ETIQUETAS[a], ETIQUETAS[b]] = f"{r:.3f}{estrellas(p)}"
guardar_tabla(tabla2, "tabla2_correlaciones")

# =============================================================================
# BLOQUE 8: REGRESIÓN LINEAL MÚLTIPLE POR MCO AGRUPADO
#   Modelo: P/B = b0 + b1*ROE + b2*Morosidad + b3*Capital + error
# -----------------------------------------------------------------------------
# QUÉ SE BUSCA: responder los OE2, OE3 y OE4 y el objetivo general: cuánto
#   INFLUYE cada variable en el P/B manteniendo las otras constantes (nivel
#   explicativo). Cada coeficiente b responde "¿en cuánto?": cuánto cambia el
#   P/B si esa variable sube 1 punto porcentual.
# QUÉ HACE:
#   1. Ordena los datos por banco y mes (lo exige la corrección de Newey-West).
#   2. Estima el modelo por MCO con errores estándar clásicos.
#   3. Estima los mismos coeficientes con errores estándar de Newey-West, que
#      corrigen los p-valores si hay autocorrelación o heterocedasticidad. Se
#      calculan dentro de cada banco, para no mezclar el último mes de un banco
#      con el primero del siguiente.
#   4. Aplica el ritual de significancia a cada hipótesis: si p <= 0.05 se
#      rechaza H0 (la variable sí influye) y lo escribe en el log.
#   5. Prueba F: evalúa la hipótesis general (las tres variables en conjunto).
# RESULTADO: tabla3 (coeficientes y p-valores), tabla3b (R², F, n) y en el log
#   la decisión de cada hipótesis.
# =============================================================================
datos_reg = mensual.dropna(subset=variables_modelo).sort_values(["banco", "mes"]).reset_index(drop=True)
y = datos_reg["pb_promedio"]                         # variable dependiente (Y)
X = sm.add_constant(datos_reg[VARIABLES_X])          # independientes (X) + constante (b0)

modelo_mco = sm.OLS(y, X).fit()                      # MCO con errores estándar clásicos

grupos = datos_reg["banco"].astype("category").cat.codes.values    # número de cada banco
modelo_nw = sm.OLS(y, X).fit(cov_type="hac-panel",
                             cov_kwds={"groups": grupos, "maxlags": MAXLAGS_NW})

nombres = ["Constante"] + [ETIQUETAS[v] for v in VARIABLES_X]
tabla3 = pd.DataFrame({
    "Coeficiente": modelo_mco.params.values,         # iguales en ambos modelos
    "EE clásico": modelo_mco.bse.values,             # EE = error estándar del coeficiente
    "p-valor clásico": modelo_mco.pvalues.values,
    "EE Newey-West": modelo_nw.bse.values,
    "p-valor Newey-West": modelo_nw.pvalues.values,
}, index=nombres)
guardar_tabla(tabla3, "tabla3_regresion_mco", 4)

tabla3b = pd.DataFrame({
    "Valor": [int(modelo_mco.nobs), modelo_mco.rsquared, modelo_mco.rsquared_adj,
              modelo_mco.fvalue, modelo_mco.f_pvalue, modelo_nw.fvalue, modelo_nw.f_pvalue]
}, index=["Observaciones (banco-mes)", "R cuadrado", "R cuadrado ajustado",
          "F (clásico)", "p-valor F (clásico)", "F (Newey-West)", "p-valor F (Newey-West)"])
guardar_tabla(tabla3b, "tabla3b_ajuste_modelo", 4)

signo_esperado = {"roe": "+ (directa)", "morosidad": "- (indirecta)", "ratio_capital": "sin dirección"}
for v in VARIABLES_X:
    for etiqueta, modelo in (("clásico", modelo_mco), ("Newey-West", modelo_nw)):
        p = modelo.pvalues[v]
        decision = "se rechaza H0" if p <= ALFA else "no se rechaza H0"
        registrar(f"H {ETIQUETAS[v]}: coef = {modelo.params[v]:.4f} (esperado {signo_esperado[v]}) | "
                  f"p {etiqueta} = {p:.4f} -> {decision}")
registrar(f"Hipótesis general (prueba F Newey-West): p = {modelo_nw.f_pvalue:.4f} -> "
          f"{'se rechaza H0' if modelo_nw.f_pvalue <= ALFA else 'no se rechaza H0'}")

# =============================================================================
# BLOQUE 9: PRUEBAS DE SUPUESTOS DE LA REGRESIÓN
# -----------------------------------------------------------------------------
# QUÉ SE BUSCA: comprobar si se cumplen los supuestos de MCO que enseña el
#   docente. Si no se cumplen, los p-valores clásicos no son confiables y se
#   deben usar los de Newey-West.
# QUÉ HACE:
#   - Durbin-Watson: autocorrelación (si los errores de un mes se parecen a los
#     del mes anterior). Valor cercano a 2 = sin autocorrelación.
#   - Breusch-Pagan: heterocedasticidad (si la dispersión de los errores cambia).
#     H0: varianza constante.
#   - Jarque-Bera: normalidad de los errores. H0: distribución normal.
#   - VIF: multicolinealidad (si las variables independientes se repiten
#     información entre sí). Mayor a 10 = problema grave.
# RESULTADO: tabla4_supuestos en salidas/ y un resumen en el log.
# =============================================================================
residuos = modelo_mco.resid                               # errores del modelo (Y real - Y estimada)
dw = durbin_watson(residuos)
bp_lm, bp_p, _, _ = het_breuschpagan(residuos, X)
jb_estad, jb_p, _, _ = jarque_bera(residuos)
filas = [
    ["Durbin-Watson (autocorrelación)", dw, None, "Cercano a 2: sin autocorrelación; menor a 1.5: autocorrelación positiva"],
    ["Breusch-Pagan (heterocedasticidad)", bp_lm, bp_p, "H0: varianza constante; p <= 0.05 indica heterocedasticidad"],
    ["Jarque-Bera (normalidad)", jb_estad, jb_p, "H0: errores normales; p <= 0.05 indica no normalidad"],
]
for i, v in enumerate(X.columns):                         # VIF de cada variable independiente
    if v != "const":
        filas.append([f"VIF {ETIQUETAS[v]}", variance_inflation_factor(X.values, i), None,
                      "Mayor a 10: multicolinealidad grave; mayor a 5: precaución"])
tabla4 = pd.DataFrame(filas, columns=["Prueba", "Estadístico", "p-valor", "Criterio"]).set_index("Prueba")
guardar_tabla(tabla4, "tabla4_supuestos", 4)
registrar(f"Durbin-Watson = {dw:.3f} | Breusch-Pagan p = {bp_p:.4f} | Jarque-Bera p = {jb_p:.4f}")

# =============================================================================
# BLOQUE 10: PRUEBA DE ROBUSTEZ Y RESUMEN COMPLETO
# -----------------------------------------------------------------------------
# QUÉ SE BUSCA: comprobar que las conclusiones no dependen de cómo se resumió el
#   P/B de cada mes. Si con el P/B del último día del mes los signos y la
#   significancia se mantienen, el resultado es "robusto" (sólido).
# QUÉ HACE:
#   1. Repite la regresión cambiando solo la variable dependiente: P/B de fin de
#      mes en lugar del promedio mensual (con errores de Newey-West).
#   2. Pone ambos resultados lado a lado para compararlos.
#   3. Guarda el resumen completo de statsmodels de los tres modelos, para el
#      anexo del artículo y para responder preguntas del docente.
# RESULTADO: tabla5_robustez y resumen_regresion.txt en salidas/.
# =============================================================================
modelo_rob = sm.OLS(datos_reg["pb_fin_mes"], X).fit(cov_type="hac-panel",
                    cov_kwds={"groups": grupos, "maxlags": MAXLAGS_NW})
tabla5 = pd.DataFrame({
    "Coef. (promedio mensual)": modelo_nw.params.values,
    "p-valor (promedio)": modelo_nw.pvalues.values,
    "Coef. (fin de mes)": modelo_rob.params.values,
    "p-valor (fin de mes)": modelo_rob.pvalues.values,
}, index=nombres)
guardar_tabla(tabla5, "tabla5_robustez", 4)

with open(os.path.join(CARPETA_SALIDAS, "resumen_regresion.txt"), "w", encoding="utf-8") as f:
    f.write("MODELO PRINCIPAL - errores estándar clásicos\n")
    f.write(modelo_mco.summary().as_text())
    f.write("\n\nMODELO PRINCIPAL - errores estándar de Newey-West (por banco)\n")
    f.write(modelo_nw.summary().as_text())
    f.write("\n\nROBUSTEZ - P/B de fin de mes (Newey-West)\n")
    f.write(modelo_rob.summary().as_text())
registrar("Resumen guardado: salidas/resumen_regresion.txt")
registrar("Fin del script 04")

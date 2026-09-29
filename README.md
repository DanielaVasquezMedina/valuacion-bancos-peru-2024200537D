# Valuación relativa de los bancos peruanos listados en bolsa: un análisis del múltiplo P/B, 2010-2025

*Relative valuation of Peruvian listed banks: an analysis of the P/B ratio, 2010–2025*

- **Autora:** Daniela Andrea Vasquez Medina
- **Código de matrícula:** 2024200537D
- **Curso:** Finanzas I (055D) - Universidad Nacional del Centro del Perú, 2026-II
- **Tema del temario:** N.º 47 - Valuación relativa de los bancos peruanos listados en bolsa
- **Repositorio:** https://github.com/DanielaVasquezMedina/valuacion-bancos-peru-2024200537D

## Estado
Completo. Ejecución final en carpeta limpia realizada el 2026-09-28: los cuatro scripts regeneraron la base con el mismo hash SHA-256.

## Fuentes de datos y endpoints

| Vía | Fuente | Endpoint o URL | Datos obtenidos |
|---|---|---|---|
| API | Yahoo Finance, librería `yfinance` (método `Ticker.history`) | Tickers `BBVAC1.LM`, `CREDITC1.LM`, `SCOTIAC1.LM`, `INTERBC1.LM` | Precio de cierre, volumen y splits |
| Descarga programática | Superintendencia de Banca, Seguros y AFP (SBS), Información Estadística de Banca Múltiple | `https://intranet2.sbs.gob.pe/estadistica/financiera/{AÑO}/{Mes}/{CÓDIGO}-{abrev}{AÑO}.XLS` | Cuadros B-2201 (balance), B-2401 (indicadores) y B-2402 (ratio de capital) |

## Parámetros de la consulta (congelados en el código)
- Precios (scripts 01 y 03): `FECHA_INICIO = 2010-01-01`, `FECHA_CORTE = 2025-12-31`.
- SBS (script 02): `PERIODO_INICIO = 2009-12`, `PERIODO_CORTE = 2025-12`. Diciembre de 2009 se descarga porque cada día usa los indicadores del mes anterior.
- Fecha de extracción: 2026-09-28.

## Muestra
BBVA Perú, BCP, Scotiabank Perú e Interbank: los bancos de banca múltiple con acción propia listada en la BVL, serie histórica de precios disponible en la vía API y negociación suficiente (se evaluaron los 19 bancos de la SBS).

## Requisitos
- Python 3.13.15.
- Librerías y versiones exactas: `requirements.txt`.
- No se requieren claves de API (ver `.env.example`).

## Orden de ejecución
Desde la carpeta raíz del proyecto:

    pip install -r requirements.txt
    python codigo/01_extraccion_api.py
    python codigo/02_scraping_web.py
    python codigo/03_limpieza_datos.py
    python codigo/04_analisis.py

El script 02 descarga 579 archivos con una pausa de 1 segundo entre solicitudes (entre 15 y 25 minutos). Cada script registra su ejecución en `log_ejecucion.txt` con fecha y hora de Lima.

## Estructura
- `codigo/`: los cuatro scripts.
- `datos_crudos/`: datos tal como salen de la fuente: precios y splits de Yahoo Finance, valores extraídos de la SBS e inventario de las 579 descargas (URL, código HTTP y hora). Los 579 archivos .XLS originales de la SBS (28.8 MB) se incluyen en la carpeta de entrega del curso y el script 02 los vuelve a descargar.
- `datos_procesados/`: base diaria (`datos_procesados_2024200537D.csv`), base mensual (`datos_mensuales_2024200537D.csv`) y eventos de acciones (`eventos_acciones_2024200537D.csv`).
- `salidas/`: tablas (.csv y .tex) y figuras (.png) del artículo.
- `diccionario_variables.md`: definición de cada variable.

## Decisiones metodológicas
1. Cada día de negociación usa los indicadores de la SBS del mes anterior (último cierre contable disponible), para no usar información futura.
2. El precio real se reconstruye deshaciendo los ajustes por splits (acciones liberadas) que aplica Yahoo Finance.
3. La SBS determina el número de acciones (capital social ÷ valor nominal) y Yahoo Finance determina la fecha efectiva del ajuste bursátil.
4. No se eliminan observaciones: la variable `observacion_valida` identifica las que se usan en la estimación.
5. La base diaria es la evidencia verificable; la regresión se estima con la base mensual, porque las variables explicativas son mensuales.

## Verificación
- SHA-256 de `datos_procesados/datos_procesados_2024200537D.csv`: `145d1a4660404ed4fa2ba0482141eeac014e5d27ea3835acf1ea7e910addbd24`    (confirmado en la ejecución final del 2026-09-28)

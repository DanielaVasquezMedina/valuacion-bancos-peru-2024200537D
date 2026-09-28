# Diccionario de variables

**Autora:** Daniela Andrea Vasquez Medina · **Código:** 2024200537D

## Fuentes y endpoints

| Código | Fuente | Endpoint o URL |
|---|---|---|
| YF | Yahoo Finance, librería `yfinance` (método `Ticker.history`, `auto_adjust=False`) | Tickers `BBVAC1.LM`, `CREDITC1.LM`, `SCOTIAC1.LM`, `INTERBC1.LM` |
| SBS-2201 | SBS, Balance General y Estado de Ganancias y Pérdidas por Empresa Bancaria | `https://intranet2.sbs.gob.pe/estadistica/financiera/{AÑO}/{Mes}/B-2201-{abrev}{AÑO}.XLS` |
| SBS-2401 | SBS, Indicadores Financieros por Empresa Bancaria | `https://intranet2.sbs.gob.pe/estadistica/financiera/{AÑO}/{Mes}/B-2401-{abrev}{AÑO}.XLS` |
| SBS-2402 | SBS, Requerimiento de Patrimonio Efectivo y Ratio de Capital Global | `https://intranet2.sbs.gob.pe/estadistica/financiera/{AÑO}/{Mes}/B-2402-{abrev}{AÑO}.XLS` |

## 1. Base diaria: `datos_procesados/datos_procesados_2024200537D.csv`

9 467 filas (una por banco y día con negociación), 21 columnas, enero 2010 - diciembre 2025. Se usa como evidencia verificable.

| Variable | Definición | Cálculo | Unidad | Frecuencia | Fuente |
|---|---|---|---|---|---|
| banco | Nombre normalizado del banco | Asignado según el ticker; los nombres históricos de la SBS se unifican (p. ej., Banco Continental = BBVA Perú) | Texto | — | Script 03 |
| ticker | Código de la acción en Yahoo Finance | Nemónico de la BVL + sufijo `.LM` | Texto | — | YF |
| fecha | Día con negociación (volumen > 0) | Fecha escrita por Yahoo Finance | AAAA-MM-DD | Diaria | YF |
| periodo_sbs | Mes de los indicadores SBS asignados al día | Mes anterior a `fecha` (último cierre contable disponible) | AAAA-MM | Mensual | Script 03 |
| volumen | Acciones negociadas en el día | Directo | Acciones | Diaria | YF |
| precio_yahoo | Precio de cierre entregado por la API (ajustado por splits, no por dividendos) | Columna `Close` | Soles por acción | Diaria | YF |
| factor_split | Producto de los factores de split posteriores a `fecha` | Producto acumulado (1 = sin corrección) | Veces | Diaria | YF (splits) |
| precio_real | Precio efectivamente negociado ese día | precio_yahoo × factor_split | Soles por acción | Diaria | Calculada |
| patrimonio | Patrimonio contable total | Fila «PATRIMONIO», columna TOTAL | Miles de soles | Mensual | SBS-2201 |
| capital_social | Capital social | Fila «Capital Social», columna TOTAL | Miles de soles | Mensual | SBS-2201 |
| valor_nominal | Valor nominal de cada acción | Constante por banco: S/ 1.00 (BBVA, BCP, Interbank) y S/ 10.00 (Scotiabank) | Soles por acción | Fijo | Memorias anuales y listado de la BVL |
| acciones_sbs | Acciones según la SBS | capital_social × 1 000 ÷ valor_nominal | Acciones | Mensual | Calculada |
| acciones | Acciones usadas para el valor contable por acción | acciones_sbs; antes de la fecha de entrega bursátil (split de Yahoo) se usa el número anterior (÷ factor del aumento) | Acciones | Diaria | Calculada |
| acciones_confirmadas | Indica si el número de acciones pudo confirmarse | False en los meses posteriores a un aumento de la SBS sin split en Yahoo (rezago máximo del banco) y en los 12 meses previos a un split sin aumento en la SBS | Verdadero / Falso | Diaria | Calculada |
| vpa | Valor contable por acción | patrimonio × 1 000 ÷ acciones | Soles por acción | Diaria | Calculada |
| pb | Múltiplo precio / valor contable (**variable dependiente**) | precio_real ÷ vpa | Veces | Diaria | Calculada |
| roe | Rentabilidad sobre el patrimonio | «Utilidad Neta Anualizada / Patrimonio Promedio» | % | Mensual | SBS-2401 |
| morosidad | Riesgo de crédito | «Créditos Atrasados (criterio SBS) / Créditos Directos» (hasta 2010: «Cartera Atrasada / Créditos Directos») | % | Mensual | SBS-2401 |
| ratio_capital | Solvencia | «Ratio de Capital Global» | % | Mensual | SBS-2402 |
| observacion_valida | Observación usada en la estimación | Todas las variables completas y acciones_confirmadas = True | Verdadero / Falso | Diaria | Calculada |
| alerta_salto_pb | Alerta informativa (no excluye la fila) | Cambio del P/B mayor a 20 % respecto al día previo del mismo banco | Verdadero / Falso | Diaria | Calculada |

## 2. Base mensual: `datos_procesados/datos_mensuales_2024200537D.csv`

707 filas (una por banco y mes), construida solo con observaciones válidas. Es la base de la regresión.

| Variable | Definición | Cálculo | Unidad |
|---|---|---|---|
| banco | Nombre del banco | Igual que en la base diaria | Texto |
| mes | Mes calendario | Mes de `fecha` | AAAA-MM |
| periodo_sbs | Mes de los indicadores SBS usados | Mes anterior a `mes` | AAAA-MM |
| pb_promedio | P/B del mes (**variable dependiente del modelo**) | Promedio del P/B de los días válidos del mes | Veces |
| pb_fin_mes | P/B del último día válido del mes (prueba de robustez) | Último valor del mes | Veces |
| dias_validos | Días válidos que forman el promedio | Conteo | Días |
| roe | ROE del mes anterior | Igual que en la base diaria | % |
| morosidad | Morosidad del mes anterior | Igual que en la base diaria | % |
| ratio_capital | Ratio de capital global del mes anterior | Igual que en la base diaria | % |

## 3. Eventos de acciones: `datos_procesados/eventos_acciones_2024200537D.csv`

Registro de trazabilidad de los cambios en el número de acciones: `banco`, `tipo` (confirmado, split sin aumento SBS, aumento SBS sin split, reducción SBS), `mes_sbs`, `fecha_entrega`, `factor_sbs`, `factor_yahoo`, `rezago_meses` y `tratamiento`.

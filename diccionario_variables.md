# Diccionario de variables

Base: `datos_procesados_2024200537D.csv` (9 467 filas, 21 columnas; frecuencia diaria, enero 2010 - diciembre 2025).

| Variable | Descripción | Unidad / tipo | Fuente |
|---|---|---|---|
| banco | Nombre del banco | Texto | Definido en el script |
| ticker | Código de la acción en la BVL | Texto | Yahoo Finance |
| fecha | Fecha de la cotización | Fecha (AAAA-MM-DD) | Yahoo Finance |
| periodo_sbs | Mes del reporte de la SBS asignado a esa fecha | Texto (AAAA-MM) | SBS |
| volumen | Acciones negociadas en el día | Número de acciones | Yahoo Finance |
| precio_yahoo | Precio de cierre tal como lo entrega la API | Soles por acción | Yahoo Finance |
| factor_split | Factor acumulado de corrección por eventos de acciones (1 = sin corrección) | Número | Eventos de acciones (script 03) |
| precio_real | Precio de cierre corregido por eventos de acciones (precio_yahoo × factor_split) | Soles por acción | Calculada |
| patrimonio | Patrimonio del banco en el mes del reporte | Miles de soles | SBS |
| capital_social | Capital social del banco | Miles de soles | SBS |
| valor_nominal | Valor nominal de cada acción, fijo por banco | Soles por acción | Definido en el script 03 |
| acciones_sbs | Acciones estimadas con datos de la SBS (capital_social × 1 000 / valor_nominal) | Número de acciones | Calculada |
| acciones | Número de acciones usado para calcular el VPA | Número de acciones | Calculada |
| acciones_confirmadas | Indica si el número de acciones fue confirmado en el script | Verdadero / Falso | Calculada |
| vpa | Valor en libros por acción (patrimonio × 1 000 / acciones) | Soles por acción | Calculada |
| pb | Múltiplo precio/valor en libros (precio_real / vpa). Variable dependiente | Veces | Calculada |
| roe | Rentabilidad sobre el patrimonio | Porcentaje | SBS |
| morosidad | Cartera morosa sobre cartera total | Porcentaje | SBS |
| ratio_capital | Ratio de capital global | Porcentaje | SBS |
| observacion_valida | Verdadero si están completos precio_real, patrimonio, acciones, roe, morosidad y ratio_capital, y las acciones están confirmadas | Verdadero / Falso | Calculada |
| alerta_salto_pb | Verdadero si el cambio del P/B supera el umbral UMBRAL_SALTO_PB definido en el script 03 | Verdadero / Falso | Calculada |

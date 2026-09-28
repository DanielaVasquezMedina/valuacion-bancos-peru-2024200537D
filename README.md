# Valuación relativa de los bancos peruanos listados en bolsa: un análisis del múltiplo P/B, 2010-2025

*Relative valuation of Peruvian listed banks: an analysis of the P/B ratio, 2010–2025*

- **Autora:** Daniela Andrea Vasquez Medina
- **Código de matrícula:** 2024200537D
- **Curso:** Finanzas I (055D) - Universidad Nacional del Centro del Perú, 2026-II
- **Tema del temario:** N.º 47 - S06 Valuación de acciones

## Estado
Completo. Listo para entrega.

## Fuentes de datos
- **API:** Yahoo Finance mediante la librería `yfinance` (precios diarios de BBVAC1, CREDITC1, SCOTIAC1 e INTERBC1).
- **Descarga programática:** Superintendencia de Banca, Seguros y AFP (SBS), cuadros B-2201, B-2401 y B-2402 de banca múltiple.

## Periodo
Enero 2010 - diciembre 2025.

## Variables
P/B (dependiente), ROE (%), morosidad (%) y ratio de capital global (%).

## Orden de ejecución
1. `00_configuracion` (Google Colab): conecta Drive y crea las carpetas.
2. `codigo/01_extraccion_api.py`: precios vía API.
3. `codigo/02_scraping_web.py`: cuadros de la SBS.
4. `codigo/03_limpieza_datos.py`: base procesada.
5. `codigo/04_analisis.py`: regresión, tablas y figuras en `salidas/`.

## Reproducibilidad
- Librerías y versiones: ver `requirements.txt`.
- Hash SHA-256 de la base procesada (`datos_procesados_2024200537D.csv`): `145d1a4660404ed4fa2ba0482141eeac014e5d27ea3835acf1ea7e910addbd24`

# De dónde sale `failure_reports.csv`

Transcripción **literal** de la tabla «Failure Information» del PDF oficial
`Data Description_Metro.pdf`, que viaja dentro del zip de UCI
(DOI 10.24432/C5VW3R, CC BY 4.0).

El PDF no se versiona aquí porque llega con el dataset. Se re-obtiene descomprimiendo
`data/metropt3.zip`.

## Lo que trae el original, sin corregir

La regla de la casa es que el original manda, así que nada de esto se ha tocado. Las cuatro
rarezas están declaradas para que nadie las «arregle» por error más adelante:

1. **La numeración va `#1`, `#1`, `#3`, `#4`.** Hay dos filas numeradas `#1` y no existe
   ninguna `#2`. En el PDF se ve igual.
2. **`Air leak` y `Air Leak` conviven**, con la ele en mayúscula y en minúscula. Son la misma
   avería escrita de dos formas.
3. **La segunda avería declara mantenimiento el 30 de abril**, casi un mes ANTES de su propia
   fecha de inicio (29 de mayo). O es una errata por `30 May`, o el parte quedó mal copiado en
   origen. No se decide aquí: se conserva y se explica.
4. **La primera avería no trae parte de mantenimiento**, la celda viene vacía.

Estas cuatro cosas no son un estorbo, son el material del módulo 5 (juntar fuentes sin mentir)
y del módulo 8 (calidad de datos y contratos). Los partes de mantenimiento reales llegan así.

## Formato de las fechas

Vienen en formato de Estados Unidos, `M/D/YYYY H:MM`, y sin zona horaria. La telemetría, en
cambio, viene en `YYYY-MM-DD HH:MM:SS`. Que las dos fuentes escriban la misma fecha de dos
maneras distintas es exactamente la trampa que el módulo 5 tiene que enseñar a resolver, así
que la conversión se hace en el código de ingesta y no editando este fichero.

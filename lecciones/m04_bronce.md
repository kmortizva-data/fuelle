---
module: 4
---

## En 30 segundos

- El lago se ordena en tres capas: **bronce, plata y oro**. Esta lección construye la primera.
- La regla de bronce es una sola: **no se limpia, no se arregla y no se interpreta**.
- Entran 208,19 MB de texto y salen **22,05 MB** en 212 carpetas, una por día.
- Las 212 carpetas no son 212 días iguales: la mediana es de **7.437 lecturas** sobre 8.640.
- Lo único que se añade es la columna del día y un recibo de lo que entró.

## Qué resuelve este módulo

El fichero crudo es intocable y a la vez incómodo: 208 MB de texto que hay que leer entero para
cualquier pregunta. Hace falta una copia con la que se pueda trabajar sin perder el original.

Esa copia es la capa de bronce, y su valor está en lo que **no** hace.

## Antes de la teoría: un ejemplo de juguete

Un turno deja seis lecturas de presión del depósito, una cada diez minutos:

| Hora | Presión |
|---|---|
| 06:00 | 9,0 |
| 06:10 | 9,0 |
| 06:20 | 8,0 |
| 06:30 | 8,0 |
| 06:40 | 6,0 |
| 06:50 | **-10,0** |

La última es imposible. Un depósito no tiene presión negativa, y menos de diez bar por debajo de
cero. Es un sensor que se desconectó y escribió su valor de aviso.

**La media con esa lectura dentro es 5,0 bar.** Sumas las seis, treinta, y divides entre seis.

**La media sin ella es 8,0 bar.** Sumas las cinco buenas, cuarenta, y divides entre cinco.

Ocho es la presión real del turno y cinco no es nada. Así que la tentación es obvia: borrar la
fila mala antes de guardar. Y ahí está el error del módulo.

Si la borras al entrar, hay tres preguntas que ya no podrás contestar nunca:

1. **Cuántas veces se cae ese sensor.** No se puede contar lo que se ha borrado.
2. **Si se cae siempre a la misma hora.** Aquí se cayó al final del turno. Con un mes de datos
   sabrías si eso es casualidad.
3. **Si alguien ya lo había arreglado antes que tú.** Y de qué manera.

Bronce guarda el **-10,0**. Plata lo marca como dato ausente y anota por qué. Oro publica la
media de 8,0. Cada capa hace una cosa, y las tres siguen existiendo.

## Glosario

- **Capa.** Una copia de los datos con un nivel de tratamiento distinto. No sustituye a la
  anterior: convive con ella.
- **Bronce.** La primera copia. Los datos tal y como llegaron, en un formato manejable.
- **Plata.** Los datos limpios, con los tipos correctos y unidos a otras fuentes.
- **Oro.** Las tablas que responden preguntas concretas, ya resumidas.
- **Arquitectura de medallón.** El nombre de este reparto en tres capas. Se llama así por los
  metales, y es la forma habitual de organizar un lago.
- **Partición.** Cada trozo en que se reparte una tabla, normalmente una carpeta por fecha.
- **Manifiesto.** Un fichero pequeño al lado de los datos que dice qué entró y de dónde.
- **Compresión.** Guardar lo mismo ocupando menos, aprovechando lo que se repite.

## Paso a paso

### Paso 1. Decidir qué no se toca

Antes de escribir código conviene fijar la regla, porque es la que se va a romper por comodidad
más tarde. En bronce no se corrigen decimales, no se rellenan huecos y no se tira ninguna fila.

Los valores raros del módulo 1 siguen ahí: los decimales con ruido como `-0.0120000000000004` y
las lecturas cada nueve segundos. Molestan, y se quedan.

### Paso 2. Añadir lo mínimo para poder trabajar

Bronce añade dos cosas, y solo dos.

La primera es una columna con el día, sacada de la marca de tiempo. No es información nueva: es
la misma fecha en su propia columna, y sirve para repartir los datos en carpetas.

La segunda es el manifiesto: un recibo con el nombre del fichero de origen, su huella y cuántas
filas trajo. Es lo que permitirá, en el módulo 5, saber si hace falta volver a ingerir.

### Paso 3. Guardar en carpetas por día

Una carpeta por fecha, con su fichero dentro. Es el reparto que hace todo el mundo, y por eso se
hace aquí también.

Conviene decirlo por delante: **el módulo 6 mide este reparto y resulta ser el peor de los que se
prueban.** Se deja igual a propósito. Primero se comete el error corriente y luego se mide, que
es distinto de contarlo ya resuelto.

## El código, por partes

### Paso 4. Las tres capas, para situarse

```diagrama
*CRUDO | El CSV de UCI | 208,19 MB, intocable
*BRONCE | Parquet por día | 22,05 MB, nada se limpia
PLATA | Tipado y unido | aquí sí se arregla, módulo 14
ORO | Tablas de respuesta | listas para preguntar, módulo 17
```

Las dos encendidas son las que existen al terminar esta lección. Las otras dos llegan en la
parte 4, y el mismo esquema irá encendiéndose a medida que se construyan.

### Paso 5. Copiar el CSV a Parquet, repartido por día

```sql
COPY (
    SELECT
        "column00" AS source_index,
        * EXCLUDE ("column00"),
        CAST(timestamp AS DATE) AS day
    FROM read_csv_auto('data/MetroPT3(AirCompressor).csv', header = true)
)
TO 'lake/bronze/telemetry'
(FORMAT PARQUET, PARTITION_BY (day), OVERWRITE_OR_IGNORE, COMPRESSION ZSTD);
```

```anota
COPY (...) TO '...' | escribe el resultado de una consulta en ficheros, en vez de enseñarlo por pantalla
"column00" | el nombre que DuckDB inventa para la primera columna del fichero, que llegó sin nombre
AS source_index | le pone nombre: es el número de fila original, y el módulo 1 lo usó como prueba del submuestreo
* EXCLUDE ("column00") | todas las demás columnas menos esa, para no repetirla
CAST(timestamp AS DATE) AS day | se queda con la parte del día y la guarda en su propia columna
FORMAT PARQUET | el formato columnar; el módulo 7 mide por qué
PARTITION_BY (day) | crea una carpeta por cada valor distinto de day
OVERWRITE_OR_IGNORE | permite escribir encima de lo que ya hubiera
COMPRESSION ZSTD | el algoritmo que comprime cada columna al guardarla
```

Una sola instrucción lee 208 MB de texto y deja 212 carpetas escritas.

### Paso 6. Comprobar lo que quedó

```sql
SELECT count(*) AS filas,
       count(DISTINCT day) AS carpetas,
       min(day) AS primera,
       max(day) AS ultima
FROM read_parquet('lake/bronze/telemetry/**/*.parquet');
```

```anota
read_parquet('.../**/*.parquet') | lee todos los ficheros que encajen; los dos asteriscos significan «y en las subcarpetas»
count(DISTINCT day) | cuenta valores distintos, no filas: cuántos días diferentes hay
AS filas | le pone nombre a la columna del resultado, para leerla mejor
```

```salida
┌─────────┬──────────┬────────────┬────────────┐
│  filas  │ carpetas │  primera   │   ultima   │
├─────────┼──────────┼────────────┼────────────┤
│ 1516948 │      212 │ 2020-02-01 │ 2020-09-01 │
└─────────┴──────────┴────────────┴────────────┘
```

Las mismas 1.516.948 filas que contó el módulo 1. Ni una más ni una menos, y eso es exactamente
lo que tenía que pasar.

### Paso 7. El recibo de lo que entró

```python
manifest = {
    "source_file": RAW_CSV.name,
    "source_sha256": source_hash,
    "source_bytes": RAW_CSV.stat().st_size,
    "rows": stats["rows"],
    "partitions": stats["partitions"],
}
```

```anota
manifest | un diccionario de Python: pares de nombre y valor, que se guardan como fichero JSON
source_sha256 | la huella del fichero de origen, que el módulo 5 explica entera
.stat().st_size | el tamaño del fichero en bytes, preguntándoselo al sistema
```

Ese diccionario se guarda junto a los datos, no en el código. Un dato sobre los datos que viaje
en el código se pierde en cuanto alguien copia la carpeta a otro sitio.

## El resultado, medido

{{FIG:fig_m4_bronce_particiones}}

**Qué esperábamos.** Una copia más pequeña y 212 carpetas más o menos del mismo tamaño.

**Qué salió.** Lo primero sí, y de sobra: **208,19 MB de texto se guardan en 22,05 MB**
repartidos en **212 particiones**, o sea 9,44 veces menos con el mismo contenido dentro.

Lo segundo no. Un día lleno son 8.640 lecturas, seis por minuto durante veinticuatro horas. La
mediana de las 212 carpetas es de **7.437 lecturas**, un 86,1 % de un día. Solo **91 días** pasan
del 90 % y hay **5 días** que no llegan al 10 %. La carpeta más grande pesa **16 veces** lo que
la más pequeña.

**Qué significa.** El registro tiene huecos por todas partes, y no son un accidente puntual: en
la figura se ven caídas repartidas por los siete meses. Eso tiene una consecuencia práctica que
va a volver en el módulo 10: **cualquier media diaria calculada sobre los 212 días mentirá**,
porque mezcla días enteros con días de dos horas.

Y una consecuencia de diseño que se ve mejor aquí que en ningún sitio. Si la ingesta hubiera
«arreglado» los huecos rellenándolos, esta figura no existiría y nadie sabría que el problema
está ahí.

## Ojo

- **Bronce no es una copia de seguridad.** El original sigue siendo el original. Bronce es una
  copia manejable, y si se pierde se vuelve a generar desde el CSV.
- **Un día lleno son 8.640 lecturas en teoría, y hay 49 días que pasan de esa cifra.** El
  muestreo no es exacto: el módulo 1 midió saltos de nueve segundos, y con ellos caben más
  lecturas en un día. Un porcentaje de día puede pasar del cien por cien.
- **La columna del día no es un dato nuevo.** Sale de la marca de tiempo que ya estaba. Añadir
  una columna derivada está permitido en bronce; cambiar un valor que llegó, no.
- **El nombre de la primera columna es un detalle del programa, no del fichero.** DuckDB la llama
  `column00` hoy y podría llamarla de otra forma mañana, así que el código la lee en vez de
  escribirla a mano.
- **Repartir por día es lo que hace todo el mundo y aquí sale mal.** El módulo 6 lo mide. Se deja
  así hasta entonces.

## Puente metalúrgico

En un laboratorio de planta, la muestra de cabeza se cuartea y se guarda un testigo antes de
hacer nada con ella. Ese testigo no se tritura, no se seca y no se ensaya. Se etiqueta y se
archiva.

Parece desperdicio hasta el día en que una ley no cuadra. Entonces el testigo es lo único que
permite distinguir entre un error de muestreo, un error de preparación y un error de ensayo. Sin
él, la discusión se resuelve por antigüedad en la empresa.

Bronce es el testigo. La tentación de limpiar al entrar es la misma tentación de secar la muestra
antes de pesarla, y se paga igual de tarde.

## Repaso

### Por qué guardar los datos sucios si de todos modos hay que limpiarlos

Porque limpiar es una decisión y las decisiones se revisan. Si la limpieza ocurre al entrar, la
decisión queda enterrada y nadie puede revisarla ni contar cuántas veces se aplicó. Guardando el
crudo, la limpieza pasa a ser un paso visible que se puede cambiar sin volver a pedir los datos.

### Qué se le permite añadir a la capa de bronce

Columnas derivadas de lo que ya está, como el día sacado de la marca de tiempo, y metadatos al
lado, como el manifiesto. Lo que no se permite es cambiar un valor que llegó, rellenar un hueco
o descartar una fila.

### El CSV ocupa 208,19 MB y el bronce 22,05. Se ha perdido algo por el camino

No. Las dos formas guardan las mismas 1.516.948 filas y se comprueba contándolas. La diferencia
es el formato. El texto escribe cada número como caracteres y repite el nombre del día en cada
fila. El formato columnar guarda junta cada columna y comprime lo que se repite, y el módulo 7 lo
mide columna a columna.

### Las carpetas no son del mismo tamaño. Es un fallo de la ingesta

No, es lo que hay en el origen. La ingesta escribe una carpeta por cada día que aparece en el
fichero, y los días vienen con huecos. La mediana es de 7.437 lecturas frente a las 8.640 de un
día completo. Que la ingesta lo respete es la prueba de que está haciendo su trabajo.

### Si hubiera que reconstruir el lago entero desde cero, qué haría falta

El CSV original y este script. Nada más, y esa es la prueba de que la capa está bien hecha. Si
para reconstruir el bronce hiciera falta algo que solo existe dentro del bronce, habría un dato
sin origen y el lago dejaría de ser reproducible.

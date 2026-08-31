---
module: 7
---

## En 30 segundos

- CSV guarda fila tras fila. Parquet guarda cada columna por separado, y eso lo cambia todo.
- Preguntar por una columna sale **54 veces** más rápido en Parquet que en el CSV.
- La ventaja **se encoge** cuando la pregunta usa más columnas: de 54 veces a **25**.
- El peso de un Parquet no está en las filas: la columna `timestamp` es el **30,4 %** del fichero.
- Las mismas 1.516.948 filas ocupan **16,83 MB con 17 columnas y 0,03 MB con 2**.

## Qué resuelve este módulo

Los módulos anteriores usaron Parquet sin explicarlo. Toca justificar por qué, y hacerlo con el
cronómetro en vez de con una lista de ventajas.

De paso aparece la regla que decide cuánto ocupa un fichero de datos, y no es la que casi todo el
mundo supone.

## Antes de la teoría: un ejemplo de juguete

Cuatro turnos, con tres datos cada uno:

| Turno | Toneladas | Ley | Operario |
|---|---|---|---|
| T1 | 100 | 20 | Ana |
| T2 | 200 | 20 | Ana |
| T3 | 300 | 20 | Luis |
| T4 | 400 | 20 | Luis |

**Guardado por filas**, que es lo que hace un CSV, el fichero dice:

```
T1,100,20,Ana
T2,200,20,Ana
T3,300,20,Luis
T4,400,20,Luis
```

**Guardado por columnas**, que es lo que hace Parquet, el mismo contenido se agrupa así:

```
turnos:      T1,T2,T3,T4
toneladas:   100,200,300,400
leyes:       20,20,20,20
operarios:   Ana,Ana,Luis,Luis
```

Ahora pregunta: **cuántas toneladas se procesaron en total**.

Por filas hay que recorrer las cuatro líneas enteras y sacar el segundo valor de cada una. Se
leen doce datos para usar cuatro.

Por columnas se lee solo la fila de toneladas. Cuatro datos para usar cuatro.

Y mira la fila de las leyes, que es el mismo veinte cuatro veces. Guardada junta, se puede
escribir como **«veinte, cuatro veces»**. Guardada por filas, ese veinte está repartido entre
cuatro líneas y no hay forma de agruparlo.

Ahí están las dos ventajas del formato columnar. Son la misma cosa vista dos veces: **lo que
está junto se salta entero, y lo que se repite se escribe una vez**.

## Glosario

- **Formato por filas.** Guarda un registro completo detrás de otro. CSV, JSON por líneas y la
  mayoría de las bases de datos tradicionales.
- **Formato columnar.** Guarda juntos todos los valores de una misma columna. Parquet, ORC,
  DuckDB por dentro.
- **Parquet.** El formato columnar más usado. Es un fichero binario que lleva dentro su propio
  índice de qué hay y dónde.
- **Metadatos.** Los datos sobre los datos. En Parquet incluyen cuánto ocupa cada columna, cuántos
  valores tiene y cuáles son su mínimo y su máximo.
- **Cardinalidad.** Cuántos valores distintos tiene una columna. Es lo que decide si comprime bien
  o mal.
- **Diccionario.** La técnica de guardar cada valor distinto una vez y luego solo referencias a
  él. Funciona bien con pocos valores distintos y mal con muchos.

## Paso a paso

### Paso 1. Hacer la misma pregunta tres veces, cada vez con más columnas

Tres preguntas, elegidas para que cambie solo cuántas columnas hacen falta: contar filas, que no
necesita ninguna; la media de una columna; y la media de las siete señales analógicas.

Si el formato columnar hace lo que dice, la ventaja de Parquet tiene que **encogerse** al pedir
más columnas. Esa pendiente es lo que se mide, y dice mucho más que un simple «Parquet gana».

### Paso 2. Preguntarle al fichero cuánto pesa cada columna

Aquí no hay que estimar nada. Parquet lleva escrita dentro su propia contabilidad, y DuckDB la
deja consultar como si fuera una tabla más.

O sea que el fichero se puede interrogar sobre sí mismo: cuánto ocupa cada columna, comprimida y
sin comprimir. Eso convierte una explicación en una medición.

### Paso 3. Quitar columnas y ver qué pasa con el tamaño

Y el experimento que remata el módulo. Se escribe el mismo número de filas cuatro veces, con
menos columnas cada vez, y se mira el tamaño del fichero.

## El código, por partes

### Paso 4. La misma pregunta, en los dos formatos

```sql
SELECT avg(TP2) FROM read_parquet('lake/_formatos/todo.parquet');
```

```anota
avg(TP2) | la media de la columna TP2, que es la presión del compresor
read_parquet | lee un fichero columnar, que ya trae los tipos escritos dentro
```

```salida
┌────────────────────┐
│      avg(TP2)      │
│       double       │
├────────────────────┤
│ 1.3678259663489851 │
└────────────────────┘
```

La misma pregunta contra el CSV se escribe cambiando una palabra, `read_parquet` por
`read_csv_auto`, y devuelve exactamente el mismo número. Lo único distinto es de dónde salen los
datos, y eso es justo lo que se quiere cronometrar.

Con esa pregunta y otras dos, el banco de pruebas imprime esto:

```salida
Three questions, two formats, median of 7 runs each.
  question                 CSV   Parquet    factor
  contar_filas          0.552s   0.0043s    128.7x
  una_columna           0.594s   0.0111s     53.6x
  siete_columnas        0.680s   0.0274s     24.8x
```

Fíjate en la columna del CSV: sus tres tiempos son casi iguales. Da lo mismo lo que preguntes,
porque hay que leer y descifrar el fichero entero de todas formas.

### Paso 5. Preguntarle al fichero qué pesa cada columna

```sql
SELECT path_in_schema AS columna,
       sum(total_compressed_size)   AS comprimido,
       sum(total_uncompressed_size) AS sin_comprimir
FROM parquet_metadata('lake/_formatos/todo.parquet')
GROUP BY columna
ORDER BY comprimido DESC;
```

```anota
parquet_metadata('...') | abre los metadatos del fichero como si fueran una tabla, sin leer los datos
path_in_schema | el nombre de la columna dentro del fichero
total_compressed_size | los bytes que ocupa esa columna ya comprimida, o sea lo que pesa de verdad
sum(...) | los suma, porque el fichero guarda un dato por cada bloque de filas
ORDER BY comprimido DESC | de mayor a menor; DESC es descendente
```

```salida
┌─────────────────┬────────────┬───────────────┐
│     columna     │ comprimido │ sin_comprimir │
│     varchar     │   int128   │    int128     │
├─────────────────┼────────────┼───────────────┤
│ timestamp       │    5284726 │      12135987 │
│ Oil_temperature │    1971125 │       2147372 │
│ TP3             │    1944693 │       2223233 │
│ Reservoirs      │    1942403 │       2222913 │
│ H1              │    1804798 │       2162780 │
│ source_index    │    1651898 │      12135987 │
└─────────────────┴────────────┴───────────────┘
```

El fichero contesta en bytes. El script hace la división a kilobytes, calcula el porcentaje y
cuenta los valores distintos de cada columna:

```salida
  column                    KB   % file   distinct
  timestamp             5160.9     30.4  1,516,948
  Oil_temperature       1924.9     11.3      2,462
  TP3                   1899.1     11.2      3,683
  source_index          1613.2      9.5  1,516,948
  Motor_current         1154.1      6.8      1,809
  TP2                    887.5      5.2      5,257
  Towers                  42.3      0.2          2
  COMP                    28.7      0.2          2
  LPS                      1.7      0.0          2
```

Esa tabla es el módulo entero. Las dos columnas que no repiten ningún valor están arriba del
todo, y las digitales, que solo valen cero o uno, están abajo pesando casi nada.

Fíjate en `timestamp` y `source_index` en la salida de arriba. Sin comprimir ocupan lo mismo,
12.135.987 bytes, porque las dos guardan un número por fila. Comprimidas siguen siendo las dos
más pesadas, y por el mismo motivo: no hay nada que se repita.

### Paso 6. Las mismas filas con menos columnas

```sql
COPY (SELECT CAST(timestamp AS DATE) AS day, COMP FROM read_parquet('...'))
TO 'cols_3.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);
```

```anota
SELECT CAST(timestamp AS DATE) AS day, COMP | se queda con dos columnas: el día y una señal digital
```

```salida
  las 17 columns ->  16.83 MB   la contabilidad predecia 16,985.4 KB, midio 17,235.4 KB
       5 columns ->   9.04 MB   la contabilidad predecia 9,130.3 KB, midio 9,257.0 KB
       4 columns ->   4.00 MB   la contabilidad predecia 3,969.4 KB, midio 4,095.0 KB
       2 columns ->   0.03 MB   la contabilidad predecia 28.7 KB, midio 34.4 KB
```

El número de filas no cambia en ninguna de las cuatro. Es siempre 1.516.948.

## El resultado, medido

{{FIG:fig_m07_csv_vs_parquet}}

**Qué esperábamos.** Que Parquet ganara al CSV, y que la ventaja fuera parecida en las tres
preguntas.

**Qué salió.** Ganó, y la ventaja **no** es parecida. Con una columna es de **54 veces**, y con
siete baja a **25 veces**. La cifra del módulo es la primera, porque preguntar por una sola
columna es el caso normal.

Esa pendiente es la definición de columnar, medida. Cuantas más columnas pide la pregunta, más se
parece Parquet a leer el fichero entero, y menos gana. Con las diecisiete la ventaja seguiría
cayendo.

**Y contar filas queda fuera de esa comparación a propósito.** Parquet no lee ni un dato para
contestarla: el número de filas está escrito en la cabecera del fichero. Así que ahí no se
comparan dos formas de leer, se compara leer 208 MB contra no leer nada. El factor sale enorme y
además **baila mucho entre corridas**: en esta salió de **129 veces** y en otra pasó del doble.
El lado de Parquet está en el suelo de lo que el reloj distingue, así que ese número no titula
nada.

**Y el resultado que no esperaba nadie.** Las mismas **1.516.948 filas** ocupan **16,83 MB con
las 17 columnas y 0,03 MB con 2**. Quinientas sesenta y una veces menos, sin quitar una sola fila.

{{FIG:fig_m07_filas_vs_columnas}}

**Qué significa.** El peso de un fichero de datos no está en cuántas filas tiene. Está en **cuánto
se repiten los valores de sus columnas**, y la figura lo enseña en sus dos paneles a la vez.

A la izquierda, lo que pesa cada columna. A la derecha, cuántos valores distintos tiene. Son
prácticamente el mismo dibujo, y ahí está la regla.

La columna `timestamp` no repite ningún valor: tiene 1.516.948 distintos en 1.516.948 filas. No
hay nada que agrupar, así que se guardan todos y se lleva el **30,4 %** del fichero ella sola.
`source_index` está en el mismo caso.

Las ocho digitales están en el extremo contrario. Solo valen cero o uno, así que el fichero
guarda esos dos valores una vez y luego referencias. `LPS` entera pesa menos de dos kilobytes.

Y una comprobación de que esa contabilidad es de fiar. El script suma lo que pesan las cuatro
columnas de la tercera fila de la escalera y le salen **3.969,4 KB**, mientras que ese fichero
mide **4.095,0 KB**. El desvío es del **3,1 %** y es la cabecera del propio fichero. Dicho de
otro modo: el reparto por columnas predice el tamaño antes de escribirlo.

## Ojo

- **Parquet no es siempre mejor.** Para añadir una fila al final, un CSV es imbatible. Parquet
  está pensado para escribir de una vez y leer muchas, que es lo que hace un lago.
- **Un CSV se abre con cualquier cosa y un Parquet no.** Se necesita una herramienta que lo lea.
  A cambio, el CSV no sabe qué tipo tiene cada columna y hay que adivinarlo en cada lectura.
- **Quitar columnas no es una técnica de compresión.** Es tirar datos. La escalera de la lección
  sirve para entender de dónde viene el peso, no para publicar ficheros mutilados.
- **La cardinalidad manda sobre el tipo.** Una columna de texto con dos valores distintos comprime
  mejor que una de números con un millón. Lo que importa es cuánto se repite, no si es texto.
- **Los tiempos de la salida son de una corrida concreta.** En otra máquina saldrán distintos. Lo
  que aguanta es la pendiente: la ventaja de Parquet se encoge al pedir más columnas.
- **Cuanto más rápida es una medida, menos fiable es su factor.** El de contar filas llegó a más
  que doblarse entre corridas, porque mide algo tan corto que domina el ruido de la máquina. Los
  otros dos apenas se movieron.

## Puente metalúrgico

Una muestra de mineral se puede guardar de dos formas en el almacén de testigos. Sondeo a sondeo,
con todos sus intervalos seguidos en una caja. O por variable, con todas las leyes de cobre de
todos los sondeos juntas en un registro.

Para reconstruir un sondeo concreto, la primera es cómoda. Para calcular la ley media de cobre
del yacimiento, la segunda te ahorra abrir todas las cajas.

Y hay un detalle que se parece al de las columnas digitales. En un registro de litología, la
misma unidad se repite metro tras metro, así que se anota una vez con su tramo. Nadie escribe
«esquisto» cuatrocientas veces seguidas. Eso es exactamente lo que hace un diccionario en
Parquet.

## Repaso

### Cuál es la diferencia entre guardar por filas y guardar por columnas

Por filas, cada registro va completo y detrás va el siguiente. Por columnas, todos los valores de
una misma columna van juntos y luego empieza la siguiente columna. El contenido es el mismo y lo
que cambia es qué hace falta leer para contestar una pregunta.

### Por qué la ventaja de Parquet baja de 54 veces a 25

Porque la ventaja consiste en no leer las columnas que no se piden. Con una sola columna se lee
una diecisieteava parte del fichero. Pidiendo siete de diecisiete ya hay que leer casi la mitad,
y la ventaja se encoge hasta lo que aporta el formato binario frente al texto.

### Las mismas filas ocupan 16,83 MB o 0,03 MB. Cómo puede ser

Porque el peso lo pone la repetición, no el recuento de filas. La versión de dos columnas guarda
el día y una señal que solo vale cero o uno, y las dos repiten muchísimo, así que se comprimen
casi a nada. La de diecisiete arrastra el `timestamp`, que no repite ni un valor y no se puede
comprimir.

### Cómo sabes lo que pesa una columna sin ir probando

Preguntándoselo al fichero. Parquet escribe dentro su propia contabilidad, con el tamaño
comprimido de cada columna en cada bloque, y DuckDB la expone con `parquet_metadata`. No es una
estimación: es el fichero describiéndose a sí mismo.

### Si tuvieras que reducir el peso de una tabla, por dónde empezarías

Por mirar la cardinalidad de sus columnas antes de tocar nada. La que no repite valores es la que
paga el fichero, y casi siempre es una marca de tiempo o un identificador. A partir de ahí las
opciones son concretas: guardarla con menos precisión, sacarla a otra tabla, o dejarla y aceptar
lo que cuesta.

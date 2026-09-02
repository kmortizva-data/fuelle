---
module: 18
---

## En 30 segundos

- Una carpeta de Parquet **olvida**. La sobrescribes y lo de ayer ya no existe.
- Un **formato de tabla abierto** guarda las versiones viejas y apunta cuál es la buena.
- El historial de este módulo no está inventado: es **el fallo real de la plata**.
- La tabla vieja decía **0,32 h contra 3,17 h** de carga al día. Un factor de diez, sin avisar.
- Se montan **los dos** formatos y se miden. Delta ocupa **4,2 veces** menos, e Iceberg lee más rápido.

## Qué resuelve este módulo

Todo lo que ha construido este curso sobrescribe. `bronze.py` borra la carpeta y la vuelve a
escribir; `dbt build` reemplaza la tabla de oro. Es lo normal, y funciona.

Hasta que alguien pregunta qué decía el panel la semana pasada.

Y no es una pregunta de curiosos. Este proyecto tuvo un fallo de verdad en la capa de plata.
La primera versión cruzaba las lecturas con la rejilla por marca de tiempo exacta, y se quedaba
con **151.657 de 1.516.948**, una de cada diez. El fallo se encontró y se arregló.

Lo que no hay forma de contestar es qué estuvo enseñando el panel mientras tanto, porque esa
tabla ya no existe. Se sobrescribió.

## Antes de la teoría: un ejemplo de juguete

El laboratorio te manda las leyes de tres lotes:

| lote | ley |
|---|---|
| L1 | 1,0 |
| L2 | 1,2 |
| L3 | 0,8 |

Calculas la media, **1,0 %**, y la mandas al cliente.

El martes el laboratorio recalibra y reenvía el fichero con leyes corregidas. Tú lo guardas
encima del anterior, recalculas y mandas **1,3 %**.

El jueves el cliente llama: por qué le dijiste 1,0 el lunes.

Y no puedes contestar. No es que no te acuerdes: **los datos del lunes ya no están**. Sabes lo que
dice el fichero de hoy y nada más.

El arreglo evidente es guardar una copia con la fecha en el nombre. Funciona hasta que hay tres
tablas y cuarenta días, y entonces nadie sabe cuál era la buena de cada momento.

El arreglo bueno es otro. Los ficheros viejos **no se borran**, y al lado se escribe un cuaderno
con una línea por cambio: «desde hoy, la tabla son estos ficheros». Para leer el lunes se lee
hasta la línea del lunes.

Eso es un formato de tabla abierto, y no es más que eso: los mismos Parquet de siempre, más un
cuaderno.

## Glosario

- **Formato de tabla abierto.** Una convención para tratar una carpeta de Parquet como una tabla
  con historial. Delta Lake e Iceberg son los dos que se usan sin Spark.
- **Versión, o instantánea.** El estado de la tabla después de un cambio. Se numeran.
- **Registro de transacciones.** El cuaderno del ejemplo. En Delta es una carpeta `_delta_log`
  dentro de la propia tabla.
- **Metadatos.** En Iceberg, los ficheros que dicen de qué ficheros se compone cada versión.
- **Catálogo.** Quien sabe dónde está cada tabla y cuál es su versión buena. Iceberg lo exige;
  Delta no.
- **Viaje en el tiempo.** Consultar una versión que ya no es la actual.

## Paso a paso

### Paso 1. Fabricar el historial, que ya existía

No hace falta inventar dos versiones. La tabla de oro se calcula dos veces: una sobre la plata
con el fallo y otra sobre la arreglada. La primera es la **versión 0** y la segunda la **1**.

Reproducir el fallo no obliga a rescatar el script viejo. El fallo cabía en un `JOIN`, así que
basta con cruzar por marca de tiempo exacta otra vez.

### Paso 2. Delta: escribir en una carpeta vacía

Se le apunta a una carpeta y se escribe. Dos escrituras seguidas dejan dos versiones, y el
`_delta_log` guarda cuál es cuál.

### Paso 3. Iceberg: montar un catálogo antes

Iceberg no arranca sin alguien que lleve la lista de tablas. El más barato sin servidor es
**SQLite en un fichero**, y ese fichero es todo el montaje.

Esta diferencia no necesita cronómetro y es la primera que aparece.

### Paso 4. Preguntar por la última y por la vieja

Las dos se leen desde DuckDB con las extensiones `delta` e `iceberg`. La consulta normal pide la
última versión. El viaje en el tiempo es la misma consulta con una pieza más.

### Paso 5. Medir, con mediana de siete

Como el módulo 6, y con su regla: si los rangos de dos medidas se solapan, **no hay diferencia
que contar**. Lo decide `distinguishable()` y no las medianas.

## El código, por partes

### Paso 6. Las dos versiones en Delta

```python
write_deltalake(str(DELTA), v0, mode="overwrite")
write_deltalake(str(DELTA), v1, mode="overwrite")
```

```anota
mode="overwrite" | reemplaza el contenido de la tabla. La versión anterior NO se borra: se queda en la carpeta y el registro apunta a la nueva
dos llamadas | dos versiones. Nada más hay que hacer, y no hay carpeta que preparar
```

### Paso 7. Las dos versiones en Iceberg

```python
cat = catalogo_iceberg()
cat.create_namespace_if_not_exists("oro")
tabla = cat.create_table("oro.ciclo_diario", schema=v0.schema)
tabla.append(v0)
tabla.overwrite(v1)
```

```anota
catalogo_iceberg() | abre el catálogo SQLite. Sin él no hay tabla que valga
create_namespace | Iceberg agrupa las tablas en espacios de nombres, como los esquemas de una base de datos
create_table | hay que declarar el esquema por adelantado. Delta lo deduce de los datos
append y overwrite | dos cambios, dos instantáneas
```

Cuatro líneas contra dos, y una de ellas monta una base de datos. Es la misma tabla.

### Paso 8. La última versión, en Delta

```sql
SELECT count(*) AS dias, round(avg(horas_de_carga), 2) AS horas
FROM delta_scan('lake/_formatos_de_tabla/delta');
```

```anota
delta_scan | lee una tabla Delta. Antes hay que INSTALL delta y LOAD delta, una sola vez
la ruta | la carpeta de la tabla, sin más. El registro vive dentro
```

```salida
┌───────┬────────┐
│ dias  │ horas  │
│ int64 │ double │
├───────┼────────┤
│   212 │   3.17 │
└───────┴────────┘
```

### Paso 9. Y ahora la vieja

```sql
SELECT count(*) AS dias, round(avg(horas_de_carga), 2) AS horas
FROM delta_scan('lake/_formatos_de_tabla/delta', version = 0);
```

```anota
version = 0 | la primera versión. Es todo lo que separa una consulta normal de un viaje en el tiempo
```

```salida
┌───────┬────────┐
│ dias  │ horas  │
│ int64 │ double │
├───────┼────────┤
│   212 │   0.32 │
└───────┴────────┘
```

Los mismos **212** días, y una décima parte de las horas de carga. Eso es lo que estuvo enseñando
el panel, y no da ningún error: es un compresor que parece ir sobrado de trabajo.

### Paso 10. Lo mismo en Iceberg, y lo que cuesta

```sql
SELECT count(*) AS dias, round(avg(horas_de_carga), 2) AS horas
FROM iceberg_scan('lake/_formatos_de_tabla/iceberg_ultima.metadata.json');
```

```anota
iceberg_scan | lee una tabla Iceberg, y quiere el fichero de metadatos exacto, no la carpeta
iceberg_ultima.metadata.json | un apaño de este proyecto, y la lección lo explica justo debajo
```

```salida
┌───────┬────────┐
│ dias  │ horas  │
│ int64 │ double │
├───────┼────────┤
│   212 │   3.17 │
└───────┴────────┘
```

Ese nombre de fichero es una copia que este proyecto mantiene a mano. El de verdad se llama
`00002-d4a1ce7d-...metadata.json`, con un identificador que cambia en cada corrida.

Y no es un capricho de la herramienta. **Quien sabe cuál es la versión buena de una tabla Iceberg
es el catálogo, no la carpeta.** DuckDB se niega a adivinarlo mirando los ficheros, y hace bien:
podría leer algo a medio escribir. Delta no tiene este problema porque su registro está dentro de
la propia tabla.

### Paso 11. Las dos versiones, una al lado de la otra

```sql-vivo
SELECT a.dia,
       a.horas_de_carga                               AS antes,
       b.horas_de_carga                               AS ahora,
       round(b.horas_de_carga - a.horas_de_carga, 2)  AS diferencia
FROM antes a
JOIN ahora b ON b.dia = a.dia
WHERE a.dia = DATE '2020-04-18';
```

```salida
┌────────────┬────────┬────────┬────────────┐
│    dia     │ antes  │ ahora  │ diferencia │
│    date    │ double │ double │   double   │
├────────────┼────────┼────────┼────────────┤
│ 2020-04-18 │   2.36 │   23.6 │      21.24 │
└────────────┴────────┴────────┴────────────┘
```

El 18 de abril es la avería número uno, el peor día del semestre. La tabla vieja lo daba en
**2,36** horas de carga, un día tirando a tranquilo. Son **23,6**.

## El resultado, medido

{{FIG:fig_m18_historial_de_versiones}}

**Qué esperábamos.** Que la versión vieja se pareciera a la buena con algo de ruido.

**Qué salió.** Una línea casi plana. La versión con el fallo no está desviada: está **aplastada**,
y los picos de las averías desaparecen dentro del grosor de la línea.

Ese es el argumento del módulo dibujado. Un panel alimentado por esa tabla no habría dado ni un
error, ni una alarma, ni un valor imposible. Habría enseñado un compresor tranquilo durante
meses.

### Los dos formatos, medidos

{{FIG:fig_m18_delta_contra_iceberg}}

Y aquí no hay empate, que era el resultado más probable a esta escala. Los dos se separan, y en
sentidos contrarios:

| Qué | Delta | Iceberg |
|---|---|---|
| Montaje | nada, una carpeta vacía | un catálogo SQLite |
| En disco | 12,9 KB | 53,7 KB |
| Ficheros | 4 | 12 |
| Escribir las dos versiones | unas 3 veces más rápido | |
| Leer, incluso preguntando al catálogo | | unas 2 veces más rápido |

**Iceberg ocupa 4,2 veces más disco** para guardar exactamente la misma tabla, y deja **12**
ficheros donde Delta deja **4**. La razón es lo que cada uno considera metadatos. Delta apunta
una línea por versión en su registro; Iceberg escribe tres cosas en cada cambio, un fichero de
metadatos, una lista de manifiestos y un manifiesto.

**Y hay un detalle de contabilidad que conviene mirar.** Delta guarda **2** versiones, que son las
dos escrituras. Iceberg deja **3** metadatos, porque crear la tabla vacía ya es un cambio con su
instantánea.

**Una honestidad sobre la medida de lectura.** Las dos primeras lecturas de Iceberg parten de un
fichero de metadatos que ya sabemos dónde está, y eso se salta el paso que una consulta de verdad
no se puede saltar. Por eso hay una cuarta medida, «leer preguntando primero», que paga la
consulta al catálogo. Sigue leyendo más rápido, así que la ventaja es real y no un regalo del
método.

**Qué significa.** Ninguno de los dos gana. Delta es más barato de montar, de escribir y de
guardar. Iceberg lee más rápido, y trae un catálogo que con unas cuantas tablas deja de estorbar
y pasa a ser lo que buscabas. Para este proyecto, con una tabla de oro y sin servidor, **Delta es
la elección**, y ahora eso es una conclusión y no una preferencia.

## Ojo

- **Guardar historial no es gratis.** Los ficheros viejos ocupan y no se limpian solos. Los dos
  formatos traen una orden para tirar lo anterior, y usarla borra el viaje en el tiempo.
- **Esto no es una copia de seguridad.** Protege de un cálculo malo, no de un disco roto. Si se
  pierde la carpeta se pierden todas las versiones a la vez.
- **El viaje en el tiempo no arregla el fallo, lo explica.** Sirve para contestar qué se enseñó y
  desde cuándo. Arreglar el dato sigue siendo trabajo aparte.
- **La extensión de DuckDB solo lee.** Escribir pide los paquetes de Python de cada formato. Es
  suficiente para un lago como este y conviene saberlo antes de diseñar sobre ello.
- **El navegador de esta página no tiene ninguna de las dos extensiones.** Por eso el reto de
  abajo no viaja en el tiempo: se baja las dos versiones ya extraídas y las cruza, que es la
  habilidad que de verdad se usa después.
- **Sin catálogo, Iceberg fuera de su herramienta es incómodo.** Hay que decirle a la consulta el
  fichero de metadatos exacto, y ese nombre solo lo conoce el catálogo.

## Puente metalúrgico

Un laboratorio no borra el resultado del lunes cuando recalibra el equipo. Emite un certificado
nuevo, con su número y su fecha, y el viejo se queda en el archivo marcado como superado.

Nadie lo hace por nostalgia. El mineral del lunes ya se vendió con aquel número delante, y el
día que alguien discuta la factura hay que enseñar en qué se basó la decisión.

Un formato de tabla abierto es ese archivo de certificados. Y la pregunta que contesta es la
misma: no cuál es la ley, sino **cuál era la ley que teníamos delante cuando decidimos**.

## Hazlo tú

```reto
pregunta: Cruza las dos versiones de la tabla y saca los cinco días donde más se contradicen. Devuelve `dia`, `antes`, `ahora` y `diferencia` con las horas que van de una a otra, redondeada a dos decimales, ordenando de mayor a menor. Cinco filas.
inicio: SELECT a.dia,
       a.horas_de_carga  AS antes,
       b.horas_de_carga  AS ahora
FROM antes a
JOIN ahora b ON b.dia = a.dia;
esperado: m18_donde_mentia
pista: El cruce ya está hecho y las dos columnas también. Falta la resta, que es `ahora` menos `antes` metida en un `round(..., 2)`, y después ordenar por ella hacia abajo y quedarse con cinco. Las dos columnas de la resta hay que escribirlas enteras, `b.horas_de_carga - a.horas_de_carga`, porque el nombre corto todavía no existe al calcularla.
solucion: SELECT a.dia,
       a.horas_de_carga                               AS antes,
       b.horas_de_carga                               AS ahora,
       round(b.horas_de_carga - a.horas_de_carga, 2)  AS diferencia
FROM antes a
JOIN ahora b ON b.dia = a.dia
ORDER BY diferencia DESC
LIMIT 5;
```

Las cinco filas que salen son cinco días de avería o de mucho trabajo, y son justo los que la
versión vieja escondía. El fallo no repartía su error por igual: se comía más cuanto más había
que ver.

## Repaso

### Por qué una carpeta de Parquet no puede contestar qué decía el panel ayer

Porque no guarda nada de ayer. Sobrescribir un fichero deja un solo estado, el último, y el
anterior no está en ninguna parte. La carpeta sabe qué contiene, y no sabe qué contenía.

### Qué añade un formato de tabla abierto a esa misma carpeta

Un cuaderno al lado. Los datos siguen siendo Parquet corriente, y lo nuevo es un registro con una
línea por cambio, diciendo de qué ficheros se compone la tabla desde ese momento. Leer una
versión vieja es leer el cuaderno hasta esa línea.

### La diferencia entre Delta e Iceberg que se nota antes de medir nada

El montaje. Delta escribe en una carpeta vacía y no pide nada más. Iceberg necesita un catálogo
antes de aceptar una sola fila, y aquí ha sido un SQLite en un fichero. Con una tabla eso es
puro estorbo, y con cuarenta es exactamente lo que hace falta.

### Tu tabla lleva un año escribiéndose a diario y ocupa diez veces lo que debería

Es el historial, y es el precio anunciado. Cada escritura deja los ficheros viejos donde estaban.
Los dos formatos traen una orden para tirar lo anterior a partir de cierta antigüedad, y hay que
elegir esa antigüedad sabiendo que borra el viaje en el tiempo hasta ahí.

### Encuentras un fallo de cálculo de hace un mes. Qué te da esto que no tenías

La respuesta a qué se enseñó y desde cuándo, que es lo que va a preguntar quien tomó decisiones
con esos números delante. Aquí la versión vieja daba 0,32 horas de carga al día y la buena da
3,17, y el 18 de abril, el peor día del semestre, aparecía como un día tranquilo.

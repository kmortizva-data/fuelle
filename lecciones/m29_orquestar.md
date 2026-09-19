---
module: 29
---

## En 30 segundos

- Hasta aquí el lago se construía **a mano**, script a script, en un orden que solo estaba escrito
  en una tabla del README.
- Un **orquestador** sabe el orden solo, porque cada pieza declara de qué sale:
  **27 activos y 31 flechas**, y ninguna dibujada a mano.
- La prueba es borrar el lago entero y pedírselo todo. **La primera vez no salió igual**, y lo que
  encontró corrigió cuatro lecciones ya publicadas.
- Arreglado, sale **14 de 14**: todas las tablas iguales, y cada fichero Parquet idéntico
  **byte a byte**.
- La regla de todo el módulo: **lo que corre el orquestador tiene que dar lo mismo cada vez**.
  Por eso el cronómetro se queda fuera.

## Qué resuelve este módulo

Todas las piezas del lago existen y están comprobadas, de la ingesta al veredicto del gemelo. Pero
existen en esta máquina, y se construyeron corriendo scripts a mano en un orden que había que saber.

Eso aguanta mientras nada se rompe. Tres situaciones lo rompen, y las tres pasan en cualquier planta:

- **Una máquina nueva.** Alguien clona el repositorio y tiene que reconstruir el lago. ¿En qué
  orden? El README lo dice, si está al día.
- **Un fallo de red a las tres de la mañana.** El clima se pide a una API ajena. Si esa noche no
  contesta, alguien tiene que acordarse de volver a pedirlo.
- **Un día que llega mal.** Si el 5 de junio se estropea, rehacer el lago entero para arreglar un
  día es tirar casi todo el trabajo.

Un orquestador resuelve las tres: **conoce el orden, reintenta lo que falla y rellena hacia atrás**.
Y con él llega la única prueba honesta de que el lago se puede reconstruir: borrarlo y mirar.

## Antes de la teoría: un ejemplo de juguete

Una concentradora cierra cada día con cuatro tareas:

| Tarea | Necesita antes |
|---|---|
| pesar el mineral | nada, sale de la báscula |
| muestrear | nada, sale del muestreador |
| analizar la ley | la muestra |
| cerrar el balance | el peso y la ley |

**Tres flechas.** Nadie tiene que escribir «primero esto, luego aquello»: el orden sale de las
flechas. Pesar y muestrear pueden ir a la vez, analizar va después de muestrear, y el balance va
el último porque necesita las otras dos.

Ahora, tres noches malas de un mes de 30 días:

1. **El analizador del laboratorio falla a las tres de la mañana.** Casi siempre es un tropiezo:
   se reintenta a los diez minutos y funciona. Nadie debería despertarse por eso.
2. **La muestra del martes llegó contaminada.** Se repite el análisis del martes y el balance del
   martes. **Un día de 30**, no el mes entero.
3. **Se pierde el libro de balances del mes.** Si se puede rehacer entero desde los pesos y las
   leyes, y sale igual, el procedimiento está escrito de verdad. Si no sale igual, algo dependía de
   la memoria de alguien.

Las tres cosas tienen nombre: **reintentar, rellenar hacia atrás y reconstruir**. Este módulo las
hace con el lago, y la tercera fue la que dio la sorpresa.

## Glosario

- **Orquestador.** El programa que sabe qué hay que construir, en qué orden, y qué hacer cuando
  algo falla. Aquí es **Dagster**.
- **Activo.** Algo que debería existir: una carpeta de Parquet, una tabla, un fichero de
  resultados. Cada uno declara de qué se construye.
- **Materializar.** Construir un activo y dejar apuntado cuándo y con qué resultado.
- **Dependencia.** La flecha «se construye a partir de». Es la misma idea que el `ref()` del
  módulo 17, para todo el proyecto y no solo para el oro.
- **Partición.** Un trozo de un activo que se puede construir por separado. Aquí, un día del
  bronce.
- **Rellenar hacia atrás.** Reconstruir un tramo de particiones pasadas sin tocar las demás. En
  inglés se dice *backfill*, y así lo llama Dagster.
- **Política de reintentos.** Cuántas veces se repite un paso que falla y cuánto se espera entre
  intento e intento.
- **Comprobación de activo.** Una prueba que corre justo después de construir un activo. Es el
  contrato del módulo 16 con otro nombre.
- **Determinista.** Que con las mismas entradas dé siempre lo mismo, hasta el último byte. Un
  cronómetro no lo es, y resultó que un escritor en paralelo tampoco.
- **Hilo.** Cada una de las tareas que un programa corre a la vez. DuckDB usa tantos como núcleos
  tiene la máquina, y eso tiene un precio que este módulo mide.
- **Huella de contenido.** Cuántas filas tiene una tabla y la suma de un número sacado de cada una.
  La del módulo 5 miraba los bytes del fichero; esta mira lo que dicen.

## Paso a paso

### Paso 1. Declarar cada pieza, y de qué sale

Cada activo lleva un nombre y la lista de lo que necesita. Con eso Dagster dibuja el grafo, decide
el orden y sabe qué queda viejo cuando algo cambia aguas arriba.

### Paso 2. Declarar también lo que nadie construye

El CSV de la UCI, la API del clima y los partes de avería no los construye nadie aquí. **Se
declaran igual**, porque el grafo tiene que empezar donde empieza de verdad. No se pueden
materializar, y en la figura van con el borde discontinuo.

### Paso 3. Partir por día lo que llega por días

El bronce ya estaba en una carpeta por día desde el módulo 4. Ahora Dagster lo sabe, y eso le
permite rehacer un día suelto o un tramo de días sin tocar los demás.

### Paso 4. Reintentar solo donde hay red

Solo una pieza habla con el exterior: la descarga del clima. **Es la única con reintentos.** Poner
reintentos en todo esconde fallos de verdad detrás de repeticiones que nunca van a funcionar.

### Paso 5. Colgar de cada activo las pruebas que ya existían

El contrato del módulo 16 pasa a vigilar la plata, las once pruebas de dbt del módulo 17 entran
solas, y la restauración del módulo 22 vigila la copia. Ninguna se reescribe: se cuelgan.

### Paso 6. Separar construir de cronometrar

Los scripts de las lecciones hacían dos cosas a la vez: construir, y medir cuánto tardaban en
construir con la mediana de siete corridas.

**Un orquestador no puede cronometrar.** El cronómetro no da dos veces lo mismo, así que cada
reconstrucción reescribiría las cifras que publican las lecciones. La regla quedó así: lo que corre
el orquestador tiene que dar lo mismo cada vez. **Seis scripts se partieron en dos**, y su parte de
medir sigue ahí, para correrla a mano.

## El código, por partes

### Paso 7. Un activo que llama a lo que ya había

```python
@dg.asset(key=["lago", "plata"], deps=[bronce], group_name="lago")
def plata() -> dg.MaterializeResult:
    from transform import silver

    hecho = _corre(silver.construye)
    return dg.MaterializeResult(metadata=hecho)
```

```anota
@dg.asset | convierte la función en un activo: algo que Dagster sabe construir
key=["lago", "plata"] | su nombre en el grafo, con el grupo delante como en una carpeta
deps=[bronce] | la flecha: la plata se construye a partir del bronce. De aquí sale el orden
silver.construye | la función del módulo 14: el orquestador no calcula nada nuevo
_corre | convierte el «me niego a seguir» de un script en un fallo del activo, con el mismo mensaje
MaterializeResult | lo que queda apuntado de esta construcción: filas, lecturas y huecos
```

Ni una línea de la plata se reescribe aquí. **El orquestador pone el orden, no la aritmética.**

### Paso 8. El bronce, día a día

```python
DIAS = dg.DailyPartitionsDefinition(start_date="2020-02-01", end_date="2020-09-02")

@dg.asset(key=["lago", "bronce"], deps=[CSV], partitions_def=DIAS,
          backfill_policy=dg.BackfillPolicy.single_run())
def bronce(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    tramo = context.partition_key_range
    dias = (tramo.start, tramo.end)
    bronze.clear(dias)
    bronze.write(con, dias)
```

```anota
DailyPartitionsDefinition | una partición por día de calendario. El último no entra, por eso se escribe el 2 de septiembre
partitions_def=DIAS | el bronce queda partido por días: se puede construir entero o a trozos
BackfillPolicy.single_run() | un tramo de días va en una sola corrida y no en una por día: leer el CSV entero cada vez sería absurdo
partition_key_range | el tramo que toca construir: del primer día al último, o un día solo
bronze.clear(dias) | borra solo las carpetas de ese tramo. Las demás ni se abren
```

El calendario tiene **214 días** y el bronce, **212 carpetas**. Los dos que faltan son el 29 de
febrero y el 26 de abril, los días sin una sola lectura que encontró el módulo 8. **El orquestador
conoce el calendario; el dato, no.** Esos dos días se construyen igual y salen vacíos.

### Paso 9. El clima, con reintentos

```python
@dg.asset(key=["lago", "clima"], deps=[OPEN_METEO],
          retry_policy=dg.RetryPolicy(max_retries=3, delay=10,
                                      backoff=dg.Backoff.EXPONENTIAL))
def clima() -> dg.MaterializeResult:
```

```anota
retry_policy | qué hacer si el paso falla: repetirlo en vez de rendirse
max_retries=3 | hasta tres intentos más después del primero
delay=10 | espera diez segundos antes del primer reintento
Backoff.EXPONENTIAL | y cada espera dobla la anterior: diez, veinte y cuarenta
```

Esperar cada vez más no es capricho. Si la API está saturada, reintentar enseguida la satura más, y
cuatro intentos seguidos en un segundo fallan los cuatro por la misma razón.

### Paso 10. El oro, sin reescribir dbt

```python
@dbt_assets(manifest=DBT.manifest_path, project=DBT)
def oro(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()
```

```anota
@dbt_assets | lee el manifest del módulo 17 y convierte cada modelo en un activo
manifest=DBT.manifest_path | el mismo fichero del que salía el mapa del módulo 17
dbt.cli(["build"]) | la misma orden de siempre: construir y probar en el orden del grafo
.stream() | cada modelo terminado se apunta en Dagster, y cada prueba de dbt, como comprobación
```

Las fuentes del proyecto dbt se llaman `lago.plata`, `lago.clima` y `lago.averias`. Los activos de
los pasos anteriores se llaman igual, así que **las flechas entre Dagster y dbt se ponen solas**.

### Paso 11. La huella de una tabla, en una consulta

La prueba compara cada tabla por lo que contiene, no por sus bytes. Delta e Iceberg escriben
fechas y nombres aleatorios en su propio registro, así que dos tablas idénticas nunca tienen los
mismos bytes. Lo que se compara es esto:

```sql
SELECT count(*) AS filas, sum(hash(t)::HUGEINT) AS huella
FROM read_parquet('lake/bronze/failures/failures.parquet') t;
```

```anota
hash(t) | un número sacado de la fila entera. Dos filas con un solo valor distinto dan números distintos
::HUGEINT | un entero enorme, para que la suma de millones de filas no se desborde
sum(...) | sumar no depende del orden de las filas, y una fila repetida sí mueve la suma
```

```salida
┌───────┬──────────────────────┐
│ filas │        huella        │
│ int64 │        int128        │
├───────┼──────────────────────┤
│     4 │ 41458351517739629285 │
└───────┴──────────────────────┘
```

Una fila duplicada, un valor cambiado o una fila de menos mueven la huella. Una tabla escrita en
otro orden, o partida en otros ficheros, no. Y esa segunda mitad es la que casi esconde el hallazgo
del módulo.

### Paso 12. Apartar el lago entero y pedirlo todo

```python
LAGO.rename(ANTES)
for grupo, que, seleccion, extra in pasos:
    tardo, r = materializa(seleccion, **extra)
```

```anota
LAGO.rename(ANTES) | el lago entero pasa a otra carpeta. Desde aquí, no hay lago
materializa(seleccion) | le pide a Dagster un grupo entero, y él decide el orden dentro
```

Esta es la última corrida, la que salió igual. Los tiempos son de esta corrida y no se repiten; lo
que se repite es cada «igual».

```salida
  el grafo: 27 activos, 24 que se pueden construir, 31 dependencias y 13 comprobaciones
  1. las huellas del lago de ahora, tabla a tabla
     14 tablas y versiones, 642 ficheros Parquet
  2. el lago entero pasa a lake_antes/: desde aquí, no hay lago
  3. Dagster lo construye todo, con los mismos pasos que construye.py
     bien  el bronce, los 214 días en una corrida       26.0 s
     bien  el resto del lago, con el oro de dbt         51.4 s
     bien  lo que consultan las lecciones                5.3 s
     bien  el gemelo, de la física al veredicto         45.0 s
     bien  PostgreSQL, desde initdb                    146.2 s
  4. las huellas del lago nuevo, y la comparación
     igual    lago/bronce                          1,516,948 filas
     igual    lago/clima                               5,136 filas
     igual    lago/averias                                 4 filas
     igual    lago/plata                           1,841,760 filas
     igual    lago/historia, Delta, versión 0            212 filas
     igual    lago/historia, Delta, versión 1            212 filas
     igual    lago/historia, Iceberg, versión 0          212 filas
     igual    lago/historia, Iceberg, versión 1          212 filas
     igual    lecciones/todo_en_un_parquet         1,516,948 filas
     igual    lago/oro_averias                             4 filas
     igual    lago/oro_ciclo_diario                      212 filas
     igual    lago/oro_horas                           4,416 filas
     igual    servidor/lecturas                    1,841,760 filas
     igual    servidor/dias                              214 filas
     igual    el servidor: 12 guardas, 3 índices, roles fuelle, mirona
     iguales  642 de 642 ficheros Parquet byte a byte (642 ahora)
     0 ficheros versionados distintos en results/ y assets/
     13 de 13 comprobaciones de Dagster en verde
  5. las diez puertas, contra el lago nuevo
     10 en verde, salida 0
  6. rellenar hacia atrás: se estropea el 2020-06-05 y se rehace solo ese día
     igual    el día rehecho, byte a byte
     211 de 211 ficheros de los otros días, sin tocar
  todo igual: lake_antes/ borrado
  4.6 minutos en total
```

### Paso 13. Escribir con un solo hilo

```python
@contextlib.contextmanager
def un_solo_hilo(con):
    antes = con.sql("SELECT current_setting('threads')").fetchone()[0]
    con.execute("SET threads = 1")
    try:
        yield
    finally:
        con.execute(f"SET threads = {antes}")
```

```anota
current_setting('threads') | cuántos hilos usa DuckDB ahora, para dejarlo igual al terminar
SET threads = 1 | una sola tarea escribiendo, así que las filas salen siempre en el mismo orden y en los mismos ficheros
finally | pase lo que pase dentro, la conexión vuelve a como estaba
```

Y la plata, además, se escribe en orden de tiempo: un `ORDER BY r.timestamp` al final de su
consulta. Ninguna de las dos cosas estaba en el plan. Salieron de la primera reconstrucción, y son
lo que cuenta el resultado.

## El resultado, medido

{{FIG:fig_m29_grafo_de_activos}}

**Qué esperábamos.** Que Dagster reconstruyera el lago y que saliera igual. Todos los scripts ya
estaban comprobados, así que la prueba parecía un trámite.

**Qué salió la primera vez.** **13 de 14** tablas iguales, las diez puertas con una en rojo, y
tres cosas que nadie había visto en 28 módulos:

1. **Una dependencia escondida.** El script del clima lee la plata para las correlaciones del módulo
   15, y el grafo no lo decía. Dagster lo corrió antes de que la plata existiera, y el script, en
   vez de negarse, **escribió `null` en siete cifras publicadas**. A mano nunca pasó, porque el 15
   siempre se corrió después del 14.
2. **Las mismas filas, otros ficheros.** El bronce y la plata volvieron con exactamente el mismo
   contenido, pero repartido en otros ficheros y en otro orden. DuckDB escribe con varios hilos a
   la vez, y cada corrida lo reparte a su manera.
3. **Y eso movía números.** Una media de coma flotante sumada en otro orden cambia en su último
   decimal, y cuando cae justo en la mitad de un redondeo, salta. En `oro_horas`,
   **cinco horas de 4.416 cambiaron una centésima**. Y los pesos de columna que publica el módulo 7, unos bytes.

Para saber qué lo causaba, un experimento escribe cada capa dos veces de cada manera. Las
maneras son dos: con los hilos de DuckDB o con uno solo. La plata, además, sin orden o en orden de
tiempo. Después compara los ficheros de las dos escrituras y las medias horarias de cada una.

```salida
  bronce varios hilos              213 y  213 ficheros,  198 idénticos,  22.06 MB
  bronce un hilo                   212 y  212 ficheros,  212 idénticos,  22.05 MB
  plata  varios hilos, sin orden   402 y  405 ficheros,    1 idénticos,  24.12 MB, 2 de 4416 medias horarias distintas
  plata  un hilo, sin orden        400 y  400 ficheros,  400 idénticos,  22.08 MB, 0 de 4416 medias horarias distintas
  plata  varios hilos, en orden    214 y  214 ficheros,  207 idénticos,  21.88 MB, 0 de 4416 medias horarias distintas
  plata  un hilo, en orden         214 y  214 ficheros,  214 idénticos,  21.88 MB, 0 de 4416 medias horarias distintas
```

**Eran dos causas, y cada una arregla una cosa.** El orden de las filas arregla las medias. La
plata de antes salía en un orden revuelto, distinto en cada corrida, y ordenarla por tiempo deja
las medias quietas incluso con varios hilos. El hilo único arregla los bytes: con varios, aunque
las filas vayan en orden, algún fichero sale distinto cada vez. El lago usa las dos cosas, y es el
paso 13.

**El arreglo del clima** fue partir su script: el orquestador solo lo baja y lo escribe, y el
análisis del módulo 15 se niega si no hay plata.

**Y el arreglo destapó lo peor.** Escrita en orden, la plata ocupa **21,88 MB**, cuando antes
salía en torno a 24: el desorden la inflaba, repartida en unos cuatrocientos ficheros revueltos.
Tres lecciones publicadas se apoyaban en ese tamaño inflado y quedaron corregidas, cada una
contando qué decía:

| Módulo | Decía | Dice ahora |
|---|---|---|
| 14 | los huecos cuestan casi dos megas | **1,38 MB**, medidos escribiendo la plata sin ellos |
| 19 | el servidor ocupa once veces más | **12,2 veces**: 21,9 MB contra 267,8 |
| 22 | la copia pesa menos que el Parquet | pesa un poco más: 22,2 contra 21,9 |
| 7 | los pesos de un fichero escrito desde el bronce revuelto | **16,84 MB**, y el factor de siete columnas baja de 25 a 22 |

**Qué salió la última vez.** Con los dos arreglos, la tercera reconstrucción salió idéntica en
todo:

- **14 de 14** tablas iguales por su contenido.
- **642 de 642** ficheros Parquet iguales byte a byte.
- Ni un resultado publicado distinto.
- Las 13 comprobaciones y las diez puertas, en verde.

Y el relleno hacia atrás: se borró del bronce el 5 de junio, como si hubiera llegado corrupto, y
Dagster rehízo ese día y solo ese. Volvió idéntico byte a byte, y los otros **211** ficheros del
bronce ni se tocaron.

**Qué significa.** Que la prueba sirvió para lo que existe. Los 28 módulos anteriores estaban
comprobados uno a uno, por diez puertas. Aun así, tres de sus cifras dependían de algo que ninguna
comprobación miraba: **que escribir dos veces lo mismo diera los mismos bytes**. Solo se ve
reconstruyendo, porque solo entonces hay dos versiones que comparar.

## Ojo

- **Reproducible no es correcto.** Si un script tuviera un fallo, Dagster lo reconstruiría igual de
  mal y la comparación saldría perfecta. Esta prueba dice que el lago **se puede rehacer**; que
  diga la verdad lo dicen las diez puertas y los módulos anteriores.
- **Una huella de contenido no ve el orden, a propósito.** Por eso la primera reconstrucción dio
  iguales el bronce y la plata mientras sus ficheros eran otros. Hacen falta las dos
  comparaciones: el contenido para las tablas, los bytes para lo que se escribe igual.
- **Un script que escribe `null` en vez de negarse es peor que un fallo.** El fallo del clima
  no dio error: dejó siete huecos en cifras publicadas, y solo lo cazó la puerta de números.
- **El cronómetro se queda fuera, y no por comodidad.** Un orquestador que midiera tiempos
  reescribiría en cada corrida las cifras que publican las lecciones.
- **La reconstrucción no tocó `data/`.** El CSV y el clima descargado son la entrada, no el lago.
  Por eso el clima no habló con la red, y **el reintento no tuvo que actuar**.
- **Una partición vacía no es un error.** El 29 de febrero y el 26 de abril se materializan sin
  una lectura. Dagster no sabe que ese día no hubo datos: eso lo sabe el dato.
- **La interfaz de Dagster es para mirar.** La prueba corre sin ella, desde Python. Si la abres,
  hazlo con `src/orchestration/abre.py`, que fija la carpeta de configuración. Sin ella, Dagster
  manda estadísticas de uso a sus autores.

## Puente metalúrgico

El arranque de un circuito de molienda y flotación lleva décadas funcionando así. Nadie arranca
las celdas antes de las bombas que las alimentan, ni el molino antes de su lubricación. Y nadie
se lo sabe de memoria: **el sistema de control lo impide con enclavamientos**, porque cada equipo
tiene declarado qué necesita aguas arriba.

Un orquestador es esa secuencia de arranque para los datos. Y el balance metalúrgico reconciliado
enseña lo mismo que el relleno hacia atrás: cuando el laboratorio corrige el ensayo de un turno, se
recalcula el balance de ese turno. **No el del año.**

Lo de los hilos también tiene su planta. Dos muestreadores que cortan el mismo flujo con otro
ritmo dan la misma ley media y **otra ley en cada muestra**. Si un informe publica la ley de una
muestra concreta, depende de qué muestreador cortó.

## Repaso

### Qué sabe Dagster que no supiera ya el README

Lo mismo, pero leído del código en vez de escrito a mano. El README tenía una tabla con el orden de
los scripts, y le faltaban dos: el del clima y el de los partes. El grafo de Dagster sale de lo que
cada activo declara, así que no puede olvidarse de nadie. Lo que sí puede es fiarse de una
declaración incompleta, y eso es lo que pasó con el clima.

### Por qué el cronómetro no puede entrar en el orquestador

Porque un orquestador corre lo mismo muchas veces, y cada vez tiene que dar lo mismo. Un tiempo
medido nunca se repite, así que cada reconstrucción reescribiría las cifras publicadas. Construir
se orquesta; medir se queda en los scripts de las lecciones, para correrlo a mano.

### Por qué la prueba compara contenido y además bytes

Porque cada comparación ve lo que la otra no ve. El contenido se puede comparar en cualquier tabla,
también en Delta, Iceberg y PostgreSQL, que nunca repiten sus bytes. Pero no ve el orden de las
filas. Los bytes sí lo ven, y fueron los que destaparon las filas revueltas.

### El 5 de junio llega corrupto. Qué se rehace y qué no

Se rehace la partición de ese día del bronce, y nada más del bronce: la prueba lo hizo y los demás
ficheros no se tocaron. Después hay que rehacer lo que cuelga de él, y ahí entra la plata entera:
en Dagster la plata no está partida por días.

### Una comprobación en verde después de reconstruir. Qué garantiza

Que lo que prometía esa comprobación se cumple sobre el lago nuevo, y nada más. Las once pruebas de
dbt y el contrato del módulo 16 pasaron en la primera reconstrucción, y aun así había siete cifras
a `null`. Una comprobación vigila lo que se le dijo que vigilara.

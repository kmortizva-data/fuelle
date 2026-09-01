---
module: 17
---

## En 30 segundos

- La capa de **oro** son las tablas que responden preguntas, y se escriben en el SQL que ya sabes.
- **dbt** es la herramienta que las construye: cada modelo es **un fichero con un SELECT dentro**.
- Nunca escribes el nombre de la tabla anterior, escribes `ref()`. Con eso dbt **deduce el orden**.
- Y de ahí sale el mapa: **9 nodos** y **8 dependencias**, ninguna colocada a mano.
- Las pruebas del módulo 16 caben en **11 líneas de YAML**, y una que no puede fallar no vale.

## Qué resuelve este módulo

El lago ya tiene tres fuentes, una capa de plata limpia y un contrato que la vigila. Lo que no
tiene es **las tablas que alguien va a consultar de verdad**.

Nadie abre un panel para mirar 1.841.760 lecturas. Se abre para preguntar cuántas horas trabajó
el compresor ayer, o qué pasó los días de avería. Esas respuestas son tablas pequeñas, calculadas
una vez y consultadas muchas, y esa es la capa de oro.

Escribirlas no es el problema: son consultas como las de la parte 3. El problema aparece a la
tercera tabla, cuando una se apoya en otra. Ya no está claro **en qué orden construir**, ni
**qué se rompe** si cambias la de abajo.

## Antes de la teoría: un ejemplo de juguete

Una planta pequeña tiene tres tablas:

| Tabla | De dónde sale |
|---|---|
| `tonelaje` | de la báscula |
| `recuperacion` | de `tonelaje` y de las leyes del laboratorio |
| `informe` | de `recuperacion` |

Dos flechas. Lo tienes en la cabeza sin esfuerzo, y si alguien cambia `tonelaje` sabes al instante
que hay que rehacer las otras dos, en ese orden.

Ahora dibújalo en una pizarra y llega el lunes. Un compañero añade una cuarta tabla, `costes`, que
también sale de `tonelaje`. Escribe su consulta, la deja funcionando y **no toca la pizarra**.

La pizarra sigue enseñando tres cajas y dos flechas. No está incompleta de una forma visible: está
**mintiendo con toda tranquilidad**, y el día que alguien cambie `tonelaje` mirará el dibujo, verá
dos cosas que rehacer y dejará `costes` calculando con datos viejos.

El arreglo no es acordarse de actualizar la pizarra. El arreglo es que **el mapa se lea del
código**, porque el código sí está siempre al día: si `costes` no leyera `tonelaje`, no
funcionaría. La dependencia ya está escrita en la consulta. Lo único que falta es que algo la lea
y la dibuje.

Eso es dbt en una frase.

## Glosario

- **Modelo.** Un fichero con un `SELECT` dentro. Su nombre de fichero es el nombre de la tabla que
  produce. No lleva `CREATE TABLE`: eso lo pone la herramienta.
- **Materializar.** Decidir si un modelo se guarda como tabla (se calcula y ocupa disco) o como
  vista (se recalcula cada vez que se consulta y no ocupa nada).
- **`ref()`.** La forma de nombrar otro modelo. Se escribe `ref('otro_modelo')` en vez del nombre
  de la tabla, y es lo que crea la flecha del mapa.
- **`source()`.** Lo mismo para lo que entra de fuera y dbt no construye: los ficheros del lago.
- **Linaje.** El mapa de qué depende de qué. Aquí se genera; no se dibuja.
- **Grafo dirigido acíclico.** El nombre formal de ese mapa: flechas con sentido y sin bucles. Sin
  bucles porque una tabla no puede depender de sí misma, ni de nadie que dependa de ella.
- **`manifest.json`.** El fichero donde dbt deja todo lo que sabe del proyecto después de
  compilarlo. De ahí sale la figura de este módulo.
- **Prueba de datos.** Lo mismo que una promesa del módulo 16, con el nombre que usa la industria.

## Paso a paso

### Paso 1. Declarar de dónde entra el dato

Las tres fuentes del lago se declaran una vez, con la ruta de su Parquet. A partir de ahí ningún
modelo vuelve a escribir una ruta.

Eso ya paga solo: el día que el lago se mueva de sitio se cambia un fichero y no seis.

### Paso 2. Escribir cada tabla como un SELECT y nada más

Sin `CREATE TABLE`, sin `DROP`, sin `INSERT`. El fichero `oro_horas.sql` contiene la consulta que
produce `oro_horas`, y punto. Dónde se guarda y con qué nombre lo decide la configuración.

### Paso 3. Nombrar a los demás con `ref()`

Esta es la única regla nueva de verdad del módulo. En vez de escribir el nombre de la tabla
anterior, se escribe `ref('prep_telemetria')`.

A cambio de esa incomodidad, **la herramienta se entera de la dependencia**. De ahí salen tres
cosas gratis: el orden de construcción, el mapa, y saber qué rehacer cuando cambia algo arriba.

### Paso 4. Poner las promesas del módulo 16 al lado

Las cuatro pruebas que dbt trae de serie (`unique`, `not_null`, `accepted_values`,
`relationships`) son las promesas del contrato con otro nombre. Se declaran en YAML, y las que no
caben en esas cuatro se escriben a mano como un fichero SQL de cero filas, que es la forma
exacta del módulo 16.

### Paso 5. Correr una sola orden

`dbt build` construye y prueba en el mismo paso, en el orden que dice el grafo, y **para en cuanto
una prueba falla**. Un modelo cuya prueba se rompe no publica su tabla, y lo que dependía de él ni
se intenta.

## El código, por partes

### Paso 6. Las fuentes, declaradas una vez

```yaml
sources:
  - name: lago
    tables:
      - name: plata
        meta:
          external_location: "read_parquet('../lake/silver/telemetry/**/*.parquet')"
```

```anota
sources | lo que entra de fuera y dbt no construye. Es el borde del mapa
name: lago | el nombre del grupo, para poder escribir source('lago', 'plata')
external_location | dbt pega ese texto detrás del FROM, así que la fuente es el Parquet del lago leído en su sitio, sin copiarlo ni importarlo
```

### Paso 7. Un modelo de preparación

```modelo
SELECT
    timestamp,
    day,
    medido,
    dudoso,
    lecturas,
    TP2,
    Oil_temperature,
    DV_eletric
FROM {{ source('lago', 'plata') }}
```

```anota
{{ source('lago', 'plata') }} | la fuente declarada en el paso anterior. Las llaves dobles son la marca de que ahí hay algo que dbt sustituye antes de ejecutar
sin CREATE TABLE | el fichero se llama prep_telemetria.sql, así que la tabla se llamará prep_telemetria. El nombre del fichero es el nombre
```

Este modelo es una **vista**: no copia las 1.841.760 filas de la plata, solo les pone nombre.
Materializarlo como tabla sería duplicar el lago para no ganar nada.

### Paso 8. Un modelo de oro que cruza dos

```modelo
WITH por_hora AS (
    SELECT
        time_bucket(INTERVAL 1 HOUR, timestamp) AS hora,
        round(avg(Oil_temperature), 2)          AS aceite,
        count(*)                                AS lecturas
    FROM {{ ref('prep_telemetria') }}
    WHERE medido
    GROUP BY hora
)
SELECT h.hora, h.aceite, c.temperatura AS calle
FROM por_hora h
JOIN {{ ref('prep_clima') }} c ON c.hora = h.hora
```

```anota
{{ ref('prep_telemetria') }} | otro modelo, nombrado por su nombre de modelo y no por el de su tabla. Esta línea es una flecha del mapa
dos ref en el mismo fichero | dos flechas entrando en este nodo. Nadie las declara aparte
WITH ... AS | los pasos del módulo 11, aquí dentro. Un modelo es SQL normal
```

Cuando dbt lo compila, sustituye cada `ref()` por el nombre real de la tabla:

```salida
FROM "fuelle"."main"."prep_telemetria"
...
JOIN "fuelle"."main"."prep_clima" c ON c.hora = h.hora
```

Y eso es todo lo que hace la marca: **cambiar un nombre por otro, y de paso apuntar la flecha**.

### Paso 9. Las promesas, en YAML

```yaml
  - name: oro_ciclo_diario
    columns:
      - name: dia
        data_tests: [unique, not_null]
      - name: dia_completo
        data_tests:
          - accepted_values:
              arguments:
                values: [true, false]
```

```anota
data_tests | la lista de promesas de esa columna. Cada una se convierte en una consulta
unique | no hay dos filas con el mismo valor. Es la promesa «timestamp no se repite» del módulo 16
not_null | ninguna casilla vacía
accepted_values | solo estos valores y ningún otro. Es la promesa de las digitales, que solo valen cero o uno
```

La prueba `unique` se convierte en esto, que dbt escribe solo:

```salida
select
    dia as unique_field,
    count(*) as n_records
from "fuelle"."main"."oro_ciclo_diario"
where dia is not null
group by dia
having count(*) > 1
```

Es **la misma consulta que escribimos a mano en el módulo 16**: buscar los incumplidores y exigir
cero filas. Lo único que cambia es que ahí la escribíamos y aquí la nombramos.

### Paso 10. Construir y probar de una vez

```python
proceso = subprocess.run([DBT_EXE, "build", "--profiles-dir", "."], cwd=DBT)
```

```anota
build | construir y probar en la misma orden. Solo run construiría sin comprobar nada
cwd=DBT | dbt se corre desde su propia carpeta, que es donde vive el proyecto
```

```salida
Concurrency: 4 threads (target='dev')

1 of 17 START sql view model main.prep_averias ................. [RUN]
2 of 17 START sql view model main.prep_clima ................... [RUN]
3 of 17 START sql view model main.prep_telemetria .............. [RUN]
4 of 17 START sql table model main.oro_ciclo_diario ........... [RUN]
5 of 17 START sql table model main.oro_horas .................. [RUN]
8 of 17 PASS not_null_oro_ciclo_diario_dia .................... [PASS]
14 of 17 START sql table model main.oro_averias ............... [RUN]
15 of 17 PASS clave_de_averias ............................... [PASS]

Done. PASS=17 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=17
```

Fíjate en el orden, porque no lo he elegido yo. Los tres de preparación arrancan a la vez, y
`oro_averias` es el último **porque se apoya en `oro_ciclo_diario`**, que a su vez tiene que estar
construida antes. Esa cadena está escrita en un `ref()` dentro de un fichero, y en ningún otro
sitio.

### Paso 11. La tabla de oro que puedes tocar

Esta es la consulta que hay dentro de `oro_horas`, con las dos tablas ya preparadas. Es un modelo
de oro entero, corriendo en tu navegador:

```sql-vivo
SELECT h.hora,
       h.aceite,
       c.temperatura                      AS calle,
       round(h.aceite - c.temperatura, 2) AS aceite_sobre_calle
FROM horas h
JOIN clima c ON c.hora = h.hora
ORDER BY h.hora
LIMIT 6;
```

```salida
┌─────────────────────┬────────┬──────────────┬────────────────────┐
│        hora         │ aceite │    calle     │ aceite_sobre_calle │
│      timestamp      │ double │ decimal(3,1) │       double       │
├─────────────────────┼────────┼──────────────┼────────────────────┤
│ 2020-02-01 00:00:00 │   51.9 │         14.2 │               37.7 │
│ 2020-02-01 01:00:00 │  51.91 │         14.4 │              37.51 │
│ 2020-02-01 02:00:00 │  51.71 │         14.3 │              37.41 │
│ 2020-02-01 03:00:00 │   51.4 │         14.4 │               37.0 │
│ 2020-02-01 04:00:00 │  52.17 │         14.5 │              37.67 │
│ 2020-02-01 05:00:00 │  52.91 │         14.0 │              38.91 │
└─────────────────────┴────────┴──────────────┴────────────────────┘
```

## El resultado, medido

{{FIG:fig_m17_linaje_dbt}}

**Qué esperábamos.** Un mapa de dependencias parecido al que dibujaría yo a mano.

**Qué salió.** **9 nodos** y **8 dependencias**, y la diferencia con dibujarlo a mano es que
ninguna de las dos cifras la he escrito. La figura de arriba se genera leyendo `manifest.json`,
que dbt escribe al compilar, que a su vez sale de los `ref()` y `source()` de dentro del SQL.

El reparto: **3 fuentes**, **3 modelos de preparación** y **3 de oro**. Y las tres tablas de oro
son lo que 1.841.760 lecturas de plata dan de sí cuando se les hace una pregunta concreta:

| Tabla de oro | Filas | Una fila es |
|---|---|---|
| `oro_ciclo_diario` | 212 | un día |
| `oro_horas` | 4.416 | una hora |
| `oro_averias` | 4 | un parte de avería |

**La construcción entera son 17 pasos**: 6 modelos y **11 pruebas**, corridos en el orden del
grafo por una sola orden.

**Y las 11 pruebas en verde no prueban nada por sí solas.** Es la regla del módulo 16 otra vez, y
aquí hay un motivo extra para desconfiar. Declarar una promesa cuesta una línea de YAML, así que
es facilísimo llenar el fichero de promesas incapaces de fallar y quedarse tranquilo.

Así que se añade a propósito una promesa destinada a fallar. La elegida: el número de parte es
único. El módulo 12 ya midió que eso es mentira, porque dos de los cuatro partes se llaman `#1`.

```salida
1 of 4 START test clave_de_averias .............................. [RUN]
4 of 4 START test unique_oro_averias_nr ......................... [RUN]
1 of 4 PASS clave_de_averias .................................... [PASS]
4 of 4 FAIL 1 unique_oro_averias_nr ............................. [FAIL]

Completed with 1 error, 0 partial successes, and 0 warnings:

[ERROR]: in test unique_oro_averias_nr (models\oro\_oro.yml)
  Got 1 result, configured to fail if != 0
```

La caza, y de paso enseña la otra mitad: la prueba `clave_de_averias`, la que dice que la clave es
la **pareja** de número y fecha, pasa en la misma corrida. Las dos miran la misma columna y solo
una es cierta.

**Qué significa.** El mapa no es documentación, es una **lectura del código**. Puede quedarse
desactualizado exactamente igual que el código puede estar mal, o sea que si el mapa miente es
porque el proyecto miente, y eso ya no es un problema de mapa.

## Ojo

- **`ref()` no es adorno.** Si escribes el nombre de la tabla directamente, la consulta funciona
  igual y **la flecha desaparece del mapa**. Es el peor fallo posible aquí, porque no da error:
  produce un mapa incompleto que parece completo. Es la pizarra del ejemplo de juguete.
- **Vista o tabla es una decisión, no un ajuste.** Los de preparación son vistas porque no ganan
  nada copiando; los de oro son tablas porque se consultan mucho y se calculan poco.
- **Una prueba que no puede fallar es peor que ninguna.** Cuesta una línea declararla y da
  tranquilidad gratis. La única forma de saber si sirve es verla fallar una vez.
- **Las cuatro pruebas de serie no cubren todo.** La clave compuesta de este proyecto no cabe en
  `unique`, así que se escribe a mano como un SQL de cero filas. Que la herramienta no traiga una
  promesa no es motivo para no exigirla.
- **dbt no es un orquestador.** Sabe el orden de sus modelos y nada más. No sabe descargar el CSV
  ni pedirle el clima a una API: de eso va el módulo 29.
- **El oro no es «los datos buenos».** Es una respuesta a una pregunta concreta. Cada tabla de oro
  tiene un grano declarado, un día o una hora o un parte, y si no lo sabes decir en una frase
  probablemente no sea una tabla de oro.

## Puente metalúrgico

Un diagrama de flujo de planta lleva décadas haciendo esto mismo. Molienda, flotación rougher,
limpieza y espesado. Cada equipo lleva declarada su corriente de entrada.

Lo interesante no es el dibujo, es lo que permite: cuando el molino baja de tonelaje, nadie tiene
que adivinar qué le pasa al espesador. Se lee del diagrama, aguas abajo.

Y ahora la parte incómoda, que cualquiera que haya trabajado en una planta reconoce. **El diagrama
que cuelga en la sala de control no es la planta.** Es la planta de cuando alguien lo dibujó,
menos la bomba que se cambió en marzo, más el reactivo que ya no se usa.

Un modelo de dbt es ese diagrama con una diferencia: **se genera de las tuberías**, no de la
memoria de quien las montó. No puede quedarse viejo, porque no hay una copia que mantener.

## Hazlo tú

```reto
pregunta: Escribe el SELECT de un modelo de oro nuevo, `oro_meses`, con un mes por fila. Devuelve `mes`, `horas` con las horas que trae el registro, `aceite` con la temperatura media del aceite y `calle` con la de la calle, las dos redondeadas a un decimal. Ocho filas.
inicio: SELECT count(*)                      AS horas,
       round(avg(h.aceite), 1)       AS aceite,
       round(avg(c.temperatura), 1)  AS calle
FROM horas h
JOIN clima c ON c.hora = h.hora;
esperado: m17_oro_por_mes
pista: El cruce del punto de partida ya está bien y las tres columnas de números también. Lo que falta es la columna que agrupa, y sale de la hora con `strftime(h.hora, '%Y-%m')`, que se queda con el año y el mes. Después se agrupa por ella y se ordena por ella.
solucion: SELECT strftime(h.hora, '%Y-%m')     AS mes,
       count(*)                      AS horas,
       round(avg(h.aceite), 1)       AS aceite,
       round(avg(c.temperatura), 1)  AS calle
FROM horas h
JOIN clima c ON c.hora = h.hora
GROUP BY mes
ORDER BY mes;
```

Lo que acabas de escribir **es** un modelo de oro. Guarda ese SELECT en un fichero llamado
`oro_meses.sql`. Dentro, cambia `horas` por `ref('prep_telemetria')` y `clima` por
`ref('prep_clima')`. Con eso aparece un décimo nodo en el mapa de arriba, con sus dos flechas, y
sin dibujar nada.

## Repaso

### Qué gana un modelo por escribir `ref()` en vez del nombre de la tabla

Tres cosas, y ninguna hay que pedirla: el orden de construcción, el mapa de dependencias, y saber
qué hay que rehacer cuando cambia algo aguas arriba. El coste es escribir seis caracteres más. Si
pones el nombre directo la consulta funciona igual, y por eso el fallo es peligroso: no avisa.

### Por qué los modelos de preparación son vistas y los de oro son tablas

Una vista no guarda nada, se recalcula al consultarla. Los de preparación solo renombran y
seleccionan columnas de un Parquet que ya existe, así que materializarlos sería copiar el lago a
cambio de nada. Los de oro agregan mucho y se consultan a menudo, así que ahí sí compensa pagar el
cálculo una vez.

### En qué se parece este módulo al 16 y en qué se diferencia

Es el mismo contrato: promesas escritas como consultas que tienen que devolver cero filas. La
diferencia es que las cuatro más comunes ya vienen hechas y se nombran en una línea, en vez de
escribirlas. Lo que no cambia es de dónde sale su valor: haberlas visto fallar una vez.

### El mapa dice 9 nodos. Qué pasaría si alguien añade un modelo y no lo dibuja

Nada, porque no hay nada que dibujar. El mapa se lee del `manifest.json`, que se regenera al
compilar, así que un modelo nuevo aparece por el hecho de existir. El mapa solo puede mentir si
un modelo nombra a sus padres sin `ref()`, y entonces el mentiroso es el modelo.

### Tu `dbt build` falla en una prueba a media construcción. Qué ha quedado en el lago

Lo que estaba antes, intacto. La tabla cuya prueba falló no se publica, y lo suyo aguas abajo ni
se intenta construir. Es la misma decisión del módulo 16: mejor un panel desactualizado que uno
con datos malos. El resto de las ramas del grafo, las que no pasan por el fallo, sí se
construyen.

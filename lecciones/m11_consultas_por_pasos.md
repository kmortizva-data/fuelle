---
module: 11
---

## En 30 segundos

- Una consulta con una consulta dentro se lee de dentro afuera, y cuesta.
- `WITH` le pone **nombre a cada paso** y la consulta se lee de arriba abajo.
- La del módulo 10 se parte en **2 pasos con nombre**: días y días completos.
- Las dos versiones devuelven las **mismas 7 filas**, comprobado fila a fila.
- Y tardan lo mismo: **sus rangos se solapan**. Escribirlo claro no cuesta nada.

## Qué resuelve este módulo

El módulo 10 acabó con una consulta que tiene otra dentro. Funciona, y hay que leerla de dentro
hacia fuera, que no es como lee nadie.

Este módulo la reescribe para leerla en el orden en que se piensa, y comprueba que la
reescritura no cambia ni el resultado ni el tiempo.

## Antes de la teoría: un ejemplo de juguete

Calcula la recuperación de un circuito con estos datos:

| Corriente | Toneladas | Ley de cobre |
|---|---|---|
| Alimentación | 100 | 2 % |
| Concentrado | 10 | 18 % |

Hazlo de dos maneras.

**Todo de una vez**, como se escribe una subconsulta:

> La recuperación es diez por dieciocho entre cien partido por cien por dos entre cien, por cien.

Lee esa frase otra vez. Es correcta y es ilegible, y para comprobarla hay que ir deshaciéndola
desde el centro.

**Por pasos, con nombre:**

1. **Cobre que entra** = 100 × 2 % = **2 t**
2. **Cobre que sale** = 10 × 18 % = **1,8 t**
3. **Recuperación** = 1,8 / 2 = **90 %**

El mismo cálculo, los mismos números y el mismo resultado. Lo único que cambia es que ahora cada
paso tiene un nombre y se puede comprobar por separado.

Si alguien duda del 90 %, en la segunda versión se puede preguntar por el paso 1 y verlo. En la
primera hay que rehacerlo todo.

Eso es exactamente lo que hace `WITH` con una consulta.

## Glosario

- **Subconsulta.** Una consulta escrita dentro de otra, entre paréntesis. La de dentro se
  resuelve primero y la de fuera trabaja sobre su resultado.
- **`WITH`.** La forma de sacar esas consultas de dentro y ponerlas antes, cada una con nombre.
- **CTE.** El nombre técnico de cada paso de un `WITH`, de «common table expression». Se dice
  mucho en ofertas de trabajo y significa eso: un paso con nombre.
- **Encadenar.** Que un paso del `WITH` use el anterior, como un cálculo que va acumulando.
- **Plan de ejecución.** Lo que la base de datos decide hacer de verdad para responder. No tiene
  por qué parecerse a como está escrita la consulta.

## Paso a paso

### Paso 1. Mirar la consulta del módulo 10 y ver por dónde se parte

Aquella consulta hacía dos cosas: primero calcular las horas de carga de cada día, y después
promediarlas por mes quedándose solo con los días completos.

Dos cosas, dos pasos. Ahí está el corte.

### Paso 2. Sacar cada paso fuera y ponerle nombre

Lo que estaba entre paréntesis después del `FROM` pasa a estar arriba, con `WITH`, y con un
nombre que diga qué es. Después la consulta principal lo usa como si fuera una tabla más.

### Paso 3. Comprobar que dice lo mismo

Y esto no se mira a ojo. Se ejecutan las dos, se comparan las filas una a una, y solo entonces se
tira la versión vieja.

### Paso 4. Comprobar que no cuesta más

La objeción de siempre a `WITH` es la velocidad: parece que guarda resultados intermedios, así
que debería salir más lento. Se cronometran las dos con la mediana de siete y se miran los
rangos.

## El código, por partes

### Paso 5. La versión del módulo 10, con la consulta dentro

```sql
SELECT strftime(day, '%Y-%m') AS mes,
       round(avg(horas), 2)   AS horas_de_carga
FROM (
    SELECT day,
           count(*) AS lecturas,
           sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas
    FROM telemetria
    GROUP BY day
)
WHERE lecturas > 0.9 * 8640
GROUP BY mes
ORDER BY mes;
```

```anota
FROM ( ... ) | en vez de una tabla, va una consulta entera entre paréntesis
strftime(day, '%Y-%m') | saca el año y el mes de una fecha, como texto
lecturas > 0.9 * 8640 | se queda con los días que tienen al menos el 90 % de las lecturas de un día lleno
```

Para entenderla hay que empezar por el paréntesis, en la línea cuatro, y luego volver arriba. Y
la columna `lecturas` que filtra el `WHERE` no está declarada en ningún sitio visible: nace
dentro del paréntesis.

### Paso 6. La misma pregunta, por pasos

```sql-vivo
WITH por_dia AS (
    SELECT day,
           count(*) AS lecturas,
           sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas
    FROM telemetria
    GROUP BY day
),
dias_completos AS (
    SELECT * FROM por_dia WHERE lecturas > 0.9 * 8640
)
SELECT strftime(day, '%Y-%m') AS mes,
       round(avg(horas), 2)   AS horas_de_carga
FROM dias_completos
GROUP BY mes
ORDER BY mes;
```

```anota
WITH nombre AS ( ... ) | define un paso con nombre, que se puede usar más abajo como una tabla
, | separa un paso del siguiente; el último no lleva coma
FROM por_dia | el segundo paso usa el primero por su nombre, sin repetir su código
FROM dias_completos | y la consulta final usa el segundo
```

```salida
┌─────────┬────────────────┐
│   mes   │ horas_de_carga │
├─────────┼────────────────┤
│ 2020-02 │           1.45 │
│ 2020-03 │           3.58 │
│ 2020-04 │           4.27 │
│ 2020-05 │           3.61 │
│ 2020-06 │           4.02 │
│ 2020-07 │           3.78 │
│ 2020-08 │           2.81 │
└─────────┴────────────────┘
```

Ahora se lee de arriba abajo: primero por día, luego solo los días completos, luego el promedio
mensual. Es el orden en el que se pensó la pregunta.

### Paso 7. Los dos pasos, dibujados

```diagrama
*POR_DIA | Las horas de carga de cada día | 212 filas, una por día
*DIAS_COMPLETOS | Solo los que pasan del 90 % | 91 filas
CONSULTA FINAL | El promedio de cada mes | 7 filas
```

Cada caja se puede consultar por separado mientras se escribe, cambiando el `SELECT` final por
`SELECT * FROM por_dia`. Eso es lo que convierte escribir SQL en algo depurable.

## El resultado, medido

**Qué esperábamos.** Que las dos versiones dieran lo mismo, y que la de `WITH` fuera algo más
lenta por guardar resultados intermedios.

**Qué salió.** Lo mismo, sí: las dos devuelven **7 filas** idénticas, comparadas una a una y no
de un vistazo.

Y lo segundo, no. Las dos versiones **no se distinguen en tiempo**: sus rangos se solapan, así
que a efectos de esta máquina tardan igual.

```salida
  las dos devuelven 7 filas y son iguales: True
  anidada:   0.023 s (from 0.019 to 0.031)
  con WITH:  0.021 s (from 0.019 to 0.022)
  ¿se distinguen en tiempo? False
  la version con WITH define 2 pasos con nombre
  lineas: 12 anidada contra 15 con WITH
```

**Qué significa.** La razón que da todo el mundo para no usar `WITH` es la velocidad. Aquí no la
pierde, y el motivo es que **la base de datos no ejecuta la consulta como está escrita**. La lee
entera, decide su propio plan, y llega al mismo sitio por los dos caminos.

Así que la elección entre una forma y otra no es una decisión de rendimiento. Es una decisión de
quién va a leer eso dentro de seis meses.

El coste real son **3 líneas más**, de 12 a 15. Ese es el precio entero.

## Ojo

- **`WITH` no es una tabla temporal.** No guarda nada en disco ni deja rastro. Es un nombre para
  un paso, y desaparece al acabar la consulta.
- **Un paso puede usar el anterior, pero no al revés.** Se leen en orden, de arriba abajo, como
  se escriben.
- **La coma va entre pasos y no después del último.** Es el error de sintaxis más frecuente al
  empezar con `WITH`, y el mensaje de error no ayuda nada.
- **Que aquí no cueste no significa que nunca cueste.** Con volúmenes grandes y un paso que se
  usa varias veces, hay motores que lo recalculan cada vez. La forma de saberlo es la de siempre:
  medir con los rangos, no suponer.
- **Nombra los pasos por lo que contienen, no por lo que hacen.** `dias_completos` dice qué hay
  dentro; `paso2` no dice nada y `filtrar_datos` dice menos todavía.

## Puente metalúrgico

Un balance metalúrgico nunca se entrega como una fórmula gigante. Se entrega como una tabla con
sus filas: alimentación, concentrado, colas, y después las recuperaciones calculadas a partir de
ellas.

No es por estética. Es porque cuando el balance no cierra, hay que poder señalar en qué fila está
el problema. Con una fórmula única solo se puede decir que el resultado es raro.

`WITH` es esa tabla de filas intermedias. Y como en el balance, lo que se gana no es velocidad:
es poder señalar dónde está el fallo cuando lo haya.

## Hazlo tú

```reto
pregunta: Reescribe con `WITH` la consulta anidada del paso 5, en dos pasos con nombre, y comprueba que devuelve las mismas 7 filas con las columnas `mes` y `horas_de_carga`.
inicio: SELECT strftime(day, '%Y-%m') AS mes,
       round(avg(horas), 2)   AS horas_de_carga
FROM (
    SELECT day,
           count(*) AS lecturas,
           sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas
    FROM telemetria
    GROUP BY day
)
WHERE lecturas > 0.9 * 8640
GROUP BY mes
ORDER BY mes;
esperado: m11_con_with
pista: Lo que está entre paréntesis después del `FROM` es el primer paso: sácalo arriba con `WITH por_dia AS ( ... )`. El `WHERE` que venía después del paréntesis es el segundo paso: `dias_completos AS (SELECT * FROM por_dia WHERE ...)`. Y la consulta final se queda con el `SELECT` de arriba, cambiando el paréntesis por `FROM dias_completos`.
solucion: WITH por_dia AS (
    SELECT day,
           count(*) AS lecturas,
           sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas
    FROM telemetria
    GROUP BY day
),
dias_completos AS (
    SELECT * FROM por_dia WHERE lecturas > 0.9 * 8640
)
SELECT strftime(day, '%Y-%m') AS mes,
       round(avg(horas), 2)   AS horas_de_carga
FROM dias_completos
GROUP BY mes
ORDER BY mes;
```

## Repaso

### Qué es una CTE y por qué sale en tantas ofertas de trabajo

Es un paso con nombre dentro de una consulta, lo que se escribe con `WITH`. Sale en las ofertas
porque marca la diferencia entre una consulta mantenible por otra persona y una que hay que
reescribir desde cero. En equipos donde el SQL lo lee más gente que quien lo escribió, eso vale
más que cualquier truco de rendimiento.

### Es más lento usar WITH que anidar subconsultas

Aquí no, y está medido: los rangos de las dos versiones se solapan, así que no se distinguen. El
motivo es que la base de datos no ejecuta lo que está escrito, sino su propio plan, y para las
dos formas llega al mismo. En otros motores y con más volumen puede no ser así, y entonces se
mide igual que aquí.

### Entonces por qué reescribirla, si el resultado y el tiempo son iguales

Porque se lee en el orden en que se piensa. La versión anidada obliga a empezar por el centro y
volver hacia fuera, y esconde la columna `lecturas`, que nace dentro del paréntesis y se usa
fuera. La versión por pasos se lee de arriba abajo y cada paso se puede consultar solo mientras
se escribe.

### Cómo depuras una consulta larga que da un resultado raro

Partiéndola en pasos con nombre y mirando cada uno. Con `WITH`, basta cambiar el `SELECT` final
por `SELECT * FROM el_paso_que_sea` y se ve su contenido. Con subconsultas anidadas hay que
desmontar la consulta a mano para conseguir lo mismo.

### Qué nombres le pones a los pasos

Los que digan qué hay dentro, no qué hace el paso. `dias_completos` dice que ahí están los días
completos, y eso es lo que necesita saber quien lee la línea de abajo. `paso2` y `datos_filtrados`
obligan a subir a leer el código para entender la consulta principal.

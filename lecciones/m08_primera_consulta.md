---
module: 8
---

## En 30 segundos

- Una consulta tiene cinco piezas y siempre van en el mismo orden.
- `SELECT` elige columnas, `WHERE` elige filas. No es lo mismo y se confunde.
- La alarma de baja presión saltó en **5.188 lecturas**, en 95 de los 212 días.
- El periodo tiene **214 días** de calendario y el registro solo **212**.
- Y esos dos días que faltan enseñan lo que ninguna definición enseña: **vacío no es cero**.

## Qué resuelve este módulo

Aquí se escribe la primera consulta entera, y se escribe contra el compresor de verdad.

Las piezas son cinco y no hay que aprendérselas de memoria: se entienden viendo qué hace cada
una. Lo importante de este módulo es otra cosa: la diferencia entre no tener valor y valer cero.
Confundirlas da resultados que parecen correctos.

## Antes de la teoría: un ejemplo de juguete

Un turno deja seis lecturas del depósito, con su presión y si sonó la alarma:

| hora | presion | alarma |
|---|---|---|
| 06:00 | 9 | 0 |
| 06:10 | 8 | 0 |
| 06:20 | 7 | 1 |
| 06:30 | 6 | 1 |
| 06:40 | 8 | 0 |
| 06:50 | 9 | 0 |

Ahora, sin SQL, contesta tres preguntas mirando la tabla:

**Enséñame solo la hora y la presión.** Tapas la tercera columna. Siguen siendo seis filas, pero
más estrechas. **Eso es `SELECT`: elige columnas.**

**Enséñame solo cuando sonó la alarma.** Tachas cuatro filas y quedan dos, las de las 06:20 y las
06:30. Siguen siendo tres columnas, pero menos filas. **Eso es `WHERE`: elige filas.**

**De menor a mayor presión, y solo la peor.** Ordenas y te quedas con la primera: la de las 06:30,
con 6 bar. **Eso son `ORDER BY` y `LIMIT`.**

Elegir columnas y elegir filas son cosas distintas y se hacen con palabras distintas. Ese es el
noventa por ciento de la confusión de quien empieza.

Y ahora la cuarta pregunta, que es la del módulo. **¿Cuál fue la presión media a las 07:00?**

No es cero. Es que no hay lectura de las 07:00. Nadie midió, así que no hay nada que promediar, y
la respuesta correcta es «no se sabe». Si tu sistema contesta cero, te está mintiendo con
seguridad aparente.

## Glosario

- **Consulta.** Una pregunta escrita en SQL. Se lee casi como una frase en inglés.
- **Cláusula.** Cada una de las piezas de una consulta. Son cinco y aquí salen todas.
- **`SELECT`.** Elige qué **columnas** salen en el resultado.
- **`FROM`.** Dice de qué tabla salen.
- **`WHERE`.** Elige qué **filas** pasan el filtro. Las demás no llegan al resultado.
- **`ORDER BY`.** Ordena el resultado. Sin él, el orden no está garantizado.
- **`LIMIT`.** Corta y deja solo las primeras filas.
- **NULL.** La ausencia de valor. No es cero, no es una cadena vacía, y no es igual a nada, ni
  siquiera a otro NULL.
- **Alias.** El nombre que le pones a una columna del resultado, con `AS`.

## Paso a paso

### Paso 1. Las cinco piezas, y el orden en que se escriben

Una consulta se escribe siempre en el mismo orden, y ese orden no es negociable. Si pones el
`WHERE` antes del `FROM`, no es que quede feo: no funciona.

### Paso 2. Preguntar por la alarma de baja presión

La ficha del dataset dice que `LPS` se activa por debajo de 7 bar. Es la señal más parecida a una
alarma que hay en el fichero, así que es buen sitio para el primer filtro.

### Paso 3. Ordenar y cortar, para no leer cinco mil filas

Filtrando por la alarma quedan miles de lecturas, que no caben en pantalla ni sirven de nada
seguidas. Ordenadas por presión y cortadas a cinco, la respuesta cabe de un vistazo.

### Paso 4. Preguntar por un día que no existe

El registro va del 1 de febrero al 1 de septiembre. Eso son 214 días de calendario, y el fichero
solo tiene 212. Faltan dos, y preguntarle al sistema por uno de ellos es la mejor forma de
entender qué es NULL.

## El código, por partes

### Paso 5. La anatomía de una consulta

```diagrama
SELECT | qué columnas | y con qué nombre
FROM | de qué tabla | aquí, telemetria
WHERE | qué filas pasan | el filtro
ORDER BY | en qué orden | salen
LIMIT | cuántas | quiero ver
```

Se escribe siempre en ese orden. Y una advertencia que ahorra disgustos: **no es el orden en que
se ejecuta**. La base de datos aplica primero el `FROM`, luego el `WHERE`, y el `SELECT` casi al
final. El módulo 10 vuelve sobre esto cuando empiece a importar.

### Paso 6. Tu primera consulta entera

```sql-vivo
SELECT day, TP2, LPS
FROM telemetria
WHERE LPS = 1
ORDER BY TP2 DESC
LIMIT 5;
```

```anota
SELECT day, TP2, LPS | pide tres columnas y en ese orden; lo que no se nombra no sale
FROM telemetria | de la tabla del compresor, que es la que trae tu navegador
WHERE LPS = 1 | solo las filas donde la alarma estaba activa; el resto se descartan
= | comparar, no asignar: en SQL un solo igual ya es comparación
ORDER BY TP2 DESC | ordena por presión de mayor a menor; DESC es descendente
LIMIT 5 | y de todas esas, enséñame solo las cinco primeras
; | cierra la consulta
```

```salida
┌────────────┬────────┬────────┐
│    day     │  TP2   │  LPS   │
│    date    │ double │ double │
├────────────┼────────┼────────┤
│ 2020-07-17 │  8.132 │    1.0 │
│ 2020-07-25 │  8.124 │    1.0 │
│ 2020-07-08 │  8.108 │    1.0 │
│ 2020-07-12 │  8.106 │    1.0 │
│ 2020-07-15 │  8.104 │    1.0 │
└────────────┴────────┴────────┘
```

Pruébala. Quita el `WHERE` y verás llegar filas donde `LPS` vale cero. Cambia el `LIMIT` a 20.
Cambia `DESC` por nada y saldrán las presiones más bajas.

Fíjate en las fechas: cuatro de las cinco son de julio, y una es del día 15, que es la fecha de la
cuarta avería.

### Paso 7. Dónde salta más la alarma

```sql
SELECT day, count(*) AS lecturas
FROM telemetria
WHERE LPS = 1
GROUP BY day
ORDER BY lecturas DESC
LIMIT 5;
```

```anota
count(*) AS lecturas | cuenta las filas de cada grupo y llama «lecturas» al resultado
GROUP BY day | junta todas las filas del mismo día en una sola; el módulo 10 va entero de esto
DESC | de mayor a menor; sin esa palabra ordena de menor a mayor
```

```salida
┌────────────┬──────────┐
│    day     │ lecturas │
├────────────┼──────────┤
│ 2020-07-15 │      534 │
│ 2020-07-17 │      414 │
│ 2020-06-08 │      312 │
│ 2020-05-19 │      272 │
│ 2020-07-31 │      247 │
└────────────┴──────────┘
```

El primero de la lista, el 15 de julio, es la fecha de la cuarta avería documentada.

### Paso 8. Preguntar por el día que no está

```sql
SELECT count(*) AS cuantas,
       avg(TP2) AS presion_media,
       sum(LPS) AS alarmas
FROM telemetria
WHERE day = DATE '2020-02-29';
```

```anota
avg(TP2) | la media de esa columna sobre las filas que pasaron el filtro
sum(LPS) | la suma de esa columna
DATE '2020-02-29' | una fecha literal; sin la palabra DATE delante SQL lo leería como texto
```

```salida
┌─────────┬───────────────┬──────────┐
│ cuantas │ presion_media │ alarmas  │
├─────────┼───────────────┼──────────┤
│       0 │          NULL │     NULL │
└─────────┴───────────────┴──────────┘
```

Mira bien esa fila, porque es el módulo entero. **La misma consulta, sobre las mismas cero filas,
devuelve 0 en una columna y NULL en las otras dos.**

Contar cuántas cosas hay cuando no hay ninguna es cero, y es un número correcto. Calcular la
media de nada no es cero: es que no hay respuesta. Y sumar nada tampoco, por el mismo motivo.

## El resultado, medido

{{FIG:fig_m08_null_no_es_cero}}

**Qué esperábamos.** Que la alarma de baja presión fuera un suceso raro y concentrado en las
averías.

**Qué salió.** Rara sí: **5.188 lecturas** de 1.516.948, el **0,342 %**. Pero concentrada no.
Esas lecturas se reparten en **95 de los 212 días**, o sea el **45 %** de los días. La alarma
salta casi uno de cada dos días.

El día que más salta es el **15 de julio**, con **534 lecturas**, y es la fecha de la cuarta
avería. Pero los otros cuatro del podio no tienen parte de avería ninguno.

**Y el hallazgo que no buscábamos.** El periodo cubre **214 días** de calendario y el registro
tiene **212**. Faltan dos enteros: el **29 de febrero** y el **26 de abril**. En la figura son las
dos aspas.

Que falte un 29 de febrero tiene su gracia, porque es el día que un programa mal escrito se salta
solo. No hay forma de saber desde aquí si fue eso o si el equipo estuvo parado.

**Qué significa.** Una alarma que salta el 45 % de los días no sirve para avisar de nada. Es
demasiado frecuente para que alguien la mire. Ese es exactamente el problema que este proyecto
quiere resolver: el gemelo tiene que avisar mejor.

Y sobre los dos días ausentes, la lección práctica. Si alguien dibuja las alarmas por día y esos
dos días salen a cero, el gráfico dirá que fueron días tranquilos. No lo fueron: **no se sabe qué
fueron.** Por eso en la figura llevan un aspa y no un hueco en blanco.

## Ojo

- **`SELECT` elige columnas y `WHERE` elige filas.** Es la confusión número uno al empezar. Una
  estrecha la tabla, la otra la acorta.
- **NULL no es igual a nada, ni siquiera a otro NULL.** Escribir `WHERE x = NULL` no devuelve las
  filas vacías: no devuelve **ninguna**. Se pregunta con `WHERE x IS NULL`.
- **`count(*)` y `avg()` no tratan la nada igual.** Contar nada es cero; promediar nada es NULL.
  Los dos son correctos, y por eso hay que saber cuál estás pidiendo.
- **Sin `ORDER BY` no hay orden.** Puede salir ordenado por casualidad, y cambiar mañana sin que
  nadie toque nada. Si el orden importa, se pide.
- **Y un `ORDER BY` con empates tampoco ordena del todo.** Esta lección iba a publicar
  `ORDER BY day LIMIT 5`, que pide cinco filas de entre las miles que comparten día sin decir
  cuáles. Corriéndola **8 veces sobre los mismos datos salieron 2 resultados distintos**.
  Ordenando por presión, que apenas empata, salió **1**. Si hay `LIMIT`, el `ORDER BY` tiene que
  desempatar hasta el final o el resultado no es reproducible.
- **Este fichero no tiene ni un solo NULL dentro.** El vacío no está en las celdas, está en las
  filas que no existen, y esas no se ven mirando la tabla.

## Puente metalúrgico

En una hoja de turno hay dos casillas que se parecen y no significan lo mismo: **cero toneladas
procesadas** y **la casilla en blanco**.

Cero toneladas es información: la planta estuvo parada y alguien lo comprobó. La casilla en
blanco es la ausencia de información. Pudo estar parada, pudo no pasar nadie a apuntarlo, pudo no
registrarse el turno entero.

Al meter esa hoja en una hoja de cálculo, las dos se convierten en un cero. A fin de mes la
disponibilidad de planta sale más baja de lo que fue. El error no está en el cálculo: está en
haber traducido «no se sabe» por «cero» al entrar el dato.

SQL, para bien, se niega a hacer esa traducción por su cuenta.

## Hazlo tú

```reto
pregunta: Devuelve las lecturas en que la alarma estaba activa **y** la presión del compresor pasaba de 6 bar, con las columnas `day`, `TP2` y `LPS`, ordenadas por presión de mayor a menor. Enséñame solo las 10 primeras.
inicio: SELECT day, TP2, LPS
FROM telemetria
WHERE LPS = 1
ORDER BY TP2 DESC
LIMIT 5;
esperado: m08_alarma_con_presion
pista: El punto de partida ya ordena y corta como hace falta. Lo único que le falta es una segunda condición en el mismo `WHERE`, unida a la primera por la palabra `AND`. Y el `LIMIT` pasa de 5 a 10.
solucion: SELECT day, TP2, LPS
FROM telemetria
WHERE LPS = 1 AND TP2 > 6
ORDER BY TP2 DESC
LIMIT 10;
```

## Repaso

### Diferencia entre SELECT y WHERE

`SELECT` elige columnas y `WHERE` elige filas. Con `SELECT` la tabla del resultado se hace más
estrecha; con `WHERE` se hace más corta. Se pueden usar los dos a la vez y son independientes:
puedes filtrar por una columna que luego no enseñas.

### Por qué WHERE x = NULL no devuelve las filas vacías

Porque NULL no es un valor, es la ausencia de uno, y no se puede comparar con el igual. La
pregunta «¿este hueco es igual a un hueco?» no tiene respuesta, así que SQL contesta que no lo
sabe y la fila no pasa el filtro. Para preguntar por la ausencia está `IS NULL`.

### La misma consulta devuelve 0 en una columna y NULL en otra. Está rota

No, y las dos respuestas son correctas. Sobre cero filas, `count(*)` vale cero porque contar nada
da cero. `avg()` y `sum()` dan NULL porque promediar y sumar nada no tiene resultado. La
diferencia importa: un cero se puede meter en un gráfico y un NULL avisa de que ahí no hay dato.

### Faltan dos días en el registro. Los rellenarías con ceros

No. Rellenar con ceros convierte «no se sabe» en «no pasó nada», y eso es inventarse un dato.
Lo correcto es dejarlos ausentes, para que cualquier cálculo sobre ellos devuelva NULL. Si un gráfico necesita una casilla para ese día, se dibuja distinta, como el aspa de la
figura.

### La alarma salta en el 45 % de los días. Sirve como aviso de avería

No, y ese es el resultado del módulo. Una alarma que suena casi uno de cada dos días deja de
mirarse a la semana de instalarla. Detecta correctamente que la presión bajó, pero la presión
baja constantemente en la operación normal de un compresor. Para avisar de una avería hay que
mirar otra cosa, y de eso va el resto del curso.

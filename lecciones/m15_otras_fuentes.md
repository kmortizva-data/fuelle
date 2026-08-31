---
module: 15
---

## En 30 segundos

- El compresor coge el aire de la calle, así que el tiempo que hace es parte de su física.
- Tres fuentes con tres ritmos: cada **10 s**, cada **hora** y **cuando se rompe algo**.
- Cruzarlas obliga a bajar todo al ritmo de la más lenta, y ahí se pierde detalle a propósito.
- La calle explica la temperatura del aceite con **0,529**, y la carga del compresor con **0,432**.
- O sea que **el tiempo de fuera pesa más que el trabajo de la máquina**. Nadie lo esperaba.

## Qué resuelve este módulo

Hasta aquí el lago tenía una sola tabla grande. Un lago con una tabla no es un lago: es un
fichero con pretensiones.

Este módulo mete las otras dos fuentes y, sobre todo, resuelve el problema que traen: **no laten
al mismo ritmo**. Y de paso contesta si el clima aporta algo o es decoración.

## Antes de la teoría: un ejemplo de juguete

Dos registros de la misma mañana. El de la planta, cada diez minutos:

| hora | toneladas |
|---|---|
| 08:00 | 20 |
| 08:10 | 30 |
| 08:20 | 40 |
| 08:30 | 30 |

Y el del laboratorio, que analiza una muestra cada media hora:

| hora | ley |
|---|---|
| 08:00 | 2 |
| 08:30 | 4 |

**Pregunta: cuánto cobre entró entre las 08:00 y las 08:30.**

Tienes cuatro pesadas y dos leyes. No se pueden multiplicar fila a fila porque no hay las mismas
filas. Hay que decidir, y hay tres respuestas defendibles:

**Una: la ley de las 08:00 vale para toda la media hora.** Entonces son 90 toneladas por 2 %, o
sea **1,8 t de cobre**. Es lo que hace un laboratorio: la muestra representa el periodo que
empieza.

**Dos: se promedian las dos leyes.** 90 toneladas por 3 %, **2,7 t**. Suena más justo y supone que
la ley cambió suavemente, que puede ser falso.

**Tres: se sube todo a la media hora.** 90 toneladas con una ley media de 3 %, que es lo mismo que
la dos pero habiendo tirado el detalle de las pesadas a propósito.

Ninguna es la correcta. **La correcta es la que se declara.** Cruzar fuentes de ritmos distintos
siempre obliga a una decisión así, y el error no es elegir mal: es elegir sin darse cuenta.

## Glosario

- **Fuente.** Un origen de datos con su propio dueño, su formato y su ritmo.
- **Frecuencia.** Cada cuánto llega un dato. Aquí hay tres: diez segundos, una hora y por suceso.
- **Grano.** A qué corresponde una fila, del módulo 2. Al cruzar dos fuentes hay que decidir en
  qué grano se trabaja.
- **Bajar al grano común.** Resumir la fuente rápida hasta el ritmo de la lenta. Se pierde
  detalle, y por eso es una decisión.
- **API.** Una dirección de internet que devuelve datos en vez de una página. La del clima es
  gratis y no pide clave.
- **UTC.** La hora universal, sin cambios de estación. Todo se pide y se guarda así.

## Paso a paso

### Paso 1. Traer el clima de Oporto, una vez

El archivo histórico de Open-Meteo es gratis, no pide clave y su licencia es la misma que la del
compresor. Se le pide el periodo entero, se guarda el JSON y las siguientes corridas leen el
fichero.

Volver a pedírselo cada vez sería maleducado con un servicio ajeno y frágil para el proyecto: el
resultado dependería de que hoy esté levantado.

### Paso 2. Pedirlo todo en UTC

La telemetría del compresor viene en UTC. Si el clima llegara en hora local de Oporto, el cruce
quedaría desplazado una hora en verano y ninguno de los dos ficheros lo diría.

### Paso 3. Meter los cuatro partes de avería con sus erratas

La tercera fuente son cuatro filas escritas a mano. Se convierten las fechas de texto a fecha de
verdad y se calcula la duración, que es lo que bronce puede hacer. Los dos `#1`, el `Air leak`
contra `Air Leak` y el mantenimiento fechado un mes antes se quedan tal cual.

### Paso 4. Bajar la telemetría al ritmo del clima

Y aquí está la decisión del módulo. La telemetría da 360 lecturas por hora y el clima da una. Para
cruzarlas se resume la telemetría a medias horarias.

Se pierde todo lo que pasa dentro de la hora, incluidos los ciclos del compresor. Se hace a
sabiendas, porque la pregunta que se quiere contestar es de hora, no de segundo.

## El código, por partes

### Paso 5. Las tres fuentes, y lo que cada una da

```diagrama
*TELEMETRÍA | Cada 10 segundos | 1.516.948 filas
*CLIMA | Cada hora | 5.136 filas
*AVERÍAS | Cuando se rompe algo | 4 filas
```

Trescientas veinte mil veces más filas en la primera que en la última. Esa desproporción es
normal y es lo que hace que cruzarlas sea un problema.

### Paso 6. Las dos tablas, antes de tocarlas

```sql-vivo
SELECT * FROM clima ORDER BY hora LIMIT 3;
```

```anota
FROM clima | la tabla del tiempo en Oporto, una fila por hora
```

```salida
┌─────────────────────┬──────────────┬─────────┬──────────────┐
│        hora         │ temperatura  │ humedad │    lluvia    │
│      timestamp      │ decimal(3,1) │  int32  │ decimal(2,1) │
├─────────────────────┼──────────────┼─────────┼──────────────┤
│ 2020-02-01 00:00:00 │         14.2 │      96 │          0.5 │
│ 2020-02-01 01:00:00 │         14.4 │      97 │          0.5 │
│ 2020-02-01 02:00:00 │         14.3 │      98 │          0.3 │
└─────────────────────┴──────────────┴─────────┴──────────────┘
```

Fíjate en el tipo de `temperatura`: **decimal**, no double. La API entrega un decimal exacto, así
que la trampa del módulo 9 no aplica aquí. Cada fuente trae sus propios tipos.

### Paso 7. La telemetría, ya bajada a la hora

```sql-vivo
SELECT * FROM horas ORDER BY hora LIMIT 3;
```

```anota
FROM horas | la telemetría resumida a medias horarias, con 360 lecturas detrás de cada fila
carga | la fracción de la hora que el compresor pasó cargando, de 0 a 1
lecturas | cuántas lecturas hubo esa hora, para no fiarse de una media hecha con cuatro
```

```salida
┌─────────────────────┬────────┬────────┬──────────┐
│        hora         │ aceite │ carga  │ lecturas │
│      timestamp      │ double │ double │  int64   │
├─────────────────────┼────────┼────────┼──────────┤
│ 2020-02-01 00:00:00 │   51.9 │ 0.0583 │      360 │
│ 2020-02-01 01:00:00 │  51.91 │ 0.0278 │      360 │
│ 2020-02-01 02:00:00 │  51.71 │ 0.0556 │      360 │
└─────────────────────┴────────┴────────┴──────────┘
```

La columna `lecturas` no es decoración. Una hora con 360 lecturas y otra con 12 dan las dos una
media, y solo una de las dos merece confianza.

### Paso 8. Cruzarlas, y preguntar quién explica el aceite

```sql-vivo
SELECT count(*) AS horas,
       round(corr(c.temperatura, h.aceite), 3) AS calle_aceite,
       round(corr(h.carga, h.aceite), 3)       AS carga_aceite,
       round(avg(h.aceite - c.temperatura), 1) AS grados_por_encima
FROM horas h
JOIN clima c ON c.hora = h.hora;
```

```anota
corr(a, b) | la correlación entre dos columnas: 1 es que van juntas del todo, 0 que no tienen nada que ver
ON c.hora = h.hora | ahora sí es una igualdad, porque las dos tablas están al mismo grano
avg(h.aceite - c.temperatura) | cuántos grados separa de media el aceite de la calle
```

```salida
┌───────┬──────────────┬──────────────┬───────────────────┐
│ horas │ calle_aceite │ carga_aceite │ grados_por_encima │
├───────┼──────────────┼──────────────┼───────────────────┤
│  4416 │        0.529 │        0.432 │              46.0 │
└───────┴──────────────┴──────────────┴───────────────────┘
```

## El resultado, medido

{{FIG:fig_m15_tres_frecuencias}}

**Qué esperábamos.** Que el clima fuera un dato de contexto, agradable de tener y poco
informativo. La temperatura del aceite de un compresor la pone el compresor.

**Qué salió.** Al revés. La temperatura de la calle explica el aceite con una correlación de
**0,529**, y la carga del propio compresor con **0,432**. **El tiempo que hace fuera pesa más que
el trabajo de la máquina.**

El aceite va **46,0 grados** por encima de la calle de media, y ese salto es el compresor. Lo que
manda sobre el resto es de dónde parte.

En la figura se ve el día de la avería #3 con las tres fuentes a la vez. Y hay algo que no estaba
buscando. **El aceite deja de ciclar y se queda plano justo a las 10:00**, en 75,7 grados de
media, y esa es la hora exacta en que empieza el parte.

Eso es lo mismo que midió el módulo 13 por otro camino. Con la fuga, el compresor no llega a
parar, así que el aceite no se enfría entre ciclo y ciclo.

**Qué significa.** Que un gemelo que prediga la temperatura del aceite sin mirar el termómetro de
la calle va a equivocarse de forma sistemática, y peor: se equivocará **más en verano**. Atribuiría
a la máquina un efecto que pone el clima, y eso es una fábrica de falsas alarmas.

Y sobre la desproporción de las fuentes, la lección práctica. **4 filas de averías valen tanto
como 1.516.948 de telemetría**, porque son las únicas que dicen qué pasó de verdad. El tamaño de
una fuente no dice nada de su valor.

## Ojo

- **Cruzar fuentes de distinto ritmo siempre pierde detalle.** Bajar la telemetría a medias
  horarias tira los ciclos del compresor. Se hace a sabiendas, no por descuido.
- **La zona horaria se pide, no se supone.** Todo va en UTC. Un cruce desplazado una hora funciona
  perfectamente y da resultados que parecen buenos.
- **Una media horaria hecha con 12 lecturas no vale lo que una hecha con 360.** Por eso la columna
  `lecturas` viaja con el dato, igual que el `medido` del módulo 14.
- **Correlación no es causa.** Que la calle y el aceite suban juntos no prueba que uno mueva al
  otro, aunque aquí la física lo respalde: el compresor aspira el aire de la calle.
- **Una fuente que no controlas puede desaparecer.** El JSON del clima se guarda en `data/` y se
  vuelve a leer de ahí. Si mañana la API cambia, el proyecto sigue reproduciéndose.
- **Los partes siguen con sus erratas.** Aquí se les añaden tipos y duración, que se derivan de lo
  que hay. Ni una mayúscula corregida.

## Puente metalúrgico

Un balance de planta cruza tres registros que nunca laten igual. La báscula pesa camión a camión,
el laboratorio analiza una compuesta por turno, y el parte de mantenimiento aparece cuando algo se
rompe.

Nadie intenta cruzarlos al segundo. Se elige el turno como grano común, se suman sus toneladas y
se les aplica la ley de la compuesta. Dentro del turno la ley varió, y esa variación se ha
perdido a sabiendas.

Lo que distingue un balance serio de uno improvisado no es evitar esa pérdida, que es inevitable.
Es que esté escrito qué grano se eligió y por qué.

## Hazlo tú

```reto
pregunta: Reparte las horas en tres tramos según la temperatura de la calle, menos de 10 grados, de 10 a 20 y más de 20, y devuelve `calle`, `horas` y `aceite_medio` con la temperatura media del aceite en cada tramo. Tres filas.
inicio: SELECT count(*) AS horas,
       round(avg(h.aceite), 1) AS aceite_medio
FROM horas h
JOIN clima c ON c.hora = h.hora;
esperado: m15_aceite_por_tramo
pista: El cruce del punto de partida ya está bien. Lo que falta es la columna que reparte, y es un `CASE` como el del módulo 9, pero sobre `c.temperatura` en vez de sobre la corriente. Después se agrupa por esa columna nueva. Nombra los tramos empezando por una letra, `a.`, `b.` y `c.`, para que el `ORDER BY` los saque en orden.
solucion: SELECT CASE WHEN c.temperatura < 10 THEN 'a. menos de 10'
            WHEN c.temperatura < 20 THEN 'b. de 10 a 20'
            ELSE 'c. mas de 20' END AS calle,
       count(*) AS horas,
       round(avg(h.aceite), 1) AS aceite_medio
FROM horas h
JOIN clima c ON c.hora = h.hora
GROUP BY calle
ORDER BY calle;
```

## Repaso

### Por qué meter el clima en un proyecto sobre un compresor

Porque el compresor aspira el aire de la calle, así que la temperatura y la humedad de fuera son
condiciones de contorno de su física. Y porque está medido: la calle explica la temperatura del
aceite mejor que la propia carga del compresor, 0,529 contra 0,432.

### Qué hay que decidir al cruzar dos fuentes de distinta frecuencia

En qué grano se trabaja. La fuente rápida hay que resumirla hasta el ritmo de la lenta, y eso tira
detalle. Aquí se pierden los ciclos del compresor dentro de cada hora. La decisión correcta es la
que se declara, porque el error caro es cruzarlas sin darse cuenta de que se ha elegido.

### Pides datos a una API que no es tuya. Qué precauciones tomas

Guardar la respuesta cruda en disco y volver a leerla de ahí, para no depender de que el servicio
esté levantado ni pedirle lo mismo cada día. Pedir siempre la misma zona horaria, en UTC. Y
anotar la licencia y la cita, que aquí es CC BY 4.0 igual que la del compresor.

### Cuatro filas de averías contra 1.516.948 de telemetría. Sirve de algo esa tabla

Es la más valiosa de las tres. La telemetría dice qué hacía la máquina y solo los partes dicen
cuándo estuvo rota, que es lo único contra lo que se puede validar cualquier detector. El tamaño
de una fuente no dice nada de su valor.

### Qué le pasaría a un gemelo que ignorase el clima

Que se equivocaría más en verano que en invierno. Predeciría la temperatura del aceite contando
solo con el trabajo de la máquina. La diferencia entre una calle de enero y una de agosto se la
atribuiría al compresor, y un detector construido sobre eso dispararía falsas alarmas con el
calor.

---
module: 13
---

## En 30 segundos

- Agrupar junta filas. Una **función de ventana** las deja sueltas y les enseña la de al lado.
- El hueco entre dos lecturas **no es una columna**: solo existe como diferencia entre filas.
- En el lago hay **179.426** huecos que no respetan los diez segundos, el 11,8 %.
- El mayor dura **48 horas**, del 25 al 27 de abril, y explica un día que faltaba.
- Un arranque tampoco es un dato: es una fila que dice carga detrás de otra que no.

## Qué resuelve este módulo

Todo lo anterior aplastaba filas. `GROUP BY` coge mil lecturas y devuelve una. Sirve para
resumir, y por eso mismo no sirve para nada que dependa del orden.

Este módulo hace lo contrario: conserva todas las filas y le enseña a cada una sus vecinas. Sin
eso no hay series de tiempo, y sin series de tiempo no hay gemelo.

## Antes de la teoría: un ejemplo de juguete

Seis lecturas de una mañana, con el estado del compresor:

| hora | carga |
|---|---|
| 08:00 | 0 |
| 08:10 | 0 |
| 08:20 | 1 |
| 08:30 | 1 |
| 08:40 | 0 |
| 09:00 | 0 |

**Pregunta uno: ¿cuánto tiempo pasó entre cada lectura y la anterior?**

Mira la tabla y ve restando: 10, 10, 10, 10 y **20 minutos**. La última es el doble que las
demás, y ahí falta una lectura.

Fíjate en algo. Ese 20 **no está escrito en ninguna parte de la tabla**. No es una columna, no es
un valor de ninguna fila. Nace de restar dos filas, y por eso hasta ahora no se podía preguntar.

**Pregunta dos: ¿cuántas veces arrancó el compresor?**

Buscas dónde la carga pasa de 0 a 1. Pasa una vez, a las 08:20. **Un arranque.**

Y otra vez lo mismo: mirando una fila sola no se sabe si es un arranque. La de las 08:20 dice 1,
igual que la de las 08:30, y sin embargo solo una de las dos es un arranque. La diferencia está
en lo que decía la anterior.

Eso es una función de ventana: **cada fila puede mirar a sus vecinas sin dejar de ser una fila.**

## Glosario

- **Función de ventana.** Una función que calcula algo para cada fila mirando un conjunto de
  filas alrededor, sin agruparlas.
- **`OVER`.** La palabra que convierte una función normal en función de ventana. Define qué filas
  ve cada una.
- **`lag(columna)`.** El valor de esa columna en la fila anterior. Si no hay anterior, NULL.
- **`lead(columna)`.** Lo mismo con la fila siguiente.
- **`ORDER BY` dentro de `OVER`.** Qué significa «anterior». Sin él no hay anterior, porque no
  hay orden.
- **`PARTITION BY`.** Reinicia la ventana en cada grupo. Con `PARTITION BY day`, la primera
  lectura de cada día no tiene anterior.
- **Hueco.** Los segundos entre una lectura y la anterior. En este fichero deberían ser diez.

## Paso a paso

### Paso 1. Mirar la fila anterior

`lag()` trae el valor de la fila de arriba. Con eso, cada fila pasa a tener dos versiones de la
misma columna: la suya y la anterior, en la misma fila y una al lado de la otra.

A partir de ahí, restarlas o compararlas ya es SQL corriente.

### Paso 2. Decir qué significa «anterior»

Y esto no es opcional. La fila anterior solo existe si hay un orden, así que `OVER` lleva siempre
un `ORDER BY` dentro. Aquí es la marca de tiempo.

Es el mismo aviso del módulo 8, ahora con consecuencias peores: allí un orden ausente daba filas
distintas, y aquí daría huecos inventados.

### Paso 3. Medir el hueco

Restar la marca de tiempo de la fila anterior a la propia. Donde salga diez, todo normal. Donde
salga otra cosa, ahí falta algo o el reloj se movió.

### Paso 4. Contar arranques

Un arranque es una fila con carga uno cuya anterior tenía carga cero. Se filtra por esa pareja de
condiciones y se cuenta.

## El código, por partes

### Paso 5. La fila anterior, al lado de la propia

```sql-vivo
SELECT timestamp,
       DV_eletric,
       lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
FROM telemetria
WHERE day = DATE '2020-06-05'
ORDER BY timestamp
LIMIT 5;
```

```anota
lag(DV_eletric) | el valor que tenía esa columna en la fila de arriba
OVER (...) | convierte lag en función de ventana; dentro va la definición de la ventana
ORDER BY timestamp | qué quiere decir «la fila de arriba»: la anterior en el tiempo
AS antes | el nombre de la columna nueva, para poder compararla con la de la propia fila
```

```salida
┌─────────────────────┬────────────┬────────┐
│      timestamp      │ DV_eletric │ antes  │
│      timestamp      │   double   │ double │
├─────────────────────┼────────────┼────────┤
│ 2020-06-05 00:00:02 │        0.0 │   NULL │
│ 2020-06-05 00:00:12 │        0.0 │    0.0 │
│ 2020-06-05 00:00:22 │        0.0 │    0.0 │
│ 2020-06-05 00:00:32 │        0.0 │    0.0 │
│ 2020-06-05 00:00:42 │        0.0 │    0.0 │
└─────────────────────┴────────────┴────────┘
```

La primera fila tiene NULL en `antes`, y es correcto: no hay fila anterior. Es el vacío del
módulo 8 apareciendo donde debe.

Y fíjate en los segundos, que van de dos en dos decenas empezando por el 02. El día no empieza
en punto. El compresor lleva midiendo desde antes, así que esas son las lecturas que le tocaron y
no un reloj puesto a cero.

### Paso 6. El hueco entre lecturas

```sql-vivo
SELECT hueco, count(*) AS veces
FROM (
    SELECT date_diff('second',
                     lag(timestamp) OVER (ORDER BY timestamp),
                     timestamp) AS hueco
    FROM telemetria
    WHERE day = DATE '2020-06-05'
)
WHERE hueco IS NOT NULL
GROUP BY hueco
ORDER BY veces DESC;
```

```anota
date_diff('second', a, b) | cuántos segundos hay entre dos marcas de tiempo
WHERE hueco IS NOT NULL | quita la primera fila, la que no tiene anterior
```

```salida
┌───────┬───────┐
│ hueco │ veces │
├───────┼───────┤
│    10 │  7953 │
│     9 │   762 │
└───────┴───────┘
```

Ese día el muestreo tiene dos ritmos: 7.953 veces de diez segundos y 762 de nueve. La ficha
prometía diez siempre.

Y fíjate en la forma de la consulta: la ventana se calcula dentro y el `GROUP BY` va fuera. No se
puede agrupar por algo todavía sin calcular, así que hacen falta dos pasos. Es el módulo 11 otra
vez.

### Paso 7. Los arranques

```sql-vivo
SELECT count(*) AS arranques
FROM (
    SELECT DV_eletric,
           lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
    FROM telemetria
    WHERE day = DATE '2020-06-05'
)
WHERE antes = 0 AND DV_eletric = 1;
```

```anota
WHERE antes = 0 AND DV_eletric = 1 | la definición de arranque: antes no cargaba y ahora sí
```

```salida
┌───────────┐
│ arranques │
├───────────┤
│        31 │
└───────────┘
```

Treinta y un arranques ese día. Guarda ese número, porque el resultado del módulo depende de
compararlo con algo.

## El resultado, medido

{{FIG:fig_m13_lag_y_hueco}}

**Qué esperábamos.** Más arranques de lo normal en un día de avería, porque el compresor tiene
que reponer el aire que se escapa.

**Qué salió.** Al revés. El 5 de junio, que es el primer día de la avería **#3**, el compresor
arrancó **31 veces**. La mediana de los 208 días con arranques es **58**, y el máximo son
**1.257** arranques el 23 de junio.

O sea que un día de avería tiene **la mitad de arranques** que un día normal.

**Qué significa.** Y aquí está lo bueno, porque ese mismo día el compresor estuvo **15,41 horas
en carga**, contra las 3,42 de un día corriente. Arrancó menos y trabajó cuatro veces más.

No se contradicen: **se explican**. Con una fuga grande, el compresor no llega a parar. En vez de
arrancar y parar sesenta veces, arranca treinta y se queda dentro. Contar arranques sin mirar
cuánto duran habría dado exactamente la conclusión contraria a la verdadera.

Es la misma trampa del módulo 5 con las medias, en otro sitio: **el número que se cuenta más
fácil no siempre es el que dice la verdad.**

**Y la cifra del módulo.** En el lago entero hay **179.426** huecos que no son de diez segundos,
el **11,8 %**. El mayor mide **48 horas**, del **25 al 27 de abril**. Eso explica el 26 de abril que faltaba en
el módulo 8: no falta una fila, faltan dos días seguidos.

## Ojo

- **Sin `ORDER BY` dentro de `OVER` no hay fila anterior.** El resultado sale igualmente, y es
  cualquier cosa. Es el peor caso del módulo 8: allí cambiaba el orden, aquí cambia el dato.
- **La primera fila siempre tiene NULL.** No hay anterior. Filtrarla con `IS NOT NULL` es parte
  de la consulta, no un apaño.
- **`PARTITION BY day` cambia el resultado, y a veces es lo correcto.** Sin él, la última lectura
  de un día se compara con la primera del siguiente, y ese hueco cruza la medianoche.
- **La ventana se calcula antes de poder agruparla.** Por eso estas consultas van en dos pasos,
  con la ventana dentro y el `GROUP BY` fuera.
- **Contar sucesos no basta.** Treinta y un arranques parecen menos que cincuenta y ocho hasta
  que se mira cuánto dura cada uno. Un suceso sin su duración es media medida.
- **Esta lección corre sobre un solo día.** La muestra que baja tu navegador es la del 5 de junio,
  porque llevar la hora exacta del lago entero costaría 5,16 MB, y el módulo 7 midió por qué. Por
  eso todas las consultas llevan su `WHERE day = DATE '2020-06-05'`.

## Puente metalúrgico

En un molino SAG, el dato que de verdad importa no es la potencia instantánea: es cómo cambia.
Una subida sostenida durante veinte minutos significa que la carga está creciendo, y eso se ve
comparando cada lectura con la de hace un rato, no mirando el número de ahora.

Por eso las salas de control no enseñan cifras: enseñan tendencias. Un operador experimentado no
te dice cuántos kilovatios marca, te dice que va subiendo.

`lag()` es esa mirada hacia atrás escrita en SQL. Y el aviso del módulo vale igual en la sala:
contar cuántas veces se disparó una alarma dice mucho menos que contar cuánto tiempo estuvo
disparada.

## Hazlo tú

```reto
pregunta: Cuenta cuántas veces **paró** el compresor ese día, o sea las filas donde la carga pasa de 1 a 0. Devuelve una sola columna llamada `paradas`.
inicio: SELECT count(*) AS arranques
FROM (
    SELECT DV_eletric,
           lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
    FROM telemetria
    WHERE day = DATE '2020-06-05'
)
WHERE antes = 0 AND DV_eletric = 1;
esperado: m13_paradas_del_dia
pista: Es el mismo cambio de estado del paso 7, pero al revés. Donde el arranque pide que antes fuera 0 y ahora 1, la parada pide que antes fuera 1 y ahora 0. Solo hay que darle la vuelta a las dos condiciones del `WHERE` y cambiarle el nombre a la columna.
solucion: SELECT count(*) AS paradas
FROM (
    SELECT DV_eletric,
           lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
    FROM telemetria
    WHERE day = DATE '2020-06-05'
)
WHERE antes = 1 AND DV_eletric = 0;
```

## Repaso

### Diferencia entre GROUP BY y una función de ventana

`GROUP BY` aplasta: coge muchas filas y devuelve una por grupo. Una función de ventana conserva
todas las filas y le añade a cada una un cálculo hecho mirando a sus vecinas. Se usa una u otra
según si la respuesta tiene una fila por grupo o una fila por lectura.

### Por qué el hueco entre lecturas no se puede sacar con lo anterior

Porque no está en ninguna fila. Es la diferencia entre dos, y hasta ahora todas las herramientas
del curso miraban una fila cada vez o un grupo entero de golpe. `lag()` es lo primero que pone
dos filas a la vez al alcance de la misma expresión.

### Qué pasa si te olvidas del ORDER BY dentro del OVER

Que la consulta funciona y el resultado no significa nada. «La fila anterior» deja de estar
definida, así que el motor devuelve alguna, y los huecos que salgan serán inventados. Es peor que
un error, porque un error se ve.

### Un día de avería tuvo menos arranques que uno normal. Cómo lo explicas

Porque con una fuga grande el compresor no llega a parar. Ese día arrancó 31 veces contra una
mediana de 58, y a la vez estuvo 15,41 horas en carga contra 3,42. Arrancó la mitad y trabajó
cuatro veces más, porque cada arranque duró muchísimo más. Contar sucesos sin medir su duración
lleva justo a la conclusión contraria.

### Para qué le sirve todo esto al gemelo digital

Para poder comparar. Un gemelo predice qué debería estar pasando ahora, y «ahora» solo tiene
sentido con el instante anterior al lado. Los huecos hay que conocerlos para no tratar como
seguidas dos lecturas separadas por 48 horas, y el ciclo de arranques es la señal donde este
proyecto espera ver la fuga.

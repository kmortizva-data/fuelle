---
module: 12
---

## En 30 segundos

- Un `JOIN` junta dos tablas por algo que tienen en común.
- El cruce bueno **no cambia el recuento**: 1.516.948 lecturas siguen siendo 1.516.948.
- El malo multiplica sin avisar: los 4 partes de avería se convierten en **6 filas**.
- La culpa la tiene una errata real: **dos partes están numerados `#1`**.
- Cruzando bien, **54.354 lecturas** caen dentro de una avería documentada, el 3,58 %.

## Qué resuelve este módulo

La telemetría dice qué hacía el compresor. Los partes de avería dicen cuándo estuvo roto. Por
separado no contestan nada interesante; juntos son el material del resto del proyecto.

Juntarlos es un `JOIN`, y es la operación con la que más gente se equivoca sin enterarse, porque
cuando sale mal no da error: da filas de más.

## Antes de la teoría: un ejemplo de juguete

Dos tablas de un día de planta. Los turnos, con lo que procesó cada uno:

| turno | toneladas |
|---|---|
| T1 | 100 |
| T2 | 200 |

Y las incidencias apuntadas:

| turno | incidencia |
|---|---|
| T1 | parada de molino |
| T1 | atasco de cinta |
| T2 | vibración en bomba |

**Cuánto se procesó ese día.** Sumas la primera tabla: 100 más 200, **300 toneladas**. Eso es la
respuesta correcta y la sabes antes de tocar nada.

Ahora júntalas por turno, para poder mirar toneladas e incidencias a la vez:

| turno | toneladas | incidencia |
|---|---|---|
| T1 | 100 | parada de molino |
| T1 | 100 | atasco de cinta |
| T2 | 200 | vibración en bomba |

Y vuelve a sumar las toneladas de esa tabla: 100 más 100 más 200, **400**.

Cien toneladas aparecidas de la nada. Y fíjate en que la tabla no está mal: cada fila es cierta.
Lo que está mal es sumar una columna que ahora se repite.

Pasó porque **T1 tenía dos incidencias**, así que su fila de turno se copió dos veces para poder
emparejarse con cada una. El turno no cambió de grano; la tabla sí.

Esa es la trampa entera del módulo: **cruzar por algo que no es único multiplica filas**, y
después todo lo que se sume o se cuente está inflado.

## Glosario

- **`JOIN`.** Juntar dos tablas emparejando filas que cumplen una condición.
- **Clave.** La columna, o el grupo de columnas, que identifica una fila sin repetirse. Si se
  repite, no es una clave.
- **`INNER JOIN`.** Se queda solo con las filas que encuentran pareja. Las demás desaparecen.
- **`LEFT JOIN`.** Se queda con **todas** las de la izquierda, con pareja o sin ella. Las que no
  la encuentran salen con NULL en las columnas de la derecha.
- **`CROSS JOIN`.** Empareja cada fila con todas las de la otra tabla. Es el cruce sin condición
  y crece muy deprisa.
- **Grano.** A qué corresponde una fila, del módulo 2. Un `JOIN` puede cambiarlo sin avisar, y ahí
  empiezan los problemas.

## Paso a paso

### Paso 1. Mirar la tabla pequeña antes de cruzar nada

Cuatro filas. Se leen en diez segundos y ahorran horas, porque casi todo lo que puede salir mal
de este cruce está a la vista en ellas.

### Paso 2. Convertir las fechas, que vienen como texto

Los partes traen `4/18/2020 0:00` escrito como texto. Comparar texto con fechas no funciona, o
peor, funciona mal. Hay que convertirlo antes, y eso es lo que el módulo 9 dejó dicho.

### Paso 3. Elegir la condición del cruce

Aquí no hay una columna compartida entre las dos tablas: la telemetría tiene un día y el parte
tiene un intervalo. Así que la condición no es una igualdad, es una pertenencia.

### Paso 4. Contar antes y contar después

Y esta es la costumbre que hay que coger. Antes de cruzar se cuentan las filas, después se
vuelven a contar, y si el número cambió sin que se pretendiera, el cruce está mal.

## El código, por partes

### Paso 5. La tabla pequeña, entera

```sql-vivo
SELECT nr, start_time, end_time, failure, report
FROM averias;
```

```anota
FROM averias | la otra tabla que trae tu navegador: los cuatro partes de avería
```

```salida
┌─────────┬─────────────────┬─────────────────┬──────────┬───────────────────────────────┐
│   nr    │   start_time    │    end_time     │ failure  │            report             │
├─────────┼─────────────────┼─────────────────┼──────────┼───────────────────────────────┤
│ #1      │ 4/18/2020 0:00  │ 4/18/2020 23:59 │ Air leak │ NULL                          │
│ #1      │ 5/29/2020 23:30 │ 5/30/2020 6:00  │ Air Leak │ Maintenance on 30Apr at 12:00 │
│ #3      │ 6/5/2020 10:00  │ 6/7/2020 14:30  │ Air Leak │ Maintenance on 8Jun at 16:00  │
│ #4      │ 7/15/2020 14:30 │ 7/15/2020 19:00 │ Air Leak │ Maintenance on 16Jul at 00:00 │
└─────────┴─────────────────┴─────────────────┴──────────┴───────────────────────────────┘
```

Cuatro filas y tres cosas que apuntar, todas verdad y ninguna corregida:

**Hay dos partes numerados `#1` y no hay ningún `#2`.** Ese número parece un identificador y no
lo es.

**`Air leak` y `Air Leak`.** La misma avería escrita de dos formas. Agrupar por esa columna daría
dos grupos donde hay uno.

**El parte del 29 de mayo dice que el mantenimiento fue el 30 de abril**, un mes antes de la
propia avería. Es una errata del original y se queda tal cual.

### Paso 6. Cruzar bien, y comprobar el recuento

```sql-vivo
SELECT count(*) AS filas,
       count(a.nr) AS dentro_de_una_averia
FROM telemetria t
LEFT JOIN (
    SELECT nr,
           CAST(strptime(start_time, '%-m/%-d/%Y %-H:%M') AS DATE) AS desde,
           CAST(strptime(end_time,   '%-m/%-d/%Y %-H:%M') AS DATE) AS hasta
    FROM averias
) a ON t.day BETWEEN a.desde AND a.hasta;
```

```anota
LEFT JOIN | se queda con todas las lecturas, encuentren avería o no
strptime(texto, formato) | convierte texto a fecha diciendo en qué formato está escrito
%-m/%-d/%Y %-H:%M | ese formato: mes, día, año y hora, sin ceros delante
ON t.day BETWEEN a.desde AND a.hasta | la condición del cruce; no es una igualdad, es caer dentro del intervalo
count(a.nr) | cuenta solo las filas donde esa columna NO es NULL, o sea las que encontraron avería
```

```salida
┌─────────┬──────────────────────┐
│  filas  │ dentro_de_una_averia │
├─────────┼──────────────────────┤
│ 1516948 │                54354 │
└─────────┴──────────────────────┘
```

Las filas siguen siendo 1.516.948, exactamente las que había antes de cruzar. Ese número es la
prueba de que el cruce no ha inventado nada.

Y fíjate en la diferencia entre las dos columnas: `count(*)` cuenta filas y `count(a.nr)` cuenta
las que tienen valor. Es el módulo 8 otra vez, ahora con un uso práctico.

### Paso 7. El cruce que multiplica

```sql
SELECT count(*) AS filas
FROM averias a
JOIN averias b ON a.nr = b.nr;
```

```anota
JOIN | sin la palabra LEFT delante, es un INNER JOIN: solo las filas con pareja
a.nr = b.nr | se cruza por el número de parte, que parece identificar una avería
a, b | dos nombres cortos para la misma tabla, porque se cruza consigo misma
```

```salida
┌───────┐
│ filas │
├───────┤
│     6 │
└───────┘
```

Seis filas de una tabla de cuatro. Cada parte `#1` encuentra dos parejas, la suya y la del otro
`#1`, así que esas dos filas se convierten en cuatro.

Ningún error, ningún aviso. Solo dos filas de más.

## El resultado, medido

{{FIG:fig_m12_tipos_de_join}}

**Qué esperábamos.** Que cruzar la telemetría con los partes marcara las lecturas averiadas sin
tocar el recuento.

**Qué salió.** Eso, con el `LEFT JOIN`: **1.516.948 filas antes y 1.516.948 después**, y
**54.354** de ellas dentro de una avería documentada, el **3,58 %** del registro.

La figura enseña las tres formas de escribir el mismo cruce. El `INNER JOIN` devuelve **54.354**,
que son solo las lecturas con avería. El `CROSS JOIN`, que no lleva condición, devuelve
**6.067.792**: cada lectura emparejada con cada uno de los cuatro partes.

Repartidas por avería, las cuatro quedan así:

| Parte | Desde | Hasta | Lecturas | Horas de carga |
|---|---|---|---|---|
| #1 | 2020-04-18 | 2020-04-18 | 8.663 | 23,8 |
| #1 | 2020-05-29 | 2020-05-30 | 16.083 | 11,3 |
| #3 | 2020-06-05 | 2020-06-07 | 20.947 | 49,4 |
| #4 | 2020-07-15 | 2020-07-15 | 8.661 | 11,6 |

{{FIG:fig_m12_join_que_multiplica}}

**Y el cruce que miente.** Cruzando los cuatro partes por su número se pasa **de 4 filas a 6**.
En la figura se ve por qué: las dos líneas gruesas son los dos partes `#1`, y cada uno se empareja
con los dos.

Cruzando por la pareja que sí identifica un parte, el número y la fecha de inicio, salen **4**,
que es lo correcto.

**Qué significa.** La errata que el módulo 1 dejó anotada y sin corregir se ha convertido aquí en
un fallo de verdad. No es un ejemplo de laboratorio: es la única fuente de verdad del proyecto,
con una numeración que no numera.

Y de ahí sale la costumbre que hay que llevarse: **contar las filas antes y después de cruzar**.
No es paranoia, es la única forma de enterarse, porque un cruce que multiplica no da error.

## Ojo

- **Un `JOIN` puede cambiar el grano de la tabla.** Si la de la derecha tiene varias filas por
  cada una de la izquierda, la izquierda se copia. Después, cualquier suma está inflada.
- **Cuenta antes y cuenta después.** Es la comprobación más barata que existe y caza casi todos
  los cruces mal hechos.
- **Que una columna se llame como un identificador no la convierte en clave.** Aquí `nr` tiene
  dos filas con el mismo valor. Se comprueba con un `GROUP BY nr HAVING count(*) > 1`.
- **`INNER JOIN` borra filas en silencio.** Las lecturas sin avería, que son el 96 %,
  desaparecerían sin decir nada. Cuando quieras conservarlas todas, `LEFT JOIN`.
- **Las fechas del parte son texto.** Comparar texto con fechas puede funcionar por casualidad y
  fallar en cuanto cambie el formato. Se convierte primero, siempre.
- **`Air leak` y `Air Leak` son grupos distintos** para un `GROUP BY`. Los datos originales no se
  tocan, así que la normalización se hace al agrupar, no al ingerir.

## Puente metalúrgico

En un balance de planta hay dos registros que se cruzan a diario: el de camiones que descargan en
la tolva y el de análisis de laboratorio. Se cruzan por número de lote.

El día que un lote se muestrea dos veces, porque el primer análisis salió raro, ese número deja de
identificar una fila. Cruzando por él, el camión de ese lote aparece dos veces, y su tonelaje se
cuenta dos veces en el balance del mes.

Nadie se entera mirando el resultado, porque el balance sigue cerrando. Se entera quien compara el
tonelaje del cruce con el tonelaje de la báscula, que es exactamente contar antes y después.

## Hazlo tú

```reto
pregunta: Marca cada avería con cuántas lecturas del compresor caen dentro de ella. Devuelve tres columnas, `nr`, `desde` y `lecturas`, una fila por parte. Cuatro filas, ordenadas por fecha.
inicio: SELECT count(*) AS filas,
       count(a.nr) AS dentro_de_una_averia
FROM telemetria t
LEFT JOIN (
    SELECT nr,
           CAST(strptime(start_time, '%-m/%-d/%Y %-H:%M') AS DATE) AS desde,
           CAST(strptime(end_time,   '%-m/%-d/%Y %-H:%M') AS DATE) AS hasta
    FROM averias
) a ON t.day BETWEEN a.desde AND a.hasta;
esperado: m12_lecturas_por_averia
pista: El cruce del punto de partida ya es el bueno, pero va del revés para lo que pide el reto: hay que poner los partes a la izquierda y la telemetría a la derecha, para que salga una fila por parte. Después es un `GROUP BY` por `a.nr` y `a.desde`, contando con `count(t.day)`, que no cuenta las lecturas ausentes.
solucion: SELECT a.nr, a.desde, count(t.day) AS lecturas
FROM (
    SELECT nr,
           CAST(strptime(start_time, '%-m/%-d/%Y %-H:%M') AS DATE) AS desde,
           CAST(strptime(end_time,   '%-m/%-d/%Y %-H:%M') AS DATE) AS hasta
    FROM averias
) a
LEFT JOIN telemetria t ON t.day BETWEEN a.desde AND a.hasta
GROUP BY a.nr, a.desde
ORDER BY a.desde;
```

## Repaso

### Diferencia entre INNER JOIN y LEFT JOIN

El `INNER` se queda solo con las filas que encuentran pareja, y las demás desaparecen sin avisar.
El `LEFT` conserva todas las de la izquierda y rellena con NULL las columnas de la derecha cuando
no hay pareja. Aquí la diferencia es enorme: 54.354 filas contra 1.516.948.

### Cómo sabes que un cruce ha salido mal

Contando filas antes y después. Si la tabla de la izquierda tenía 1.516.948 y después del cruce
hay más, alguna fila se ha duplicado por tener varias parejas. Es la comprobación más barata que
hay y casi nadie la hace, porque un cruce mal hecho no da error.

### Por qué no puedes cruzar por el número de parte

Porque dos de los cuatro partes son `#1`. Ese número parece un identificador, y cruzando por él
cada `#1` se empareja con los dos, así que cuatro filas salen seis. La clave de verdad aquí es la
pareja de número y fecha de inicio, que sí identifica una fila.

### Los partes traen erratas. Por qué no las corriges antes de cruzar

Porque son la única fuente de verdad del proyecto y no son mías. Corregir la numeración sería
inventar un dato que nadie midió. La regla del curso es que el crudo se conserva literal, y las
correcciones se hacen al consultar, donde quedan a la vista y se pueden revisar.

### Sumas toneladas después de cruzar con una tabla de incidencias. Qué compruebas

Que el cruce no haya cambiado el grano. Si un turno tiene dos incidencias, su fila se copia dos
veces y su tonelaje se cuenta dos veces. Se comprueba contando filas antes y después, o sumando
antes de cruzar y comparando con la suma de después.

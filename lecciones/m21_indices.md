---
module: 21
---

## En 30 segundos

- Un índice es una copia ordenada de una columna, para no tener que mirar la tabla entera.
- La misma pregunta del módulo 6, un día concreto, pasa de barrer **1.841.760** filas a saltar.
- Va **entre 58,1 y 114,3 veces** más rápida según la repetición, y esa horquilla es el resultado.
- Lo que sí es estable: el índice ocupa **12,3 MB** y pone la escritura al **doble**.
- La prueba de que funciona no es el cronómetro, es **el plan** que la base te enseña.

## Qué resuelve este módulo

El módulo 6 hizo esta misma pregunta a un Parquet: dame un día. Allí la respuesta fue cómo repartir
los ficheros en el disco, y la conclusión sorprendió, porque partir por día era la peor opción.

Aquí la pregunta es la misma y la herramienta es otra. Una base de datos no reparte ficheros:
construye **índices**, que es una estructura aparte cuyo único trabajo es encontrar deprisa.

Y como todo lo que se añade, hay que saber qué cuesta. Un índice no es gratis y este módulo lo mide
por los dos lados.

## Antes de la teoría: un ejemplo de juguete

Un archivador con las fichas de mil lotes, metidas por orden de llegada. Te piden las del 5 de
junio.

No hay más remedio que **mirarlas todas**, porque la fecha puede estar en cualquier sitio. Mil
fichas, una por una. Eso es un recorrido secuencial.

Ahora alguien monta al lado un fichero de tarjetas con las fechas ordenadas, y cada tarjeta dice en
qué cajón está su ficha:

| fecha | cajón |
|---|---|
| 4 de junio | 812 |
| 5 de junio | 813 |
| 5 de junio | 814 |
| 6 de junio | 815 |

Ahora la respuesta es: ir al fichero, que está ordenado, y con dos saltos plantarse en las
tarjetas del 5 de junio. **De mil miradas a unas pocas.**

El fichero de tarjetas es el índice. Y trae tres facturas que nadie enseña cuando lo vende:

1. **Ocupa sitio.** Es una copia de la columna de fechas.
2. **Hay que mantenerlo.** Cada ficha nueva obliga a escribir también su tarjeta, en su sitio.
3. **Solo sirve para lo que ordena.** Ordenado por fecha, no ayuda a buscar por número de lote.

## Glosario

- **Índice.** Una estructura ordenada, aparte de la tabla, que dice dónde está cada valor.
- **Recorrido secuencial.** Leer la tabla entera. En inglés `Seq Scan`, y es lo que la base hace
  cuando no tiene nada mejor.
- **Recorrido por índice.** Usar el índice para ir directo. `Index Scan`.
- **Plan de ejecución.** Lo que la base ha decidido hacer con tu consulta. Se pide con `EXPLAIN`.
- **Selectividad.** Qué proporción de la tabla devuelve un filtro. Un índice ayuda cuando es baja.
- **`ANALYZE`.** Actualiza las estadísticas que el planificador usa para decidir.

## Paso a paso

### Paso 1. Preguntar sin índice, y mirar el plan

Antes de tocar nada, ver qué hace la base. `EXPLAIN` cuenta su plan sin ejecutarlo, y ahí aparece
la frase que importa: `Seq Scan`, o sea que va a leer la tabla entera.

### Paso 2. Medir, con la regla de siempre

Mediana de siete corridas y su rango, como el módulo 6 y el 18. Y `distinguishable()` decidiendo si
hay diferencia que contar.

### Paso 3. Crear el índice y volver a mirar el plan

Primero el plan, después el reloj. **El plan pasa de `Seq Scan` a `Index Scan`, y ahí está la
prueba de que el índice se usa.** No depende de lo ocupada que esté la máquina.

### Paso 4. `ANALYZE`, o el índice puede quedarse mirando

El planificador decide con estadísticas. Si están viejas puede seguir prefiriendo el recorrido
completo aunque el índice exista, y entonces la medición compararía dos veces lo mismo.

### Paso 5. Medir lo que cuesta

Un índice cobra en disco y en cada escritura. Se mide escribiendo **200.000 filas** en una tabla de
usar y tirar, con el índice y sin él.

Se hace en una tabla aparte a propósito: medir escrituras sobre la buena la dejaría con filas de
más al terminar.

## El código, por partes

### Paso 6. El plan sin índice

```postgres
SELECT count(*) AS lecturas,
       round(avg(oil_temperature)::numeric, 2) AS aceite
FROM lecturas
WHERE day = DATE '2020-06-05';
```

```anota
WHERE day = ... | el filtro. De 1.841.760 filas, este día tiene 8.640
la pregunta | es la del módulo 6, a propósito: allí se resolvía repartiendo ficheros y aquí con un índice
```

```salida
 lecturas | aceite
----------+--------
     8640 |  70.57
(1 row)
```

Y esto es lo que la base dice que va a hacer para contestarla:

```salida
Finalize Aggregate
  ->  Gather
        Workers Planned: 2
        ->  Partial Aggregate
              ->  Parallel Seq Scan on lecturas
                    Filter: (day = '2020-06-05'::date)
```

**`Seq Scan`**: recorrido secuencial. Va a leer las 1.841.760 filas y quedarse con las 8.640 que
cumplen. Y ya está usando dos trabajadores en paralelo, que es la base haciendo lo que puede con
una mala mano.

### Paso 7. El índice, y el plan otra vez

```postgres
SELECT count(*) AS indices
FROM pg_indexes
WHERE tablename = 'lecturas';
```

```anota
pg_indexes | otra vista del catálogo, como el pg_constraint del módulo 20
```

```salida
 indices
---------
       2
(1 row)
```

Dos: el de la clave primaria, que PostgreSQL creó solo en el módulo 20, y el nuestro sobre `day`.
Con él, el plan de la misma consulta es otro:

```salida
Aggregate
  ->  Index Scan using lecturas_por_dia on lecturas
        Index Cond: (day = '2020-06-05'::date)
```

Desapareció el recorrido completo y desaparecieron los trabajadores en paralelo: **ya no hace falta
repartirse un trabajo que ha dejado de existir**.

### Paso 8. Y lo que cuesta

```python
escritura_sin = measure(escribe, setup=vacia_sin_indice)
escritura_con = measure(escribe, setup=vacia_con_indice)
peaje = times_slower(escritura_con, escritura_sin)
```

```anota
setup= | prepara la tabla antes de cada repetición, y ese trabajo NO se cronometra
las dos medidas | la misma escritura, con la única diferencia de si hay un índice que mantener
times_slower | solo devuelve un factor si los rangos no se pisan
```

```salida
  lo que cuesta mantenerlo, escribiendo:
    sin índice  0.494 s
    con índice  1.208 s
    2.45 veces más lento
```

## El resultado, medido

{{FIG:fig_m21_indice_antes_despues}}

**Qué esperábamos.** Un factor limpio para publicar, del estilo «el índice hace la consulta N veces
más rápida».

**Qué salió.** Que ese factor **no existe**. La pareja de medidas se repitió cuatro veces en la
misma corrida y dio **107,5**, **114,3**, **58,1** y **82,9** veces. El índice gana siempre y con
muchísima diferencia, pero el número concreto es medio ruido.

El motivo ya lo dejó escrito el módulo 7: **cuanto más rápida es una medida, menos fiable es su
factor**. Con la lectura por índice en cuatro milésimas de segundo, cualquier cosa que haga la
máquina se lleva la mitad del resultado.

Se publica entonces la horquilla, **entre 58,1 y 114,3 veces**. Y aparte, lo firme:

| Qué | Sin índice | Con índice |
|---|---|---|
| El plan | `Parallel Seq Scan` | `Index Scan` |
| Leer un día | 0,2925 s | 0,0027 s |
| Escribir 200.000 filas | 0,494 s | 1,208 s |
| En disco | nada | **12,3 MB** |

**El plan es la prueba de verdad.** No se mueve entre corridas, no depende de si el antivirus está
mirando, y dice explícitamente que la base ha dejado de barrer la tabla. Cuando alguien pregunte si
un índice se está usando, la respuesta es `EXPLAIN`, no un cronómetro.

**Y la factura.** La escritura se pone al doble, **2,45 veces** en esta corrida, y el índice ocupa
12,3 MB, que es la mitad de lo que ocupa la plata entera en Parquet. Para una tabla que se lee
mucho y se escribe una vez al día, el trato es evidente. Para una que recibe escrituras todo el
rato, hay que pensarlo.

## Ojo

- **Un índice que no se usa es todo coste.** Ocupa y frena las escrituras sin dar nada. `EXPLAIN`
  es la única forma de saber si el tuyo se usa.
- **No sirve para todo filtro.** Si la consulta devuelve media tabla, la base ignora el índice a
  propósito, y hace bien: saltar de aquí para allá sale más caro que leer de corrido.
- **El orden importa.** Un índice sobre `(day, tp2)` sirve para filtrar por `day`, y también para
  `day` y `tp2` a la vez. Para filtrar solo por `tp2`, no.
- **Después de una carga grande, `ANALYZE`.** Sin estadísticas frescas el planificador decide a
  ciegas y puede ignorar un índice perfectamente bueno.
- **No midas un índice una sola vez.** Aquí el mismo experimento dio 58,1 y 114,3 en la misma
  corrida. Publicar la primera habría sido inventarse un dato.
- **La clave primaria ya trae índice.** PostgreSQL lo crea solo, así que el módulo 20 dejó uno
  puesto sin decirlo. Contar índices antes de crear otro evita duplicarlo.

## Puente metalúrgico

El almacén de testigos de sondaje es una tabla sin índice. Cajas apiladas por orden de llegada, y
encontrar un tramo concreto obliga a recorrer el pasillo mirando etiquetas.

El libro de registro es el índice: sondaje, profundidad, y el número de estantería. Con él se va
directo, y por eso todos los almacenes serios tienen uno.

Y tiene las mismas tres facturas. Ocupa un armario. **Se actualiza con cada caja que entra**, y si
alguien deja de hacerlo durante un mes, el libro miente y es peor que no tenerlo. Y está ordenado
por sondaje: para la pregunta «qué tramos analizó tal laboratorio» no sirve de nada, y hay que
recorrer el pasillo igual.

## Repaso

### Qué es un índice y por qué acelera una consulta

Una estructura ordenada, aparte de la tabla, que dice dónde vive cada valor de una columna. Sin
ella la base tiene que leer la tabla entera para saber qué filas cumplen un filtro. Con ella salta
directa a las que cumplen, y aquí eso es la diferencia entre mirar 1.841.760 filas y mirar 8.640.

### Cómo se comprueba que un índice se está usando

Con `EXPLAIN`, que enseña el plan sin ejecutar la consulta. Si dice `Seq Scan`, la base sigue
barriendo la tabla. Si dice `Index Scan`, lo está usando. Es mejor prueba que el reloj porque no
depende de lo ocupada que esté la máquina.

### Por qué este módulo no publica un factor de mejora

Porque no es reproducible. La misma pareja de medidas dio 107,5, 114,3, 58,1 y 82,9 veces en
cuatro repeticiones. Con la lectura rápida en milésimas de segundo, el factor es en buena parte
ruido del reloj. Lo honesto es publicar la horquilla y apoyarse en el plan, que no se mueve.

### Qué cobra un índice

Disco y escrituras. Este ocupa 12,3 MB y pone al doble el tiempo de insertar 200.000 filas, porque
cada fila nueva obliga a colocar también su entrada en el índice. En una tabla de mucha lectura y
poca escritura compensa de sobra. En una de escritura continua, hay que medirlo.

### Tienes una consulta lenta. Creas un índice y no mejora nada. Qué pasa

Tres sospechosos, y se descartan con `EXPLAIN`. Que el filtro devuelva demasiada tabla, y entonces
la base prefiere el recorrido completo a propósito. Que las estadísticas estén viejas y haga falta
`ANALYZE`. O que el índice esté sobre otra columna, o en un orden que no sirve para ese filtro.

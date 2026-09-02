---
module: 20
---

## En 30 segundos

- El módulo 16 escribió promesas que un script comprobaba. Aquí las impone el motor.
- La diferencia: un contrato que **avisa** contra uno que **no deja escribir**.
- **12 guardas** puestas, y se prueban igual: intentando **6** escrituras imposibles.
- La base rechaza **6 de 6**, cada una por una guarda distinta y con su error.
- Y antes de poner una restricción hay que contar quién la rompe. Eso es el reto.

## Qué resuelve este módulo

La tabla del módulo 19 aceptaba cualquier cosa. Dos lecturas con la misma marca de tiempo, una
presión de menos novecientos bar, una señal digital valiendo 2. Todo entraba sin una queja,
exactamente igual que entraba en el Parquet.

El contrato del módulo 16 detectaba esas cosas, pero **después**, corriendo un script. Entre que
el dato malo entra y que alguien mira, el panel ya lo enseñó.

Una base de datos puede hacer algo que un fichero no: **negarse**. Este módulo es cómo se le dice
qué es imposible, y sobre todo cómo se comprueba que de verdad se niega.

## Antes de la teoría: un ejemplo de juguete

Una libreta de pesadas con tres columnas:

| lote | toneladas | turno |
|---|---|---|
| L1 | 20 | mañana |
| L2 | 30 | tarde |
| L3 | 25 | mañana |

Cuatro cosas no deberían poder escribirse nunca, y cada una necesita una guarda distinta:

| Lo imposible | La guarda |
|---|---|
| dos filas con el lote `L1` | el lote es **único** |
| una fila sin toneladas | las toneladas **no pueden faltar** |
| `-5` toneladas | las toneladas están **entre 0 y 500** |
| el turno `madrugada`, que no existe | el turno **sale de la lista de turnos** |

Fíjate en que ninguna de las cuatro se puede deducir de los datos. Que las toneladas no puedan ser
negativas **no está en la libreta**: está en tu cabeza, o en la de quien montó la báscula. Escribir
el esquema es sacarlo de ahí y ponerlo donde la máquina lo pueda aplicar.

Y hay un orden que importa. **Antes de exigir que las toneladas estén entre 0 y 500, hay que mirar
si alguna fila ya se sale.** Si hay una de 600, la base se negará a poner la regla y hará bien: el
problema no es la regla, son los datos que ya están dentro.

## Glosario

- **Restricción.** Una condición que la tabla obliga a cumplir. Si una escritura la incumple, no
  entra.
- **Clave primaria.** La columna que identifica una fila. Única y nunca vacía.
- **Clave foránea.** Una columna que solo admite valores que existen en otra tabla.
- **`NOT NULL`.** Esta casilla no puede quedarse vacía.
- **`CHECK`.** Una condición cualquiera sobre los valores de la fila.
- **Catálogo.** Las tablas internas donde la base guarda lo que sabe de sí misma. `pg_constraint`
  e `information_schema` son parte de él.
- **Integridad referencial.** El nombre formal de lo que hace una clave foránea: que no queden
  referencias a algo que no está.

## Paso a paso

### Paso 1. Decidir qué es imposible

No qué es raro: qué es **imposible**. Una presión de 14 bar es rara y puede pasar; una de menos
novecientos no es una medida, es un fallo. La línea se traza mirando los datos, como los cortes
del módulo 9 y los rangos del contrato del módulo 16.

### Paso 2. Escribirlo en la tabla, con nombre

Cada guarda lleva su nombre puesto a mano. No es cosmética: **el nombre de la guarda es lo único
que verá quien esté mirando el error a las tres de la mañana.** `tp2_en_rango` explica qué pasó y
`lecturas_tp2_check1` no explica nada.

### Paso 3. Añadir la tabla que falta

Una clave foránea necesita algo a lo que apuntar. Aparece `dias`, con un día por fila, y las
lecturas apuntan a ella: **una lectura de un día que no existe deja de ser escribible**.

### Paso 4. Intentar seis disparates

Y aquí está la única parte que convierte esto en algo comprobado. Se intentan seis escrituras
imposibles, una por cada tipo de guarda, y se cuenta cuántas rechaza.

Sin esto, doce restricciones en el catálogo son doce buenas intenciones. Es la misma regla del
módulo 16, y del 17, y de los propios verificadores de este curso.

## El código, por partes

### Paso 5. Las guardas, contadas por la propia base

```postgres
SELECT conname AS guarda, pg_get_constraintdef(oid) AS dice
FROM pg_constraint
WHERE conrelid = 'lecturas'::regclass AND contype IN ('p', 'f')
ORDER BY conname;
```

```anota
pg_constraint | una de las tablas del catálogo: lo que la base sabe de sus propias reglas
conrelid = 'lecturas'::regclass | quédate con las de esta tabla
contype IN ('p', 'f') | p de primary key, f de foreign key. Hay más letras: c para CHECK
```

```salida
            guarda            |                  dice
------------------------------+------------------------------------------
 el_dia_esta_en_el_calendario | FOREIGN KEY (day) REFERENCES dias(dia)
 lecturas_pk                  | PRIMARY KEY ("timestamp")
(2 rows)
```

No se lo he contado yo: **se lo he preguntado a ella**. Es lo mismo que hace el módulo 17 con el
mapa de dbt, y por el mismo motivo: si la herramienta sabe describirse, se la deja hablar.

### Paso 6. El esquema, en el sitio donde manda

```postgres
SELECT count(*) AS guardas
FROM pg_constraint
WHERE conrelid IN ('lecturas'::regclass, 'dias'::regclass);
```

```anota
count(*) | cuántas guardas hay puestas entre las dos tablas
```

```salida
 guardas
---------
      12
(1 row)
```

Doce, repartidas en **13** columnas, y **8** de esas columnas además no admiten vacío.

Ninguna es nueva. El rango de TP2 es el del contrato del módulo 16, y que las digitales solo
valgan cero o uno lo dijo el módulo 2.

### Paso 7. Las seis imposibles

```python
for que, sql in IMPOSIBLES.items():
    try:
        pg.execute(sql)
        pg.commit()
    except psycopg.errors.Error as e:
        pg.rollback()
        resultados.append({"que": que, "guarda": e.diag.constraint_name})
```

```anota
try / except | se intenta la escritura esperando que falle. Si no falla, la guarda no sirve
pg.rollback() | imprescindible: en PostgreSQL un error aborta la transacción entera, y sin deshacerla la siguiente escritura fallaría por culpa de la anterior
e.diag.constraint_name | el nombre de la guarda que ha saltado, que la base devuelve dentro del error
```

```salida
  y ahora, seis escrituras imposibles:
    la rechaza     la misma marca de tiempo dos veces
                   duplicate key value violates unique constraint "lecturas_pk"
    la rechaza     una presion de -900 bar
                   new row for relation "lecturas" violates check constraint "tp2_en_rango"
    la rechaza     una casilla sin decir si se midio
                   null value in column "medido" of relation "lecturas" violates not-null constraint
    la rechaza     una digital que vale 2
                   new row for relation "lecturas" violates check constraint "comp_es_binaria"
    la rechaza     una lectura de un dia que no existe
                   insert or update on table "lecturas" violates foreign key constraint "el_dia_esta_en_el_calendario"
    la rechaza     un dia con 30 horas de carga
                   new row for relation "dias" violates check constraint "horas_de_un_dia"
```

Seis intentos, seis puertas en la cara, **y cada una dice por qué**. Compara eso con el módulo 16,
donde el mismo dato malo entraba y un script lo encontraba más tarde.

### Paso 8. Lo que hay que hacer antes de poner una regla

```sql-vivo
SELECT count(*) AS incumplen,
       round(count(*) * 100.0 / (SELECT count(*) FROM telemetria), 2) AS por_ciento
FROM telemetria
WHERE DV_eletric = COMP;
```

```anota
DV_eletric = COMP | las dos señales son opuestas por diseño, así que aquí valen lo mismo y eso es imposible
la subconsulta | el total de lecturas, para poder dar el porcentaje. Es la del módulo 11
```

```salida
┌───────────┬────────────┐
│ incumplen │ por_ciento │
│   int64   │   double   │
├───────────┼────────────┤
│     16762 │        1.1 │
└───────────┴────────────┘
```

**16.762 lecturas romperían una restricción que dijera que esas dos señales son opuestas.** Así
que esa restricción no se puede poner, y la base tendría razón al negarse. El módulo 14 decidió
marcarlas con la columna `dudoso` en vez de borrarlas, y esta es la consecuencia de aquella
decisión.

## El resultado, medido

{{FIG:fig_m20_esquema}}

**Qué esperábamos.** Que la base rechazara las seis, porque las seis las elegí yo sabiendo qué
guardas había puesto.

**Qué salió.** Rechaza **6 de 6**, y por el camino hubo un tropiezo que enseña más que el
resultado. La quinta escritura era una lectura del **29 de febrero de 2020**, un día que el módulo
13 dio por desaparecido. La rechazó **la clave primaria en vez de la foránea**.

O sea que ese día sí existe en la plata. Y claro que existe: el módulo 14 puso el dato en una
rejilla regular, y **la rejilla creó filas para los huecos**. En bronce el 29 de febrero no estaba;
en plata está, con `medido` en falso y todo lo demás vacío.

Por eso la tabla `dias` tiene **214** días donde el módulo 19 contaba 212: aquel contaba solo los
días con lecturas de verdad. El disparate de la quinta prueba tuvo que mudarse a 2019, que sí está
fuera del registro.

En la figura se ve el reparto, y no está dibujado a mano: sale de `pg_constraint` y de
`information_schema`, o sea de lo que la base cuenta de sí misma.

**Qué significa.** Un esquema no es documentación ni decoración: es la única capa capaz de
decir que no.

El contrato del módulo 16 sigue haciendo falta, porque hay promesas que no caben en una
restricción. Pero lo que sí cabe **debe** vivir aquí, donde no depende de que alguien se acuerde
de correr un script.

## Ojo

- **Una guarda que no se ha visto rechazar nada no protege.** Doce restricciones en el catálogo son
  doce afirmaciones hasta que se intenta escribir algo imposible.
- **Ponle nombre a cada una.** Sin nombre, PostgreSQL se inventa uno y le pega sufijos al recrear
  la tabla. Y en el error, el nombre es lo único que se lee.
- **Antes de añadir una restricción, cuenta quién la rompe.** Si ya hay filas que no la cumplen, la
  base se niega a ponerla. Ese recuento es el reto de abajo.
- **Un `CHECK` no puede mirar otras filas.** Solo ve la fila que se está escribiendo. «El timestamp
  no se repite» necesita una clave, no un `CHECK`.
- **Una clave foránea exige que la tabla apuntada esté antes.** Por eso `dias` se llena primero, y
  por eso borrarla obliga a borrar lo que apunta a ella.
- **Las restricciones cuestan al escribir.** Cada fila se comprueba. Da igual en una carga diaria
  y se nota si se insertan millones de filas una a una.

## Puente metalúrgico

Una balanza de camiones tiene topes. No un cartel que diga cuánto pesa un camión: **topes
físicos**, un rango de la celda de carga fuera del cual no da lectura, un tara mínimo, un máximo
que dispara alarma.

Nadie considera eso desconfianza hacia el operador. Es que un camión de menos cinco toneladas no
es un camión mal pesado: es un sensor roto, y aceptar ese número contamina el balance del mes
entero.

Y hay algo más, que es la parte incómoda. Cuando se instalan esos topes en una planta que lleva
años funcionando, **casi siempre saltan con datos históricos**. Ahí es cuando se descubre que
llevaban un año entrando pesadas imposibles y nadie lo había mirado.

## Hazlo tú

```reto
pregunta: Antes de poner una restricción hay que saber quién la rompería. Devuelve los cinco días con más lecturas donde `DV_eletric` y `COMP` valen lo mismo, con `day` y `lecturas`, de mayor a menor. Cinco filas.
inicio: SELECT day, count(*) AS lecturas
FROM telemetria
GROUP BY day;
esperado: m20_quien_la_rompe
pista: Al punto de partida le falta el filtro y el orden. El filtro es la condición imposible, `DV_eletric = COMP`, y va en un `WHERE` antes de agrupar. Después se ordena por el recuento hacia abajo y se piden cinco.
solucion: SELECT day, count(*) AS lecturas
FROM telemetria
WHERE DV_eletric = COMP
GROUP BY day
ORDER BY lecturas DESC
LIMIT 5;
```

Un día se lleva casi la tercera parte de todos los incumplimientos. Eso no es ruido repartido: es
un episodio concreto, y da una pista mejor que el total. Antes de decidir qué hacer con esas
lecturas, conviene ir a mirar qué pasó ese día.

## Repaso

### En qué se diferencia esto del contrato del módulo 16

En quién lo hace cumplir y cuándo. El contrato es un script que mira los datos después de
escribirlos y avisa. El esquema es el motor negándose a escribirlos. Uno detecta y el otro impide,
y los dos hacen falta: hay promesas que no caben en una restricción.

### Por qué se le pone nombre a cada restricción

Porque el nombre viaja dentro del mensaje de error, y ese mensaje es lo que ve quien esté de
guardia. Sin nombre, PostgreSQL genera uno y además le añade sufijos al recrear la tabla, así que
el que aparezca en un aviso puede no ser el mismo de la semana pasada.

### Qué hay que comprobar antes de añadir una restricción a una tabla con datos

Cuántas filas ya la incumplen. La base recorre la tabla entera antes de aceptar la regla y se
niega si encuentra una sola que no encaje. Aquí, exigir que `DV_eletric` y `COMP` sean opuestas
chocaría con 16.762 lecturas.

### La tabla dias tiene 214 días y el módulo 19 contaba 212. Cuál miente

Ninguna. El módulo 19 contaba días con lecturas de verdad, y `dias` cuenta todos los del
calendario que la plata cubre. La diferencia son los dos días sin registro, que existen como filas
vacías desde que el módulo 14 puso el dato en una rejilla regular.

### Tu clave foránea rechaza una fila que crees correcta. Qué miras primero

La tabla apuntada, no la que estás escribiendo. Una clave foránea solo falla cuando el valor no
existe al otro lado. La pregunta no es si el dato está bien: es si el día, el equipo o el lote al
que apunta llegó a darse de alta. Casi siempre falta la fila de arriba, no sobra la de abajo.

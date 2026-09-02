---
module: 22
---

## En 30 segundos

- Un servidor puede decidir **quién entra y a qué**. Se crea un rol de solo lectura y se le pide borrar.
- No puede: `permission denied for table lecturas`. Un permiso que no se ha visto negar no cuenta.
- La copia de la base pesa **22,2 MB**, menos que el Parquet del que salió.
- Y se restaura de verdad, en otra base, comparando **recuento y huella** tabla por tabla.
- Coinciden las dos, y también las **12** guardas. Eso ya es una copia de seguridad.

## Qué resuelve este módulo

Quedan las dos cosas que un fichero no puede hacer y por las que se monta un servidor.

La primera es **quién**. Un Parquet lo lee cualquiera que llegue a la carpeta, y no hay forma de
dejar que el cliente mire sin poder tocar. La segunda es **volver atrás**: si el disco se rompe, un
lago se rehace corriendo el pipeline, pero una base con seis meses de escrituras no.

Las dos se resuelven con órdenes de una línea. Este módulo enseña otra cosa: **ninguna de las dos
vale hasta comprobarla**, y comprobarlas cuesta más trabajo que darlas.

## Antes de la teoría: un ejemplo de juguete

El laboratorio guarda sus certificados en una carpeta compartida. Dos problemas, uno cada semana.

**El primero es de permisos.** El cliente pide ver sus certificados, así que alguien le da acceso a
la carpeta. Ahora el cliente puede ver los de los demás, y puede borrar. Nadie quería eso: se
quería «leer, y solo lo suyo», y una carpeta no sabe decir eso.

**El segundo es de copias.** Hay una copia automática todas las noches desde hace dos años. El día
que el disco falla se descubre que la copia lleva catorce meses guardando **una carpeta vacía**,
porque alguien cambió el nombre de la carpeta buena y nadie lo notó.

Fíjate en que el segundo problema no se detecta mirando la copia. Se detecta **restaurándola**, y
esa es la única prueba que existe. Una copia que nadie ha restaurado no es una copia: es un fichero
del que se espera mucho.

## Glosario

- **Rol.** Un usuario de la base, o un grupo. En PostgreSQL es la misma cosa.
- **`GRANT`.** Dar un permiso concreto sobre un objeto concreto.
- **Volcado.** El fichero que produce `pg_dump`: las órdenes y los datos necesarios para rehacer la
  base desde cero.
- **`pg_restore`.** Lo que lee ese fichero y reconstruye.
- **Huella.** Aquí, unas cuantas cuentas sobre el contenido de una tabla. Sirven para comparar dos
  copias sin mirarlas fila a fila.
- **Recuperación ante desastre.** El nombre serio de tener una copia que de verdad restaura.

## Paso a paso

### Paso 1. Crear un rol que solo pueda leer

Tres permisos, y ninguno de más: conectarse a la base, ver el esquema y leer las tablas. Nada de
escribir.

### Paso 2. Pedirle que borre

Y aquí está la única parte que convierte el permiso en algo comprobado. Se abre una conexión **con
ese rol** y se intenta un `DELETE`. Si pasa, el rol es decoración.

Es la misma regla del contrato del módulo 16 y de las guardas del 20, aplicada a los permisos.

### Paso 3. Hacer la copia

`pg_dump` en formato propio, que comprime. Sale un solo fichero con todo: tablas, datos,
restricciones e índices.

### Paso 4. Restaurarla en otra base

No encima de la buena. Se crea una base nueva y se restaura ahí, que además de ser lo prudente es
lo que permite comparar las dos.

### Paso 5. Comprobar que dice lo mismo

Recuento y huella, tabla por tabla, más el número de guardas. Una restauración que pierde las
restricciones **no es la misma base**, aunque las filas cuadren.

## El código, por partes

### Paso 6. El rol, y lo que se le da

```postgres
SELECT rolname, rolcanlogin, rolsuper
FROM pg_roles
WHERE rolname IN ('fuelle', 'mirona')
ORDER BY rolname;
```

```anota
pg_roles | otra vista del catálogo. Los usuarios también son datos
rolcanlogin | si puede abrir una conexión
rolsuper | si es superusuario, o sea si se salta todos los permisos
```

```salida
 rolname | rolcanlogin | rolsuper
---------+-------------+----------
 fuelle  | t           | t
 mirona  | t           | f
(2 rows)
```

`fuelle` es superusuario porque lo creó `initdb` en el módulo 19. `mirona` no lo es, y es lo que
hace que sus permisos signifiquen algo: **a un superusuario no se le puede quitar nada.**

### Paso 7. Pedirle que borre

```python
con = psycopg.connect(f"... user={SOLO_LECTURA} dbname={BASE}")
leyo = con.execute("SELECT count(*) FROM lecturas").fetchone()[0]
try:
    con.execute("DELETE FROM lecturas WHERE day = DATE '2020-06-05'")
    escribio = True
except psycopg.errors.Error as e:
    escribio, error = False, str(e).splitlines()[0]
```

```anota
psycopg.connect(user=...) | una conexión NUEVA con el rol limitado. Con la de siempre se probaría al superusuario
primero lee | para confirmar que el rol sirve para algo. Un rol que no puede ni leer no demuestra nada
try / except | se intenta borrar esperando que falle
```

```salida
  un rol de solo lectura, y se le pide que borre:
    lee 1,841,760 filas
    no puede escribir
    permission denied for table lecturas
```

Lee el millón ochocientas mil filas y no puede borrar ni una. **Las dos mitades hacen falta**: sin
la primera, un rol roto que no pudiera ni conectarse pasaría la prueba.

### Paso 8. Copiar y restaurar

```consola
pg_dump    -h localhost -p 5433 -U fuelle -d fuelle -Fc -f fuelle.dump
createdb   -h localhost -p 5433 -U fuelle fuelle_restaurada
pg_restore -h localhost -p 5433 -U fuelle -d fuelle_restaurada fuelle.dump
```

```anota
-Fc | formato propio de PostgreSQL, comprimido. El otro formato es SQL de texto plano, que abulta mucho más
una base nueva | se restaura al lado, nunca encima de la buena. Si la restauración sale mal, no se ha perdido nada
```

### Paso 9. Y la comprobación, que es el módulo

```postgres
SELECT count(*),
       count(*) FILTER (WHERE medido),
       round(sum(oil_temperature)::numeric, 2),
       count(DISTINCT day)
FROM lecturas;
```

```anota
count(*) FILTER (WHERE ...) | cuenta solo las filas que cumplen. Es una forma corta del CASE del módulo 9
sum y count DISTINCT | la huella. Dos tablas con el mismo recuento pueden tener datos distintos; con la misma suma y los mismos días, ya no es casualidad
```

```salida
 count  |  count  |    round    | count
--------+---------+-------------+-------
1841760 | 1504107 | 94224402.00 |   214
(1 row)
```

Esa fila se pide a las dos bases y se comparan. Si no coinciden, la copia no vale.

## El resultado, medido

{{FIG:fig_m22_copia_y_restauracion}}

**Qué esperábamos.** Que la copia pesara algo parecido a la base.

**Qué salió.** Que pesa **22,2 MB** cuando la tabla dentro del servidor ocupa **267,8**. Doce veces
menos, y **menos incluso que los 23,8 MB del Parquet** del que salió todo.

No hay magia: el volcado guarda los datos comprimidos y **no guarda nada de la maquinaria** que el
módulo 19 pagaba. Ni el registro de transacciones, ni el espacio que la tabla reserva para crecer,
ni los índices, que se reconstruyen al restaurar.

Y la comprobación:

| Qué se compara | Original | Restaurada |
|---|---|---|
| filas de `lecturas` | 1.841.760 | 1.841.760 |
| las que tienen medida | 1.504.107 | 1.504.107 |
| suma del aceite | 94.224.402,00 | 94.224.402,00 |
| días distintos | 214 | 214 |
| filas de `dias` | 214 | 214 |
| **guardas** | **12** | **12** |

**Las guardas son la fila que casi nadie mira.** Una restauración puede traer todas las filas y
dejarse las restricciones por el camino, y el resultado se parece muchísimo a la base buena hasta
el día que alguien escribe algo imposible. Por eso se cuentan.

**Qué significa.** Que ahora sí hay una copia de seguridad, y no antes. El fichero existía desde
que corrió `pg_dump`. Lo convierte en copia haberlo restaurado y comprobado.

Restaurar cuesta unos veinticinco segundos aquí, y es la mitad importante: **copiar es lo que hace
todo el mundo y restaurar es lo que casi nadie prueba.**

## Ojo

- **Una copia sin restaurar no es una copia.** Es la frase del módulo y no es retórica: la única
  forma de saber que sirve es usarla.
- **Comprueba también las guardas y los índices.** Contar filas no basta. Una base restaurada sin
  sus restricciones se comporta bien hasta el primer dato imposible.
- **Restaura al lado, nunca encima.** Si la restauración falla a la mitad y era sobre la base
  buena, el desastre lo has provocado tú.
- **A un superusuario no se le puede quitar nada.** Si el rol de solo lectura es superusuario, los
  `GRANT` no hacen nada y la prueba pasa por el motivo equivocado.
- **`-Fc` y no SQL plano.** El formato propio comprime y además permite restaurar solo una tabla.
  El SQL de texto es legible y pesa varias veces más.
- **La copia va a otro sitio.** Aquí vive en `lake/`, que es la misma carpeta que se quiere salvar.
  En producción eso no es una copia de seguridad, es una copia.

## Puente metalúrgico

Toda planta tiene un plan de emergencia y un generador de respaldo. Y en toda planta seria, alguien
tiene la obligación de **arrancar ese generador una vez al mes**, con la planta funcionando y sin
que haga falta.

No se hace por gusto. Se hace porque un generador que lleva tres años sin arrancarse tiene el
gasóleo degradado, la batería muerta, o un fusible que alguien sacó para otra cosa. Sobre el papel
está; el día que baje la red, no arranca.

La prueba mensual es exactamente `pg_restore`. Y la comparación de huellas es el técnico
comprobando algo más: el generador no solo arranca, **da la tensión debida**.

## Repaso

### Qué hace falta para que un rol de solo lectura signifique algo

Que no sea superusuario, y que reciba solo los permisos necesarios: conectar, ver el esquema y
leer las tablas. Y después, intentar escribir con él. Si el `DELETE` pasa, el rol es decoración, y
eso solo se descubre probándolo.

### Por qué la copia pesa menos que el Parquet original

Porque guarda los datos comprimidos y nada de la maquinaria del servidor. Fuera el registro de
transacciones, fuera el espacio reservado para crecer y fuera los índices, que se reconstruyen al
restaurar. Los 267,8 MB de la tabla eran sobre todo eso.

### Qué se compara para dar una restauración por buena

El contenido y la estructura. El recuento de filas, alguna suma y algún recuento de valores
distintos, que juntos hacen de huella, y además el número de restricciones. Una base con las mismas
filas pero sin sus guardas no es la misma base.

### Por qué la restauración va a una base nueva y no encima de la de siempre

Porque una restauración que falla a la mitad deja la base destrozada, y si era la buena el
desastre lo has causado tú probando. Al lado se puede comparar las dos, que es justo lo que hace
falta para saber si la copia sirve.

### Llevas dos años haciendo copias todas las noches. Cuántas sirven

Ninguna que se sepa. Hasta que una se restaura y se compara, lo que hay son ficheros con nombre de
copia. El caso corriente no es un fallo: llevan meses guardando algo que ya no importa, y nadie
mira porque el proceso no da error.

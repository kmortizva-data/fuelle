---
module: 19
---

## En 30 segundos

- Hasta aquí la base de datos era **un fichero**. Ahora es **un servicio** que hay que arrancar.
- Pasarle las **1.841.760** lecturas cuesta **unos 20 s**. Al fichero ya las tenía.
- Y la sorpresa: responder **no va más rápido**. Los rangos se pisan, así que no se distinguen.
- Lo que sí cambia es el disco: **23,8 MB** en Parquet contra **267,8** en el servidor.
- La tabla que acabamos de crear acepta cualquier disparate. Eso es el módulo 20.

## Qué resuelve este módulo

Todo lo que ha hecho este curso cabía en un proceso. DuckDB abre el fichero, contesta y se cierra,
y mientras tanto nadie más puede tocarlo.

Eso se acaba en cuanto hay dos personas. O un panel que consulta mientras la ingesta escribe. O
alguien que necesita permiso de lectura y nada más.

Un servidor de base de datos existe para eso: es un proceso que está siempre levantado, atiende a
varios a la vez y decide quién puede hacer qué. **PostgreSQL** es el que se pide en las ofertas y
el que lleva treinta años de ventaja en esa tarea.

Lo que este módulo mide es qué cuesta ese cambio, porque no es gratis.

## Antes de la teoría: un ejemplo de juguete

Tienes el cuaderno de laboratorio en tu mesa. Apuntas la ley de cada lote y la consultas cuando
quieres. Es rápido, es tuyo, y no hay que pedirle permiso a nadie.

Ahora llegan tres personas más:

| Quién | Qué necesita |
|---|---|
| el jefe de turno | leer la ley del último lote |
| el laboratorio | escribir la del siguiente |
| el cliente | leer, y nada más que leer |

Con el cuaderno en tu mesa hay tres problemas y ninguno es de velocidad. **No pueden mirarlo a la
vez**, porque el cuaderno está donde estás tú. **No hay forma de dejar que el cliente lea sin
poder escribir**, porque un cuaderno no distingue. Y si dos escriben a la vez, **gana el que
cierre el último** y el otro no se entera.

La respuesta no es un cuaderno más rápido. Es poner el cuaderno en un mostrador, con alguien
detrás que atiende por turnos y sabe quién es cada cual.

Eso es un servidor de base de datos. Y fíjate en lo que **no** ha mejorado: buscar una ley sigue
costando lo mismo. Lo que se ha comprado es el mostrador, no la velocidad.

## Glosario

- **Servidor.** Un proceso que está levantado esperando peticiones. Si no está arrancado, no hay
  base de datos que valga.
- **Cliente.** Cualquiera que le pregunta: `psql`, un script de Python, un panel.
- **Puerto.** El número por el que se le habla. El estándar de PostgreSQL es el 5432; este curso
  usa el **5433** para no chocar con ninguno instalado de verdad.
- **Clúster.** La carpeta con todos los ficheros del servidor, que aquí es `lake/pg`. Confuso: no
  tiene nada que ver con varias máquinas.
- **`initdb`.** El programa que crea esa carpeta la primera vez.
- **`COPY`.** La orden de carga masiva de PostgreSQL. Mete millones de filas sin pasar por
  `INSERT` una a una.
- **OLTP y OLAP.** Dos maneras de usar una base: muchas operaciones pequeñas (OLTP) o pocas
  preguntas que barren todo (OLAP). PostgreSQL nació para la primera y DuckDB para la segunda.

## Paso a paso

### Paso 1. Conseguir PostgreSQL sin ser administrador

El instalador oficial pide permisos de administrador y deja un servicio de Windows arrancado. Los
mismos binarios se publican también en un zip, y ese **se descomprime donde quieras y se ejecuta
tal cual**.

Es lo que este proyecto ya hace con Tectonic y con ffmpeg. La parte 5 deja de depender de que
alguien tenga permisos de nada.

### Paso 2. Crear el clúster

`initdb` prepara la carpeta de datos: la base de sistema, la configuración y los ficheros de
registro. Se hace una vez y no se vuelve a tocar.

Va dentro de `lake/`, que este proyecto ya deja fuera de git. La base se reconstruye como el
resto del lago, y no sube ni un byte suyo al repositorio.

### Paso 3. Arrancarlo en un puerto que no sea el de todos

Dos decisiones que se ven en `postgresql.conf` y que conviene explicar:

- **Puerto 5433**, no el 5432, para que un PostgreSQL de verdad instalado mañana en esta máquina
  pueda convivir con este sin que ninguno de los dos se entere.
- **`listen_addresses = 'localhost'`**, para que la instancia no sea alcanzable desde la red. La
  autenticación es `trust`, o sea que no pide contraseña, y **eso solo es defendible por culpa de
  esa línea**: nada de fuera de esta máquina puede abrir una conexión. El módulo 22 lo cambia por
  usuarios que significan algo.

### Paso 4. Pasarle las filas

Aquí está la diferencia que un fichero nunca cobra. El Parquet ya estaba en el disco: DuckDB lo
lee donde está. El servidor **no tiene los datos hasta que se los das**, fila por fila, por una
conexión.

### Paso 5. Hacerle la misma pregunta a los dos

Y compararlos midiendo, no opinando. La pregunta es la del proyecto: cuántas horas al día carga el
compresor.

## El código, por partes

### Paso 6. Las tres órdenes que montan el servidor

```consola
initdb  -D lake/pg -U fuelle --encoding=UTF8 --locale=C --auth=trust
pg_ctl  -D lake/pg -l lake/pg/servidor.log start
psql    -h localhost -p 5433 -U fuelle -d fuelle
```

```anota
initdb | crea la carpeta del clúster. Solo la primera vez
--locale=C | ordenación y mensajes independientes del idioma del sistema, para que el resultado no cambie de una máquina a otra
pg_ctl start | levanta el servidor. Sin esto, todo lo demás da «connection refused»
psql | el cliente de línea de órdenes que trae PostgreSQL
```

Ninguna de las tres pide administrador, y al terminar no queda ningún servicio instalado: se para
con `pg_ctl stop` y desaparece.

### Paso 7. La tabla, deliberadamente ingenua

```postgres
SELECT count(*) AS filas, min(day) AS desde, max(day) AS hasta
FROM lecturas;
```

```anota
FROM lecturas | la tabla que acaba de recibir la plata. Veinte columnas, sin clave y sin restricciones
```

```salida
  filas  |   desde    |   hasta
---------+------------+------------
 1841760 | 2020-02-01 | 2020-09-01
(1 row)
```

Sin clave primaria, sin `NOT NULL`, sin nada. **No es un descuido, es el punto de partida del
módulo 20.** Ahora mismo esta base aceptaría dos lecturas con la misma marca de tiempo, o una
presión de menos mil bar, igual que lo aceptaba el Parquet.

### Paso 8. Darle las filas

```python
with pg.cursor() as cur, cur.copy(
        "COPY lecturas FROM STDIN WITH (FORMAT csv, HEADER)") as copia:
    with io.open(CSV, "rb") as fh:
        while bloque := fh.read(1 << 20):
            copia.write(bloque)
```

```anota
COPY ... FROM STDIN | carga masiva por la conexión. Un INSERT por fila tardaría horas
STDIN y no una ruta | leer un fichero del disco del servidor exige que el fichero esté en su máquina y permiso para leerla. Por la conexión funciona siempre, también con el servidor en otro sitio
fh.read(1 << 20) | se manda de mega en mega, para no cargar 190 MB en memoria
```

```salida
  1,841,760 filas, 190.0 MB de CSV
  1,841,760 filas en el servidor
```

El CSV intermedio pesa **190,0 MB** para unos datos que en Parquet ocupan 23,8. Es el módulo 7
otra vez: el texto no comprime nada y aquí se paga por partida doble, en disco y en lo que hay que
empujar por la conexión.

### Paso 9. La pregunta del proyecto, contra el servidor

```postgres
SELECT day,
       count(*) AS lecturas,
       round((sum(CASE WHEN dv_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0)::numeric, 2) AS horas
FROM lecturas
WHERE medido
GROUP BY day
ORDER BY horas DESC
LIMIT 5;
```

```anota
::numeric | PostgreSQL es más tiquismiquis con los tipos que DuckDB: round con dos decimales quiere numeric, no un número de coma flotante
el resto | idéntico a lo que llevas escribiendo desde el módulo 10
```

```salida
    day     | lecturas | horas
------------+----------+-------
 2020-04-18 |     8588 | 23.60
 2020-06-06 |     7279 | 20.22
 2020-05-20 |     7398 | 20.02
 2020-03-29 |     7136 | 19.82
 2020-06-24 |     7162 | 15.91
(5 rows)
```

Los mismos días y las mismas horas que salían en el módulo 18. **El SQL que aprendiste vale
aquí**, que es medio módulo resuelto: cambiar de motor no cambia el idioma.

## El resultado, medido

{{FIG:fig_m19_fichero_vs_servicio}}

**Qué esperábamos.** Que un motor columnar como DuckDB ganara de calle a uno de filas en una
pregunta analítica. Es lo que dice la teoría del módulo 7 y es lo que yo daba por hecho.

**Qué salió.** Que **no se distinguen**. Sus rangos de siete corridas se pisan, así que por la
regla del módulo 6 no hay diferencia que contar. A 1,8 millones de filas los dos barren la tabla y
ninguno suda.

Las medianas exactas están en la figura y no aquí a propósito: **se mueven de una corrida a otra**,
como todo lo que se mide en décimas de segundo. Lo que no se mueve es que los rangos se pisen.

Lo que sí se separa, y por mucho, es todo lo demás:

| Qué | Un fichero | Un servicio |
|---|---|---|
| Tenerlo listo | ya lo estaba | **unos 20 s** de carga |
| En disco | 23,8 MB | **267,8 MB** |
| Arrancarlo | nada | un proceso levantado |
| Varios a la vez | no | sí |
| Permisos por usuario | no | sí |

**Once veces más disco.** Concretamente **11,2**, para exactamente las mismas lecturas. Y la
carpeta entera del clúster pasa del gigabyte, porque además de la tabla guarda el registro de
transacciones que le permite no perder nada si se va la luz.

**Qué significa.** Que la pregunta «cuál es más rápido» estaba mal planteada. **Con un servidor
no se compra velocidad: se compran concurrencia, permisos y garantías.** Y se pagan en disco, en
carga y en tener un proceso levantado.

Para el trabajo de este curso hasta aquí, un fichero era la elección correcta y sigue siéndolo.
Lo que un fichero no sabe hacer es dejar entrar a tres personas con permisos distintos. Y eso hará
falta cuando el panel del módulo 30 consulte mientras la ingesta escribe.

## Ojo

- **Un servidor parado no es una base de datos.** Es el error número uno con PostgreSQL: todo da
  «connection refused» y no es la red, es que nadie lo arrancó. Por eso en este proyecto lo
  arranca y lo para un solo fichero.
- **`trust` solo vale porque escucha en localhost.** Sin contraseña y abierto a la red sería
  regalar la base. Las dos decisiones van juntas o no van.
- **El puerto 5432 se deja libre a propósito.** Ocupar el estándar con una instancia de juguete es
  la forma más rápida de romperle a alguien la de verdad.
- **La carga por `COPY`, nunca por `INSERT` fila a fila.** La diferencia entre veinte segundos y
  una tarde.
- **El CSV intermedio se borra.** Son 190 MB que no aportan nada una vez cargados, y dejarlos
  ahí es la clase de basura que llena un disco sin que nadie sepa por qué.
- **Esta tabla todavía no promete nada.** Aceptaría un duplicado o una presión imposible sin
  pestañear. Eso se arregla en el módulo 20, y hasta entonces el servidor no es más seguro que el
  fichero.

## Puente metalúrgico

Un laboratorio pequeño lleva sus resultados en una hoja de cálculo. Funciona mientras haya una
persona.

En cuanto la planta crece llega un LIMS, o sea una base de datos con su servidor detrás. Y lo
primero que nota todo el mundo: **no analiza más rápido**. El ensayo tarda lo que tarde.

Lo que cambia es otra cosa. El de turno de noche consulta sin llamar a nadie. El cliente ve sus
certificados y no los de otro. Dos técnicos cargan resultados a la vez sin pisarse. Y cuando
alguien pregunta quién cambió una ley, hay respuesta.

Nadie compra un LIMS por velocidad. Se compra por las mismas razones de un servidor de base de
datos, y cuesta lo mismo: más disco, más mantenimiento, y algo encendido a todas horas.

## Repaso

### Qué gana un servidor de base de datos frente a un fichero

Atender a varios a la vez, distinguir quién es cada cual y qué puede hacer, y garantizar que dos
escrituras simultáneas no se pisen. No gana velocidad: aquí la misma pregunta tarda lo mismo en
los dos, con los rangos solapados.

### Por qué la carga cuesta veinte segundos si los datos ya estaban en el disco

Porque estaban en el disco pero no dentro del servidor. Un fichero se lee donde está. A un
servidor hay que entregarle cada fila por una conexión, y él la vuelve a escribir en su propio
formato y en su registro de transacciones. Esos veinte segundos son el precio de la entrega.

### Qué significa que las dos medidas tengan los rangos solapados

Que la diferencia entre sus medianas no se puede defender. Es la regla del módulo 6: si en siete
corridas el peor caso de uno cae dentro del rango del otro, lo que se está midiendo es el ruido de
la máquina. Publicar un ganador ahí sería inventarse un resultado.

### Por qué la tabla se crea sin clave primaria ni restricciones

Porque el módulo empieza donde estaba el lector: con un Parquet que aceptaba cualquier cosa.
Crear la tabla ya blindada escondería la lección del módulo 20: una base de datos no protege de
nada hasta que le dices qué es imposible. Es el mismo criterio del módulo 4, que particiona por
día a sabiendas de que es la peor opción.

### El servidor ocupa once veces más para los mismos datos. A cambio de qué

De poder recuperarse. Buena parte de ese peso es el registro de transacciones, que apunta cada
cambio antes de aplicarlo para que un corte de luz no deje la tabla a medias. Un Parquet no ofrece
eso: si se corta la escritura, el fichero queda roto y hay que rehacerlo.

---
module: 6
---

## En 30 segundos

- Particionar es repartir una tabla en carpetas para que una pregunta lea solo una.
- El consejo que se repite en todas partes es partir por día. Aquí se mide.
- Leer un día tarda **0,014 s contra 0,171 s** entre no particionar y partir por día.
- Partir por día sale **12,2 veces más lento** y ocupa un **31 %** más. Es la peor de las cuatro.
- Partir por mes y no partir **no se distinguen**: sus rangos se solapan.

## Qué resuelve este módulo

El módulo 4 dejó el lago repartido en 212 carpetas, una por día, porque es lo que hace todo el
mundo. Este módulo comprueba si eso era buena idea.

Resulta que no, y el motivo enseña más sobre cómo funciona un formato columnar que cualquier
explicación.

## Antes de la teoría: un ejemplo de juguete

Tienes 120 partes de turno de un año y te preguntan por los de junio. Tres formas de guardarlos:

| Dónde | Cuántas carpetas | Para junio abres | Papeles que miras |
|---|---|---|---|
| Una caja | 1 | la caja | 120 |
| Doce carpetas, una por mes | 12 | 1 carpeta | 10 |
| Trescientas sesenta y cinco, una por día | 365 | 30 carpetas | 10 |

Las dos últimas te hacen mirar los mismos diez papeles. La diferencia está en **cuántas carpetas
tienes que abrir y cerrar** para llegar a ellos: una contra treinta.

Abrir una carpeta cuesta. Poco, pero cuesta, y ese coste no depende de cuántos papeles tenga
dentro. Si las carpetas son muchas y pequeñas, llega un punto en que se pasa más tiempo abriendo
carpetas que leyendo papeles.

Ese punto es lo que este módulo busca con el cronómetro. La pregunta no es si particionar ayuda,
es **con qué tamaño**.

## Glosario

- **Particionar.** Repartir una tabla en varios ficheros según el valor de una columna,
  normalmente la fecha. Cada valor distinto es una carpeta.
- **Poda de particiones.** Que el motor descarte carpetas enteras sin abrirlas, mirando solo el
  nombre. Es lo que hace útil particionar.
- **Estadísticas del fichero.** Los valores mínimo y máximo que Parquet guarda por cada bloque de
  filas, para poder saltárselo entero sin leerlo.
- **Sobrecarga.** El coste fijo de cada fichero, independiente de lo que contenga: abrirlo, leer
  su cabecera, cerrarlo.
- **Ficheros pequeños.** El problema de tener muchísimos ficheros diminutos. Tiene nombre propio
  porque es un clásico de los lagos de datos.

## Paso a paso

### Paso 1. Escribir lo mismo de cuatro formas

Las mismas 1.516.948 filas y el mismo contenido, repartidos de cuatro maneras. En un solo
fichero, por mes, por semana y por día. Lo único que cambia es el reparto.

### Paso 2. Hacerles a las cuatro la misma pregunta

Cuántas lecturas hay del 5 de junio. Particionar por fecha existe para responder justo a eso,
así que es donde el reparto por día debería lucirse.

### Paso 3. Cronometrar siete veces y quedarse con el rango

Aquí está la corrección más importante de este módulo. La primera versión de este script
cronometraba **una sola vez** cada reparto, y con esos números la conclusión era otra.

Con una sola medida, partir por mes salía más rápido que no partir. Con siete medidas y sus
rangos, los dos se solapan: **no se distinguen**. La primera versión iba a publicar un ganador
que no existe.

### Paso 4. Comprobar que las cuatro contestan lo mismo

Antes de comparar tiempos, las cuatro disposiciones tienen que devolver el mismo número de filas.
Si no, no se está midiendo el reparto: se está midiendo un error de escritura.

## El código, por partes

### Paso 5. Escribir un reparto

```sql
COPY (
    SELECT *, date_trunc('month', timestamp) AS part
    FROM read_parquet('lake/bronze/telemetry/**/*.parquet')
)
TO 'lake/_bench/by_month'
(FORMAT PARQUET, PARTITION_BY (part), OVERWRITE_OR_IGNORE, COMPRESSION ZSTD);
```

```anota
date_trunc('month', timestamp) | recorta la fecha al principio de su mes: el 5 de junio pasa a ser el 1 de junio
AS part | la columna por la que se va a repartir; el nombre da igual, lo que importa es que exista
PARTITION_BY (part) | una carpeta por cada valor distinto de part, o sea una por mes
```

Cambiando `month` por `week` o por el día entero salen los otros repartos. El resto del código es
idéntico, que es lo que hace justa la comparación.

### Paso 6. Medir la lectura de un día, siete veces

```python
read = measure(lambda: con.sql(
    f"SELECT count(*) FROM read_parquet('{glob}') "
    f"WHERE CAST(timestamp AS DATE) = DATE '{ONE_DAY}'"
).fetchone()[0])
```

```anota
measure(...) | la función de src/medir.py: corre lo que se le pase siete veces y devuelve la mediana con su rango
lambda: ... | una función sin nombre, escrita en una línea; sirve para pasar «esto que hay que hacer» como si fuera un dato
DATE '2020-06-05' | una fecha literal en SQL; sin la palabra DATE delante sería texto
```

```salida
Writing single_file, 7 times...
     1 files    16.84 MB  write     0.99 s  read one day 0.014 s (0.012 to 0.017)
Writing by_month, 7 times...
     8 files    17.64 MB  write     0.94 s  read one day 0.019 s (0.016 to 0.085)
Writing by_week, 7 times...
    32 files    17.79 MB  write     2.51 s  read one day 0.039 s (0.026 to 0.053)
Writing by_day, 7 times...
   212 files    22.09 MB  write     3.18 s  read one day 0.171 s (0.154 to 0.201)
```

### Paso 7. Decidir con los rangos, no con las medianas

```python
row["read_distinguishable_from_fastest"] = (
    False if row["layout"] == fastest_name
    else distinguishable(reads[fastest_name], other))
```

```anota
distinguishable(a, b) | de src/medir.py: devuelve falso si los dos rangos se pisan
False if ... else ... | una condición escrita en una línea: si es la más rápida, no se compara consigo misma
```

```salida
  All layouts return the same 8,716 rows for 2020-06-05: True
  fastest read: single_file
  by_month reads the same as single_file: the ranges overlap, so there is no difference to report
```

Esa última línea no la escribió nadie: la decidió el script comparando los rangos.

## El resultado, medido

{{FIG:fig_m06_curva_de_particion}}

**Qué esperábamos.** Que particionar por día ganara. Es el consejo estándar y la pregunta es
justo por un día. La lógica parece sólida: con los datos del día en su propia carpeta, no hay que
mirar las otras doscientas once.

**Qué salió.** Lo contrario, y con margen. Leer un día tarda **0,014 s contra 0,171 s** entre no
particionar y partir por día. Partir por día es **12,2 veces más lento** justo en el caso para el
que se supone que sirve, y además ocupa un **31 %** más, 212 ficheros frente a uno.

En el panel de la izquierda de la figura se ve la curva subiendo con el número de ficheros, y en
el de la derecha el tamaño haciendo lo mismo.

**Qué significa.** Parquet ya sabe saltarse lo que no necesita. Cada fichero guarda, por cada
bloque de filas, cuál es el valor mínimo y el máximo de cada columna. Preguntando por un día, el
motor lee esas estadísticas y descarta los bloques que no pueden contenerlo, sin leerlos.

O sea que la poda ya estaba hecha **dentro** del fichero. Repartir en 212 carpetas no añade una
capacidad nueva: añade 212 cabeceras que abrir, leer y cerrar. La sobrecarga se paga entera y el
beneficio ya estaba cobrado.

Y el segundo resultado, que es el que solo aparece midiendo bien. **Partir por mes y no partir no
se distinguen**: el rango de uno se solapa con el del otro, así que no hay diferencia que contar.
La primera versión de este script, con una sola medida, daba a partir por mes como ganador.

## Ojo

- **Esto vale a esta escala y en esta máquina.** Con mil millones de filas y varios discos en
  paralelo, la respuesta cambia, porque entonces las carpetas se leen a la vez. La conclusión que
  viaja no es «no particiones», es **mide antes de partir**.
- **El número de ficheros es la perilla, no la fecha.** Partir por día es una forma de decir «212
  ficheros». Lo que decide es cuántos salen y cuánto pesa cada uno, no si la columna es una fecha.
- **Escribir por día también sale más caro**, y eso se paga cada noche. Un reparto malo no solo
  ralentiza las lecturas.
- **Las medianas no bastan para ordenar.** Dos repartos con rangos solapados son el mismo reparto
  a efectos de esta máquina. Ordenar por mediana habría inventado un ganador.
- **`bronze.py` sigue particionando por día.** Se deja a propósito: el módulo 4 comete el error
  corriente y este lo mide. Cambiarlo antes de tiempo habría borrado la lección.

## Puente metalúrgico

Un molino de bolas tiene un tamaño de bola óptimo, y no es el más grande ni el más pequeño. Bolas
grandes rompen bien lo grueso y desperdician energía en lo fino. Bolas pequeñas hacen lo
contrario.

Nadie elige la carga de bolas copiando la de otra planta. Se elige mirando la distribución
granulométrica de la alimentación y el producto que se busca, porque con otro mineral la
respuesta es otra.

El tamaño de partición es exactamente eso. Particionar por día es una carga de bolas por defecto,
y aquí la alimentación pedía otra.

## Repaso

### Qué es particionar y para qué se supone que sirve

Repartir una tabla en carpetas según el valor de una columna, casi siempre una fecha. Sirve para
que una pregunta acotada abra solo las carpetas que le tocan y se ahorre el resto. Es cierto
cuando cada carpeta es grande, y deja de serlo cuando son muchas y pequeñas.

### Por qué particionar por día salió peor que no particionar

Porque Parquet ya se saltaba lo que no necesitaba. Guarda el mínimo y el máximo por bloque de
filas, así que descarta lo que no puede contener el día pedido sin abrirlo. Repartir en 212
ficheros no añadió poda, añadió 212 cabeceras que abrir.

### Cómo se elige entonces el tamaño de partición

Midiendo, con la pregunta real y en la máquina real. Se escriben varios repartos, se cronometra
la misma consulta en todos, y se mira dónde la curva empieza a subir. Copiar el valor de un blog
es elegir sin datos.

### Dos repartos dan medianas distintas. Ya se puede decir cuál es mejor

No, si sus rangos se solapan. Aquí pasó con no particionar y particionar por mes, y por eso el
script lo dice en vez de ordenarlos. Una diferencia que no sobrevive a repetir la medición no es
una diferencia.

### Si mañana el lago tuviera mil millones de filas, valdría esta conclusión

No necesariamente, y esa es la parte importante. A esa escala un fichero único deja de caber
cómodo y las carpetas se pueden leer en paralelo, así que la sobrecarga se reparte. Lo que sí
viaja es el método: escribir varios repartos, cronometrarlos con la pregunta real, y mirar los
rangos antes de declarar un ganador.

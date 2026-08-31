---
module: 5
---

## En 30 segundos

- Correr la misma ingesta tres veces dejó **4.550.844 filas** donde solo había 1.516.948.
- Nadie avisó. No hubo error, ni aviso, ni nada raro en los datos.
- La cura es una **huella** del origen guardada al lado de los datos.
- Con ella, de tres corridas solo trabajó **una**, y el recuento no se movió.
- Se cambió **un byte** del origen y la huella cambió en **126 de sus 256 bits**.

## Qué resuelve este módulo

Una ingesta se va a correr dos veces. Por un reintento, por un cron mal puesto, porque alguien la
lanzó a mano sin saber que ya estaba lanzada. Es cuestión de tiempo.

Este módulo mide qué pasa entonces, y construye la pieza que lo impide.

## Antes de la teoría: un ejemplo de juguete

El turno de mañana deja tres muestras con su ley de hierro:

| Muestra | Ley |
|---|---|
| M1 | 10 |
| M2 | 20 |
| M3 | 30 |

Las cargas en el registro. No estás seguro de si se guardó, así que las cargas otra vez. Ahora el
registro tiene seis filas, las tres de antes y las tres repetidas.

Mira lo que le pasa a cada número:

| Qué preguntas | Antes | Después | ¿Se nota? |
|---|---|---|---|
| Cuántas muestras | 3 | 6 | Sí |
| Suma de las leyes | 60 | 120 | Sí |
| **Ley media** | **20** | **20** | **No** |

La media no se mueve. Sumas las seis, ciento veinte, divides entre seis, y sale veinte otra vez.

Esa fila de la tabla es el módulo entero. **El número que más se mira es justo el que no delata
la duplicación.** Puedes tener el doble de datos de los que hay, mirar la ley media todos los
días, y no enterarte nunca.

Lo que sí revienta es todo lo que se suma. Si esas tres muestras representaran tres toneladas
procesadas, el informe diría seis. Se habría duplicado la producción del turno sin que nadie
tocara una tecla dos veces a propósito.

## Glosario

- **Idempotente.** Que se puede repetir sin cambiar el resultado. Pulsar el botón de un ascensor
  es idempotente: la segunda vez no lo llama dos veces.
- **Huella.** Un número corto que se calcula a partir de un fichero entero. Si el fichero cambia,
  la huella cambia. También se le llama hash o resumen.
- **SHA-256.** La forma concreta de calcular esa huella que se usa aquí. Devuelve siempre 256
  bits, o sea 64 caracteres, mida el fichero lo que mida.
- **Bit.** La unidad más pequeña de información: vale cero o uno. Un byte son ocho bits.
- **Byte.** Lo que ocupa aproximadamente un carácter de texto. El fichero de este curso tiene
  218.300.507.
- **Manifiesto.** El fichero pequeño donde se guarda la huella junto a los datos, para poder
  compararla en la siguiente corrida.
- **Ingesta incremental.** La que solo trae lo que falta, en vez de traerlo todo cada vez.

## Paso a paso

### Paso 1. Escribir la versión ingenua a propósito

La primera versión de cualquier ingesta escribe lo que lee y no pregunta nada. No está mal
escrita: está incompleta, y la diferencia solo aparece la segunda vez que corre.

Aquí se escribe así a propósito, se corre tres veces y se cuenta. Sin ver el fallo ocurrir, la
regla del módulo sería una advertencia más de las que se leen y se olvidan.

### Paso 2. Contar después de cada corrida

Tres corridas de la misma ingesta sobre el mismo origen, contando después de cada una. Si la
ingesta fuera idempotente, los tres recuentos serían iguales.

### Paso 3. Guardar la huella del origen y preguntar antes de trabajar

La versión con guarda hace una pregunta antes de mover un solo dato: **¿el origen es el mismo que
la última vez?** Calcula la huella del fichero, la compara con la que dejó guardada, y si
coinciden no hace nada.

Esa huella vive en un fichero al lado de los datos, no en memoria. Así la respuesta sobrevive al
final del proceso, al reinicio de la máquina y al cambio de ordenador.

### Paso 4. Comprobar que la huella puede cambiar

Y aquí está el paso que casi nadie da. Una huella que nunca se ha visto cambiar no demuestra
nada: podría estar devolviendo siempre el mismo valor y el resultado sería idéntico.

Así que se copia el fichero de origen, se le cambia **un solo byte** por otro, y se vuelve a
calcular. Es la misma idea que hay detrás de los verificadores de este curso: **una guarda que no
se ha visto fallar no cuenta**.

## El código, por partes

### Paso 5. La ingesta ingenua, corrida tres veces

```python
for run in range(1, 4):
    naive_ingest(con, naive_dir, run)
    print(count(con, naive_dir))
```

```anota
range(1, 4) | los números 1, 2 y 3; el último no entra
naive_ingest(...) | escribe los datos leídos en un fichero nuevo, sin mirar si ya había algo
count(...) | cuenta las filas que hay en la carpeta de destino
```

```salida
  naive    run 1:  1,516,948 rows
  naive    run 2:  3,033,896 rows
  naive    run 3:  4,550,844 rows
```

Tres corridas, tres veces los datos. Y ni un error por ninguna parte.

### Paso 6. La misma ingesta, preguntando primero

```python
def guarded_ingest(con, target, part, source, manifest):
    current = sha256_of(source)
    if manifest.exists():
        seen = json.loads(io.open(manifest, encoding="utf-8").read())
        if seen.get("source_sha256") == current:
            return False
    naive_ingest(con, target, part)
    ...
    return True
```

```anota
sha256_of(source) | calcula la huella del fichero de origen, leyéndolo entero
if manifest.exists() | solo hay algo con lo que comparar si ya hubo una corrida anterior
seen.get("source_sha256") | la huella que dejó guardada la corrida anterior
== current | si son iguales, el origen no ha cambiado
return False | se sale sin ingerir nada, y avisa de que no hizo trabajo
```

```salida
  guarded  run 1:  1,516,948 rows   ingested
  guarded  run 2:  1,516,948 rows   skipped, source unchanged
  guarded  run 3:  1,516,948 rows   skipped, source unchanged
```

Las tres corridas dejan el mismo recuento, y las dos últimas ni siquiera abrieron los datos.

### Paso 7. Un byte, y la huella tiene que enterarse

```python
with io.open(copy, "r+b") as fh:
    fh.seek(position)
    original_byte = fh.read(1)
    new_byte = b"7" if original_byte != b"7" else b"3"
    fh.seek(position)
    fh.write(new_byte)
```

```anota
"r+b" | abre el fichero para leer y escribir, en modo binario: bytes crudos, no texto
fh.seek(position) | coloca el cursor en esa posición exacta del fichero
fh.read(1) | lee un solo byte, el que hay bajo el cursor
b"7" | un byte con el carácter 7 dentro; la b delante significa que es binario y no texto
fh.write(new_byte) | escribe encima, sin mover nada de alrededor
```

Se cambia un dígito por otro para que el fichero siga siendo un CSV válido. Ese es el caso
difícil: un cambio que ningún programa que lea el fichero notaría.

```salida
  byte 109,150,253 of 218,300,507: '6' -> '7'
  before  db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24
  after   2dd4fd02dd3ae1bcd82933a9ed224952493821edfd368076c0c90466f1681be6
  126 of 256 bits in the hash changed
  the guarded pipeline ingests again: True
```

Las dos huellas no se parecen en nada, y eso es exactamente lo que se le pide a una.

## El resultado, medido

{{FIG:fig_m5_idempotencia}}

**Qué esperábamos.** Que la ingesta ingenua duplicara y que la huella lo impidiera. Las dos cosas
eran predecibles, y por eso el experimento vale: si alguna hubiera salido de otra forma, habría
un fallo que encontrar.

**Qué salió.** La cifra del módulo es **4.550.844 contra 1.516.948**. Tres corridas de la ingesta
sin guarda dejan el primer número donde el origen tiene el segundo, o sea **3,0 veces** los
datos. Con la huella delante, las mismas tres corridas dejan **1.516.948 filas**, y solo **1 de
las 3** hizo algún trabajo.

Y la parte que hace que lo anterior signifique algo. Cambiando **un byte** de los **218.300.507**
del fichero, la huella cambió en **126 de sus 256 bits**, el **49,2 %**. Después de ese cambio la
ingesta con guarda volvió a trabajar, y era lo que tenía que hacer.

**Qué significa.** Cerca de la mitad de los bits es justo lo que se espera de una huella sana. Si
un cambio pequeño moviera poco la huella, dos ficheros parecidos tendrían huellas parecidas, y
comparar huellas dejaría de servir para decidir. Que un dígito cambiado a mitad de fichero
reescriba la mitad del resultado es la propiedad que hace útil todo esto.

Sobre el coste, que es la objeción razonable: leer 208 MB para calcular una huella parece caro
frente a no hacerlo.

```salida
Fingerprinting the source, 7 times...
  sha256 db30ccb4ea402e3c...  0.422 s (from 0.376 to 0.447)  (494 MB/s)
```

Comparado con lo que cuesta la ingesta entera, la guarda no se nota. Y evita reprocesar todo
cuando no hace falta, así que la mayoría de las veces sale ganando.

## Ojo

- **Duplicar no salta a la vista.** La media aguanta, como en el ejemplo de las tres muestras. Lo
  que se rompe es todo lo que se suma o se cuenta, y eso suele ser el informe, no el panel.
- **La huella dice si el fichero cambió, no qué cambió.** Para saber qué, hace falta comparar los
  datos. El módulo 18 vuelve sobre esto con el viaje en el tiempo.
- **Borrar y volver a escribir también es idempotente**, y es lo que hace `bronze.py`. Es la
  opción más simple y aquí es la correcta. Deja de serlo cuando los datos ya no caben en una
  reescritura completa, y entonces hace falta esta guarda.
- **Una huella que nunca se ha visto cambiar no prueba nada.** Es la mitad del experimento que
  casi siempre falta, y es la que convierte una afirmación en una comprobación.
- **La huella se guarda al lado de los datos, no en el código.** Un dato sobre los datos que viva
  en el código desaparece en cuanto alguien copia la carpeta.

## Puente metalúrgico

En un circuito de flotación, el balance metalúrgico se cierra comparando lo que entra con lo que
sale. Si un turno registra dos veces la misma carga de alimentación, el balance no da error:
sencillamente da una recuperación imposible, o da una perfectamente creíble y equivocada.

Por eso las cargas se identifican con un número de lote y no por su contenido. Dos camiones con
la misma ley no son el mismo camión, y el mismo camión pesado dos veces no son dos camiones. El
lote es lo que distingue una cosa de la otra.

La huella del fichero es ese número de lote. Sin él, el sistema no tiene forma de saber si lo que
está entrando ya entró.

## Repaso

### Qué significa que un proceso sea idempotente

Que correrlo varias veces deje el mismo resultado que correrlo una. No significa quedarse quieto
la segunda vez: significa dejar detrás lo mismo. Borrar y reescribir cumple la definición, y
saltarse el trabajo cuando el origen no cambió también.

### Cómo se detecta que una tabla tiene datos duplicados

Contando, no promediando. La media es lo primero que se mira y lo último que se entera, porque
duplicar cada fila deja la media exactamente igual. Lo que delata son los recuentos, las sumas y
las filas repetidas con la misma clave.

### Por qué no basta con calcular la huella y compararla en memoria

Porque el proceso termina. La siguiente corrida es un proceso nuevo, muchas veces en otra máquina
y días después, y no recuerda nada de la anterior. Guardar la huella en un fichero al lado de los
datos es lo que hace que la comparación siga siendo posible mañana.

### Se cambió un byte y la huella cambió en 126 de 256 bits. Por qué es eso lo deseable

Porque significa que la huella no conserva parecidos. Si un cambio pequeño produjera una huella
parecida, dos ficheros distintos podrían dar huellas casi iguales y la comparación dejaría de ser
fiable. Cerca de la mitad de los bits cambiados es lo que se espera de una huella sana.

### Tu ingesta corre cada noche sobre un fichero que casi nunca cambia. Qué haces

Guardar la huella y comparar antes de trabajar. La ingesta pasa a hacer nada la mayoría de las
noches, que es lo correcto cuando no hay nada nuevo, y sigue reaccionando el día que el fichero
cambie de verdad. La comprobación cuesta leer el fichero, y eso es una fracción de lo que cuesta
procesarlo.

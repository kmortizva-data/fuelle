---
module: 1
---

## En 30 segundos

- Un compresor de un tren del Metro de Oporto, registrado durante siete meses.
- La ficha oficial promete **15.169.480 mediciones**. El fichero trae **1.516.948**.
- Cuatro averías reales, con fecha y parte de mantenimiento, y las cuatro son fugas de aire.
- Los partes vienen con erratas de fábrica y **no se corrigen**.
- La pregunta del curso entero: qué señal delata una fuga, si la presión no baja.

## Qué resuelve este módulo

Antes de tocar una sola herramienta hay que saber qué se tiene delante. Este módulo abre el
archivo, cuenta lo que hay dentro y lo compara con lo que su documentación dice que hay.

No coinciden. Esa es la primera lección del curso, y no es sobre datos: es sobre confianza.

Un fichero de datos viene siempre con una historia contada por alguien. La historia ayuda, pero
**manda el fichero**.

## Antes de la teoría: un ejemplo de juguete

Imagina que recibes el registro de una balanza de cinta. La ficha que lo acompaña dice:

> Registro continuo, una pesada por segundo, 3.600 pesadas en la hora de ensayo.

Abres el fichero y cuentas las filas. Hay **360**.

**Divide.** 3.600 entre 360 son 10. Por cada diez pesadas que la ficha promete, el fichero trae
una.

**Mira la primera columna.** Los números de fila van 0, 10, 20, 30. No van 0, 1, 2, 3.

Ahí está la explicación, y no es que falten datos. La balanza sí pesó 3.600 veces. Lo que te
entregaron es **una de cada diez**, conservando la numeración original. La ficha describe la
captura; el fichero es lo que publicaron.

Esa división de una línea es todo el método de este módulo. Lo que cambia con el compresor es la
escala: en vez de 3.600 y 360, son 15.169.480 y 1.516.948.

## Glosario

- **Telemetría.** El registro que una máquina va dejando de sí misma mientras funciona. Aquí,
  quince señales anotadas cada diez segundos durante siete meses.
- **Señal analógica.** La que mide una magnitud con todos sus decimales: una presión, una
  temperatura, una corriente.
- **Señal digital.** La que solo dice sí o no. Que una válvula está abierta, que una alarma está
  activa.
- **Muestreo.** Cada cuánto se anota una lectura. Aquí cada diez segundos, aunque no siempre.
- **Submuestrear.** Quedarse con una lectura de cada N y tirar el resto. Reduce el tamaño y
  pierde detalle, y es lo que le hicieron a este fichero antes de publicarlo.
- **Parte de avería.** El informe que la empresa escribe cuando algo falla. Aquí son cuatro, y
  son la única verdad terreno que tiene el proyecto.

## Paso a paso

### Paso 1. La máquina

Un compresor de aire alimenta los frenos, las puertas y la suspensión de un tren. Si se para, el
tren se para. Por eso lleva sensores.

Su trabajo es sencillo de describir: mantener un depósito lleno de aire. Cuando la presión baja
de un umbral, arranca y comprime. Cuando llega arriba, para. Y vuelta a empezar.

{{FIG:fig_m1_anatomia_del_compresor}}

Ahí está la máquina entera en dos horas de un martes cualquiera. La presión baja despacio,
porque el tren va consumiendo aire. Toca el umbral, el compresor arranca, y la presión sube casi
en vertical. Después el motor sigue girando un rato sin comprimir nada, que es lo que la ficha
llama funcionar en vacío, y por eso la corriente se queda en unos 4 A en vez de caer a cero.

Tres ciclos en dos horas. Ese ritmo es el que hay que vigilar todo el curso.

### Paso 2. Lo que la ficha promete

El zip de la Universidad de California trae, además del fichero, un PDF de descripción. Dice
dos cosas que conviene retener:

> Number of Instances: 15169480

> The data were logged at 1Hz by an onboard embedded device.

Quince millones de mediciones, una por segundo. Y describe las quince señales una a una, con
detalles que valen oro para más adelante: que el compresor arranca cuando la presión baja de
**8,2 bar**, que hay una alarma que salta por debajo de **7 bar**, y que el motor consume unos
7 A en carga y unos 4 A en vacío.

### Paso 3. Lo que el fichero trae

Se cuentan las filas y se miran las fechas. Es lo primero que se hace con cualquier archivo, y
casi nadie lo hace.

## El código, por partes

### Paso 4. Contar lo que hay

```python
import duckdb

con = duckdb.connect()
src = "read_csv_auto('data/MetroPT3(AirCompressor).csv')"
print(con.sql(f"SELECT count(*), min(timestamp), max(timestamp) FROM {src}").fetchone())
```

```anota
import duckdb | trae la herramienta que sabe leer y consultar ficheros de datos
con = duckdb.connect() | abre una base de datos en memoria; no crea ningún fichero
read_csv_auto(...) | lee el CSV averiguando solo los tipos de cada columna
f"..." | una cadena con huecos: lo que va entre llaves se sustituye por su valor
count(*) | cuenta las filas
min / max | el valor más pequeño y el más grande de una columna
.fetchone() | trae la primera fila del resultado a Python
```

```salida
(1516948, datetime.datetime(2020, 2, 1, 0, 0), datetime.datetime(2020, 9, 1, 3, 59, 50))
```

Un millón y medio de filas, del 1 de febrero al 1 de septiembre de 2020.

Primer desajuste, y menor: la ficha del repositorio dice que los datos van «de febrero a agosto».
Llegan al 1 de septiembre.

### Paso 5. Medir el muestreo en vez de suponerlo

La ficha dice 1 Hz. En lugar de creerlo, se mide la distancia entre lecturas consecutivas.

```python
con.sql(f"""
    SELECT gap, count(*) AS veces
    FROM (SELECT date_diff('second', lag(timestamp) OVER (ORDER BY timestamp),
                           timestamp) AS gap
          FROM {src})
    WHERE gap IS NOT NULL
    GROUP BY gap ORDER BY veces DESC LIMIT 3
""").show()
```

```anota
lag(timestamp) OVER (ORDER BY timestamp) | mira el valor de la fila anterior, ordenando por fecha
date_diff('second', a, b) | cuántos segundos hay entre dos marcas de tiempo
IS NOT NULL | descarta la primera fila, que no tiene anterior
```

```salida
┌───────┬──────────┐
│  gap  │  veces   │
├───────┼──────────┤
│    10 │  1337521 │
│     9 │   128277 │
│    12 │    38321 │
└───────┴──────────┘
```

**Cada diez segundos, no cada segundo.** Y no siempre: 179.426 lecturas llegan con otro
intervalo. La más común es de nueve segundos, 128.277 veces, y la siguiente de doce, 38.321.

### Paso 6. La división que lo explica

```python
print(15_169_480 / 1_516_948)
```

```salida
10.0
```

Exactamente diez. No 9,97 ni 10,3.

Y la primera columna del CSV, esa que no tiene nombre, va 0, 10, 20, 30. Conserva la numeración
del registro original.

## El resultado, medido

**Qué esperábamos.** Que el fichero trajera lo que su ficha declara, o algo parecido.

**Qué salió.** La ficha declara **15.169.480** mediciones a 1 Hz. El fichero trae **1.516.948**
lecturas cada 10 s. El cociente es **10,0000**, y la columna índice conserva la numeración
original.

**Qué significa.** El registro original sí fue a un dato por segundo. Lo que se publicó es **una
lectura de cada diez**. La ficha no miente: describe la captura, no el fichero. Pero si alguien
programa suponiendo 1 Hz, todos sus cálculos de tiempo saldrán diez veces mal.

Y las cuatro averías, que son la verdad terreno del proyecto:

{{FIG:fig_m1_las_cuatro_averias}}

Cada punto es un día. La altura son las horas que el compresor pasó trabajando de verdad. La
línea de puntos es la media, **3,42 horas**. Los cuatro círculos son los días con parte de
avería, y los cuatro están arriba, muy por encima de la media.

Ese dibujo es el proyecto entero. El resto del curso va de construir lo necesario para verlo sin
saber de antemano dónde mirar.

## Ojo

- **La ficha describe la captura, no el fichero.** Es el desajuste de este módulo, y es normal en
  datos públicos. Se comprueba contando, no leyendo.
- **Los partes de avería vienen con erratas y no se corrigen.** Están numerados `#1`, `#1`, `#3`
  y `#4`: hay dos unos y no existe el dos. Uno escribe `Air leak` y otro `Air Leak`. Y la avería
  del 29 de mayo declara mantenimiento el **30 de abril**, un mes antes de sí misma. Se copian
  literales y se explican, porque así llegan los partes reales.
- **El muestreo no es regular.** 179.426 lecturas, el 11,8 %, no respetan los diez segundos.
  Contar filas y medir tiempo no será lo mismo.
- **Cuatro averías no dan para estadística.** Con cuatro eventos se hace un estudio de casos y se
  dice que lo es. Cualquier porcentaje calculado sobre cuatro cosas es una anécdota con decimales.
- **Los decimales traen basura.** En el fichero hay valores como `-0.0120000000000004`. No es un
  error de nadie: es cómo un ordenador guarda los números con coma. Se arregla en el módulo 14.

## Puente metalúrgico

Cuando llega un certificado de laboratorio con la ley de un lote, lo primero que hace un
metalurgista con oficio no es usar el número. Es mirar cuántas alícuotas lo respaldan, de qué
fecha son y si el método declarado es el que se usó.

Un certificado que dice 64,03 % de hierro durante treinta y tres días seguidos no es una ley
estable: es un ensayo que dejó de actualizarse. El número parece bueno hasta que se pregunta de
dónde salió.

Este módulo es eso mismo con un fichero. La ficha es el certificado, el CSV es la pulpa, y
contar las filas es pesar la alícuota antes de fiarse del papel.

## Repaso

### Te dan un fichero de datos y su documentación. Por dónde empiezas

Por contar. Filas, columnas, primera y última fecha, y cada cuánto llega una lectura. Son cuatro
consultas y se hacen antes de nada. La documentación se lee después, para explicar lo que se ha
contado, no para sustituirlo.

### La ficha decía 15 millones y el fichero trae 1,5. Es un error del repositorio

No. El cociente es exactamente diez y la columna índice conserva la numeración original, así que
lo publicado es un submuestreo del registro original. La ficha describe la captura de la máquina.
Es una imprecisión de redacción, no un dato perdido.

### Por qué no corriges las erratas de los partes de avería

Porque son la única verdad terreno del proyecto y no me pertenecen. Si corrijo la numeración o
la fecha de mantenimiento, estoy inventando un dato que no medí. Se conservan literales, se
declaran en un LEEME al lado del fichero, y se explican en la lección donde estorban.

### Qué te hace pensar que la fuga se verá en algo, si la presión no baja

La figura del final. Los cuatro días con parte de avería son días en los que el compresor trabajó
mucho más de lo normal, hasta 23,81 horas de 24 frente a una media de 3,42. La presión la sostiene
el control; lo que se dispara es el esfuerzo por sostenerla.

### Un compresor no es una planta de flotación. Qué pinta esto en tu portafolio

Pinta que el aire comprimido es lo que alimenta las columnas de flotación, y que una fuga en la
red de aire es recuperación perdida sin que salte ninguna alarma. La máquina cambia, el problema
es el mismo: la variable que se controla no delata nada, y la que trabaja para controlarla sí.

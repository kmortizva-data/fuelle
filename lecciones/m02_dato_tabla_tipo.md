---
module: 2
---

## En 30 segundos

- Una **tabla** es una rejilla: cada fila un momento, cada columna una señal.
- Un **tipo** es la promesa de qué clase de valor cabe en una columna.
- Siete señales de este compresor miden magnitudes. Ocho solo dicen sí o no.
- Esa clasificación no se lee en la ficha: se cuenta. Una señal con dos valores es digital.
- Contada, coincide con lo que la ficha declara. **Esta vez el papel acierta.**

## Qué resuelve este módulo

El módulo anterior abrió el archivo y contó las filas. Este mira dentro de una.

Suena elemental y no lo es. Casi todo lo que falla más adelante nace de una suposición sobre el
contenido de una columna.

Un número escrito como texto. Un sí o no tratado como cantidad. Una fecha ordenada
alfabéticamente.

Tres palabras y ya está: dato, tabla y tipo.

## Antes de la teoría: un ejemplo de juguete

Un turno de tres lecturas de una celda de flotación, apuntadas en un cuaderno:

| hora | pH | espumador | alarma |
|---|---|---|---|
| 08:00 | 10,4 | 12 | no |
| 08:30 | 10,1 | 14 | no |
| 09:00 | 9,8 | 14 | sí |

**Eso es una tabla.** Tres filas, cuatro columnas. Cada fila es un momento y cada columna una
cosa que se midió en todos ellos.

**Cada columna tiene su tipo**, y basta mirarla para saberlo:

- `hora` es una **hora**. Se puede ordenar y restar. Las 09:00 van después de las 08:30.
- `pH` es un **número con decimales**. Se puede promediar: 10,1.
- `espumador` es un **número entero**, en gramos por tonelada.
- `alarma` solo dice **sí o no**. No tiene decimales ni promedio. Lo único que se puede hacer con
  ella es contar cuántas veces dijo sí.

**Cuenta los valores distintos de cada columna.** `pH` tiene tres, `espumador` dos, `alarma` dos.

Y ahí aparece la trampa que este módulo enseña a esquivar: **`espumador` y `alarma` tienen los
dos dos valores distintos, y no son la misma clase de cosa**. El espumador podría haber tomado
13 o 15; es una cantidad que en este turno solo tomó dos valores. La alarma no puede tomar 13
jamás.

Con tres filas, contar valores distintos no basta. Con un millón y medio, sí.

## Glosario

- **Dato.** Un valor suelto. El 10,4 de la primera fila.
- **Fila.** Todo lo que se midió en un mismo instante. Aquí, un momento del compresor.
- **Columna.** La misma señal a lo largo del tiempo. Se llama también campo, o variable.
- **Tabla.** Filas y columnas juntas, con la promesa de que todas las filas tienen las mismas
  columnas.
- **Tipo.** Qué clase de valor cabe en una columna. Texto, entero, decimal, fecha o sí y no. La
  base de datos lo usa para saber qué operaciones tienen sentido.
- **Grano.** A qué corresponde una fila. Aquí una lectura de diez segundos. Es la pregunta que
  hay que contestar antes de tocar cualquier tabla.
- **Valores distintos.** Cuántos valores diferentes aparecen en una columna. Es la forma más
  rápida de adivinar de qué tipo es algo cuando nadie te lo ha dicho.

## Paso a paso

### Paso 1. Mirar una fila entera

El compresor deja una fila cada diez segundos. En esa fila caben quince señales, y todas se
midieron en el mismo instante.

Esa última parte no es un detalle: es lo que hace que una tabla sea una tabla y no quince listas
sueltas. Si la presión y la corriente de una misma fila fueran de momentos distintos, compararlas
no significaría nada.

### Paso 2. Preguntarse qué clase de cosa es cada columna

La ficha oficial lo dice: siete analógicas y ocho digitales, con nombres y todo.

Y en el módulo anterior esa misma ficha se equivocó en el número de mediciones. Así que se cuenta.

### Paso 3. Contar valores distintos

Una señal que mide una presión toma miles de valores diferentes a lo largo de siete meses. Una
válvula que solo puede estar abierta o cerrada toma dos. No hace falta más para separarlas.

## El código, por partes

### Paso 4. Cuántos valores distintos toma cada señal

```python
for señal in FICHA:
    distintos, minimo, maximo = con.sql(
        f'SELECT count(DISTINCT "{señal}"), min("{señal}"), max("{señal}") FROM t'
    ).fetchone()
    medido = "digital" if distintos <= 2 else "analógica"
```

```anota
for señal in FICHA | repite lo de dentro una vez por cada señal de la lista
count(DISTINCT col) | cuenta valores diferentes, no filas: si 8 se repite mil veces, cuenta una
f'...' con comillas dobles dentro | las comillas dobles protegen el nombre de la columna en SQL
distintos <= 2 | la regla entera: dos valores o menos, digital
```

```salida
señal              distintos        min        max   ficha       dato
TP2                   5,257      -0.03      10.68   analógica  analógica
TP3                   3,683       0.73      10.30   analógica  analógica
H1                    2,665      -0.04      10.29   analógica  analógica
DV_pressure           2,257      -0.03       9.84   analógica  analógica
Reservoirs            3,682       0.71      10.30   analógica  analógica
Oil_temperature       2,462      15.40      89.05   analógica  analógica
Motor_current         1,809       0.02       9.29   analógica  analógica
COMP                      2       0.00       1.00   digital    digital
DV_eletric                2       0.00       1.00   digital    digital
Towers                    2       0.00       1.00   digital    digital
MPG                       2       0.00       1.00   digital    digital
LPS                       2       0.00       1.00   digital    digital
Pressure_switch           2       0.00       1.00   digital    digital
Oil_level                 2       0.00       1.00   digital    digital
Caudal_impulses           2       0.00       1.00   digital    digital
```

No hay término medio. Las siete primeras toman entre mil ochocientos y cinco mil valores. Las
ocho últimas toman exactamente dos.

### Paso 5. Ver la diferencia dibujada

{{FIG:fig_m2_analogica_vs_digital}}

La misma hora, dos señales. Arriba la presión del panel, que baja despacio, sube de golpe cuando
el compresor arranca y vuelve a bajar. Abajo la válvula de admisión, que solo sabe estar en cero
o en uno.

La de abajo está dibujada con escalones y no con líneas rectas a propósito. Una válvula no pasa
por los valores intermedios: salta. Unirla con una rampa sería dibujar algo que la máquina nunca
hizo.

Y hay algo que se ve solo poniéndolas juntas: **la válvula baja a cero justo cuando la presión
sube**. Son la misma historia contada por dos sensores.

## El resultado, medido

**Qué esperábamos.** Que la clasificación medida coincidiera con la ficha. O que apareciese alguna
señal a medio camino, de esas que la documentación llama digital y en realidad son un contador.

**Qué salió.** **Siete analógicas y ocho digitales**, exactamente lo que la ficha declara. Cero
discrepancias. Las digitales toman dos valores clavados, cero y uno, sin un solo caso raro en
1.516.948 filas.

**Qué significa.** Esta vez el papel acierta, y conviene decirlo con la misma claridad con la que
se dijo que en el módulo 1 fallaba. Comprobar no es desconfiar por sistema: es saber cuánto vale
lo que te dan. Ahora esa ficha vale más, porque una parte suya se contrastó y aguantó.

Los rangos, además, salen coherentes con la máquina. La temperatura del aceite va de 15,4 a
89,05 grados, que es un arranque en frío y un régimen caliente. La corriente del motor llega a
9,29 A, que es el pico de arranque que la ficha anunciaba.

## Ojo

- **Contar valores distintos es un atajo, no una definición.** Funciona con un millón y medio de
  filas y falla con tres, como en el ejemplo del cuaderno. Un contador que en el periodo medido
  solo tomó dos valores parecería digital sin serlo.
- **Cero y uno no siempre significan lo mismo.** En `COMP`, activo significa que **no** entra
  aire. Leer un uno como «encendido» es equivocarse en el sentido, y ese error no lo caza ningún
  tipo de dato.
- **Un sí o no no se promedia.** La media de `LPS` es un número que sale y no significa nada. Lo
  que tiene sentido es contar cuántas veces dijo sí, o cuánto tiempo estuvo diciéndolo.
- **El grano manda sobre todo lo demás.** Una fila aquí es una lectura de diez segundos. En cuanto
  se agrupe por día, una fila será un día, y todo lo que se escriba después tiene que contar con
  eso.
- **`Caudal_impulses` se llama contador y toma dos valores.** No cuenta acumulando: marca cada
  pulso de aire con un uno. El nombre sugiere una cosa y el dato hace otra.

## Puente metalúrgico

Un certificado de laboratorio y una hoja de turno son las dos tablas, y no se leen igual.

En el certificado, la ley de cobre es un número con decimales: se promedia, se compara con la del
lote anterior, se le calcula una desviación. En la hoja de turno, «molino parado» es un sí o un
no: no tiene media, tiene horas acumuladas y número de veces.

Confundirlas es el error clásico del que empieza a manejar datos de planta. Preguntar cuál fue la
media de «molino parado» no es una pregunta difícil: es una pregunta que no significa nada, y la
base de datos te dará un número igualmente.

## Repaso

### Qué es el grano de una tabla y por qué preguntas siempre por él

Es a qué corresponde una fila. Aquí, una lectura de diez segundos de todas las señales a la vez.
Se pregunta primero porque determina qué operaciones tienen sentido: contar filas es contar
lecturas, no minutos ni averías. Cuando el grano cambia, cambia el significado de todo lo demás.

### Cómo distingues una señal analógica de una digital sin que nadie te lo diga

Contando valores distintos. Con 1.516.948 filas delante, una presión toma miles y una válvula
toma dos. Aquí la separación fue limpia: de 1.809 valores a 2, sin nada en medio. Con pocas filas
el atajo no vale, porque una cantidad puede haber tomado solo dos valores por casualidad.

### La ficha decía siete y ocho, y salieron siete y ocho. Perdiste el tiempo comprobando

No. Sé algo que antes no sabía: que en esta parte la ficha es fiable. En el módulo 1 la misma
ficha se equivocó en el número de mediciones, así que no era una comprobación de trámite.
Comprobar y acertar cambia lo que puedes apoyar en ese papel más adelante.

### Alguien te pasa un CSV donde el pH viene como texto. Qué pasa si no lo conviertes

Que ordena alfabéticamente y compara mal. El texto «10,4» va delante de «9,8», porque el uno va
delante del nueve.

Los promedios fallarán o darán error. Y lo peor: un orden mal hecho no da error ninguno, solo un
resultado equivocado con buena cara.

### En este compresor, un uno en COMP significa que el compresor está trabajando

No, significa lo contrario. `COMP` marca la válvula de admisión y está activa cuando **no** entra
aire, o sea con el compresor parado o girando en vacío. Es el ejemplo de por qué el tipo de dato
no basta: sé que es un sí o no, y aun así puedo leer al revés lo que dice.

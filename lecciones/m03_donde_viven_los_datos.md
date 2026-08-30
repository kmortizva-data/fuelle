---
module: 3
---

## En 30 segundos

- «Fichero», «base de datos», «lago» y «almacén» no son sinónimos, aunque se usen así.
- La misma pregunta, en los cuatro sitios: de **0,587 s a 0,003 s**. Casi doscientas veces.
- El fichero de texto es el más grande y el más lento. Los dos a la vez, y no es casualidad.
- El lago ocupa **22,08 MB** frente a **208,19**: casi diez veces menos con el mismo dato dentro.
- Y una sorpresa: **el índice del almacén no aceleró nada** y costó 17,8 MB.

## Qué resuelve este módulo

Estas cuatro palabras salen en toda oferta de trabajo del sector y casi nadie las distingue.
Explicarlas con definiciones no sirve: las definiciones se parecen demasiado entre sí.

Así que aquí se hace lo contrario. Se coge una pregunta sencilla, se guarda el mismo dato de
cuatro maneras, y se cronometra. Las diferencias se ven solas.

## Antes de la teoría: un ejemplo de juguete

Tienes los partes de turno de un año en la oficina de planta, y alguien pregunta cuántas paradas
hubo el 5 de junio.

**Sitio uno: una caja de folios.** Están todos, sin orden. Para contestar hay que sacarlos y
mirarlos uno a uno hasta el final, porque hasta el último no sabes si queda alguno del 5 de junio.

**Sitio dos: doce carpetas, una por mes.** Vas a la de junio y miras solo esa. Los otros once
meses no los tocas. La caja pesaba lo mismo, pero ahora la pregunta cuesta un doceavo.

**Sitio tres: un archivador con fichas ordenadas por fecha.** Vas directo al 5 de junio. Ni
siquiera abres la carpeta entera.

**Sitio cuatro: una libreta donde alguien ya anotó, cada noche, cuántas paradas hubo ese día.**
Miras una línea.

Esos cuatro sitios son, en el mismo orden: **un fichero, un lago, una base de datos y un
almacén**. Y todos guardan exactamente la misma información.

Lo que cambia no es el dato. Es cuánto trabajo hay que hacer para preguntarle algo.

## Glosario

- **Fichero.** Un archivo suelto con los datos dentro, normalmente texto. No sabe nada de sí
  mismo: para responder cualquier cosa hay que leerlo entero.
- **Formato columnar.** Guardar juntos todos los valores de una misma columna, en vez de juntar
  las filas. Permite leer solo las columnas que hacen falta y comprime mucho mejor.
- **Lago de datos.** Ficheros en carpetas, normalmente en formato columnar y repartidos por
  fecha. Barato, y se consulta sin meter nada en ningún servidor.
- **Base de datos.** Un programa que guarda los datos en su propio formato y responde preguntas.
  Sabe qué hay dentro, así que puede saltarse lo que no necesita.
- **Almacén de datos.** Una base de datos preparada para las preguntas que se repiten: columnas ya
  calculadas, tablas ya resumidas, índices donde hacen falta.
- **Índice.** Una estructura aparte que apunta dónde está cada valor, para no tener que buscarlo.
  Acelera unas preguntas, ocupa sitio y frena las escrituras.

## Paso a paso

### Paso 1. Elegir una pregunta y no cambiarla

Cuántas lecturas hay del 5 de junio. Es de las más simples que se pueden hacer, y por eso vale:
lo que se mide es el sitio, no la pregunta.

### Paso 2. Guardar el mismo dato de cuatro formas

El CSV original tal cual llegó. El lago de Parquet particionado por día. Una base de datos con la
tabla dentro. Y un almacén, que es esa misma base con la fecha ya calculada en su propia columna
y un índice encima.

### Paso 3. Cronometrar siete veces cada uno, y quedarse con la mediana

Una sola medida no es una medida. La primera versión de este script cronometraba una vez, y dos
ejecuciones seguidas del mismo código dieron 203,7 y 143,8 veces entre los extremos. La
conclusión gruesa aguantaba, pero el número que iba a publicarse no.

Así que se mide siete veces y se publica la mediana, para que un pico aislado no mueva el
resultado, y también el mínimo y el máximo, porque esconder la variabilidad sería fingir una
precisión que no existe.

## El código, por partes

### Paso 4. La misma pregunta, cambiando solo el sitio

```python
tiempos = []
for _ in range(7):
    inicio = time.perf_counter()
    filas = con.sql(sql).fetchone()[0]
    tiempos.append(time.perf_counter() - inicio)
tiempos.sort()
mediana = tiempos[len(tiempos) // 2]
```

```anota
CAST(timestamp AS DATE) | se queda con la parte del día y tira la hora
time.perf_counter() | el cronómetro más preciso de Python, en segundos
.fetchone()[0] | la primera fila, y de ella el primer valor: el número que cuenta
for _ in range(7) | repite siete veces; el guion bajo significa que el número de vuelta no se usa
tiempos[len(tiempos) // 2] | el del medio una vez ordenados, o sea la mediana
```

```salida
mediana de 7 corridas por sitio
sitio                 formato                 tamaño  mediana     min     max
un fichero de texto   CSV                     208.19 MB   0.587   0.563   0.617
un lago de ficheros   Parquet particionado     22.08 MB   0.229   0.191   0.310
una base de datos     DuckDB                   50.01 MB   0.003   0.002   0.004
un almacén            DuckDB con índice        67.76 MB   0.004   0.003   0.006
```

### Paso 5. Comprobar que los cuatro dicen lo mismo

Antes de comparar tiempos hay que comprobar que las cuatro respuestas coinciden. Si no, no se
está midiendo el sitio: se está midiendo un error.

```salida
los cuatro devuelven 8,716 filas del 2020-06-05: True
del más lento al más rápido: 195.7 veces
```

## El resultado, medido

{{FIG:fig_m3_cuatro_sitios}}

**Qué esperábamos.** Que el fichero de texto fuera el más lento y la base de datos la más rápida.
Y que el almacén, con su índice, fuera más rápido todavía.

**Qué salió.** Lo primero sí, y por goleada: el fichero de texto tarda **0,587 s**
y la base de datos **0,003 s**, que son casi doscientas veces.

**El índice no aceleró nada.** El almacén y la base de datos dan medianas de
0,004 y 0,003 segundos, y **sus rangos se solapan**. Cuando dos
rangos se pisan no hay diferencia que enseñar, por mucho que las medianas no sean idénticas. Lo
único que el índice consiguió con seguridad fue ocupar **17,8 MB
más**.

**Qué significa.** Un índice sirve para no tener que mirar todo. Pero esta base de datos es
columnar y ya guarda, por cada bloque de filas, cuál es el valor mínimo y el máximo. Preguntando
por un día, se salta de golpe los bloques que no pueden contenerlo. El índice llega tarde a un
trabajo que ya estaba hecho.

Ojo con la lectura fina: a escala de milésimas de segundo los tiempos bailan, y por eso se miden
siete veces y se publica el rango. **Los tiempos exactos del bloque de arriba son de una corrida
concreta y en la tuya saldrán parecidos pero no iguales.** Lo que aguanta entre corridas es la
conclusión en negativo: el índice no aporta una mejora que se pueda ver. El módulo 21 vuelve
sobre esto con PostgreSQL, que no es columnar, y allí la respuesta es distinta.

Y el dato que más se va a repetir en el curso: **el mismo contenido pasa de 208,19 MB a 22,08 MB**
solo por cambiar de formato. Eso es el módulo 7 entero, y aquí ya asoma.

## Ojo

- **El más grande es también el más lento, y no es coincidencia.** El CSV es texto: cada número
  hay que interpretarlo carácter a carácter al leerlo. Ocupar más es leer más.
- **Una sola medida no es una medida.** Cronometrando una vez, dos corridas del mismo código
  dieron 203,7 y 143,8 veces entre los extremos. Con siete repeticiones y la mediana, el número
  se queda quieto. Si una diferencia no sobrevive a repetir la medición, no existe.
- **Un índice no es gratis.** Ocupa disco, hay que mantenerlo en cada escritura, y solo paga si
  el motor no tenía ya otra forma de saltarse lo que no necesita.
- **El lago es el que más baila**, entre 0,191 y 0,310 segundos según la corrida, Con 212 carpetas
  entre la corrida más rápida y la más lenta. Con 212 carpetas que abrir y cerrar, esa
  variabilidad es el sistema de ficheros, no los datos.
- **Ninguno de los cuatro es «el mejor».** El fichero es el que llegó y no se toca. El lago es
  barato y no necesita servidor. La base de datos es rápida y necesita que alguien la cuide. El
  almacén es para preguntas que se repiten mucho.

## Puente metalúrgico

Una muestra de pulpa se puede guardar de cuatro maneras, y todas contienen el mismo mineral.

En un bidón sin etiqueta, que es el fichero: está todo, y para saber algo hay que volver a
ensayarlo entero. En bandejas rotuladas por turno, que es el lago: vas a la del turno que te
interesa. En el registro del laboratorio, que es la base de datos: buscas por número de muestra y
está. Y en el informe mensual de leyes, que es el almacén: alguien ya calculó las medias que se
piden todos los meses.

Nadie tira las bandejas porque exista el informe. Cada sitio responde a una pregunta distinta, y
el informe se puede rehacer desde las bandejas, pero no al revés.

## Repaso

### Diferencia entre un lago de datos y un almacén de datos

El lago guarda el dato como llegó, en ficheros, y sirve para preguntas que todavía no sabes que
vas a hacer. El almacén guarda el dato ya preparado para preguntas concretas que se repiten. El
lago es barato y flexible; el almacén es rápido y rígido. En un proyecto serio conviven, y el
almacén se reconstruye desde el lago.

### Por qué el CSV es a la vez el más grande y el más lento

Porque es texto. El número 8,716 ocupa cinco caracteres y hay que convertirlo a número cada vez
que se lee. En formato columnar ocupa unos pocos bytes y se lee tal cual. Más tamaño significa
más lectura de disco, y encima con trabajo de interpretación por medio.

### Pusiste un índice y no aceleró. Estaba mal puesto

No, estaba puesto sobre la columna correcta. Lo que pasa es que la base de datos es columnar y
guarda el mínimo y el máximo de cada bloque, así que ya se saltaba lo que no hacía falta. El
índice repetía un trabajo ya hecho y encima ocupaba 17,8 MB. En una base de datos por filas, como
PostgreSQL, la respuesta habría sido otra, y eso se mide en el módulo 21.

### Tienes 208 MB. Merece la pena montar una base de datos

Para 208 MB, casi nunca. El lago de Parquet contesta en dos décimas de segundo sin instalar ni
mantener nada. Una base de datos empieza a valer la pena cuando hay varias personas escribiendo a la vez,
o cuando hacen falta garantías de que dos cosas ocurren juntas o no ocurren. Por velocidad sola,
a esta escala, no.

### Te dicen «tenemos un data lake» y ves una carpeta con CSV. Qué preguntas

Si están en formato columnar, si están repartidos por alguna fecha o clave, y quién decide qué
entra. Una carpeta con CSV sueltos es una caja de folios con nombre en inglés. Lo que convierte
una carpeta en un lago es que las preguntas cuesten poco y que alguien sepa qué hay dentro.

---
module: 27
---

## En 30 segundos

- El residual sale de una identidad, no de un ajuste: `carga × entrega − consumo`, en bar/min.
- Y con una fuga de tamaño **f**, el residual vale **exactamente f**. No se le parece: es ella.
- El suelo de ruido, sobre 579 horas sanas, llega a **0,1165**. El techo está en **1,1796**.
- Diez veces de margen, y por eso funciona: **0,1165 contra 1,1796**.
- Ojo con dos cosas: el residual **se topa** arriba, y por días pierde la avería de madrugada.

## Qué resuelve este módulo

El módulo 23 dijo que un gemelo entrega una diferencia y nada más. El 24 midió los cuatro números,
el 25 los puso a correr y el 26 comprobó que significan algo. Falta lo único que el curso ha
prometido desde el principio: **convertir esa diferencia en un número con unidades**.

Y hay una forma de hacerlo que no necesita simular nada, porque sale de la conservación del aire.
En cualquier tramo largo, el compresor mete tanto aire como la planta saca. Y mete `entrega`
bar/min mientras carga, durante una fracción del tiempo, así que

```
aire que se está gastando = carga × entrega
```

Restarle el consumo de cuando la máquina estaba bien deja **lo que se gasta de más**. Eso es el
residual, y es la fuga.

## Antes de la teoría: un ejemplo de juguete

Un depósito de agua con una bomba que mete **10 litros por minuto**. Nadie ha visto nunca el
depósito por dentro ni sabe dónde está la fuga. Solo se sabe cuánto tiempo estuvo la bomba
encendida, porque hay un contador de horas.

| | Bomba encendida | Litros metidos | |
|---|---|---|---|
| Una semana normal | 60 min al día | 600 l/día | así vive esta casa |
| Esta semana | 180 min al día | 1.800 l/día | |

**Sobran 1.200 litros al día.** Y fíjate en lo que ha hecho falta para decirlo: el caudal de la
bomba, el contador de horas, y saber qué era normal. Ni una gota medida en la fuga, ni haber
encontrado dónde está.

Eso es todo. Cambia litros por bar, la bomba por el compresor y el contador de horas por el ciclo
de trabajo, y tienes el residual de este curso.

## Glosario

- **Residual.** Lo que la máquina gasta de más respecto a cuando estaba sana, en bar/min.
- **Suelo de ruido.** Lo más alto que llega el residual sin que pase nada. Todo aviso tiene que
  estar por encima, o suena solo.
- **Techo, o censura.** El residual no puede pasar de `llena`, porque el compresor no puede cargar
  más del 100 % del tiempo. Cuando llega ahí, dice «al menos esto» y no puede decir cuánto.
- **Grano.** El trozo de tiempo sobre el que se promedia. Aquí es la hora, y la elección importa
  más de lo que parece.
- **Indicador congelado.** El residual contra la máquina sana de febrero. Dice cuánto se ha alejado.
- **Indicador móvil.** El mismo residual contra los catorce días anteriores. Dice cuánto ha
  cambiado. Son dos preguntas distintas y hacen falta las dos.

## Paso a paso

### Paso 1. Escribir el residual

`carga × entrega − consumo`, hora a hora. Tres números, dos de ellos medidos en el módulo 24 y
congelados desde entonces, y la carga que sale de contar lecturas.

### Paso 2. Medir el suelo antes de mirar ninguna avería

Sobre las 579 horas de febrero, que es la ventana sana que el módulo 26 dejó limpia. **Primero el
suelo y después las averías**, no al revés: un listón elegido después de ver la señal es un listón
elegido a conveniencia.

### Paso 3. Elegir el grano, y comprobar la elección

Por horas o por días. Parece un detalle de implementación y decide si una de las cuatro averías se
ve o no.

### Paso 4. Sacar el mismo número por otro camino

La pendiente de vaciado mide el consumo directamente: cuánto baja la presión dividido por los
minutos en vacío. No usa la entrega, ni el modelo, ni nada. Si las dos rutas coinciden en día sano,
las dos están bien.

## El código, por partes

### Paso 5. El residual, entero

```python
avg(DV_eletric) * entrega - consumo AS residual
```

```anota
avg(DV_eletric) | el ciclo de trabajo de esa hora: la fracción de lecturas con el compresor cargando
× entrega | eso convierte tiempo en aire: bar por minuto que de verdad se están moviendo
− consumo | y le quita lo que gastaba la máquina sana. Lo que queda es lo que sobra
```

No hay más. El gemelo del módulo 25 no aparece por ninguna parte, y es a propósito: **en régimen la
simulación y esta cuenta dan lo mismo**, así que simular sería dar un rodeo.

El simulador sigue haciendo falta para otra cosa: preguntar por una fuga que todavía no ha
ocurrido. Es lo que hace la perilla de aquí abajo.

### Paso 6. La segunda ruta, que no comparte nada con la primera

```python
sum(p_ini - p_fin) / sum(minutos) AS consumo
```

```anota
p_ini − p_fin | lo que baja la presión en un tramo de vacío, en bar
sum / sum | el total entre el total, no la media de las medias: un tramo de veinte minutos pesa veinte veces más que uno de uno
qué no lleva | ni entrega, ni carga, ni el modelo. Por eso vale como segunda opinión
```

### Paso 7. Toca la perilla

```perilla
m27_fuga
```

La perilla mete una fuga que no existió, de cero a 0,30 bar/min, y enseña qué haría el compresor.
Mira el pie mientras la mueves: **el residual va marcando el mismo número que la fuga**, y eso no es
casualidad ni ajuste. Es la identidad del paso 5 despejada.

Y contesta la pregunta del temario con un número: la fuga se nota **a partir de 0,12 bar/min**, que
es cuando el residual pasa del suelo de ruido.

Con la perilla a cero verás un residual de **−0,003** en vez de un cero limpio. No es un error de
la cuenta: es el paso de la simulación, el mismo del módulo 25. Ocho horas simuladas no caben en un
número exacto de ciclos, y el ciclo a medias del final se nota en la tercera cifra.

## El resultado, medido

{{FIG:fig_m27_residual}}

**Qué esperábamos.** Que el residual se despegara del suelo en las cuatro averías documentadas.

**Qué salió.** Eso, y tres cosas más que no estaban en el guion.

```salida
  el residual es carga x 1.2507 - 0.0711, en bar/min

  el suelo, sobre 579 horas de febrero:
    mediana 0.0053   p95 0.0505   p99 0.0728   máximo 0.1165
  el techo, que es `llena`: 1.1796   o sea 10.1 veces el suelo
  y 156 horas de 3924 llegan a tocarlo

  por día contra por hora, en los cuatro partes:
    #1   2020-04-18   diario  1.1663 (10.01x el suelo)   horario  1.1796 (10.13x)
    #1   2020-05-29   diario  0.1268 ( 1.09x el suelo)   horario  0.8704 ( 7.47x)
    #3   2020-06-05   diario  0.7245 ( 6.22x el suelo)   horario  1.1796 (10.13x)
    #4   2020-07-15   diario  0.5307 ( 4.56x el suelo)   horario  1.1796 (10.13x)

  la segunda ruta, el consumo por pendiente de vaciado:
    2020-02-18     44 tramos,   1368 min   consumo 0.0648   (el residual iba por 0.0505)
    2020-03-06     74 tramos,    894 min   consumo 0.1662   (el residual iba por 1.1796)
    2020-04-18   sin un solo tramo de vacío: la ruta no contesta
    2020-05-30     52 tramos,    947 min   consumo 0.1117   (el residual iba por 1.1796)
    2020-06-05     25 tramos,    508 min   consumo 0.1014   (el residual iba por 1.1796)
    2020-06-06   sin un solo tramo de vacío: la ruta no contesta
    2020-07-15    127 tramos,    726 min   consumo 0.349   (el residual iba por 1.1796)
```

### El margen: diez veces

El suelo llega a **0,1165** y el techo está en **1,1796**. Entre uno y otro hay un factor de
**10,1**, y ahí es donde cabe todo lo que este gemelo puede decir.

El techo no es un tope elegido: es `llena`, lo que sube el depósito por minuto cargando. Cuando el
compresor carga el 100 % del tiempo, la carga vale 1 y el residual no puede subir más aunque la
fuga siga creciendo. **156 horas de las 3.924 medidas llegan a tocarlo.**

### El grano: por días se pierde la avería de madrugada

La #1b empieza el 29 de mayo a las 23:30, así que ensucia media hora de un día de veinticuatro. Por
horas el residual llega a **0,8704**, que es **7,47 veces** el suelo. Por días queda en **0,1268**,
que es **1,09 veces**: cruza el listón por un nueve por ciento, y eso no es detectar, es acertar.

Es el módulo 15 al revés. Allí la señal rápida bajaba al grano de la lenta para poder cruzarlas.
Aquí bajar al grano lento **destruye la señal**: un pico de media hora se reparte entre
veinticuatro.

### Las dos rutas, y la que se calla

En día sano las dos coinciden: el 18 de febrero la pendiente da **0,0648** bar/min de consumo, muy
cerca de los 0,0711 con los que se calibró.

Y en avería pasa lo que hace que las dos merezcan la pena:

| | Ruta del ciclo de trabajo | Ruta de la pendiente |
|---|---|---|
| 18 de abril | topada en 1,1796 | **no contesta**, ni un tramo de vacío |
| 6 de junio | topada en 1,1796 | **no contesta** |
| 15 de julio | topada en 1,1796 | **0,349 bar/min** |

**La que siempre contesta no puede decir cuánto, y la que puede decir cuánto a veces no contesta.**
El 15 de julio la pendiente da un consumo de 0,349, que es **cinco veces** el sano y muy por encima
de donde el residual se topa. El 18 de abril el compresor no descansó ni un tramo, así que no hay
pendiente que medir.

No son dos formas de calcular lo mismo. Son dos instrumentos con rangos distintos, y a un gemelo le
conviene llevar los dos.

### La deriva, y por qué hacen falta dos lecturas del mismo número

El panel de abajo de la figura es el mismo residual leído de otra forma: cada día contra la mediana
de los catorce anteriores. Y hace falta porque el de arriba enseña algo incómodo.

| Mes | Días por encima del suelo | Residual mediano |
|---|---|---|
| Febrero | 1 de 28 | 0,0053 |
| Marzo | 19 de 31 | 0,0574 |
| Abril | 14 de 29 | 0,0331 |
| Mayo | 18 de 28 | 0,0644 |
| Junio | 25 de 28 | 0,0852 |
| Julio | 26 de 31 | 0,0818 |
| Agosto | 24 de 31 | 0,0713 |

**La máquina no vuelve a febrero.** Y el gemelo no se ha estropeado: el aire de la planta sube de
verdad, de 0,0711 bar/min a más del doble. Con el suelo puesto en febrero, casi todos los días de
junio en adelante quedan por encima.

Eso no es un fallo del indicador congelado, es su respuesta: **la máquina de julio no es la de
febrero**. Pero para poner una alarma no sirve, porque estaría sonando siempre.

Por eso el mismo residual se lee también contra los catorce días anteriores. Ahí los partes vuelven
a destacar, contra una mediana de **0,0052** en un día corriente:

| Día | Sobre la tendencia |
|---|---|
| 18 de abril | **+1,0631** |
| 29 de mayo | **+0,5368** |
| 5 de junio | **+0,8182** |
| 15 de julio | **+1,0169** |

**Y esto no contradice la regla del módulo 23.** El gemelo sigue calibrado con lo sano y congelado;
lo que se mueve es la referencia contra la que se lee su residual. Son dos preguntas distintas
sobre el mismo número: cuánto se ha alejado la máquina de cuando estaba bien, y cuánto ha cambiado
desde la semana pasada.

**Qué significa.** Que el residual ya es un número con unidades, con un suelo y un techo medidos, y
con dos lecturas que contestan a dos preguntas. Lo que no tiene todavía es un umbral, y eso es el
módulo 28 a propósito: si el mismo script eligiera el umbral y midiera el resultado, estaría
eligiendo su propio examen.

## Hazlo tú

```reto
pregunta: Calcula el residual hora a hora con la fórmula del módulo (`carga * 1.2507 - 0.0711`) y saca, para los cuatro días con parte de avería, cuántas horas pasan del suelo de ruido de 0,1165 y cuál fue el residual máximo. Salta las horas incompletas, las de menos de 300 lecturas. Devuelve `dia`, `horas` y `residual_maximo`, ordenado por día. Cuatro filas.
inicio: SELECT hora, carga, lecturas,
       carga * 1.2507 - 0.0711 AS residual
FROM horas
WHERE lecturas >= 300;
esperado: m27_horas_sobre_el_suelo
pista: `count(*) FILTER (WHERE ...)` cuenta solo las filas que cumplen la condición, sin tener que hacer una subconsulta. Para agrupar por día de una marca de tiempo, `hora::DATE` la recorta. Y el máximo se saca con `max` del mismo residual.
solucion: SELECT hora::DATE AS dia,
       count(*) FILTER (WHERE carga * 1.2507 - 0.0711 > 0.1165) AS horas,
       round(max(carga * 1.2507 - 0.0711), 4) AS residual_maximo
FROM horas
WHERE lecturas >= 300
  AND hora::DATE IN (DATE '2020-04-18', DATE '2020-05-29',
                     DATE '2020-06-05', DATE '2020-07-15')
GROUP BY 1 ORDER BY 1;
```

El 18 de abril y el 15 de julio pasan **las veinticuatro horas** por encima del suelo. El 5 de junio,
quince. Y el 29 de mayo, **cuatro**: es la avería de madrugada, y ahí se ve por qué a grano diario
se diluye.

Fíjate además en la columna del máximo: tres de los cuatro días marcan **1,1796** exacto. No es que
las tres averías tuvieran el mismo tamaño, es que las tres tocaron el techo.

## Ojo

- **El residual es la fuga, en las mismas unidades.** No es un índice ni una puntuación. Con una
  fuga de 0,12 bar/min el residual vale 0,12, y eso se puede llevar a una reunión.
- **Un residual topado no dice cuánto.** Dice «al menos `llena`». Publicar un máximo de 1,1796 en
  tres días distintos y presentarlos como igual de graves sería mentir con un número cierto.
- **El grano no es un detalle de implementación.** La misma avería vale 7,47 o 1,09 veces el suelo
  según se mire por horas o por días.
- **Mide el suelo antes de mirar la avería.** Un listón elegido después de ver la señal siempre
  queda justo debajo de ella.
- **Dos estimadores independientes valen más que uno bueno**, sobre todo si se rompen en sitios
  distintos. El día que uno se calla, el otro tiene la palabra.
- **Un suelo puesto en el pasado envejece.** Si la máquina se degrada de verdad, el indicador
  congelado acaba encendido siempre, y eso es información pero no es una alarma.
- **El umbral no se decide aquí.** Quien mide y quien pone la nota no deberían ser el mismo script.

## Puente metalúrgico

Es exactamente el balance metalúrgico de una planta, con otro nombre. Nadie pone un cubo debajo de
las colas para medir la pérdida: se mide la alimentación, se mide el concentrado, y **la pérdida es
la resta**. La cifra sale de un balance, no de un instrumento apuntando a ella.

Y las dos limitaciones de este módulo se reconocen igual de rápido en una planta.

La primera es la censura. Si una celda desborda, el medidor de nivel marca su tope, y a partir de
ahí todos los desbordes se parecen aunque uno sea el doble del otro.

La segunda es la referencia. Un balance contra la campaña de arranque dice cuánto ha envejecido el
circuito; contra la semana pasada dice qué se rompió ayer. Nadie discute cuál es el bueno, porque
se llevan los dos.

## Repaso

### De dónde sale el residual, si no se simula nada

De la conservación del aire. El compresor mete `entrega` bar/min mientras carga, así que en régimen
el aire que se gasta es `carga × entrega`. Restarle el consumo de la máquina sana deja lo que se
gasta de más, en bar por minuto. El simulador da lo mismo en régimen y por eso aquí no se usa.

### Por qué el residual se mide por horas y no por días

Porque una avería que empieza a las 23:30 se reparte entre veinticuatro horas si se promedia el día
entero. La #1b pasa de valer 7,47 veces el suelo por horas a 1,09 por días, o sea de una detección
clara a una moneda al aire.

### Qué quiere decir que el residual esté censurado

Que tiene un tope físico, `llena` = 1,1796, al que llega cuando el compresor carga el 100 % del
tiempo. A partir de ahí la fuga puede seguir creciendo y el número no se mueve. 156 horas del
registro están ahí, y tres de los cuatro días de parte marcan ese mismo máximo.

### Para qué sirve la segunda ruta si ya hay una

Porque se rompen en sitios distintos. La pendiente de vaciado no está censurada, así que el 15 de
julio pudo decir 0,349 bar/min donde la primera se topaba. A cambio necesita tramos de vacío que
medir, y el 18 de abril no hubo ninguno. Un instrumento que a veces se calla no es inútil: es un
instrumento con rango.

### Por qué se lee el mismo residual de dos formas

Porque contestan a dos preguntas y las dos hacen falta. Contra febrero dice cuánto se ha alejado la
máquina de cuando estaba bien, que es lo que quiere saber quien decide si se cambia. Contra los
catorce días anteriores dice qué ha pasado esta semana, que es lo que quiere saber quien lleva un
turno. El gemelo no se recalibra en ninguno de los dos casos.

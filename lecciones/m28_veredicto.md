---
module: 28
---

## En 30 segundos

- **4 de 4 contra 2 de 4**: las averías que pilla el gemelo, y las que pilla la alarma instalada.
- Y lo hace despertando a alguien **1,5 veces al mes** contra las 11,4 de la instalada.
- Como **detector** gana. Como **predictor** no: solo avisa antes en una de las cuatro, y un día.
- Encuentra además los doce días de marzo que nadie documentó, y eso va en las dos cuentas.
- Y una incómoda, comprobada y no supuesta: **ordena los días igual que un umbral sobre la carga**.

## Qué resuelve este módulo

Aquí se cobra o no se cobra. Cinco módulos construyendo un gemelo, y la pregunta que queda es si
sirve para algo que no sirviera antes.

Y hay tres formas de contestar esa pregunta haciendo trampa, así que conviene decir cómo se evitan
las tres antes de enseñar ningún número.

**La primera es corregirse el propio examen.** El módulo 27 midió el residual y **se negó a elegir
un umbral**. Así, quien mide y quien pone la nota no son el mismo script. Aquí el umbral se barre
entero, de 0,10 a 1,20, y los números se publican para el barrido completo.

**La segunda es llamar aviso a una alarma que ya estaba puesta.** Si la alarma saltó doce días
antes del parte, eso son doce días de antelación solo si alguien habría hecho algo. Si llevaba dos
meses encendida, no vale nada. Por eso cada antelación viene con **cuánto llevaba sonando la
racha** a la que pertenece.

**Y la tercera es competir contra nadie.** Se compara contra dos rivales: un umbral corriente sobre
el ciclo de trabajo, y **la alarma de baja presión que este compresor ya tiene instalada**.

## Antes de la teoría: un ejemplo de juguete

Un detector de humo en una cocina. En un año hay **2 incendios** y el detector suena **50 veces**.

| | Suena | No suena |
|---|---|---|
| Hay incendio | 2 | 0 |
| No hay incendio | 48 | 313 |

Pilla los dos incendios: como detector es perfecto. Y suena **48 veces sin motivo**, casi una por
semana, así que a la tercera alguien le quita la pila y el detector deja de existir.

**Las dos cifras van siempre juntas.** Un detector que lo pilla todo es fácil: se pone el umbral en
cero y ya está. Un detector que no molesta nunca es igual de fácil. La pregunta es dónde queda la
pareja, y contra qué pareja se compara.

## Glosario

- **Detector.** Se juzga por si se entera de la avería mientras está pasando.
- **Predictor.** Se juzga por si avisa **antes**. Son dos notas distintas y este módulo pone las dos.
- **Falsa alarma.** Un día en que salta y no había nada. Aquí se cuentan por mes, que es la unidad
  en la que las sufre quien está de guardia.
- **Racha.** Días de alarma seguidos. Hace falta para no confundir un aviso con una alarma que ya
  llevaba puesta media semana.
- **Barrido.** Probar todos los umbrales y publicar la curva entera, en vez de elegir uno y enseñar
  solo lo que sale bien con él.

## Paso a paso

### Paso 1. Decidir qué cuenta como acierto

Un parte de avería cubre unos días. Si la alarma salta en alguno de ellos, ese parte está detectado.
Los cuatro partes cubren **7 días** entre todos.

### Paso 2. Decidir qué cuenta como aviso, que es más difícil

No basta con que la alarma esté puesta antes del parte. Hay que mirar **cuándo se encendió la racha**
que llega hasta él. Si se encendió el día anterior, es un aviso de un día. Si llevaba tres semanas,
no es un aviso: es ruido de fondo que resultó incluir la fecha.

### Paso 3. Barrer el umbral, no elegirlo

Veintitrés umbrales, de 0,10 a 1,20 bar/min. El de abajo está justo encima del suelo de ruido que
midió el módulo 27; por debajo, la alarma sonaría en febrero.

### Paso 4. Buscarse rivales de verdad

Uno trivial, para ver si el gemelo aporta algo. Y uno instalado, para ver si aporta algo **más
que lo que ya había**.

## El código, por partes

### Paso 5. La racha, que es lo que impide inflar la antelación

```python
for ini, fin in rachas:
    if ini < suceso.date() <= fin + timedelta(days=1):
        antes = (suceso.date() - ini).days
        largo = (fin - ini).days + 1
```

```anota
rachas | los días de alarma agrupados en tiradas seguidas, no sueltos
antes | los días desde que se encendió la racha hasta el parte. Eso es la antelación de verdad
largo | y cuánto duró la racha entera, que es contra lo que hay que leer la antelación
```

### Paso 6. El rival trivial se comprueba, no se afirma

```python
por_residual = sorted(dias, key=lambda f: -f.pico)
por_carga = sorted(dias, key=lambda f: -f.carga)
mismo_orden = por_residual == por_carga
```

```anota
sorted(...) | los mismos días, ordenados por el residual y por el ciclo de trabajo
== | si las dos listas son idénticas, cualquier umbral de una tiene su gemelo exacto en la otra
mismo_orden | es la afirmación más incómoda de la lección, y una afirmación incómoda sin comprobar es una excusa
```

### Paso 7. Toca la perilla

```perilla
m28_umbral
```

La perilla arranca en el umbral que el barrido eligió. Bájalo y mira cómo el trazo se despega de
la línea de puntos. Esa línea son los días con avería de verdad, y todo lo que sobra por encima son
noches de guardia gastadas en nada.

## El resultado, medido

{{FIG:fig_m28_cuatro_averias}}

**Qué esperábamos.** Que el gemelo detectara las cuatro y avisara con algo de antelación.

**Qué salió.** Lo primero sí, y bien. Lo segundo no.

```salida
  el suelo de ruido del módulo 27 está en 0.1165, y de ahí para arriba se barre el umbral
  el registro abarca 8 meses, y ese es el divisor de todos
  los cuatro partes cubren 7 días

  congelado, marzo cuenta
    umbral | detecta | avisa antes | antelación | falsas/mes
       0.1 |  5 de 5 |           2 |       10 d |       15.6
       0.3 |  5 de 5 |           1 |        1 d |        3.6
       0.5 |  5 de 5 |           1 |        1 d |        2.9
       0.7 |  5 de 5 |           1 |        1 d |        2.2
       0.9 |  5 de 5 |           1 |        1 d |        1.9
       1.1 |  5 de 5 |           0 |          - |        1.2
```

### Como detector: gana, y le gana a lo que ya había

El umbral más alto que todavía las pilla todas es **1,15 bar/min**. Ahí el gemelo:

| | El gemelo | La alarma instalada |
|---|---|---|
| Averías detectadas | **4 de 4** | 2 de 4 |
| Días con alarma | 18 | 94 |
| Falsas alarmas al mes | **1,5** | 11,4 |

**El doble de averías con una séptima parte de las falsas alarmas.** En la figura del intercambio, la
cruz naranja queda abajo y muy a la derecha de la curva: peor en las dos cosas a la vez.

**Y ahora el matiz, que es obligatorio.** La LPS no es un detector de fugas al que el gemelo le haya
ganado en su terreno. Es una alarma de baja presión, y salta sobre todo **cuando el registro vuelve
después de un corte**, con el depósito vacío y el compresor recuperando. De sus 136 horas con la
alarma puesta, 101 caen en horas incompletas de registro.

Así que la comparación honesta no es «el gemelo detecta mejor que la LPS». Es esta otra, la que le
importa a una planta: **lo único instalado en esta máquina suena un tercio de los días y aun así se
pierde la mitad de las averías**. Un gemelo hecho con cuatro números medidos lo mejora en las dos
cosas. Que el rival estuviera contestando a otra pregunta forma parte del problema, no de la
excusa.

**Un apunte de método, porque cambió el resultado.** Esas 94 días salen de contar la LPS sobre las
lecturas crudas. La primera versión la contaba sobre las mismas horas completas que usa el gemelo, y
salían 28 días y 3,1 falsas al mes. El filtro de horas completas existe porque un ciclo de trabajo
sacado de treinta lecturas no es el de esa hora, pero **la LPS no promedia nada**: salta o no salta.
Aplicarle una regla pensada para el gemelo le quitaba tres cuartas partes de sus disparos y la
dejaba mejor de lo que es. Ganar una comparación por el reglamento es la forma más silenciosa de
hacer trampa.

{{FIG:fig_m28_antelacion_vs_falsas}}

Y fíjate en la forma de esa curva, porque dice algo que no esperaba: **es un acantilado, no una
pendiente**. Bajar el umbral por debajo de 1,15 no compra ni una avería más y sí compra falsas
alarmas, hasta 17 al mes en el extremo. El intercambio clásico entre sensibilidad y molestia aquí
no existe, porque las cuatro averías llevan el residual al techo.

### Como predictor: no

De las cuatro, **solo una avisa antes**: la del 15 de julio, con **un día**, y en una racha que duró
dos días en total. Las otras tres levantan la alarma **el mismo día del parte**.

En los cinco paneles de la lupa se ve igual: la curva sube justo en la banda sombreada, no antes.
El temario de este curso prometía «días de antelación», y **los datos no los dan**. Así que el
módulo publica las dos notas por separado y no promedia una con otra.

Hay una razón física para que sea así, y no es consuelo: una fuga de aire en un sistema neumático no
crece despacio durante días. Se abre. El compresor pasa de trabajar el 6 % del tiempo a trabajar el
100 % en unas horas, y no hay rampa que ver por adelantado.

### Y la detección llega tarde

Conviene decirlo aunque estropee el titular. El umbral que consigue el 4 de 4 es **1,15**, y el
techo del residual está en **1,1796**. O sea que la alarma salta cuando el compresor va
prácticamente a tope. Eso no es sutileza, es constatar un desastre en curso.

Con umbrales más bajos la alarma se adelanta un poco y las falsas se disparan. La razón es la
deriva del módulo 27: la máquina se degrada de verdad y el gemelo lo nota. Está en la tabla, y cada
cual pone el umbral donde le duela menos.

### Los doce días de marzo, en las dos cuentas

El módulo 26 encontró que del 1 al 12 de marzo la máquina estaba averiada sin que ningún parte lo
recogiera. Contarlo como acierto es creerse el propio modelo; no contarlo es tirar la mejor prueba
que hay a favor del gemelo. Así que van las dos cuentas:

| Con umbral 1,15 | Detecta | Falsas al mes |
|---|---|---|
| Marzo cuenta como avería | **5 de 5** | **1,2** |
| Marzo cuenta como falsa alarma | **4 de 4** | **1,5** |

**La diferencia entre las dos filas es lo que cuesta una etiqueta que falta.** Doce días de
máquina enferma sin apuntar mueven el resultado de este proyecto. En cualquier planta pasa igual: el
modelo se juzga contra un registro de averías, y ese registro también es un dato con sus huecos.

### Lo incómodo, dicho entero

Con los parámetros congelados,

```
residual = carga × entrega − consumo
```

es una función creciente de la carga y nada más. Así que **un umbral sobre el residual y otro
sobre el ciclo de trabajo ordenan los días exactamente igual**. Y esto no es un razonamiento: el
script lo comprueba sobre los **207** días del registro y da que sí.

Dicho de otro modo: **cualquier cosa que este gemelo detecte, la detecta también contar cuánto
trabaja el compresor**, que es una consulta de SQL de tres líneas y ningún modelo.

Entonces, ¿para qué el gemelo? Para tres cosas que el umbral no da, y ninguna de ellas es detectar:

1. **Unidades.** El gemelo dice «se están fugando 0,35 bar por minuto», no «el índice está en 0,73».
   Eso se lleva a una reunión de mantenimiento y se discute.
2. **No necesita historial.** El umbral hay que aprenderlo de averías pasadas. Los parámetros del
   gemelo se miden en un mes sano, sin una sola avería dentro, como se hizo en el módulo 24.
3. **Contesta preguntas que no han pasado.** Cuánto tendría que fugar para que saltara, cuánto
   aguantaría el depósito con media planta parada. La perilla del módulo 27 es exactamente eso.

**Qué significa.** El gemelo sirve, le gana a la alarma instalada, y no vale para lo que más se
vende de él. Un proyecto con solo la primera mitad de esa frase sería más bonito y menos cierto.

## Hazlo tú

```reto
pregunta: Reproduce el veredicto en una consulta. Saca el residual máximo de cada día (`carga * 1.2507 - 0.0711`, saltando las horas de menos de 300 lecturas), clasifica cada día en `con parte` o `sin parte` según esté o no en los siete días que cubren los cuatro partes, y cuenta cuántos días hay de cada clase y cuántos pasan del umbral de 1,15. Devuelve `clase`, `dias` y `saltan`. Dos filas.
inicio: SELECT hora::DATE AS dia,
       max(carga * 1.2507 - 0.0711) AS residual
FROM horas
WHERE lecturas >= 300
GROUP BY 1;
esperado: m28_aciertos_y_falsas
pista: El punto de partida ya da un día por fila. Envuélvelo en un `WITH` y encima clasifica con un `CASE WHEN dia IN (...)`. Los siete días son el 18 de abril, el 29 y 30 de mayo, el 5, 6 y 7 de junio, y el 15 de julio. Para contar los que pasan del umbral, `count(*) FILTER (WHERE residual > 1.15)`.
solucion: WITH d AS (
  SELECT hora::DATE AS dia,
         max(carga * 1.2507 - 0.0711) AS residual
  FROM horas WHERE lecturas >= 300 GROUP BY 1
)
SELECT CASE WHEN dia IN (DATE '2020-04-18', DATE '2020-05-29',
                         DATE '2020-05-30', DATE '2020-06-05',
                         DATE '2020-06-06', DATE '2020-06-07',
                         DATE '2020-07-15') THEN 'con parte'
            ELSE 'sin parte' END AS clase,
       count(*)                               AS dias,
       count(*) FILTER (WHERE residual > 1.15) AS saltan
FROM d GROUP BY 1 ORDER BY 1;
```

De los **7** días con parte saltan **6**, y de los **200** sin parte saltan **12**.

Y ahí hay una lección escondida: **6 de 7 días no es lo mismo que 4 de 4 averías**. El día que falta
es uno de los que cubre un parte largo, y el parte sigue detectado porque saltó en otro de sus días.
Contar días y contar averías dan notas distintas, y hay que decir cuál se está contando.

## Ojo

- **Detector y predictor son dos notas.** Aquí una es buena y la otra no. Publicar solo la media
  sería esconder la mala detrás de la buena.
- **Una antelación sin la duración de la racha no dice nada.** Doce días de aviso con una alarma que
  llevaba cuarenta días encendida son cero días de aviso.
- **Compara contra lo que ya está instalado**, no contra nada. Un detector que no le gana a la
  alarma que la máquina trae de fábrica no se instala.
- **Comprueba el rival trivial.** Si un umbral corriente ordena los días igual que tu modelo, tu
  modelo no gana en detección y hay que decir en qué gana.
- **Cuatro averías no son una muestra.** Es un estudio de cuatro casos y así se presenta: con cuatro
  eventos, un acierto más o menos cambia el resultado entero.
- **El registro de averías también es un dato, y tiene huecos.** Doce días de máquina enferma sin
  parte estaban ahí desde el principio.
- **Un umbral que solo salta con el compresor a tope detecta desastres, no avisa de ellos.**

## Puente metalúrgico

Cualquiera que haya puesto una alarma de ley en colas conoce esta tabla entera. Se pone el umbral
apretado y la sala de control lo silencia a la semana; se pone flojo y no avisa del vuelco que
importaba. Y la conversación siempre acaba igual: no en qué umbral es el correcto, sino en cuántas
veces por turno está dispuesto el operador a levantarse.

El otro paralelo es el del registro de paradas. El modelo se valida contra el libro de
mantenimiento, y ese libro lo escribe gente con prisa a las tres de la mañana. Las paradas cortas no
se apuntan, las causas se copian de la anterior, y un turno entero puede quedar en blanco. Cuando el
modelo marca un día que el libro no recoge, la primera reacción es que el modelo se equivoca. A
veces es al revés, y aquí lo fue durante doce días de marzo.

## Repaso

### Qué contesta exactamente este módulo

Si el gemelo detecta las cuatro averías documentadas, con cuántas falsas alarmas, con cuánta
antelación, y si eso es mejor que la alarma que la máquina ya lleva puesta. Cuatro preguntas y
cuatro respuestas separadas, sin promediarlas en una nota global.

### Por qué el gemelo gana como detector y pierde como predictor

Porque una fuga de aire no crece despacio. El compresor pasa del 6 % al 100 % de carga en unas
horas, así que cuando hay algo que ver ya es enorme y cuando no lo hay no hay nada. Detectar es
fácil; anticipar exigiría una señal que se moviera antes, y en este registro no la hay.

### Por qué la antelación se mide con la racha y no con la fecha

Porque una alarma encendida desde hace semanas incluye por fuerza el día del parte, y presentarlo
como antelación sería contar como mérito un ruido de fondo. Midiendo desde que se encendió la racha,
solo una de las cuatro avisa, y avisa un día.

### Si un umbral sobre el ciclo de trabajo hace lo mismo, para qué el gemelo

Para lo que el umbral no hace. Da la fuga en bar por minuto y no en un índice sin unidades. Se
calibra con un mes sano, sin historial de averías. Y admite preguntas sobre una fuga que todavía no
ha pasado. En detección pura no gana, y el módulo lo comprueba en vez de suponerlo.

### Qué habría que hacer para que este gemelo predijera

Cambiar de señal. El ciclo de trabajo salta con la fuga ya abierta. Haría falta algo que se mueva
antes: la temperatura del aceite, la corriente de arranque, o la firma de las válvulas dentro de un
ciclo. Este proyecto no lo promete ni lo entrega, y decirlo es parte del entregable.

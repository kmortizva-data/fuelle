---
module: 23
---

## En 30 segundos

- Un gemelo digital no es un dibujo en tres dimensiones ni un panel bonito.
- Es **un modelo que corre en paralelo a la máquina**, y su desacuerdo significa algo.
- Ese desacuerdo se llama **residual**, y es lo único que un gemelo entrega.
- Entre los días sanos el gemelo no se separa más de **14,0 minutos** de la máquina.
- El 18 de abril se separa **1.335,7**, que es **95 veces** ese peor caso sano.

## Qué resuelve este módulo

Con «gemelo digital» se venden cosas muy distintas. Una maqueta que gira. Un panel con la foto del
equipo y unos números encima. Un modelo entrenado con seis meses de datos que predice una avería.

Ninguna de las tres es lo que este proyecto va a construir, y conviene decirlo antes de construirlo.

Un gemelo, aquí, es **un modelo de la física de la máquina que corre a la vez que ella, con las
mismas entradas**. Y lo que se mira no es lo que predice: es **en qué se diferencia de la realidad**.

## Antes de la teoría: un ejemplo de juguete

Dos hornos idénticos, uno al lado del otro, con la misma carga y el mismo gas.

| Hora | Horno A | Horno B |
|---|---|---|
| 08:00 | 900 °C | 900 °C |
| 10:00 | 920 °C | 918 °C |
| 12:00 | 915 °C | 870 °C |
| 14:00 | 918 °C | 845 °C |

Nadie necesita saber de hornos para ver que el B tiene un problema desde el mediodía. **Y no hace
falta saber cuál es la temperatura correcta**: basta con que haya otro horno igual al lado.

Eso es un gemelo, y su valor está justo ahí. No dice «910 grados es lo normal», una regla con
dueño y con fecha de caducidad. Dice **«estos dos deberían coincidir y no coinciden»**.

La diferencia entre las dos columnas es el residual. Cuando vale cero, no hay noticia. Cuando se
abre, la hay.

Y ahora la parte que hace útil todo esto. **En una planta no tienes dos hornos.** Tienes uno, así
que el segundo hay que fabricarlo, y para eso sirve un modelo: es el horno B.

## Glosario

- **Gemelo digital.** Un modelo de una máquina que corre con sus mismas entradas, en paralelo a
  ella, para poder comparar.
- **Residual.** La diferencia entre lo que hace la máquina y lo que hace el modelo.
- **Variable controlada.** La que un lazo de control mantiene donde quiere. Aquí, la presión.
- **Variable manipulada.** Lo que el control mueve para conseguirlo. Aquí, cuánto trabaja el
  compresor.
- **Primeros principios.** Un modelo hecho de física conocida, no de datos ajustados. El de este
  curso lo es.
- **Falsa alarma.** Un aviso sin avería detrás. Es la moneda con la que se paga la sensibilidad.

## Paso a paso

### Paso 1. Decidir qué tiene que acertar

Un gemelo no reproduce la máquina entera, y querer eso es la forma más rápida de no terminar
ninguno. Reproduce **una cosa**, y aquí es el **ciclo de trabajo**: cuánto tiempo pasa el compresor
cargando.

### Paso 2. Y decidir qué NO va a mirar

La presión, porque el control la sostiene. En un compresor con fuga la presión sigue donde debe, y
lo que cambia es **cuánto hay que trabajar para sostenerla**.

Esto no es una teoría de este curso, está medido. En la página de pruebas de este proyecto, al
mover una fuga simulada de 5 a 40 litros por minuto, **las dos curvas de presión se separaban 32
píxeles y luego 31**. Nada. Las de trabajo acumulado se separaban de 15 a 51.

### Paso 3. Correr el modelo con lo que sabía de antes

El gemelo se calibra con un periodo sano y después **no se toca**. Va a ver días de avería con los
parámetros de cuando todo iba bien, y por eso se queda corto: no sabe que hay una fuga.

### Paso 4. Mirar el hueco, no la predicción

Si el gemelo acierta, no hay noticia. Si falla, hay una noticia y el tamaño del fallo es la noticia.
Ese es el cambio de mentalidad de este módulo: **un modelo cuyo error es el producto**.

## El código, por partes

### Paso 5. Todo el gemelo, otra vez

```python
if cargando:
    p += (entrega - consumo) * paso
    if p >= para: cargando = False
else:
    p -= consumo * paso
    if p <= arranca: cargando = True
```

```anota
entrega - consumo | lo que sube el depósito por minuto cargando. Los cuatro números salen del lago en el módulo 24, ninguno inventado
p >= para | el presostato suelta arriba y vuelve a pedir carga al bajar a `arranca`. No hay temperatura, ni geometría, ni datos ajustados
```

No hay más. Ese es el gemelo entero, y los módulos 24 y 25 son de dónde salen sus cuatro números y
cómo se le hace correr sin romperlo.

### Paso 6. Y el residual

```python
residual = minutos_que_carga_la_maquina - minutos_que_carga_el_gemelo
```

```anota
residual | eso es todo. Un gemelo no entrega una predicción, entrega una diferencia
minutos_que_carga_la_maquina | la unidad importa: son minutos de compresor, algo que un jefe de mantenimiento entiende
```

```salida
  día sano   : la máquina 80.8 min, el gemelo 80.5, hueco 0.3
  los 7 días sanos completos van de 66.5 a 90.0 min, y el hueco mayor entre ellos es 14.0
  18 de abril: la máquina 1416.2 min, el gemelo 80.5, hueco 1335.7
  el hueco de la avería es 95,4 veces el mayor de los días sanos
```

## El resultado, medido

{{FIG:fig_m23_gemelo_y_residual}}

**Qué esperábamos.** Que el gemelo siguiera a la máquina en un día sano y se quedara corto en uno
de avería.

**Qué salió.** Exactamente eso, y con una distancia entre los dos casos que no deja lugar a dudas.

En un día sano y completo, el 18 de febrero, la máquina cargó **80,8** minutos y el gemelo predijo
**80,5**. Se llevan menos de veinte segundos.

Ese acuerdo es demasiado bonito para creérselo, y hay que decir por qué. El gemelo predice lo
mismo todos los días, y el 18 de febrero es **el día más cercano a la mediana** de los días sanos.
O sea que se está comparando la costumbre contra el día que más se parece a la costumbre. Con
cualquier otro día saldría peor, y eso es exactamente lo que hay que medir.

**Así que el listón no sale de un día, sale de todos.** En la ventana sana hay **siete** días con
sus 8.640 lecturas completas, y la máquina cargó entre **66,5** y **90,0** minutos en ellos. Contra
la predicción única del gemelo, el peor de esos días se va **14,0 minutos**.

El 18 de abril, la primera avería documentada, la máquina cargó **1.416,2** minutos, o sea casi el
día entero. El gemelo, que sigue sin saber nada, predijo los mismos **80,5** de siempre.

| | Los siete días sanos | El 18 de abril |
|---|---|---|
| La máquina | de 66,5 a 90,0 min | **1.416,2 min** |
| El gemelo | 80,5 min | 80,5 min |
| El hueco | hasta 14,0 min | **1.335,7 min** |

**95 veces el peor día sano.** Ese cociente es el que hace funcionar la idea. Y está medido contra
el peor caso, no contra el mejor. Para poner un aviso es lo único que vale: una alarma no
tiene que superar el día tranquilo, sino el día sano más raro.

**Qué significa.** Que hay margen. Un gemelo que puede fallar 14 minutos no sirve para decir
cuántos minutos exactos cargará mañana el compresor, y **no hace falta que sirva para eso**. Sirve
para notar algo noventa y cinco veces mayor que su peor error.

Lo que queda por delante es de ingeniería, no de concepto. Comprobar si buscando los parámetros en
vez de medirlos se afina algo, en el módulo 26. Decidir a partir de qué hueco se avisa, en el 27. Y
comprobar contra las cuatro averías si el aviso llega a tiempo y sin despertar a nadie por nada, en
el 28.

## Ojo

- **Un gemelo no es una predicción, es una comparación.** Si te lo venden por lo bien que acierta,
  te están vendiendo otra cosa.
- **No mires la variable controlada.** El control la sostiene, así que ahí no hay señal. Está
  medido en este proyecto: 32 píxeles contra 31 al cuadruplicar la fuga.
- **El gemelo no se recalibra con los datos de la avería.** Si se le deja aprender del periodo
  malo, deja de extrañarse y el residual desaparece. Se calibra con lo sano y se congela.
- **Un residual grande no dice qué pasa.** Dice que algo pasa. Distinguir una fuga de un filtro
  sucio es otro trabajo, y este proyecto no lo promete.
- **Con cuatro averías no hay estadística.** Lo que va a haber en el módulo 28 es un estudio de
  cuatro casos, y así se dirá.
- **Un día sano no es un suelo de ruido.** Si mides el error del gemelo contra un solo día, y
  encima contra el que más se parece a la media, te sale un error de doce segundos y un cociente
  de miles. Eso no es precisión, es haber dividido por casi cero. El suelo sale del reparto.
- **Y la ventana sana hay que mirarla, no solo elegirla por fecha.** La de este curso iba hasta el
  15 de marzo, escogida antes de la primera avería documentada precisamente para no elegir a
  conveniencia. Llevaba doce días de avería dentro que nadie había documentado. El módulo 26
  cuenta cómo apareció.

## Puente metalúrgico

Cualquier planta lleva un balance metalúrgico teórico al lado del real. No porque el teórico sea
más cierto, sino para restarlos.

Supón una recuperación medida del 88 % y un modelo que, con esa ley de cabeza y esa granulometría,
esperaba 91. Esos tres puntos de diferencia **son el trabajo del metalurgista de esa semana**.
Puede ser una celda con la espuma caída, un reactivo dosificando mal o un muestreo sesgado, pero
nadie los habría mirado sin el modelo al lado.

Y fíjate en que a nadie le importa si el modelo clava el 91. Importa que sea **el mismo modelo todas
las semanas**, para que un cambio en la diferencia signifique un cambio en la planta.

## Repaso

### Qué es exactamente un gemelo digital, en este proyecto

Un modelo de la física del compresor, con parámetros medidos de un periodo sano. Corre en paralelo
a la máquina y produce una sola cosa: la diferencia entre lo hecho y lo esperado. Esa diferencia es
el residual, y es el producto.

### Por qué el gemelo mira el ciclo de trabajo y no la presión

Porque la presión es la variable controlada y el lazo la sostiene pase lo que pase. Una fuga no
baja la presión, hace que el compresor trabaje más para mantenerla. La señal está en la variable
manipulada, y aquí eso es el tiempo que pasa cargando.

### Por qué el gemelo no se vuelve a calibrar cuando llegan datos nuevos

Porque entonces aprendería la avería y dejaría de extrañarse. El gemelo tiene que seguir
representando la máquina sana; su desacuerdo con la máquina de hoy es precisamente lo que se está
midiendo.

### El gemelo puede equivocarse 14 minutos en un día sano. No es demasiado

Depende de contra qué. Para predecir la carga de mañana sí lo es. Para detectar algo 95 veces mayor
que ese error, no. La pregunta útil no es cuánto se equivoca un modelo, es cuánto se equivoca
comparado con lo que tiene que distinguir.

Y fíjate en de dónde sale ese 14: es el **peor** de los siete días sanos, no el mejor ni el
promedio. Un listón puesto con el mejor caso se cae el primer día raro.

### Qué NO va a poder decir este gemelo

Qué avería es. Un residual grande dice que la máquina trabaja más de lo que debería, y eso puede
ser una fuga, un filtro sucio o una demanda mayor de la planta. Separar esas causas necesitaría más
señales de las que hay, y prometerlo sería vender otra cosa.

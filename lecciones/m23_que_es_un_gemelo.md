---
module: 23
---

## En 30 segundos

- Un gemelo digital no es un dibujo en tres dimensiones ni un panel bonito.
- Es **un modelo que corre en paralelo a la máquina**, y su desacuerdo significa algo.
- Ese desacuerdo se llama **residual**, y es lo único que un gemelo entrega.
- Un día sano el gemelo se lleva **12 minutos** de carga con la máquina. El 18 de abril, **1.264,2**.
- El hueco es **105,4 veces** mayor. Eso es lo que hace falta para que sirva de algo.

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
cuatro números | arranca, para, entrega y consumo. Salen del lago en el módulo 24, ninguno inventado
ni una línea más | no hay temperatura, ni geometría, ni datos ajustados. Es física de primeros principios
```

No hay más. Ese es el gemelo entero, y los módulos 24 y 25 son de dónde salen sus cuatro números y
cómo se le hace correr sin romperlo.

### Paso 6. Y el residual

```python
residual = minutos_que_carga_la_maquina - minutos_que_carga_el_gemelo
```

```anota
la resta | eso es todo. Un gemelo no entrega una predicción, entrega una diferencia
en minutos | la unidad importa: son minutos de compresor, algo que un jefe de mantenimiento entiende
```

```salida
  día sano   : la máquina 140.0 min, el gemelo 152.0, hueco -12.0
  18 de abril: la máquina 1416.2 min, el gemelo 152.0, hueco 1264.2
  el hueco es 105,4 veces mayor
```

## El resultado, medido

{{FIG:fig_m23_gemelo_y_residual}}

**Qué esperábamos.** Que el gemelo siguiera a la máquina en un día sano y se quedara corto en uno
de avería.

**Qué salió.** Exactamente eso, y con una distancia entre los dos casos que no deja lugar a dudas.

En un día sano y completo, el 8 de marzo, la máquina cargó **140,0** minutos y el gemelo predijo
**152,0**. Se lleva **12 minutos**, un 8,6 %, y se los lleva **de más**: el gemelo cree que la
máquina trabajará algo más de lo que trabajó.

El 18 de abril, la primera avería documentada, la máquina cargó **1.416,2** minutos, o sea casi el
día entero. El gemelo, que sigue sin saber nada, predijo los mismos **152,0** de siempre.

| | Un día sano | El 18 de abril |
|---|---|---|
| La máquina | 140,0 min | **1.416,2 min** |
| El gemelo | 152,0 min | 152,0 min |
| El hueco | −12,0 min | **1.264,2 min** |

**105,4 veces más hueco.** Ese cociente es el que hace funcionar la idea: en condiciones normales
el error del gemelo queda dos órdenes de magnitud por debajo de la señal a detectar.

**Qué significa.** Que hay margen. Un gemelo con un 8,6 % de error no sirve para decir cuántos
minutos exactos cargará mañana el compresor, y **no hace falta que sirva para eso**. Sirve para
notar algo que es cien veces mayor que su propio error.

Lo que queda por delante es de ingeniería, no de concepto. **Bajar ese 8,6 %** en el módulo 26.
Decidir a partir de qué hueco se avisa, en el 27. Y comprobar contra las cuatro averías si el aviso
llega a tiempo y sin despertar a nadie por nada, en el 28.

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
- **Un gemelo se puede equivocar en la dirección cómoda.** Aquí predice de más en día sano, o sea
  que tiende a no avisar. Conviene saberlo antes de poner un umbral.

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

### El gemelo se equivoca un 8,6 % en un día sano. No es demasiado

Depende de contra qué. Para predecir la carga de mañana sí lo es. Para detectar algo 105 veces
mayor que ese error, no. La pregunta útil no es cuánto se equivoca un modelo, es cuánto se equivoca
comparado con lo que tiene que distinguir.

### Qué NO va a poder decir este gemelo

Qué avería es. Un residual grande dice que la máquina trabaja más de lo que debería, y eso puede
ser una fuga, un filtro sucio o una demanda mayor de la planta. Separar esas causas necesitaría más
señales de las que hay, y prometerlo sería vender otra cosa.

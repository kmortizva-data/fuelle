---
module: 26
---

## En 30 segundos

- Los parámetros de un modelo se pueden **medir** o se pueden **buscar**. El módulo 24 los midió.
- Aquí se buscan, y no para mejorarlos: para ver si buscando se llega al mismo sitio.
- Buscando con el ciclo de trabajo solo **no sale una respuesta, sale un valle**: entregas de 0,72
  a 1,08 puntúan igual de bien.
- Hace falta un segundo observable. Con los arranques por hora los dos valles se cruzan en un punto.
- Ahí el ajuste dice **1,27 bar/min** y la medida decía **1,1796**: **1,18 contra 1,27**.

## Qué resuelve este módulo

Calibrar suena a mejorar. En la mayoría de los proyectos lo es: se coge un modelo con perillas, se
mueven hasta que la curva encaja, y se publica lo bien que encaja.

Este módulo hace lo contrario, y conviene decir por qué antes de empezar. **Los dos parámetros del
gemelo ya están medidos**, uno a uno, con un balance de aire que cuadra. Buscarlos por ajuste no
puede mejorar un modelo que no tiene perillas sueltas. Lo que sí puede hacer es contestar a una
pregunta que vale más: **¿los dos caminos llevan al mismo sitio?**

Si llevan, los parámetros significan algo. Son la velocidad a la que este compresor llena su
depósito y el aire que gasta este tren, y da igual cómo los consigas. Si no llevan, uno de los dos
está mal, y hay que averiguar cuál antes de seguir.

Salieron a un **7,8 %** el uno del otro. Y en el camino, el ajuste destapó dos fallos que la
medida no había visto.

## Antes de la teoría: un ejemplo de juguete

Un depósito con un flotador. Se llena, y cuando llega arriba una válvula lo suelta hasta que baja
diez litros, y vuelta a empezar. Dos técnicos lo miran.

El primero dice: **entra a 10 litros por minuto y sale a 1**.
El segundo dice: **entra a 20 y sale a 2**.

Están en desacuerdo por un factor de dos. Comprueba cuánto tiempo pasa llenándose cada uno:

| | Entra | Sale | Sube 10 l en | Baja 10 l en | Ciclo | Fracción llenando |
|---|---|---|---|---|---|---|
| El primero | 10 l/min | 1 l/min | 1,11 min | 10 min | 11,1 min | **1 de 11** |
| El segundo | 20 l/min | 2 l/min | 0,56 min | 5 min | 5,6 min | **1 de 11** |

**La misma fracción.** Con un cronómetro que solo mire cuánto tiempo está la bomba encendida, los
dos técnicos aciertan y no hay forma de decidir. Y no es que uno de los dos tenga razón: es que
esa medida **no distingue** entre ellos.

Ahora cuenta las veces que arranca en una hora. El primero, 5 veces. El segundo, casi 11. **Ahí sí
se separan**, porque el reloj de la pared no se deja engañar por un cociente.

Eso es todo este módulo. Una medida que solo ve el cociente, otra que ve la escala, y hacen falta
las dos.

## Glosario

- **Calibrar.** Poner los parámetros de un modelo en su valor. Aquí, buscarlos por ajuste para
  comprobar los que ya se midieron.
- **Observable.** Algo que la máquina hace y que se puede contar en el registro. Aquí hay dos: el
  ciclo de trabajo y los arranques por hora.
- **Superficie de error.** Lo mal que lo hace cada combinación de parámetros, dibujada sobre todas
  las combinaciones probadas.
- **Valle.** Cuando esa superficie no tiene un fondo sino un surco: muchas combinaciones puntúan
  igual y el ajuste no tiene forma de preferir una.
- **Identificable.** Un parámetro lo es cuando los datos que tienes bastan para fijarlo. Si no, el
  número que salga viene de la rejilla o del punto de partida, no de la máquina.
- **Rejilla.** Probar todas las combinaciones de una lista, en vez de dejar que un optimizador
  busque. Es lento y torpe, y a cambio **enseña la superficie entera**, que es lo que hace falta
  aquí.

## Paso a paso

### Paso 1. Decidir qué se busca, y en qué rejilla

Dos parámetros: la entrega del compresor y el consumo de la planta. Se prueban 33 entregas por 31
consumos, **1.023 combinaciones**, alrededor de lo que midió el módulo 24 y con sitio de sobra a
los lados.

Rejilla y no optimizador, a propósito. Un optimizador devuelve un punto y se calla; lo que hay que
ver aquí es la forma de la superficie.

### Paso 2. Decidir contra qué se compara

Un ajuste necesita algo que la máquina hizo. La primera opción es la obvia: **el ciclo de trabajo**,
que es lo que el gemelo existe para reproducir.

### Paso 3. Descubrir que con eso solo no basta

Y aquí está el módulo. En régimen, el ciclo de trabajo de un depósito con histéresis vale

```
carga = consumo / entrega
```

o sea que **depende solo del cociente**. Duplica los dos y no se mueve. Así que ajustar contra el
ciclo de trabajo no puede devolver dos números: devuelve una relación entre ellos.

### Paso 4. Añadir el segundo observable

El tiempo que tarda un ciclo entero es `banda / llena` para subir más `banda / consumo` para bajar,
y eso **sí** cambia cuando los dos parámetros se escalan a la vez. Contar arranques por hora es
gratis, está en el mismo registro, y es lo que fija la escala.

## El código, por partes

### Paso 5. El error de un punto de la rejilla

```python
carga, arranques = resumen(dep)
e_carga = abs(carga - obs["carga"]) / obs["carga"]
e_arr = abs(arranques - obs["arranques_por_hora"]) / obs["arranques_por_hora"]
error = (e_carga if pesa_carga else 0) + (e_arr if pesa_arranques else 0)
```

```anota
resumen(dep) | simula doce horas con esos parámetros y devuelve las dos cosas que se pueden comparar
/ obs[...] | dividir por lo observado. Una es una fracción y la otra son sucesos por hora: sin dividir, la de números más grandes mandaría
pesa_carga, pesa_arranques | los dos interruptores que hacen los tres ajustes del módulo con un solo bucle
```

### Paso 6. El guardián del borde, y por qué no vale para todos

```python
if ganador["entrega"] in (ENTREGAS[0], ENTREGAS[-1]) or \
        ganador["consumo"] in (CONSUMOS[0], CONSUMOS[-1]):
    raise SystemExit("El ajuste completo se pega al borde de la rejilla")
```

```anota
ganador | el ajuste completo es el único que debe tener un mínimo de verdad, así que solo a él se le exige
ENTREGAS[0], ENTREGAS[-1] | los dos bordes. Un valle no tiene fondo, así que acaba en uno de ellos le des la rejilla que le des
raise SystemExit | saltó de verdad: la primera rejilla llegaba a 1,200 y el óptimo salió justo ahí. El número lo ponía la rejilla, no la máquina
```

### Paso 7. Toca la perilla

```perilla
m26_valle
```

Mueve la entrega. La perilla mantiene el cociente fijo, o sea que **recorre el valle**. Mira el
trazo: apenas se mueve, porque todos estos pares dan la misma carga. Mira el número de arranques:
se dobla de punta a punta.

Eso es un valle, tocándolo. Y es la razón por la que un ajuste con un solo observable no tiene una
respuesta que dar.

## El resultado, medido

{{FIG:fig_m26_ajuste}}

**Qué esperábamos.** Que la búsqueda cayera donde cayó la medida, y que hiciera falta un solo
observable para conseguirlo.

**Qué salió.** Lo primero sí. Lo segundo no.

```salida
  la máquina, del 2020-02-01 al 2020-02-29:
    carga              0.0572
    arranques por hora 2.031

  el gemelo con los parámetros MEDIDOS (entrega 1.2507, consumo 0.0711):
    carga              0.0560   (2.1% de error)
    arranques por hora 1.833   (9.7%)

  y ahora buscándolos, con tres objetivos distintos:
    solo la carga        entrega 0.720  consumo 0.0420  cociente 0.0583  error 0.0004
    solo los arranques   entrega 0.600  consumo 0.0810  cociente 0.1350  error 0.0153
    las dos cosas        entrega 1.350  consumo 0.0780  cociente 0.0578  error 0.0334

  puntos que empatan con el mejor (dentro de 0,002), y qué abarcan:
    solo la carga           4 puntos   entrega de 0.720 a 1.080   cociente de 0.0571 a 0.0588
    solo los arranques     40 puntos   entrega de 0.600 a 1.560   cociente de 0.05 a 0.135
    las dos cosas           1 puntos   entrega de 1.350 a 1.350   cociente de 0.0578 a 0.0578
```

Los tres paneles de la figura son las tres líneas de esa tabla.

**Ajustando la carga** sale una diagonal: cuatro puntos empatados, con entregas de **0,72** a
**1,08**, todos con el mismo cociente. El ajuste ha encontrado la relación correcta y no tiene
nada que decir sobre la escala.

**Ajustando los arranques** sale una vertical, y peor: **cuarenta** puntos empatados, de punta a
punta de la rejilla. Su mejor punto tiene un cociente de **0,1350**, que daría un ciclo de trabajo
más del doble del real. Un observable acertado con un modelo disparatado.

**Ajustando las dos cosas** queda **un punto**, donde las dos rectas se cruzan.

**Y ahí está la respuesta del módulo:**

| | Medido, sin ajustar nada | Buscado por ajuste |
|---|---|---|
| Entrega | 1,2507 bar/min | 1,350 |
| Consumo | 0,0711 bar/min | 0,0780 |
| Sube por minuto cargando | **1,1796** | **1,272** |

Un **7,8 %**. Dos caminos que no se hablan entre ellos, uno de física y otro de fuerza bruta, y
acaban a menos de un diez por ciento el uno del otro.

**Y lo que eso vale, dibujado sobre una semana sana:**

{{FIG:fig_m26_gemelo_vs_real_sano}}

Del 16 al 22 de febrero la máquina cargó **497,2** minutos. El gemelo con los parámetros medidos
predijo **528,5**, y el gemelo con los ajustados, **536,7**.

**Los dos gemelos se llevan 8,2 minutos en una semana entera.** Un 7,8 % en los parámetros se
convierte en un 1,6 % del trabajo de la máquina, y en la figura las dos curvas serían la misma
línea. Fíjate además en cuál queda más cerca de la realidad: **el medido**, por ocho minutos. El
ajuste optimizó dos resúmenes y no ganó nada donde importa.

### Y lo que el ajuste encontró sin buscarlo

Todo lo de arriba es la segunda versión de este módulo. La primera no cuadraba, y perseguir por qué
destapó dos cosas.

**La primera: el registro tiene huecos, y se estaban contando como tiempo de compresor.** La
duración de cada tramo salía de restar dos marcas de tiempo, la del final menos la del principio. Y
en la ventana de entonces había **35 huecos** de más de una hora, casi todos de madrugada. Un tramo
que salta un hueco se lleva las horas del hueco, y eso hundía las dos velocidades a la vez.

**Y el guardián que había no podía verlo.** Comparaba el ciclo de trabajo predicho contra el
observado, y el ciclo de trabajo es un cociente: si las dos duraciones se inflan por el mismo
factor, no se entera. Los arranques por hora sí, porque se cuentan contra el reloj. Con los
parámetros de entonces fallaban un **15,4 %** y nadie los estaba mirando.

Esto es el módulo 16 otra vez, con otra ropa: **una comprobación que comparte el error con lo que
compara siempre da verde.**

**La segunda es más gorda.**

{{FIG:fig_m26_ventana_sucia}}

Arreglado lo de los huecos, los parámetros seguían sin cuadrar. Mirando la ventana de calibración
día a día, en vez de en bloque, apareció esto:

| | Febrero, 28 días | Del 1 al 12 de marzo | Del 13 al 22 |
|---|---|---|---|
| Ciclo de trabajo | 0,0461 a 0,0781 | 0,0972 a **0,5808** | 0,0676 a 0,1136 |
| Arranques por hora | 1,58 a 2,42 | 1,46 a **5,0** | 1,96 a 2,77 |
| Aceite | 53,9 a 59,2 °C | **60,7 a 69,2** | 53,5 a 62,0 |
| Corriente del motor | 1,0 a 1,5 A | **1,78 a 3,91** | 1,23 a 1,8 |
| Alarma de baja presión | 0,0002 | **0,0208** | 0,0108 |

**Del 1 al 12 de marzo de 2020 esta máquina está averiada, y no hay ningún parte que lo diga.** El
aceite y la corriente ni se rozan con los de febrero: el máximo de febrero queda por debajo del
mínimo de marzo en los dos. El día 11 salta la alarma de baja presión por primera vez en todo el
registro. El día 13 vuelve todo a lo de antes.

Son cinco señales de cinco instrumentos distintos moviéndose juntas. Una sola sería una discusión.

**Y la ventana de calibración de este curso llegaba hasta el 15 de marzo**, así que se estaba
calibrando el gemelo con **doce días de avería dentro**. La ventana se había elegido por fecha,
antes del primer parte documentado, precisamente para no escoger los datos que confirman el modelo.
Eso protege de una cosa y no protege de esta.

**Qué significa.** Que el ajuste no mejoró el gemelo, y aun así valió la pena. Buscar los
parámetros fue la primera pregunta que el modelo podía responder con un no. Respondió que no dos
veces, y las dos tenía razón.

## Hazlo tú

```reto
pregunta: Saca las dos cosas contra las que se calibra el gemelo, en una sola consulta, para el 5 de junio de 2020. Devuelve `carga` (la fracción de lecturas con el compresor cargando, con cuatro decimales) y `arranques_por_hora` (con dos). Una fila.
inicio: SELECT DV_eletric,
       lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
FROM telemetria WHERE day = DATE '2020-06-05';
esperado: m26_los_dos_observables
pista: La carga es una media de unos y ceros, así que `avg` sobre un `CASE` la da directa. Para los arranques hay que contar las lecturas en las que `antes` valía 0 y `DV_eletric` vale 1, y dividir por las horas del día, que son `count(*) * 10 / 3600.0` porque cada lectura son diez segundos.
solucion: SELECT round(avg(CASE WHEN DV_eletric = 1 THEN 1.0 ELSE 0.0 END), 4) AS carga,
       round(sum(CASE WHEN antes = 0 AND DV_eletric = 1 THEN 1 ELSE 0 END)
                 / (count(*) * 10 / 3600.0), 2) AS arranques_por_hora
FROM (SELECT DV_eletric,
             lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
      FROM telemetria WHERE day = DATE '2020-06-05');
```

Carga **0,6363** y **1,28** arranques por hora. Compáralo con febrero, que hizo 0,0572 y 2,031.

La carga es **once veces mayor** y los arranques han **bajado**. No es una contradicción: el 5 de
junio es uno de los cuatro días con parte de avería, el compresor está cargando casi todo el rato y
por eso casi no cicla. Guarda esa rareza, porque el módulo 27 se tropieza con ella.

## Ojo

- **Ajustar no es mejorar.** Si el modelo no tiene perillas sueltas, el ajuste no puede mejorarlo.
  Sirve para comprobarlo, que es otra cosa y a veces vale más.
- **Un observable puede fijar una relación y no los números.** Antes de creerte un parámetro
  ajustado, pregunta si lo que mediste podía distinguirlo de otro.
- **Un óptimo pegado al borde de la rejilla no es un óptimo**, es el borde. Y si ensanchas la
  rejilla y se vuelve a pegar, lo que tienes es un valle.
- **Una comprobación que comparte el error con lo que compara siempre da verde.** El ciclo de
  trabajo no puede validar unas duraciones porque es un cociente de esas duraciones.
- **Elegir la ventana sana por fecha no basta.** Protege de escoger a conveniencia y no protege de
  una avería no documentada. Hay que mirarla, señal por señal y día por día.
- **Una señal rara es una discusión; cinco a la vez es un hecho.** Ninguna de las cinco de marzo
  habría convencido sola.
- **Con el ajuste al lado se puede preguntar por el precio.** Aquí un 7,8 % en los parámetros
  costaba 8,2 minutos en una semana. Sin esa cuenta, un 7,8 % no se sabe si es mucho o poco.

## Puente metalúrgico

Un modelo de molienda con dos parámetros ajustados a la vez, la constante de rotura y la función
de selección. Y una sola curva granulométrica de salida contra la que ajustarlos.

Sale un ajuste precioso y los dos parámetros son inventados. La curva no distingue una rotura
rápida con poca selección de una lenta con mucha, porque solo ve el producto.

La forma de romper el empate es la misma que aquí: **otra medida que dependa de otra combinación**.
Un ensayo a distinto tiempo de molienda, una carga circulante, una potencia consumida. No más datos
de lo mismo, sino datos de otra cosa.

Y el otro paralelo es el de la ventana. Quien haya calibrado un modelo con datos de planta sabe
que el periodo de referencia se elige mirando, no por fecha. Una campaña con la celda de arrastre
parada dentro se lleva la calibración por delante. Aquí pasó exactamente eso, y hubo que
descubrirlo tarde.

## Repaso

### Qué es exactamente calibrar aquí

Buscar los dos parámetros del gemelo probando 1.023 combinaciones y quedándose con la que mejor
reproduce lo que la máquina hizo. No para sustituir a los medidos, sino para comprobarlos: dos
caminos independientes que acaban en el mismo sitio son una prueba de que ese sitio significa algo.

### Por qué el ciclo de trabajo no basta para calibrar

Porque vale `consumo / entrega`, así que solo depende del cociente. Todos los pares con el cociente
correcto puntúan exactamente igual, y el ajuste no tiene forma de preferir uno. En esta rejilla eso
son entregas desde 0,72 hasta 1,08 empatadas.

### Qué añaden los arranques por hora

La escala. El ciclo entero tarda `banda / llena` más `banda / consumo`, y ese tiempo se acorta
cuando los dos parámetros crecen a la vez, aunque el cociente no cambie. Es la única medida del
registro que ve lo que el ciclo de trabajo no puede ver.

### El ajuste dio 1,272 y la medida 1,1796. Cuál es el bueno

El medido, y no por lealtad. El ajuste optimiza dos resúmenes de la ventana; la medida sale de un
balance de aire que cierra al 0,7 %. Y cuando se les pone a competir sobre una semana real, el
medido queda ocho minutos más cerca. Un 7,8 % de diferencia en los parámetros vale un 1,6 % del
trabajo de la máquina, así que la pregunta de cuál es el bueno importa menos de lo que parecía.

### Por qué se cambió la ventana sana a febrero, y qué habría pasado sin mirarla

Porque del 1 al 12 de marzo la máquina está averiada. El ciclo de trabajo llega a 0,5808, el aceite
sube diez grados, la corriente dobla y salta la alarma de baja presión. No hay ningún parte que lo
recoja. Y calibrar con una avería dentro le enseña al gemelo que la avería es normal, justo lo
único que no puede aprender.

Sin mirar la ventana, el gemelo habría salido con una entrega muy por debajo de la real. Y nadie se
habría enterado, porque la única comprobación que había era ciega a ese error. Los módulos 27 y 28
se habrían montado encima. Ese es el argumento para calibrar aunque no haga falta calibrar.

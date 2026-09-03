---
module: 25
---

## En 30 segundos

- Simular es avanzar el modelo a trocitos de tiempo. El tamaño del trocito **decide el resultado**.
- Se barre el paso y se compara todo contra el más fino. El que aún vale es **5 s**.
- La mitad de lo que el registro tarda entre lectura y lectura, y tiene su razón.
- Y el criterio no puede ser el ciclo de trabajo: con paso de 30 s parece perfecto.
- Ya ha perdido **2 ciclos de 15**. Contar ciclos no se puede equivocar así.

## Qué resuelve este módulo

El módulo 24 dejó cuatro números y cuatro líneas. Con eso ya se sabe **cuánto** carga el compresor:
consumo entre entrega, sin simular nada.

Lo que no se sabe es **cuándo**. Cuántos arranques, cada cuánto, y qué pasa si el consumo cambia a
media tarde. Para eso hay que hacer correr el modelo en el tiempo, y ahí aparece una decisión que
nadie anuncia: **de cuánto en cuánto se avanza**.

Parece un detalle de implementación. No lo es: es el parámetro que puede dejar la simulación
diciendo cosas que la máquina no hace.

## Antes de la teoría: un ejemplo de juguete

Un depósito que baja 1 litro por minuto, con una alarma a los 50 litros. Empieza con 55.

Si miras **cada minuto** los ves bajar de uno en uno: 55, 54, 53 y así hasta 50, donde salta la
alarma. A los cinco minutos, correcto.

Ahora mira **cada diez minutos**. Ves 55 y luego 45. La alarma salta igual, pero **cinco minutos
tarde**, y si además el depósito se hubiera rellenado a los 52 no te habrías enterado de nada.

Con un paso de una hora el asunto es peor: puedes ver 55 y luego 55 otra vez, porque entremedias
bajó, saltó la alarma, alguien rellenó y volvió a subir. **El paso grande no da un resultado
aproximado: da un resultado de otra máquina.**

Y ahora la trampa de este módulo. Si lo que mides es el **nivel medio** del depósito, los tres
pasos te dan casi lo mismo, porque los errores se compensan. El nivel medio no se entera. Lo que se
entera es **cuántas veces sonó la alarma**.

## Glosario

- **Integrar en el tiempo.** Avanzar el estado a trocitos: nuevo estado igual al de antes más lo
  que cambia en ese trocito.
- **Paso.** El tamaño del trocito.
- **Método de Euler.** Justo eso, la forma más simple de integrar. Es lo que hace este gemelo.
- **Convergencia.** Que al afinar el paso el resultado deje de moverse. Si no deja de moverse, no
  hay resultado.
- **Patrón.** La corrida con el paso más fino, contra la que se comparan las demás.
- **Falso verde.** Una comprobación que da bien por el motivo equivocado. Ya salió en el módulo 16.

## Paso a paso

### Paso 1. Escribir el avance

Dos ramas, una por cada cosa que puede estar haciendo el compresor, y una comprobación del
presostato en cada una. Es el modelo del módulo 24, ahora dentro de un bucle.

### Paso 2. Elegir contra qué comparar

No hay verdad absoluta, así que se fabrica una: la misma simulación con un paso **doscientas veces
más fino que el registro**, una décima de segundo. Esa es el patrón.

### Paso 3. Barrer el paso

Diez tamaños, de una décima de segundo a dos minutos, todos sobre el mismo turno de ocho horas.

### Paso 4. Elegir en qué fijarse, que es lo difícil

Y aquí está el módulo. El primer criterio que probé fue el ciclo de trabajo, la cifra que de
verdad importa. **Salió inservible**, y no por poco: su error no crece con el paso, sube y baja.

Lo que sí crece siempre es otra cosa, y es la que se acaba usando.

## El código, por partes

### Paso 5. El avance, entero

```python
for _ in range(int(minutos / paso)):
    if cargando:
        p += (entrega - consumo) * paso
        if p >= para: cargando = False
    else:
        p -= consumo * paso
        if p <= arranca: cargando = True; arranques += 1
    if cargando: cargados += paso
```

```anota
range(int(minutos / paso)) | cuántos trocitos caben. Con paso más fino, más vueltas y más lento
p += ... * paso | el método de Euler: lo que cambia por minuto, multiplicado por el trocito
las comprobaciones | el presostato se mira DESPUÉS de mover la presión, así que un paso grande puede pasarse el umbral de largo
arranques | lo que se va a contar. Es la medida que no se deja engañar
```

Fíjate en dónde está el problema: la presión se mueve y **luego** se mira si cruzó el umbral. Con
un paso de dos minutos, en un solo salto puede subir 1,5 bar y pasarse la banda entera.

### Paso 6. La prueba, y su tabla

```python
patron = avanza(dep, consumo, 8 * 60, 0.1 / 60)
for segundos in (0.1, 0.5, 1, 2, 5, 10, 20, 30, 60, 120):
    r = avanza(dep, consumo, 8 * 60, segundos / 60)
    se_parece = r["arranques"] == patron["arranques"]
```

```anota
0.1 / 60 | el paso en minutos, que es la unidad en la que están las dos tasas
se_parece | el criterio: los mismos arranques que el patrón. Ni parecidos, los mismos
```

```salida
    paso patrón s   carga 0.0543   arranques  15   error de carga 0.00000
    paso    0.1 s   carga 0.0543   arranques  15   error de carga 0.00000
    paso    0.5 s   carga 0.0544   arranques  15   error de carga 0.00010
    paso      1 s   carga 0.0547   arranques  15   error de carga 0.00036
    paso      2 s   carga 0.0552   arranques  15   error de carga 0.00089
    paso      5 s   carga 0.0547   arranques  15   error de carga 0.00036
    paso     10 s   carga 0.0535   arranques  14   error de carga 0.00085   pierde 1 ciclos
    paso     20 s   carga 0.0542   arranques  13   error de carga 0.00016   pierde 2 ciclos
    paso     30 s   carga 0.0542   arranques  13   error de carga 0.00016   pierde 2 ciclos
    paso     60 s   carga 0.0542   arranques  13   error de carga 0.00016   pierde 2 ciclos
    paso    120 s   carga 0.0542   arranques  13   error de carga 0.00016   pierde 2 ciclos
```

Lee la columna del error de carga de arriba abajo y luego la de arranques. **Una sube y baja; la
otra solo empeora.**

### Paso 7. Toca la perilla

```perilla
m25_paso
```

Mueve el paso y mira el trazo. Al principio no cambia nada, y a partir de cierto punto los
escalones se van haciendo más largos y más pocos: son los ciclos que la simulación se está saltando.

## El resultado, medido

{{FIG:fig_m25_ciclo_carga_vacio}}

Eso es lo que hace el gemelo por dentro: la presión sube mientras carga, cruza los **10,10 bar** y
el compresor suelta; baja despacio hasta los **8,05** y vuelve a arrancar. Un diente de sierra, y
la histéresis es lo que le da los dientes.

Es la única figura de este curso que dibuja la presión, y se puede porque aquí **explica el
mecanismo**. La regla del doble trazo prohíbe otra cosa: buscar una fuga mirando la presión, que es
justo lo que no funciona.

{{FIG:fig_m25_paso_de_tiempo}}

**Qué esperábamos.** Un error que creciera con el paso, y un paso bueno igual al último por
debajo de cierto umbral.

**Qué salió.** Que el error del ciclo de trabajo **no crece**. Con paso de 30 s es el más pequeño
de toda la tabla salvo el del patrón, y a esas alturas la simulación ya se ha comido **2 ciclos de
15**.

No es casualidad ni mala suerte. Un paso grueso se salta arranques, y cada arranque que se salta
alarga el vacío siguiente y acorta la carga siguiente, **y los dos errores se compensan en la
media**. El ciclo de trabajo sale bien por el motivo equivocado: es el falso verde del módulo 16,
ahora en una simulación.

Contando ciclos no pasa eso:

| Paso | Ciclos de 15 | ¿Vale? |
|---|---|---|
| 0,1 a 5 s | 15 | sí |
| 10 s | 14 | no |
| 20 a 120 s | 13 | no |

**El paso más grande que aún vale es 5 s**, la mitad de lo que tarda el registro entre lectura y
lectura. Y tiene sentido que sea más fino, porque son dos trabajos distintos. El registro solo
tiene que **ver** los ciclos. La simulación tiene que **cerrarlos**.

Cada paso avanza la presión y luego mira si ha cruzado. Con diez segundos se pasa de largo hasta
0,2 bar, o sea la décima parte de la banda.

Contra qué compararlo para que no sea un número suelto: la fase corta del ciclo, que es la carga,
dura **1,74 minutos**. El paso bueno es una veinteava parte de eso.

**Qué significa.** Que el paso no se elige, se mide. Y **la magnitud con la que se mide importa
más que el umbral**: con el ciclo de trabajo, dos minutos habría parecido suficiente.

## Ojo

- **El paso se comprueba, no se elige.** Y se comprueba contra una corrida más fina, porque no hay
  otra verdad con la que comparar.
- **No uses la magnitud que te interesa como criterio de convergencia.** Aquí el ciclo de trabajo
  es lo que se quiere calcular y es justo el peor juez, porque sus errores se compensan.
- **Cuenta sucesos.** Arranques, cruces, cambios de estado. Un suceso o pasa o no pasa: no hay
  forma de que se compense con otro.
- **Un paso fino no es gratis.** El patrón de este módulo da una vuelta por cada décima de
  segundo de las ocho horas. Para un turno da igual; para los escenarios del gemelo, no.
- **Euler se salta los umbrales.** Mueve el estado y luego mira. Hay métodos que detectan el cruce
  y retroceden, y aquí no hacen falta porque con 5 s ya se resuelve todo.
- **Si la máquina se hace más rápida, el paso tiene que bajar.** Este barrido se rehízo cuando los
  parámetros del módulo 24 se corrigieron, y el paso bueno pasó de 10 s a 5. No se corrigió a
  mano: se volvió a correr.
- **Esto vale para el consumo de este compresor.** Con un consumo cinco veces mayor los ciclos son
  cinco veces más cortos y el paso bueno bajaría. La prueba se repite si cambia el régimen.

## Puente metalúrgico

Un muestreador automático en una cinta toma un incremento cada cierto tiempo. Y la pregunta de
siempre es cada cuánto.

Imagina mineral en tandas de camión, con leyes distintas de una a otra. Un muestreador que toma un
incremento cada dos horas dará **una ley media plausible** y no verá ni una sola tanda. El promedio
del turno sale clavado y el muestreo no sirve: no puede decirte qué camión traía la ley mala.

Es exactamente el paso de este módulo. La media aguanta cualquier frecuencia; **lo que se pierde
son los sucesos**, y los sucesos son lo que se busca.

## Hazlo tú

```reto
pregunta: Mide cuánto dura cada carga y cada vacío el 5 de junio de 2020, que es lo que la simulación tiene que reproducir. Devuelve `estado`, `tramos` y `minutos` con la mediana de la duración en minutos, ordenado por `estado`. Dos filas.
inicio: SELECT timestamp, DV_eletric,
       sum(CASE WHEN antes IS DISTINCT FROM DV_eletric THEN 1 ELSE 0 END)
           OVER (ORDER BY timestamp) AS tramo
FROM (SELECT timestamp, DV_eletric,
             lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
      FROM telemetria WHERE day = DATE '2020-06-05');
esperado: m25_cuanto_dura
pista: El punto de partida ya numera los tramos: cada vez que el compresor cambia de idea, la suma acumulada sube uno. Falta agrupar por `tramo` para sacar la duración de cada uno con `date_diff` entre su primera y su última marca, y después agrupar otra vez por si cargaba o no.
solucion: SELECT CASE WHEN cargando = 1 THEN 'carga' ELSE 'vacio' END AS estado,
       count(*)                  AS tramos,
       round(median(minutos), 2) AS minutos
FROM (SELECT any_value(DV_eletric) AS cargando,
             date_diff('second', min(timestamp), max(timestamp)) / 60.0 AS minutos
      FROM (SELECT timestamp, DV_eletric,
                   sum(CASE WHEN antes IS DISTINCT FROM DV_eletric THEN 1 ELSE 0 END)
                       OVER (ORDER BY timestamp) AS tramo
            FROM (SELECT timestamp, DV_eletric,
                         lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
                  FROM telemetria WHERE day = DATE '2020-06-05'))
      GROUP BY tramo)
GROUP BY estado
ORDER BY estado;
```

Treinta y un ciclos en el día, con cargas de **2,13** minutos y vacíos de **19,98**. Compara esas
dos cifras con lo que hace el gemelo en la perilla de arriba, en su posición de partida: es la
misma máquina.

## Repaso

### Qué significa simular aquí

Avanzar el estado del modelo a trocitos de tiempo, sumando en cada uno lo que cambia. El estado es
una sola variable, la presión. En cada trocito se le suma la entrada menos la salida, y después se
mira si el presostato cambia de idea.

### Por qué el tamaño del paso cambia el resultado

Porque el presostato se comprueba después de mover la presión. Con un paso grande la presión salta
por encima de la banda entera en un solo movimiento, y el arranque que tenía que haber ocurrido en
medio no ocurre. La simulación no sale aproximada: sale de otra máquina.

### Por qué el ciclo de trabajo es mal juez de la convergencia

Porque sus errores se compensan. Cada arranque que se pierde alarga un vacío y acorta una carga, y
la media apenas se mueve. Aquí, con paso de 30 s el error del ciclo era de los más pequeños de la
tabla y ya se habían perdido dos ciclos de quince.

### Cuál es entonces el criterio

Contar sucesos, que aquí son los arranques. Un arranque ocurre o no ocurre, así que no hay forma de
que un error tape a otro. Con ese criterio la degradación es monótona y la frontera queda clara.

### El paso bueno es más fino que el registro. Por qué

Porque son dos trabajos distintos. El registro solo tiene que **ver** los ciclos, y una carga de
1,74 minutos se ve de sobra con una lectura cada diez segundos.

La simulación tiene que **cerrarlos**. Avanza la presión un paso entero y solo después mira si ha
cruzado la presión de parada. Con diez segundos se pasa de largo hasta 0,2 bar, y un ciclo de
quince se le escapa.

Una versión anterior de esta lección publicaba aquí que el paso bueno coincidía con el del
registro, y le buscaba un sentido. Coincidía, y el sentido era inventado: al corregir los
parámetros del módulo 24 la coincidencia se deshizo sola.

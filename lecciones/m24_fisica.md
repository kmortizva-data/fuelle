---
module: 24
---

## En 30 segundos

- Un depósito que se llena y se vacía, y un interruptor con memoria. No hay más.
- La ficha promete que arranca a **8,2 bar** y arranca a 8,05: **8,2 contra 8,05**.
- Los dos parámetros del modelo salen de un **balance de aire** que cuadra al **0,7 %**.
- Y con ellos el modelo predice una carga de **0,0568** cuando la máquina hizo **0,0572**.
- Ojo con los huecos del registro: **28 tramos** se tragaban **3.129 minutos** de compresor
  que nunca existieron.

## Qué resuelve este módulo

Para que un gemelo sirva tiene que ser un modelo de algo, y ese algo aquí es sencillo: **un
depósito de aire con un interruptor de presión**. El compresor lo llena, la planta lo vacía, y un
presostato decide cuándo arrancar.

Lo difícil no es escribir esas ecuaciones. Es **de dónde salen sus números**, porque un modelo con
parámetros inventados es un dibujo animado.

Aquí no se inventa ninguno. Los cuatro se miden del lago y se contrastan con la ficha del
fabricante donde se puede. Y se comprueban con **una ley que no admite discusión**: el aire entrado
iguala al gastado.

## Antes de la teoría: un ejemplo de juguete

Un tanque de agua con una bomba y un grifo abierto.

| Qué | Cuánto |
|---|---|
| El tanque, lleno | 100 litros |
| La bomba mete | 10 litros por minuto |
| El grifo saca | 2 litros por minuto |
| La bomba arranca por debajo de | 40 litros |
| La bomba para al llegar a | 80 litros |

Con eso ya se puede contar todo lo que hace ese tanque, sin más física.

**Llenando:** entran 10 y salen 2, así que sube 8 litros por minuto. De 40 a 80 hay 40 litros, o
sea **5 minutos bombeando**.

**Vaciando:** la bomba está parada y el grifo sigue, así que baja 2 por minuto. De 80 a 40 hay 40
litros, o sea **20 minutos de descanso**.

Así que el ciclo dura 25 minutos y la bomba trabaja 5, o sea **el 20 % del tiempo**. Y ese 20 %
sale también de una cuenta más corta: lo gastado partido por lo metido, 2 entre 10.

Eso último es el resultado que hay que llevarse. **El ciclo de trabajo es el consumo dividido por
la entrega**, y no hace falta simular nada para saberlo. Simular sirve para lo que viene después.

Y ahora la parte incómoda. En el tanque de juguete te he dado los cinco números. En el compresor de
verdad **no te los da nadie**: la ficha da uno, se equivoca en él, y los demás hay que sacarlos de
los datos.

## Glosario

- **Depósito.** El volumen de aire a presión, que amortigua entre entrada y salida. En este tren
  es la APU con sus botellas.
- **Presostato.** El interruptor que mira la presión y decide. `MPG` en este fichero.
- **Histéresis.** Que arranque a una presión y pare a otra más alta. Sin eso, el compresor
  encendería y apagaría sin parar en el umbral.
- **Banda.** La distancia entre esas dos presiones.
- **Entrega.** Lo que el compresor mete por minuto, medido en subida de presión.
- **Consumo.** Lo que la planta gasta, medido igual.
- **Ciclo de trabajo.** La fracción del tiempo que el compresor pasa cargando.

## Paso a paso

### Paso 1. Encontrar las dos presiones del presostato

No se pregunta a la ficha: se miran los momentos en que `DV_eletric` cambia, y se anota qué presión
había. La mediana de esos momentos es la presión de conmutación.

### Paso 2. Partir el registro en tramos

Cada carga y cada vacío, de punta a punta. Un tramo es un trozo con el compresor haciendo lo mismo.

**Sin filtrar por duración**, y eso costó un rato entenderlo. El primer intento se quedaba solo con
los tramos de dos minutos o más, para que la pendiente fuera fiable. Como las cargas duran 1,8
minutos y los vacíos 22, aquel filtro tiraba casi todas las cargas y ningún vacío.

### Paso 3. Cuadrar el aire

Sobre seis semanas la presión acaba donde empezó, así que **los bar metidos tienen que igualar a
los gastados**. Es la comprobación que decide si la medida vale algo.

Si no cuadran, lo que está mal es la medida, no la máquina. Y si cuadran, los dos parámetros salen
solos: la subida por minuto cargando, y la bajada por minuto en vacío.

### Paso 4. Comprobar que predicen el ciclo

El ciclo de trabajo del ejemplo de juguete, consumo entre entrega, tiene que dar lo que la máquina
hizo de verdad. **Ninguno de los dos parámetros se ajustó para eso**, así que si coinciden es
porque el modelo describe la máquina.

## El código, por partes

### Paso 5. Las dos presiones, medidas

```sql
SELECT CASE WHEN antes = 0 THEN 'arranca' ELSE 'para' END AS momento,
       round(median(TP3), 2) AS presion
FROM (SELECT TP3, DV_eletric,
             lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
      FROM plata WHERE medido AND day BETWEEN DATE '2020-02-01' AND DATE '2020-03-15')
WHERE antes IS NOT NULL AND antes <> DV_eletric
GROUP BY momento
ORDER BY momento;
```

```anota
lag(DV_eletric) | lo que hacía el compresor en la lectura anterior. Es la función de ventana del módulo 13
antes <> DV_eletric | quédate solo con las lecturas donde cambió de idea
median(TP3) | la presión típica en ese momento. La mediana y no la media, porque alguna transición cae en un hueco del registro
```

```salida
┌─────────┬─────────┐
│ momento │ presion │
│ varchar │ double  │
├─────────┼─────────┤
│ arranca │    8.06 │
│ para    │   10.12 │
└─────────┴─────────┘
```

**La ficha dice 8,2 y la máquina arranca a 8,05.** Es el módulo 1 otra vez, y la ficha no está
equivocada: un presostato real tiene tolerancia, e importa el que está montado en este tren. La
presión de parada la ficha no la da, y son **10,10**.

### Paso 6. El balance, que es lo que valida la medida

```python
metidos  = sum(p_fin - p_ini for tramo in tramos if tramo.cargando)
gastados = sum(p_ini - p_fin for tramo in tramos if not tramo.cargando)
entrega  = metidos / minutos_cargando + consumo
consumo  = gastados / minutos_en_vacio
```

```anota
metidos y gastados | los bar que suben mientras carga y los que bajan mientras no. Sobre seis semanas tienen que ser iguales
partido por minutos | de ahí salen los dos parámetros, por minuto y no por lectura: lo que mueve el aire es el total, no la pendiente de un instante
entrega = subida + consumo | mientras carga también se está gastando, así que lo que el compresor mete es lo que se ve subir más lo que se va
```

```salida
  el balance de aire, que es lo que decide si la medida vale:
    metidos             4159.7 bar
    gastados            4127.6 bar
    descuadre             0.8%

  sube por minuto cargando   0.6735 bar/min
  mediana instantánea         1.032 bar/min   un 53% de más
  consumo                    0.0806 bar/min
```

Cuadra al **0,8 %** en seis semanas. Eso no lo he impuesto yo: los dos números se miden por
separado y coinciden, y esa coincidencia es la que dice que la medida está bien hecha.

### Paso 7. Y el modelo entero, en cuatro líneas

```python
if cargando:
    p += (entrega - consumo) * paso
    if p >= para: cargando = False
else:
    p -= consumo * paso
    if p <= arranca: cargando = True
```

```anota
p | la presión, que es todo el estado del gemelo. Una sola variable
paso | el trocito de tiempo que se avanza cada vez. De eso va el módulo 25
las dos condiciones | el presostato entero. La histéresis es que los dos umbrales sean distintos
```

Eso es el gemelo. Cuatro líneas y cuatro números, y ninguno de los cuatro está inventado.

### Paso 8. Toca la perilla

```perilla
m24_consumo
```

Sube el consumo y mira el trazo: el compresor pasa más tiempo cargando, y los escalones se juntan.
Baja el consumo y se separan. **La presión no aparece por ninguna parte**, y es a propósito: es la
variable que el control sostiene, y por eso no cuenta nada.

## El resultado, medido

{{FIG:fig_m24_balance_del_deposito}}

**Qué esperábamos.** Que el compresor llenara a un ritmo, uno solo, medible tomando una pendiente
cualquiera de las que sube.

**Qué salió.** Que no hay un ritmo, hay una rampa. Los primeros diez segundos la presión sube
**0,804 bar/min**, porque el motor está arrancando y es la corriente de 9 A que la ficha menciona.
Después pica en **1,608** y a partir de ahí **cae** según se llena el depósito y empuja hacia
atrás.

La **mediana instantánea** de esas pendientes es **1,248 bar/min**, y lo que el compresor consigue
de verdad por minuto cargando es **1,1796**. Un **5,8 %** de diferencia, y la mediana es la que
sale si uno mide sin pensar.

**Cuesta menos de lo que parece, y conviene decirlo así.** Un modelo montado sobre la mediana
predice una carga de **0,0539**, un **5,8 %** por debajo de lo que la máquina hizo. La rampa es
real y la mediana es la medida equivocada, pero el precio de equivocarse aquí es pequeño. Con la
media por minuto:

| Qué | Valor |
|---|---|
| Carga que predice el modelo | **0,0568** |
| Carga que hizo la máquina | **0,0572** |
| Se llevan | 0,7 % |

**Qué significa.** Que el gemelo ya existe, y que sus dos parámetros no se tocaron para hacerlo
cuadrar. Se midieron por separado, se comprobó el balance de aire, y la predicción salió sola.

## Ojo

- **Una mediana de pendientes no es una tasa media.** Aquí se llevan un 5,8 %, y la buena para un
  ciclo de trabajo es la media por minuto, porque lo que cuenta es el aire total.
- **Filtra con cuidado.** Descartar tramos cortos parecía prudente y tiraba casi todas las cargas,
  que duran 1,8 minutos. El balance salía descuadrado por un factor de 2,3 por culpa del filtro.
- **La ficha del fabricante es una pista, no un dato.** Dice 8,2 y son 8,05. Un presostato tiene
  tolerancia, y se modela la pieza montada.
- **El consumo instantáneo no se puede medir a diez segundos.** TP3 trae dos decimales, así que el
  cambio más pequeño visible son 0,01 bar, o sea 0,06 bar/min. La mediana instantánea de consumo
  cae exactamente ahí: no es una medida, es la resolución del sensor.
- **Cuadrar el aire antes de creerse nada.** Si los bar que entran no son los que salen, no hay
  modelo posible y el fallo está en la medición.
- **La presión no es la variable interesante.** El control la sostiene, así que apenas se mueve.
  Todo lo que este gemelo va a decir sale del ciclo de trabajo.

## Puente metalúrgico

Un balance metalúrgico es esto mismo y se hace desde siempre. Lo que entra a la planta sale por el
concentrado más las colas. Si no cierra, el balance no vale, y **no se discute ninguna recuperación
hasta que cierre**.

Y la razón de hacerlo es la misma que aquí: no es por gusto contable. Un balance que cierra al 1 %
dice que las básculas, los muestreos y las leyes son coherentes entre sí. Uno que cierra al 30 %
dice que hay un instrumento mintiendo, y hasta encontrarlo cualquier conclusión sobre el proceso es
aire.

El balance de aire de este módulo cierra al 0,8 %. Por eso se puede seguir.

## Hazlo tú

```reto
pregunta: Mide tú la banda del presostato, con un solo día. Devuelve `momento`, `veces` y `presion` con la presión mediana en las transiciones del 5 de junio de 2020, ordenado por `momento`. Dos filas.
inicio: SELECT TP3, DV_eletric,
       lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
FROM telemetria
WHERE day = DATE '2020-06-05';
esperado: m24_la_banda
pista: El punto de partida ya trae la columna que dice qué hacía antes. Falta envolverlo en un `SELECT` de fuera que se quede solo con las filas donde `antes <> DV_eletric`, agrupe por si arranca o para, y saque `count(*)` y `round(median(TP3), 2)`.
solucion: SELECT CASE WHEN antes = 0 THEN 'arranca' ELSE 'para' END AS momento,
       count(*)              AS veces,
       round(median(TP3), 2) AS presion
FROM (SELECT TP3, DV_eletric,
             lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
      FROM telemetria WHERE day = DATE '2020-06-05')
WHERE antes IS NOT NULL AND antes <> DV_eletric
GROUP BY momento
ORDER BY momento;
```

Un solo día da **8,04** y **10,13**, contra los 8,05 y 10,10 de un mes entero. Con treinta y una
transiciones ya se ve la banda entera: el presostato es de las cosas más estables que tiene esta
máquina.

## Repaso

### Qué necesita un modelo del compresor, y qué no

Necesita un depósito, dos presiones de conmutación y dos tasas: lo que entra y lo que sale. No
necesita geometría, ni temperatura, ni el modelo del motor. Con cuatro números se reproduce el
ciclo de trabajo, que es de donde va a salir todo lo demás.

### Por qué el ciclo de trabajo es el consumo dividido por la entrega

Porque en régimen la presión ni sube ni baja a la larga. Todo el aire gastado lo metió el
compresor mientras cargaba, así que si mete 10 y se gastan 2, carga la quinta parte del tiempo. No
hace falta simular nada para saberlo.

### Por qué la mediana de las pendientes de llenado no sirve

Porque el compresor no llena a ritmo constante. Arranca despacio, unos 0,8 bar/min los primeros
diez segundos, pica en 1,6 y va cayendo según sube la presión. La mediana coge el tramo bueno del
medio y sale un 5,8 % por encima de su media por minuto, que es la cifra que mueve el aire.

Y hay que decir la otra mitad: un 5,8 % es poco. La mediana es la medida equivocada por una razón
que se entiende, pero en esta máquina te habría costado barato. La versión anterior de esta
lección publicaba aquí un 53 %, y ese número era casi todo un fallo de medida propio, no de la
mediana. Está contado en el módulo 26.

### Qué comprobación decide si estos parámetros valen

Que el aire cuadre. Sobre febrero entero entraron 2.311,7 bar y salieron 2.295,0, un 0,7 % de
diferencia. Sin ese cierre, dos números medidos por separado no son un modelo, son dos números.

Y hay una segunda comprobación que este módulo no tenía y ahora sí: **cuántas veces arranca por
hora**. Hace falta porque el balance no puede verlo todo. Si las dos duraciones se midieran mal
por el mismo factor, el ciclo de trabajo es un cociente y no se enteraría; los arranques se
cuentan contra el reloj y sí. Pasó, y lo cuenta el módulo 26.

### La ficha dice 8,2 bar y tú publicas 8,05. Quién se equivoca

Ninguno de los dos. La ficha describe el modelo de presostato y los datos describen la pieza
montada en este tren, con su tolerancia y su desgaste. Para un gemelo de esta máquina manda la
segunda, igual que en el módulo 1 mandaba el fichero sobre la ficha.

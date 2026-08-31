---
module: 14
---

## En 30 segundos

- Bronce se negaba a decidir. Plata decide, y **cada decisión deja una columna o un número**.
- El ruido de coma flotante afecta al **85,5 %** de los valores de TP2. Se redondea a 3 decimales.
- Las **16.762** lecturas contradictorias se **marcan**, no se borran.
- El reloj no cae en ninguna rejilla: camina. Ajustando, **12.841** lecturas comparten casilla.
- Y aparecen **337.653 huecos** que en bronce no existían como filas.

## Qué resuelve este módulo

El módulo 4 dejó una regla: bronce no limpia. Eso convierte la limpieza en un problema aplazado,
y este módulo es donde vence el plazo.

Aquí se decide qué es un dato bueno. Lo importante no es la decisión concreta, es que **queda
escrita en código y con su precio medido**, en vez de en la cabeza de quien la tomó.

## Antes de la teoría: un ejemplo de juguete

Cuatro lecturas de un turno, tal como salen del sensor:

| hora | presión | válvula abierta | compresor admitiendo |
|---|---|---|---|
| 06:00:02 | 8,200000000000001 | 1 | 0 |
| 06:00:12 | 8,4 | 1 | 1 |
| 06:00:31 | 8,6 | 0 | 1 |
| 06:00:41 | 8,8 | 0 | 1 |

Hay tres problemas ahí dentro, y cada uno pide una decisión distinta.

**Uno: el 8,200000000000001.** El manómetro tiene tres decimales, así que los doce siguientes no
son medida, son basura de coma flotante. **Se redondea.** Eso no pierde nada.

**Dos: la segunda fila dice que la válvula está abierta y que el compresor admite aire a la vez.**
Las dos señales son opuestas por diseño, así que una de las dos miente y no se sabe cuál. Borrar
la fila escondería un sensor averiado. **Se marca** con una columna que diga que esa fila es
sospechosa, y quien la use decidirá.

**Tres: falta la lectura de las 06:00:22.** Entre la segunda y la tercera pasan 19 segundos, no
10. Rellenar con una presión inventada sería mentir. **Se crea la fila vacía**, con NULL dentro.
Es exactamente lo que el módulo 8 dejó dicho sobre los huecos.

Fíjate en el patrón: **redondear quita, marcar añade una columna, y la rejilla añade filas.** Las
tres son decisiones y ninguna es obvia. Lo que las separa de una chapuza es que están escritas y
se sabe cuánto costaron.

## Glosario

- **Plata.** La segunda capa del lago. Los datos limpios, tipados y listos para trabajar, con las
  decisiones tomadas y anotadas.
- **Remuestrear.** Pasar unas medidas tomadas a un ritmo a otro ritmo distinto. Aquí, a una
  rejilla regular de diez segundos.
- **Rejilla.** Una fila cada diez segundos exactos, haya lectura o no.
- **Casilla.** Cada uno de esos huecos de diez segundos de la rejilla.
- **Ajustar.** Poner cada lectura en la casilla que le toca. En inglés se dice `bucketing`.
- **Colisión.** Dos lecturas que caen en la misma casilla.
- **Bandera.** Una columna que no es un dato, es un juicio sobre el dato. Aquí, `dudoso`.

## Paso a paso

### Paso 1. Medir lo que va a costar cada decisión, antes de tomarla

Antes de redondear nada conviene saber cuántos valores se van a tocar. Si fueran cuatro, el
redondeo es un detalle. Si son un millón trescientos mil, es una decisión de las que se declaran.

### Paso 2. Redondear a la precisión que el sensor tiene de verdad

El fichero enseña tres decimales. Todo lo que hay por debajo lo puso el ordenador al guardar el
número en binario, y el módulo 9 midió lo que cuesta dejarlo.

### Paso 3. Marcar las contradicciones en vez de borrarlas

`DV_eletric` y `COMP` son opuestas por diseño. Cuando coinciden, algo va mal en la instrumentación
y esa información vale. Una columna `dudoso` la conserva.

### Paso 4. Ajustar el reloj a una rejilla, y descubrir que camina

Y aquí está la parte que no salió a la primera. La primera versión de este script cruzaba cada
lectura con la rejilla por marca de tiempo exacta, y **conservó una de cada diez**.

El motivo es que **este reloj no está en ninguna rejilla fija**. Cada hueco de nueve segundos le
mueve la fase un segundo, así que las lecturas se reparten por igual entre los diez restos
posibles. No hay un instante «de referencia».

## El código, por partes

### Paso 5. Lo que va a costar, contado antes

```sql
SELECT
  sum(CASE WHEN TP2 <> round(TP2, 3) THEN 1 ELSE 0 END) AS tp2_con_ruido,
  sum(CASE WHEN DV_eletric = COMP THEN 1 ELSE 0 END)    AS contradictorias,
  count(*) AS filas
FROM telemetria;
```

```anota
TP2 <> round(TP2, 3) | el valor no es igual a sí mismo redondeado, o sea que lleva decimales de más
<> | distinto de; también se escribe !=
DV_eletric = COMP | las dos señales valen lo mismo, y son opuestas por diseño
```

```salida
┌───────────────┬─────────────────┬─────────┐
│ tp2_con_ruido │ contradictorias │  filas  │
├───────────────┼─────────────────┼─────────┤
│       1296720 │           16762 │ 1516948 │
└───────────────┴─────────────────┴─────────┘
```

Un millón doscientas noventa y seis mil de un millón quinientas dieciséis mil. **El ruido no es la
excepción, es la norma.**

### Paso 6. Ajustar cada lectura a su casilla

```sql
SELECT count(*) AS lecturas,
       count(DISTINCT casilla) AS casillas_ocupadas,
       count(*) - count(DISTINCT casilla) AS colisiones
FROM (SELECT time_bucket(INTERVAL 10 SECOND, timestamp) AS casilla FROM telemetria);
```

```anota
time_bucket(INTERVAL 10 SECOND, x) | recorta la marca de tiempo a la casilla de diez segundos que le toca
count(DISTINCT casilla) | cuántas casillas quedan ocupadas, que no es lo mismo que cuántas lecturas hay
```

```salida
┌──────────┬───────────────────┬────────────┐
│ lecturas │ casillas_ocupadas │ colisiones │
├──────────┼───────────────────┼────────────┤
│  1516948 │           1504107 │      12841 │
└──────────┴───────────────────┴────────────┘
```

Doce mil ochocientas cuarenta y una lecturas caen en una casilla ya ocupada. Hay que decidir qué
hacer con ellas, y tirar una de las dos no es una opción de este curso.

### Paso 7. Fundir sin perder nada

```sql
SELECT casilla,
       count(*)                 AS lecturas,
       round(avg(TP2), 3)       AS TP2,
       max(DV_eletric)          AS DV_eletric
FROM (SELECT time_bucket(INTERVAL 10 SECOND, timestamp) AS casilla, *
      FROM telemetria)
GROUP BY casilla
ORDER BY lecturas DESC
LIMIT 3;
```

```anota
avg(TP2) | la media de las lecturas que cayeron en esa casilla; con una sola, es esa
max(DV_eletric) | el máximo de una señal de cero y uno: si estuvo abierta en algún momento, cuenta como abierta
count(*) AS lecturas | cuántas lecturas se fundieron ahí, guardado como columna para que se vea
```

Las analógicas se promedian y las digitales se quedan con el máximo, porque una válvula que
estuvo abierta en algún momento de esos diez segundos estuvo abierta. Y `lecturas` deja la fusión
a la vista en vez de esconderla.

### Paso 8. La rejilla entera, con sus huecos

```sql
SELECT timestamp, medido, lecturas, TP2
FROM plata
WHERE timestamp BETWEEN TIMESTAMP '2020-06-12 00:54:30'
                    AND TIMESTAMP '2020-06-12 00:55:30'
ORDER BY timestamp;
```

```anota
FROM plata | la capa nueva, que ya no es la telemetría cruda
medido | una columna nueva: verdadero si esa casilla tiene lectura detrás
```

```salida
┌─────────────────────┬─────────┬──────────┬────────┐
│      timestamp      │ medido  │ lecturas │  TP2   │
├─────────────────────┼─────────┼──────────┼────────┤
│ 2020-06-12 00:54:30 │ false   │        0 │   NULL │
│ 2020-06-12 00:54:40 │ false   │        0 │   NULL │
│ 2020-06-12 00:54:50 │ false   │        0 │   NULL │
│ 2020-06-12 00:55:00 │ true    │        1 │  7.212 │
│ 2020-06-12 00:55:10 │ true    │        1 │  7.422 │
│ 2020-06-12 00:55:20 │ true    │        1 │  7.576 │
│ 2020-06-12 00:55:30 │ true    │        1 │   7.79 │
└─────────────────────┴─────────┴──────────┴────────┘
```

Ahí está el cambio de verdad de este módulo. **El hueco ha pasado de ser la ausencia de una fila a
ser una fila que dice que no hay nada.** En bronce nadie podía verlo sin restar marcas de tiempo.

## El resultado, medido

{{FIG:fig_m14_huecos}}

**Qué esperábamos.** Limpiar unos cuantos valores raros y dejar el dato más ordenado.

**Qué salió.** Que los valores raros eran casi todos. El ruido de coma flotante toca el **85,5 %**
de TP2 y el 98,6 % de `DV_pressure`. Redondear a tres decimales no es un retoque: es tocar más de
un millón de valores.

Y sobre todo, la rejilla destapó lo que estaba escondido. Las **1.841.760 casillas** de diez
segundos que caben entre la primera y la última lectura contienen solo **1.504.107** ocupadas.
Los otros **337.653** son huecos, el **18,3 %**.

En la figura se ve que no se reparten igual. Abril pierde el 24 % y febrero el 15 %.

{{FIG:fig_m14_remuestreo}}

El zoom enseña un hueco corriente: noventa casillas seguidas sin nada, y después el compresor
arrancando. Las cuatro primeras lecturas tras el hueco son las del paso 8, con la presión subiendo
de 7,212 a 7,79 bar en cuatro casillas.

**Qué significa.** El bronce parecía completo porque no tenía forma de enseñar lo que le faltaba.
Poner el dato en una rejilla no añade información: **convierte una ausencia en algo que se puede
contar**. Por eso la capa de plata pesa 23,85 MB contra los 22,06 del bronce.

Eso es lo que se paga: casi dos megas por poder ver los agujeros. A cambio, comparar una fila con
la anterior deja de depender de si el reloj saltó, y eso es todo lo que hará el gemelo.

**Y la comprobación que importa.** La plata conserva las **1.516.948** lecturas del bronce, ni una
menos, repartidas en sus 1.504.107 casillas. El script se niega a terminar si esa cuenta no sale,
y esa negativa es lo que cazó la primera versión, que se dejaba nueve de cada diez por el camino.

## Ojo

- **Limpiar no es tirar.** La plata conserva todas las lecturas del bronce. Lo que cambia es el
  formato y lo que se añade, nunca lo que desaparece.
- **Una bandera vale más que un borrado.** `dudoso` deja las 16.762 contradictorias a la vista.
  Quien haga un cálculo decide si las quiere, y esa decisión queda en su consulta.
- **El reloj de un registro no está donde crees.** Aquí camina, y cruzar por marca de tiempo
  exacta conservaba una de cada diez lecturas. Se comprueba contando, no suponiendo.
- **Fundir dos lecturas es una decisión y debe verse.** La columna `lecturas` dice cuántas hay
  detrás de cada casilla, así que nadie se encuentra un promedio sin saberlo.
- **Un hueco en la rejilla no es un cero.** Es NULL, y cualquier media que lo cruce devolverá
  NULL, que es lo correcto. El módulo 8 lo dejó dicho y aquí es estructural.
- **Rellenar los huecos es tentador y aquí no se hace.** Interpolar inventaría 337.653 medidas
  que nadie tomó. Si algún módulo del gemelo las necesita, las inventará él y lo declarará.

## Puente metalúrgico

Un laboratorio no entrega la ley que midió el equipo. Entrega la ley con su cifra significativa,
su fecha, y una nota cuando el ensayo salió fuera de control.

Esa nota es la columna `dudoso`. El laboratorio no borra el ensayo raro: lo entrega marcado, y
quien hace el balance decide si lo usa. Borrarlo dejaría el balance más limpio y escondería que
el equipo se está descalibrando.

Y las cifras significativas son el redondeo. Un espectrómetro que escupe 0,4987654321 no está
midiendo diez cifras: está midiendo cuatro y rellenando el resto. Publicarlas todas no es más
precisión, es menos honestidad.

## Repaso

### Qué hace la plata que el bronce se negaba a hacer

Decidir. Bronce guarda lo que llegó sin tocarlo, y eso deja los problemas intactos y aplazados.
Plata redondea el ruido, marca lo sospechoso y pone el dato en una rejilla regular. La diferencia
con una limpieza cualquiera es que cada decisión está en el código y su coste está medido.

### Por qué marcar las contradicciones y no borrarlas

Porque son 16.762 lecturas donde dos señales que deberían ser opuestas coinciden, y eso es
información sobre la instrumentación. Borrarlas dejaría la tabla más limpia y escondería un
sensor que falla. Marcadas, cualquiera puede excluirlas en su consulta, y la decisión queda a la
vista en vez de enterrada en la ingesta.

### Qué es remuestrear y por qué aquí no bastaba con cruzar por la marca de tiempo

Remuestrear es pasar unas medidas a un ritmo regular. Aquí no bastaba con cruzar porque el reloj
del registro camina. Cada hueco de nueve segundos le mueve la fase, así que las lecturas caen por
igual en los diez restos posibles de segundo. Cruzando por igualdad exacta se conservaba una de
cada diez, y hay que ajustar cada lectura a su casilla.

### Dos lecturas caen en la misma casilla de diez segundos. Qué haces

Fundirlas dejando rastro. Las analógicas se promedian y las digitales se quedan con el máximo,
porque una válvula abierta en algún instante de esos diez segundos estuvo abierta. Y una columna
guarda cuántas lecturas había, para que nadie se encuentre un promedio creyendo que es una medida.

### La plata ocupa más que el bronce. Para qué sirve entonces

Para que los huecos existan. El bronce parecía completo porque no tenía filas donde faltaban
datos, y solo restando marcas de tiempo se podía saber. La plata tiene 337.653 filas que dicen
«aquí no hay nada», y ese es todo el sobrecoste: casi dos megas por poder contar lo que falta.

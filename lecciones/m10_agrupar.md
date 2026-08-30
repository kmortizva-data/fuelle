---
module: 10
---

## En 30 segundos

- Un compresor normal de este tren trabaja en carga **3,42 horas al día**.
- El 18 de abril trabajó **23,81 horas de 24**. Ese día hubo una avería.
- Agrupar es pasar de 1.516.948 lecturas a una tabla de siete meses que cabe en la pantalla.
- La trampa: solo **91 de los 212 días** están completos. Promediarlos todos daría un número falso.
- Los cuatro días de avería documentada caen entre los seis de más carga del semestre.

## Qué resuelve este módulo

Hasta ahora cada consulta devolvía filas: muchas, y una por lectura. Ninguna respondía a una
pregunta de operación, porque las preguntas de operación no son sobre lecturas sueltas.

Nadie pregunta qué marcaba el sensor a las 04:31:20. Se pregunta cuánto trabajó ayer la máquina.

`GROUP BY` es lo que convierte lo primero en lo segundo. Es el verbo que hace útil una tabla
grande, y es la mitad del SQL que se escribe en un trabajo de verdad.

## Antes de la teoría: un ejemplo de juguete

Olvida el millón y medio de filas. Mira un turno de seis lecturas, una cada diez minutos.

| lectura | hora | en carga |
|---|---|---|
| 1 | 08:00 | sí |
| 2 | 08:10 | sí |
| 3 | 08:20 | no |
| 4 | 08:30 | no |
| 5 | 08:40 | sí |
| 6 | 08:50 | no |

**Cuenta a mano.** Hay seis lecturas. Tres dicen que sí. Tres dicen que no.

**Convierte a tiempo.** Cada lectura representa diez minutos, así que tres lecturas en carga son
treinta minutos. El compresor trabajó **media hora de esa hora**.

Ese número, treinta minutos, se llama tiempo de carga. Y la cuenta que acabas de hacer tiene
exactamente tres pasos: separar en grupos, contar dentro de cada grupo, y multiplicar por lo que
dura una lectura.

`GROUP BY` hace el primer paso. Los agregados hacen el segundo. La aritmética la pones tú.

Ahora cambia dos cosas y tienes el caso real: los grupos son días en vez de horas, y cada lectura
dura diez segundos en vez de diez minutos.

## Glosario

- **Agrupar.** Repartir las filas en montones según el valor de una columna. Todas las lecturas
  del 18 de abril van al montón del 18 de abril.
- **Agregado.** Una función que recibe un montón entero y devuelve un solo número. Contar, sumar
  y promediar son las tres que se usan siempre.
- **Grano.** A qué corresponde una fila. Antes de agrupar, el grano es una lectura. Después, el
  grano es un día. Cambiar el grano es lo que hace `GROUP BY`.
- **Ciclo de trabajo.** La fracción del tiempo que una máquina pasa trabajando de verdad. Aquí,
  las horas que el compresor pasa en carga.
- **En carga.** El compresor comprimiendo aire de verdad. Lo contrario es girar en vacío, que
  gasta corriente y no llena el depósito.

## Paso a paso

### Paso 1. Decidir qué es una fila del resultado

Antes de escribir nada, contesta a esto: qué quieres que sea cada fila de la tabla final.

Aquí la respuesta es un día. Eso ya te dice lo que va detrás de `GROUP BY`.

Es la decisión más importante del módulo y la que más se salta la gente. Si te equivocas de
grano, la consulta funciona y el número está mal, que es la peor combinación posible.

### Paso 2. Elegir la señal que dice si está trabajando

El fichero trae quince señales y tres de ellas hablan de lo mismo. La ficha oficial dice que
`DV_eletric` se activa cuando el compresor funciona en carga, que `COMP` se activa cuando **no**
entra aire, y que la corriente del motor ronda los 7 A en carga.

Tres fuentes para un solo hecho piden comprobar que están de acuerdo. Lo hacemos en el paso 4.

### Paso 3. Convertir lecturas en tiempo

Contar lecturas no es medir tiempo. Se parecen tanto que es fácil confundirlos.

Una lectura cada diez segundos significa que cada lectura en carga vale diez segundos de trabajo.
Dividiendo entre 3.600 quedan horas. Ese `× 10 / 3600` es toda la física de la lección.

## El código, por partes

### Paso 4. Comprobar que las señales están de acuerdo

Antes de fiarnos de `DV_eletric`, miramos qué dicen las otras dos cuando ella dice que sí.

```sql
SELECT DV_eletric, COMP, count(*) AS lecturas,
       round(avg(Motor_current), 2) AS corriente_media
FROM telemetria
GROUP BY DV_eletric, COMP
ORDER BY lecturas DESC;
```

```anota
SELECT | elige qué columnas quieres ver en el resultado
count(*) | cuenta las filas de cada montón, sin mirar ninguna columna
AS lecturas | le pone nombre a la columna calculada, para poder leerla
avg(...) | promedia los valores del montón
GROUP BY a, b | hace un montón por cada combinación distinta de a y b
ORDER BY lecturas DESC | ordena de mayor a menor, DESC es descendente
```

```salida
DV_eletric  COMP    lecturas    corriente_media
         0     1   1,263,084               1.34
         1     0     237,102               5.73
         0     0      10,226               2.69
         1     1       6,536               3.91
```

Las dos primeras filas son las esperadas: cuando una señal dice que sí, la otra dice que no, y la
corriente acompaña. Las dos últimas no deberían existir.

**16.762 lecturas, el 1,1 %, tienen las dos señales diciendo lo mismo.** Seis mil de ellas
afirman que el compresor está en carga y que no entra aire a la vez, cosa imposible. Se apunta y
se sigue: el módulo 16 se ocupa de esto. Para contar horas, un 1,1 % no cambia la respuesta.

### Paso 5. Agrupar por día

Ahora la consulta de verdad. Cada fila del resultado será un día.

Esta la puedes correr tú: el botón trae el motor de base de datos al navegador y la ejecuta contra los datos reales del compresor. Cámbiala y vuelve a pulsar.

```sql-vivo
SELECT day,
       count(*) AS lecturas,
       sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas_de_carga
FROM telemetria
GROUP BY day
ORDER BY horas_de_carga DESC
LIMIT 6;
```

```anota
sum(CASE WHEN ... THEN 1 ELSE 0 END) | cuenta solo las filas que cumplen la condición, poniendo un 1 en las que sí y un 0 en las que no
* 10 | cada lectura vale diez segundos
/ 3600.0 | de segundos a horas; el punto obliga a dividir con decimales
LIMIT 6 | corta el resultado en seis filas, después de ordenarlo
```

```salida
day          lecturas   horas_de_carga
2020-04-18       8663            23.81
2020-06-05       8716            15.41
2020-03-12       8202            13.24
2020-07-15       8661            11.57
2020-05-13       8716            11.31
2020-05-30       8617             8.06
```

Seis días. Y cuatro de ellos son fechas de avería documentada.

### Paso 6. El promedio, solo sobre días completos

Para saber cuánto es normal hace falta un promedio, y aquí aparece la trampa del módulo.

```sql
SELECT round(avg(horas_de_carga), 2) AS media,
       min(horas_de_carga) AS minimo,
       max(horas_de_carga) AS maximo
FROM (
    SELECT day,
           count(*) AS lecturas,
           sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas_de_carga
    FROM telemetria GROUP BY day
)
WHERE lecturas > 0.9 * 8640;
```

```anota
FROM ( ... ) | una consulta puede beber de otra consulta; la de dentro se resuelve primero
8640 | las lecturas que caben en un día entero: 24 horas por 360 lecturas cada hora
WHERE lecturas > 0.9 * 8640 | se queda solo con los días que tienen al menos el 90 % de sus lecturas
```

```salida
media   minimo   maximo
 3.42     1.11    23.81
```

### Paso 7. Filtrar grupos con HAVING, y el orden en que SQL trabaja

En el paso 5 la consulta salió sin filtrar días incompletos. Si intentas añadirle un `WHERE`
para quedarte solo con los días completos, no funciona.

La razón está en el orden. **SQL no se ejecuta en el orden en que se escribe.** Primero coge las
filas (`FROM`), luego las filtra una a una (`WHERE`), después las reparte en montones
(`GROUP BY`), y solo entonces existe algo llamado «cuántas lecturas tiene este día».

`WHERE` llega demasiado pronto: cuando actúa, los montones todavía no existen. Para filtrar
montones hay otra palabra.

```sql
SELECT day,
       count(*) AS lecturas,
       round(sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0, 2) AS horas_de_carga
FROM telemetria
GROUP BY day
HAVING count(*) > 0.9 * 8640
ORDER BY horas_de_carga DESC
LIMIT 6;
```

```anota
HAVING | filtra montones, no filas; solo se puede usar después de GROUP BY
count(*) > 0.9 * 8640 | la misma condición del paso 6, pero sin necesitar la consulta de dentro
```

```salida
day          lecturas   horas_de_carga
2020-04-18       8663            23.81
2020-06-05       8716            15.41
2020-03-12       8202            13.24
2020-07-15       8661            11.57
2020-05-13       8716            11.31
2020-05-30       8617             8.06
```

Mismo resultado que el paso 5, pero ahora con la garantía de que ningún día partido se ha
colado. Y más corto que el paso 6, que necesitaba una consulta dentro de otra.

Entonces, ¿por qué el paso 6 usaba esa consulta anidada? Porque allí el promedio se calculaba
**sobre un valor que ya era el resultado de agrupar**. Eso es un segundo nivel, y `HAVING` no
llega: hace falta agrupar una vez, guardar el resultado, y volver a agrupar encima. El módulo 11
va de eso.

## El resultado, medido

**Qué esperábamos.** Un compresor de servicio en un tren debería pasar bastante más tiempo parado
que trabajando. Un valor de entre dos y cinco horas al día sería lo razonable.

**Qué salió.** **3,42 horas de carga al día**, promediadas sobre los 91 días completos. El rango
va de 1,11 a 23,81. Mes a mes:

| mes | días completos | horas de carga |
|---|---|---|
| 2020-02 | 11 | 1,45 |
| 2020-03 | 15 | 3,58 |
| 2020-04 | 11 | 4,27 |
| 2020-05 | 13 | 3,61 |
| 2020-06 | 16 | 4,02 |
| 2020-07 | 13 | 3,78 |
| 2020-08 | 12 | 2,81 |

**Qué significa.** La media cae dentro de lo razonable, así que la señal elegida se comporta como
debe. Lo interesante no es la media, es lo que se sale de ella.

El 18 de abril el compresor estuvo en carga el **98,9 %** del día. Es siete veces lo normal, y esa
fecha es la primera avería documentada del fichero. La presión de la red no se movió: el sistema
la mantuvo. Lo que se movió fue el esfuerzo necesario para mantenerla.

Ahí está la idea que sostiene el resto del curso, y ha aparecido con una consulta de agrupar,
mucho antes de construir ningún modelo.

Dos avisos, para no venderlo mejor de lo que es. Dos de esos seis días, el 12 de marzo y el 13 de
mayo, **no figuran como avería en ningún parte**. O son falsas alarmas, o son averías que nadie
reportó. No se sabe, y se dice.

## Ojo

- **Promediar días incompletos miente.** Solo 91 de los 212 días tienen el 90 % de sus lecturas.
  La mediana de un día es 7.435 lecturas, cuando caben 8.640. Sin el filtro, un día con dos horas
  de registro entra en la media como si fuera un día entero.
- **Contar lecturas no es medir tiempo.** Solo son lo mismo si el muestreo es regular, y aquí no
  lo es del todo: el módulo 1 midió 179.426 huecos irregulares.
- **`count(*)` cuenta filas; `count(columna)` cuenta valores presentes.** Se parecen y dan
  distinto en cuanto hay algún hueco.
- **Una columna que no está en `GROUP BY` no puede salir en `SELECT`** sin decir cómo se resume.
  Es el error que más sale al empezar, y el mensaje que devuelve la base de datos lo explica bien.
- **`WHERE` no puede filtrar un promedio.** El orden real es `FROM`, `WHERE`, `GROUP BY`,
  `HAVING`, `SELECT`, `ORDER BY`, `LIMIT`. Cuando `WHERE` actúa, los montones aún no existen.
  Entender ese orden arregla la mitad de los errores de quien empieza.
- **El grano cambia debajo de tus pies.** Después de agrupar por día, una fila ya no es una
  lectura. Todo lo que escribas a partir de ahí tiene que contar con eso.

## Hazlo tú

La consulta de abajo funciona y agrupa por día. Cámbiala para que agrupe por mes.

```reto
pregunta: Devuelve dos columnas, `mes` y `horas_de_carga`, con el promedio de horas de carga de cada mes, contando solo los días completos. Siete filas, de `2020-02` a `2020-08`.
inicio: SELECT day,
       round(sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0, 2) AS horas
FROM telemetria
GROUP BY day
ORDER BY day;
esperado: m10_horas_por_mes
pista: Hay que agrupar dos veces. Primero por día, para tener las horas de cada día, y después por mes para promediarlas. La consulta de dentro va entre paréntesis después de FROM, como en el paso 6. Para sacar el mes de una fecha, `strftime(day, '%Y-%m')`.
solucion: SELECT strftime(day, '%Y-%m') AS mes,
       round(avg(horas), 2) AS horas_de_carga
FROM (
    SELECT day,
           count(*) AS lecturas,
           sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas
    FROM telemetria
    GROUP BY day
)
WHERE lecturas > 0.9 * 8640
GROUP BY mes
ORDER BY mes;
```

## Puente metalúrgico

En una celda de flotación, la ley del concentrado la sostiene el lazo de control. Si la
alimentación se ensucia, el operador sube la dosificación de colector y la ley se mantiene. Quien
mire solo la ley dirá que no ha pasado nada.

Lo que ha pasado se ve en el consumo de reactivo, no en la ley.

Aquí ocurre exactamente lo mismo con otro equipo. La presión de la red es la ley: el control la
sostiene y no se mueve. El ciclo de trabajo es la dosificación: es lo que sube cuando algo va
mal. Por eso este módulo mide las horas de carga y no la presión media.

Es la misma lección que dejó el análisis causal del proyecto de sílice, en otra máquina: **mira
la variable manipulada, porque la controlada te va a mentir.**

## Repaso

### Por qué agrupas por día y no por hora, si el dato viene cada diez segundos

Porque el grano lo decide la pregunta, no el dato. La pregunta es cuánto trabaja la máquina en
una jornada, así que cada fila del resultado tiene que ser un día. El dato de diez segundos sigue
ahí debajo, y agrupar por hora sería otra consulta para otra pregunta.

### Qué hace exactamente `sum(CASE WHEN condición THEN 1 ELSE 0 END)`

Cuenta solo las filas que cumplen la condición. Pone un uno donde se cumple y un cero donde no, y
suma. Es la forma portátil de contar con condición, y funciona en cualquier base de datos.

### Por qué filtras los días incompletos, y por qué al 90 %

Porque un día con dos horas de registro entraría en la media como si fuera un día entero y la
hundiría. El 90 % no es un número sagrado: es el corte que deja fuera los días manifiestamente
partidos sin tirar los que solo tienen un hueco pequeño. Con otro umbral la media se mueve poco,
y eso conviene comprobarlo antes de defenderlo.

### El día de más carga fue de 23,81 horas. Cómo sabes que no es un error del sensor

No lo sé por la consulta sola, y ese es el punto. Lo que sé es que esa fecha coincide con una
avería documentada por la empresa, y que otras tres fechas de avería también están entre las seis
de más carga. Cuatro coincidencias sobre cuatro no prueban causalidad, pero descartan que sea
casualidad del sensor.

### Alguien te dice que el ciclo de trabajo medio de la flota es 3,4 horas. Qué preguntas

Sobre qué días está calculado. Un promedio sin decir su denominador no significa nada. En este
mismo fichero, la media sobre los 212 días y la media sobre los 91 completos son dos números
distintos, y solo uno de los dos responde a la pregunta que se hizo.

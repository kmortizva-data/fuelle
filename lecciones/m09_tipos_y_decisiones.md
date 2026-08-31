---
module: 9
---

## En 30 segundos

- Pedir `TP2 = 8.2` encuentra **107 lecturas**. Las que querías eran **5.237**.
- No falla porque no encuentre nada: falla porque encuentra el **2 %** y parece bien.
- La culpa no es del número, es del **tipo**. En DECIMAL sale exacto y en DOUBLE no.
- `CASE` traduce un número a un estado, y así la corriente se vuelve parado, vacío o carga.
- El compresor pasa **54,6 % parado, 30,1 % en vacío y 15,2 % en carga**.

## Qué resuelve este módulo

Hasta aquí las columnas eran números y ya está. Este módulo mira qué **tipo** tiene cada una,
porque el tipo decide cómo se comparan y cuándo mienten.

Y después construye la primera regla del curso: convertir una medida continua en un estado con
nombre. Eso es lo que hace útil un dato en bruto.

## Antes de la teoría: un ejemplo de juguete

Seis lecturas de un turno, tal como las enseña la pantalla:

| hora | presion | corriente |
|---|---|---|
| 06:00 | 8,20 | 0 |
| 06:10 | 8,20 | 0 |
| 06:20 | 8,15 | 4 |
| 06:30 | 8,20 | 4 |
| 06:40 | 8,31 | 6 |
| 06:50 | 8,15 | 6 |

**Primera pregunta: ¿cuántas veces la presión fue exactamente 8,20?** Cuentas y salen **tres**.

Ahora mira lo que el sensor midió de verdad, que trae un decimal más:

| hora | lo que enseña la pantalla | lo que hay guardado |
|---|---|---|
| 06:00 | 8,20 | 8,202 |
| 06:10 | 8,20 | 8,200 |
| 06:30 | 8,20 | 8,198 |

Preguntando por el valor exacto, **el ordenador encuentra una, no tres**. Las otras dos no son
8,2: son 8,202 y 8,198, y la pantalla te las enseñaba iguales porque solo tenía sitio para dos
decimales.

Y ahí está lo peligroso: no da error, y una es un número perfectamente creíble.

La pantalla redondea. La comparación no. Esa frase es medio módulo.

**Segunda pregunta: ¿en qué estado estaba el motor en cada fila?** Con la regla de que menos de
1 A es parado, de 1 a 5 A es vacío y más de 5 A es carga, salen **dos de cada**. Un tercio del
turno en cada estado.

Esa traducción, de un número a una palabra, es lo que hace `CASE`.

## Glosario

- **Tipo.** Qué clase de valor guarda una columna, y por tanto qué operaciones tienen sentido.
- **DOUBLE.** El tipo de los números con coma que usan casi todos los sensores. Guarda el número
  en binario y **no todos los decimales caben exactos**.
- **DECIMAL.** Otro tipo para números con coma que sí guarda los decimales exactos. Se usa en
  dinero, donde un céntimo perdido es un problema.
- **Coma flotante.** La forma en que DOUBLE guarda los números. Rápida, y aproximada.
- **`CASE`.** La forma de escribir «si pasa esto, entonces aquello» dentro de una consulta.
- **`CAST`.** Convertir un valor de un tipo a otro, a propósito.
- **Umbral.** El valor a partir del cual algo cambia de estado. Aquí, los amperios que separan
  parado de vacío y vacío de carga.

## Paso a paso

### Paso 1. Mirar de qué tipo es cada columna

Antes de comparar nada conviene saber con qué se está comparando. La base de datos lo dice, y no
hay que adivinarlo.

### Paso 2. Preguntar por el umbral de la ficha, y contar lo que sale

La ficha del dataset dice que el compresor arranca cuando la presión baja de 8,2 bar. Parece una
pregunta directa: cuántas lecturas hay a 8,2. Se hace, se cuenta, y luego se hace bien y se
vuelve a contar.

### Paso 3. Elegir los cortes mirando la distribución

La ficha dice que el motor consume unos 0 A parado, unos 4 A en vacío y unos 7 A en carga. Eso
son tres puntos, no dos cortes, y hay que decidir dónde poner la frontera.

Se pone donde la distribución tiene sus valles, que es donde menos lecturas hay y por tanto donde
menos gente se clasifica mal.

### Paso 4. Comprobar la regla con una señal que no se usó para hacerla

Y este paso es el que separa una regla de una opinión. `DV_eletric` marca la carga por su cuenta,
sin mirar la corriente. Si los cortes están bien, casi todas las lecturas por encima del corte de
carga tienen que llevar esa marca.

## El código, por partes

### Paso 5. Qué tipo tiene cada cosa

```sql
SELECT typeof(TP2) AS tipo_de_la_columna,
       typeof(0.1) AS tipo_de_un_literal,
       0.1 + 0.2 = 0.3 AS suman_exacto,
       0.1::DOUBLE + 0.2::DOUBLE = 0.3::DOUBLE AS suman_exacto_en_double
FROM telemetria LIMIT 1;
```

```anota
typeof(x) | dice de qué tipo es un valor, sin tener que adivinarlo
0.1 | un número escrito a mano en la consulta; SQL elige un tipo para él
::DOUBLE | convierte a coma flotante; los dos puntos dobles son la forma corta de CAST
= | comparar; aquí el resultado es verdadero o falso, y sale como una columna más
```

```salida
┌────────────────────┬────────────────────┬──────────────┬────────────────────────┐
│ tipo_de_la_columna │ tipo_de_un_literal │ suman_exacto │ suman_exacto_en_double │
├────────────────────┼────────────────────┼──────────────┼────────────────────────┤
│ DOUBLE             │ DECIMAL(2,1)       │ true         │ false                  │
└────────────────────┴────────────────────┴──────────────┴────────────────────────┘
```

Lee esa fila despacio, porque desmonta lo que casi todo el mundo cree.

El famoso «0,1 más 0,2 no es 0,3» **es falso aquí**: sale `true`. Porque un número escrito a mano
en la consulta es DECIMAL, y DECIMAL guarda los decimales exactos.

El fallo aparece solo al pedir el tipo coma flotante, con `::DOUBLE`, y entonces sale `false`. Y
mira de qué tipo es `TP2`: **DOUBLE**. La columna del sensor está guardada precisamente en el
tipo que no es exacto.

### Paso 6. La pregunta directa, y lo que se deja fuera

```sql-vivo
SELECT count(*) AS con_el_igual
FROM telemetria
WHERE TP2 = 8.2;
```

```anota
WHERE TP2 = 8.2 | pide las filas cuya presión sea exactamente ese valor
count(*) AS con_el_igual | cuenta cuántas son y le pone nombre al resultado
```

```salida
┌──────────────┐
│ con_el_igual │
│    int64     │
├──────────────┤
│          107 │
└──────────────┘
```

Ciento siete. Cámbialo por `WHERE round(TP2, 1) = 8.2` y vuelve a correrlo.

### Paso 7. La pregunta bien hecha

```sql
SELECT count(*) AS redondeando
FROM telemetria
WHERE round(TP2, 1) = 8.2;
```

```anota
round(TP2, 1) | redondea a un decimal antes de comparar, que es lo que hace el ojo al leer 8,2
```

```salida
┌─────────────┐
│ redondeando │
│    int64    │
├─────────────┤
│        5237 │
└─────────────┘
```

Cinco mil doscientas treinta y siete. La pregunta directa encontraba el **2 %** de eso.

### Paso 8. Traducir la corriente a un estado

```sql-vivo
SELECT CASE WHEN Motor_current < 1 THEN 'parado'
            WHEN Motor_current < 5 THEN 'en vacio'
            ELSE 'en carga' END AS estado,
       count(*) AS lecturas,
       round(avg(Motor_current), 2) AS corriente_media,
       round(avg(DV_eletric) * 100, 1) AS por_ciento_marcado_en_carga
FROM telemetria
GROUP BY estado
ORDER BY corriente_media;
```

```anota
CASE WHEN ... THEN ... | si se cumple la condición, el valor es ese; si no, se prueba la siguiente
ELSE | lo que vale cuando no se cumplió ninguna condición anterior
END | cierra el CASE; sin él la consulta no es válida
AS estado | el CASE produce una columna nueva, y aquí se le pone nombre
GROUP BY estado | agrupa por esa columna recién inventada, que ahora existe como cualquier otra
avg(DV_eletric) * 100 | el porcentaje de filas marcadas en carga, porque la señal vale cero o uno
```

```salida
┌──────────┬──────────┬─────────────────┬─────────────────────────────┐
│  estado  │ lecturas │ corriente_media │ por_ciento_marcado_en_carga │
├──────────┼──────────┼─────────────────┼─────────────────────────────┤
│ parado   │   829000 │            0.04 │                         0.2 │
│ en vacio │   457356 │            3.79 │                         3.4 │
│ en carga │   230592 │            5.82 │                        98.1 │
└──────────┴──────────┴─────────────────┴─────────────────────────────┘
```

La última columna es la que valida la regla, y no se usó para construirla.

## El resultado, medido

{{FIG:fig_m09_coma_flotante}}

**Qué esperábamos.** Cero filas. Es lo que cuentan todos los manuales sobre la coma flotante.

**Qué salió.** Peor: devolvió **107**. En una pantalla de dos decimales se ven como 8,20 nada
menos que **498** lecturas, y las que hay alrededor de 8,2 con un decimal son **5.237**. Contra
esas, el igual encontró el **2,0 %**.

Cero filas habría sido una suerte, porque un resultado vacío hace sospechar a cualquiera. Ciento
siete lecturas es un número creíble, cabe en un informe y nadie lo mira dos veces.

En la figura se ve por qué. Alrededor de 8,2 bar no hay un valor: hay una nube de valores
parecidos. El igual cae en una sola rendija de esa nube.

{{FIG:fig_m09_tres_estados}}

**Y la regla de los tres estados.** El reparto del tiempo sale
**54,6 / 30,1 / 15,2 %**: parado, en vacío y en carga.

La figura enseña por qué los cortes están en 1 y en 5 A. Son los dos valles de la distribución,
las zonas donde casi no hay lecturas. Poner una frontera donde hay pocos datos es ponerla donde
pocas lecturas se clasifican mal.

**Qué significa.** La regla se sostiene sola: el **98,1 %** de las lecturas que llama «en carga»
llevan la marca de `DV_eletric`, una señal que no se usó para escribirla. Dos formas
independientes de saber lo mismo coinciden.

Y hay un desacuerdo con la ficha que conviene decir. La ficha declara unos **7 A** en carga y en
el fichero lo más frecuente son **6,0 A**. En la figura, la línea de puntos de los 7 A cae en una
zona casi vacía. No es un error grave, y es el segundo sitio del curso donde el papel y el
fichero no coinciden del todo.

## Ojo

- **Nunca compares un decimal con el igual.** Ni en SQL ni en ningún otro sitio. Se compara con
  `round()`, con `BETWEEN` o pidiendo que la diferencia sea pequeña.
- **El fallo no es «no encuentra nada», es «encuentra algo».** Un cero llama la atención; un 2 %
  se publica. Por eso este error sobrevive tanto tiempo en los informes.
- **El tipo manda sobre el número.** El mismo 0,1 es exacto como DECIMAL e inexacto como DOUBLE.
  Antes de comparar, mira `typeof`.
- **Aquí hay dos causas, y la común no es la famosa.** La que más gente conoce es la binaria, la
  de DOUBLE. La que de verdad rompe esta consulta es más tonta: **el sensor da tres decimales y
  la pantalla enseña dos**. Las dos llevan al mismo sitio, y las dos se arreglan igual.
- **Un `CASE` sin `ELSE` deja huecos.** Las filas que no cumplen ninguna condición se quedan en
  NULL, y el módulo 8 ya enseñó lo silencioso que es eso.
- **El orden de los `WHEN` importa.** Se evalúan de arriba abajo y gana el primero que se cumple.
  Poniendo `< 5` antes que `< 1`, todo lo parado acabaría clasificado como vacío.
- **Los cortes son una decisión, no un dato.** Aquí están justificados con la distribución y
  comprobados con una segunda señal. Sin eso serían dos números elegidos a ojo.

## Puente metalúrgico

Una ley de corte no se elige con el igual. Nadie dice «mándame al concentrador el mineral que
tenga exactamente 0,5 % de cobre», porque no existe una muestra con exactamente esa ley: existen
0,4987 y 0,5013.

Lo que se dice es «por encima de 0,5». Un umbral, no una igualdad.

Y esa ley de corte tampoco se copia del informe de otra mina. Se calcula con el precio del metal,
el coste de proceso y la recuperación de la planta, y se revisa cuando cambian. Es exactamente lo
que hacen los dos cortes de amperios de este módulo: se eligen mirando los datos propios, y se
comprueban contra algo que no se usó para elegirlos.

## Hazlo tú

```reto
pregunta: Escribe la regla que reparte las lecturas en los tres estados y devuelve dos columnas, `estado` y `horas`, con las horas que el compresor pasó en cada uno. Tres filas. Cada lectura son 10 segundos.
inicio: SELECT CASE WHEN Motor_current < 1 THEN 'parado'
            WHEN Motor_current < 5 THEN 'en vacio'
            ELSE 'en carga' END AS estado,
       count(*) AS lecturas
FROM telemetria
GROUP BY estado
ORDER BY lecturas DESC;
esperado: m09_horas_por_estado
pista: El `CASE` ya está escrito en el punto de partida y no hay que tocarlo. Lo que cambia es la segunda columna: en vez de contar lecturas, hay que pasar esas lecturas a horas. Cada lectura son 10 segundos y una hora son 3.600, así que se multiplica por 10 y se divide entre 3600.0. Redondea a un decimal con `round(..., 1)`.
solucion: SELECT CASE WHEN Motor_current < 1 THEN 'parado'
            WHEN Motor_current < 5 THEN 'en vacio'
            ELSE 'en carga' END AS estado,
       round(count(*) * 10 / 3600.0, 1) AS horas
FROM telemetria
GROUP BY estado
ORDER BY horas DESC;
```

## Repaso

### Por qué WHERE TP2 = 8.2 no encuentra lo que esperabas

Porque `TP2` es DOUBLE, que guarda los números en binario, y 8,2 no tiene una representación
binaria exacta. Lo que hay guardado son valores como 8,1999999999999993, que no son iguales a 8,2
aunque en pantalla se vean igual. El igual compara los bits, no lo que se ve.

### Y cómo se pregunta bien

Con un margen en vez de con una igualdad. `round(TP2, 1) = 8.2` redondea antes de comparar, que
es lo que hace el ojo al leer la pantalla. También sirve `TP2 BETWEEN 8.15 AND 8.25`. Lo
importante es decidir el margen a propósito, en vez de heredarlo del azar.

### Encontró 107 filas en vez de 5.237. Por qué es eso peor que encontrar cero

Porque cero se nota. Un resultado vacío hace que cualquiera revise la consulta. Ciento siete es
un número plausible que entra en un informe sin llamar la atención, y el error puede vivir años
ahí dentro. Los fallos que dan un resultado creíble son los caros.

### Para qué sirve CASE si ya tienes el número

Para convertir una medida en una decisión. Nadie opera una planta preguntándose cuántos amperios
consume el motor: se pregunta si está parado, en vacío o en carga. `CASE` es donde se escribe esa
traducción, una sola vez y a la vista, en vez de repartirla por hojas de cálculo distintas.

### Cómo sabes que los cortes de 1 A y 5 A son los correctos

Por dos motivos, y ninguno es la ficha. Primero, están en los valles de la distribución, donde
casi no hay lecturas y por tanto casi nada se clasifica mal. Segundo, y más importante: el 98,1 %
de lo que la regla llama «en carga» lleva la marca de `DV_eletric`. Esa señal es distinta y no se
usó para construir la regla. Cuando dos caminos independientes llegan al mismo sitio, la regla es
más que una opinión.

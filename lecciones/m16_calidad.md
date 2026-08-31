---
module: 16
---

## En 30 segundos

- Un contrato de datos es una lista de promesas **escritas como código que corre**.
- Se prueba rompiéndolo: cinco averías de las que llegan un lunes cualquiera.
- La primera versión, con **7 promesas**, cazó **4 de 5**. Una se le escapó entera.
- Con la promesa que faltaba son **8**, y caza **5 de 5**.
- La que faltaba: miraba si estaban las columnas acordadas, pero no si sobraba alguna.

## Qué resuelve este módulo

El lago ya tiene tres fuentes y dos capas. A partir de aquí el problema deja de ser construirlo y
pasa a ser que siga funcionando el lunes.

Un contrato es lo que convierte «esto debería venir así» en algo que se entera cuando deja de
venir así. Y como cualquier guarda de este curso, **no vale nada hasta que se le ve fallar**.

## Antes de la teoría: un ejemplo de juguete

Un laboratorio te manda cada día un fichero con la ley de cobre de cada lote:

| lote | ley |
|---|---|
| L1 | 0,8 |
| L2 | 1,2 |
| L3 | 1,0 |

Tú calculas el cobre del día multiplicando por las toneladas. **Media de 1,0 %.**

Un lunes llega esto:

| lote | ley |
|---|---|
| L1 | 800 |
| L2 | 1200 |
| L3 | 1000 |

El laboratorio cambió de equipo y ahora entrega en **partes por millón** en vez de en por ciento.
El fichero es perfectamente válido: tres filas, dos columnas, números correctos. Nada da error.

Y tu informe dice que el mineral tiene una ley media del **1.000 %**.

Ahora imagina tres promesas escritas antes de que pasara:

1. **El fichero trae las columnas `lote` y `ley`, y ninguna más.**
2. **`ley` está entre 0 y 5.**
3. **`lote` no se repite.**

La segunda se habría roto ese lunes y el fichero no habría entrado. Eso es un contrato: no
documentación, sino **una condición que impide el paso**.

Fíjate en la primera promesa, porque tiene truco y este módulo se tropezó con él. Dice dos cosas:
que las columnas estén, y que no haya otras. Comprobar solo la mitad es fácil, y deja pasar el día
en que aparece una columna nueva.

## Glosario

- **Contrato de datos.** El conjunto de promesas que una tabla cumple, escrito como código y
  ejecutado en cada corrida.
- **Promesa.** Una condición concreta y comprobable. «La presión está en bar» no lo es; «TP2 está
  entre -2 y 15» sí.
- **Prueba de datos.** Cada comprobación individual del contrato.
- **Esquema.** La lista de columnas de una tabla, con sus nombres y sus tipos.
- **Deriva de esquema.** Un cambio de esquema sin avisar: una columna que se va, otra que llega,
  otra renombrada.
- **Falso verde.** Una comprobación que pasa siempre, incluso cuando debería fallar. Es peor que
  no tener ninguna, porque da confianza.

## Paso a paso

### Paso 1. Escribir las promesas como consultas que devuelven cero filas

El truco de forma que hace útil un contrato: cada promesa es una consulta en busca de **los
incumplidores**. Si devuelve cero filas, la promesa se cumple.

Así el mensaje de error ya trae los datos culpables dentro, en vez de un «algo falla» que obliga a
investigar desde cero.

### Paso 2. Correrlo sobre la capa de verdad

Sobre la plata del módulo 14, el contrato tiene que pasar entero. Si no pasa, el problema no es
del contrato: es de la capa, y hay que arreglarla antes de seguir.

### Paso 3. Romperlo a propósito, cinco veces

Y aquí está lo que separa este módulo de una lista de buenas intenciones. Se coge la capa, se
estropea de cinco formas distintas, y se mira cuántas caza el contrato.

Las cinco son averías reales de las que llegan un lunes: una columna renombrada, una unidad
cambiada, una columna nueva, una ingesta que corrió dos veces y un valor imposible.

### Paso 4. Mirar la que se escapa

Porque se escapó una, y esa es la lección del módulo.

## El código, por partes

### Paso 5. Una promesa, escrita

```sql
SELECT timestamp, count(*) AS veces
FROM plata
GROUP BY timestamp
HAVING count(*) > 1;
```

```anota
HAVING count(*) > 1 | se queda con los grupos que tienen más de una fila, o sea las marcas repetidas
```

```salida
┌───────────┬───────┐
│ timestamp │ veces │
├───────────┴───────┤
│      0 filas      │
└───────────────────┘
```

Cero filas quiere decir que la promesa se cumple. Y si algún día devuelve algo, lo que devuelve es
justo la lista de marcas de tiempo duplicadas, lista para investigar.

### Paso 6. El contrato entero, y las cinco roturas

```python
for rotura, sql in ROTURAS.items():
    roto = duckdb.connect()
    roto.execute(f"CREATE VIEW datos AS {sql}")
    cazada = revisa(roto, completo)
```

```anota
ROTURAS | un diccionario de nombre de avería y la consulta que la provoca sobre una copia
CREATE VIEW datos AS ... | la copia estropeada se llama igual que la buena, así el contrato no cambia
revisa(roto, completo) | corre las ocho promesas contra esa copia y devuelve las que se rompen
```

```salida
  el contrato tiene 8 promesas
  sobre la plata de verdad se incumplen: 0

  y ahora, rompiéndolo a propósito:
    la caza    una columna llega con otro nombre
    la caza    la presion llega en milibares
    la caza    aparece una columna que nadie anuncio   (la primera versión la dejaba pasar)
    la caza    la ingesta corrio dos veces
    la caza    un recuento de lecturas negativo
```

### Paso 7. Lo que decía la promesa incompleta

```sql
SELECT column_name
FROM (DESCRIBE SELECT * FROM plata)
WHERE column_name IN ('timestamp', 'day', 'lecturas', 'medido', 'dudoso');
```

```anota
DESCRIBE SELECT * FROM plata | devuelve una fila por columna, con su nombre y su tipo
column_name IN (...) | se queda con las que están en la lista de acordadas
```

Esa consulta cuenta cuántas de las columnas acordadas están presentes. Y ahí está el agujero: **si
llega una columna de más, sigue habiendo veinte acordadas y la cuenta sale bien.**

### Paso 8. La promesa que faltaba

```sql
SELECT column_name
FROM (DESCRIBE SELECT * FROM plata)
WHERE column_name NOT IN ('timestamp', 'day', 'lecturas', 'medido', 'dudoso');
```

```anota
NOT IN (...) | al revés: se queda con las que NO están en la lista, o sea las que sobran
```

Es la misma consulta con la condición dada la vuelta, y es lo que faltaba. Una mira lo que debería
estar y la otra lo que no debería.

## El resultado, medido

{{FIG:fig_m16_contrato_roto}}

**Qué esperábamos.** Que el contrato cazara las cinco roturas. Estaban elegidas por mí, sabiendo
lo que el contrato comprobaba.

**Qué salió.** Cazó **4 de 5** con sus **7 promesas** iniciales. Se le escapó la columna nueva.

Y el motivo es exactamente el que se veía venir en el ejemplo de juguete. La promesa decía que las
veinte columnas acordadas estuvieran presentes, y con una columna de más **siguen estando las
veinte**. La comprobación pasa, y el esquema ha cambiado.

Con la promesa que faltaba, «no llegan columnas de más», el contrato tiene **8 promesas** y caza
**5 de 5**.

En la figura se ve de un vistazo. La columna de la rotura «columna nueva» tiene una sola casilla
encendida, y es la de la promesa de abajo, la que no estaba.

**Qué significa.** Un contrato incompleto no es medio contrato: es un **falso verde**. Da luz
verde a diario y por eso genera confianza, y el día que la deriva de esquema entra por el hueco
que no cubre, nadie mira.

Y de ahí la regla que este proyecto ya aplica a sus propios verificadores, ahora aplicada a los
datos: **una promesa que nunca se ha visto fallar no protege de nada.** La única forma de saber si
un contrato sirve es romper los datos a propósito y comprobar que se entera.

Fíjate también en la fila de arriba de la figura. La rotura de la columna renombrada enciende
cuatro promesas, no una: dos porque detectan el cambio y **dos porque ya ni siquiera pueden
ejecutarse**. Una consulta que pregunta por `TP2` cuando `TP2` ya no existe no da un resultado
malo: da un error. Ese error también es información del contrato, y por eso cuenta como promesa
rota en vez de tumbar la comprobación entera.

## Ojo

- **Comprobar que están las columnas no es comprobar el esquema.** Hacen falta las dos mitades:
  lo obligatorio y lo prohibido.
- **Una promesa vaga no es una promesa.** «La presión es razonable» no se puede ejecutar. «TP2
  está entre -2 y 15» sí, y el rango se elige mirando los datos, como los cortes del módulo 9.
- **El contrato se prueba rompiendo los datos, no releyéndolo.** Es la misma regla de los
  verificadores de este curso, y llegó por el mismo camino: uno de ellos tenía el bucle vacío y
  daba verde sin comparar nada.
- **Una promesa que no puede ejecutarse cuenta como rota.** Al desaparecer una columna, la
  consulta que preguntaba por ella falla, y esa es justo la noticia.
- **Un contrato demasiado estricto también es un problema.** Si salta cada semana por cosas que no
  importan, alguien lo desactivará, y volvemos al módulo 8: una alarma que suena siempre no es una
  alarma.
- **El contrato va en el repositorio, con el código.** Un documento de esquema en una carpeta
  compartida se queda desactualizado el primer mes y nadie se entera.

## Puente metalúrgico

Un laboratorio serio no entrega un resultado sin sus controles. En cada tanda mete una muestra de
referencia de ley conocida, un duplicado de una muestra real y un blanco.

Si la referencia no sale donde debe, la tanda entera se repite. No se entrega el resultado con una
nota diciendo que el control salió raro: **no se entrega**.

Eso es un contrato de datos, y lleva décadas siendo obligatorio en un laboratorio mientras en los
datos todavía se discute si hace falta. Y fíjate en el blanco, la muestra sin contenido: está ahí
para detectar contaminación, o sea para cazar **lo que no debería aparecer**. Es exactamente la
promesa que le faltaba a la primera versión de este contrato.

## Repaso

### Qué es un contrato de datos y en qué se diferencia de la documentación

Es un conjunto de condiciones comprobables que se ejecutan en cada corrida y pueden impedir que
los datos pasen. La documentación describe lo que debería pasar y no se entera cuando deja de
pasar; el contrato falla y para el proceso. La diferencia práctica es que uno tiene código de
retorno y el otro no.

### Por qué cada promesa se escribe como una consulta que devuelve cero filas

Porque así el error trae las pruebas dentro. Una promesa que devuelve verdadero o falso obliga a
investigar desde cero cuando falla; una que devuelve las filas culpables ya te ha dicho cuáles
son. Y la forma es siempre la misma, así que añadir una promesa es escribir una consulta más.

### Tu contrato pasa todos los días desde hace un año. Buena señal

No necesariamente. Los datos pueden estar bien, o el contrato puede no comprobar nada capaz de
fallar. La única forma de distinguirlo es romper los datos a propósito y ver si se entera.
Aquí, la primera versión pasaba tranquilamente una rotura de cinco.

### La promesa que faltaba parecía trivial. Por qué se escapó

Porque comprobaba media condición. Verificaba la presencia de las veinte columnas acordadas, y
una columna de más no quita ninguna de las veinte. Es un fallo por omisión, la clase que no se ve
releyendo: lo escrito es correcto, y lo que falta no está escrito en ninguna parte.

### Qué haces si el contrato falla a las tres de la mañana

Nada automático. El contrato para el proceso y deja los datos anteriores intactos, que es lo
importante: mejor un panel desactualizado que un panel con datos malos. Después alguien mira qué
promesa se rompió y cuáles fueron las filas culpables, que el propio contrato dejó escritas.

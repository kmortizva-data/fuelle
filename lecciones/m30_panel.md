---
module: 30
---

## En 30 segundos

- Quien no va a leer treinta y un módulos necesita **una página**: una perilla que elige el día,
  dos curvas y una frase con el veredicto.
- Los días se calculan antes, en Python, y la página solo elige cuál enseñar: **214 días en 26,5
  KB**, sin ningún servidor.
- **Cómo se escriben los números pesa más que cuántos**: el mismo semestre pesa 44,8 KB como
  acumulado y 14,3 KB como minutos de cada tramo.
- Redondear cada tramo por separado aparta la curva hasta **72 minutos** en un día; redondear el
  acumulado y restar, medio minuto como mucho.
- El navegador no decide nada: la frase de cada día sale de Python y **cuadra día a día con el
  veredicto** del módulo 28.

## Qué resuelve este módulo

El veredicto del módulo 28 es una tabla, y una tabla se lee despacio. Alguien que llega desde el
portafolio, un jefe de planta o quien revisa una candidatura, no va a leer treinta y un módulos
para llegar a ella.

Este módulo construye la puerta para esa persona: una página con el semestre entero, día a día. Y
la decisión que la sostiene es de ingeniería de datos, no de diseño. Hay que decidir qué se calcula
antes, qué se calcula al pedirlo y cuánto pesa cada cosa en el navegador del lector.

## Antes de la teoría: un ejemplo de juguete

Un compresor sano carga poco y a menudo. Parte un turno en cinco tramos, y supón que en cada uno
carga **0,4 minutos**: en total, 2 minutos.

Hay que guardar esa curva en números enteros, porque los enteros son cortos. Se puede redondear de
dos maneras:

| Tramo | 1 | 2 | 3 | 4 | 5 | Suma |
|---|---|---|---|---|---|---|
| Carga de verdad, min | 0,4 | 0,4 | 0,4 | 0,4 | 0,4 | 2 |
| Redondeada tramo a tramo | 0 | 0 | 0 | 0 | 0 | **0** |
| Acumulado de verdad | 0,4 | 0,8 | 1,2 | 1,6 | 2,0 | |
| Acumulado redondeado | 0 | 1 | 1 | 2 | 2 | |
| Cada acumulado menos el anterior | 0 | 1 | 0 | 1 | 0 | **2** |

**Redondeada tramo a tramo, la curva pierde los 2 minutos enteros**: cada 0,4 se queda en cero, y
el error de un tramo se suma al del siguiente. Redondeando el acumulado y restando salen los ceros
y unos de la última fila, que suman 2 exactos. Ningún punto se aparta más de medio minuto, porque
cada uno se redondea contra la curva de verdad y no contra el anterior.

Y hay una segunda ganancia que a mano no se ve y en el panel se mide: **los tramos se repiten**.
Aquí son ceros y unos. El acumulado no se repite nunca, porque siempre crece, y un compresor de
ficheros vive justo de las repeticiones.

## Glosario

- **Precalcular.** Calcular antes todas las respuestas que se van a poder pedir, y guardarlas.
  Quien abre la página no calcula nada: elige.
- **Servidor.** Un programa encendido día y noche para contestar a quien llama. Hay que pagarlo,
  protegerlo y ponerlo al día.
- **Página estática.** Una página hecha solo de ficheros fijos. GitHub Pages las sirve gratis, y
  no se caen porque no hay nada dentro que se pueda caer.
- **Codificación.** La manera de escribir unos datos dentro de un fichero. Los mismos números
  pueden ocupar el triple según cómo se escriban.
- **Compresión.** Reescribir un fichero para que ocupe menos sin perder nada, aprovechando lo que
  se repite. El servidor comprime y el navegador descomprime sin que nadie lo note.
- **Huella en la URL.** Un trozo de la huella del fichero pegado a su dirección, `?v=`. Si el
  fichero cambia, la dirección cambia, y ninguna caché puede servir el viejo.
- **Estado final sin JavaScript.** Lo que se ve si el script no llega. Aquí, el día de partida
  dibujado entero desde el servidor.

## Paso a paso

### Paso 1. Contar las preguntas

El panel contesta una sola pregunta, qué pasó tal día, y hay 214 días. **Doscientas catorce
respuestas se pueden calcular todas antes.** Una consulta libre, en cambio, no se puede
precalcular: para eso el módulo 8 manda al navegador el motor de base de datos entero, 8,12 MB.

La regla que sale de aquí sirve para cualquier panel. Si las preguntas se pueden contar, se
calculan antes; si no, hace falta un servidor o un motor en el navegador.

### Paso 2. Decidir qué lleva cada día

Tres curvas: lo que cargó el compresor, lo que habría cargado el gemelo con la máquina sana y la
zona sana. Además los huecos del registro, las marcas de la alarma y de los partes, y la frase del
veredicto en el idioma de la página.

**El gemelo corre solo mientras hay registro.** Si corriera también en los huecos, la máquina se
quedaría quieta en ellos y el gemelo no. Las dos curvas se separarían por una razón que no tiene
nada que ver con el aire.

### Paso 3. Pesar antes de elegir

Tres maneras de escribir las mismas curvas, a seis resoluciones, comprimidas como las comprime
GitHub Pages. Se pesa antes de decidir porque la intuición dice que manda la resolución, y la
medida dice otra cosa.

### Paso 4. Escribir la frase en Python, no en el navegador

La página podría decidir sola si un día saltó la alarma, porque tiene los números. Pero entonces
habría dos definiciones de «día con alarma», la del módulo 28 y la de la página. **Una sola
implementación no se puede contradecir.** Es la regla de las perillas, que no simulan nada en el
navegador, llevada al veredicto.

### Paso 5. Dibujar en el servidor el día de partida

Sin JavaScript la página tiene que leerse igual. Así que el 5 de junio llega dibujado desde el
servidor, con sus dos curvas, sus marcas y su frase. El script solo añade poder elegir otro día.

## El código, por partes

### Paso 6. Los tramos, sin arrastrar el redondeo

```python
def en_tramos(acumulado: list[float]) -> list[int]:
    redondo = [round(v) for v in acumulado]
    return [b - a for a, b in zip([0] + redondo, redondo)]
```

```anota
round(v) for v in acumulado | se redondea el acumulado y no cada tramo: así ningún punto se aparta más de medio minuto de la curva de verdad
zip([0] + redondo, redondo) | empareja cada punto con el anterior. El cero de delante hace de anterior del primero
b - a | lo que cargó el compresor en ese tramo, en minutos enteros. Sumándolos vuelve el acumulado redondeado, exacto
```

```salida
  el redondeo, en el peor punto de todo el semestre:
    tramo a tramo          72.0 min de error
    acumulado y restar      0.5 min de error
```

Es el ejemplo de juguete a escala. Redondeando tramo a tramo, el peor punto del semestre se aparta
**72 minutos** de la curva de verdad; redondeando el acumulado, medio minuto como mucho.

### Paso 7. El veredicto, con las reglas del módulo 28

```python
if pico is None:
    return "sin_juzgar"
if pico > umbral:
    if partes_del_dia:
        return "acierto"
    return "marzo_alarma" if marzo else "falsa"
if partes_del_dia:
    return "escapa"
```

```anota
pico is None | el día no tiene ni una hora completa, así que el gemelo no lo juzga
pico > umbral | el residual más alto del día pasa del umbral del veredicto: salta la alarma
partes_del_dia | los partes de avería que cubren ese día. Con alarma es un acierto, y sin ella, un día que se escapa
marzo_alarma | los doce días de marzo sin parte, que el veredicto cuenta de las dos maneras
```

```salida
  los días, por clase:
    acierto               6
    se escapa             1
    falsa alarma         10
    marzo, con alarma     2
    marzo, sin alarma    10
    sobre el ruido       99
    normal               79
    sin juzgar            7
  semestre.es.json       284.4 KB en disco,   26.5 KB por la red
  semestre.en.json       285.3 KB en disco,   26.5 KB por la red

  escrito en results\m30_panel.json
  las cuatro cuentas cuadran con el módulo 28, y el 5 de junio sigue saltando a la hora del parte
```

Los seis aciertos son los seis días con parte en los que salta la alarma. El que se escapa es el
29 de mayo: la fuga se abre a las 23:30 y la alarma salta al día siguiente. **Antes de escribir
nada, el script compara sus cuentas con el veredicto del módulo 28**, y si no cuadran se niega.

### Paso 8. Pesar como pesa en la red

```python
def pesa(objeto) -> dict:
    crudo = json.dumps(objeto, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {"kb": round(len(crudo) / 1024, 1),
            "kb_red": round(len(gzip.compress(crudo, compresslevel=NIVEL_DE_PAGES,
                                              mtime=0)) / 1024, 1)}
```

```anota
separators=(",", ":") | sin los espacios que JSON pone por defecto detrás de cada coma: en 214 días son miles de bytes de nada
compresslevel=NIVEL_DE_PAGES | nivel 5, el mismo con el que GitHub Pages comprime lo que sirve. Se comprobó contra sus ficheros de verdad
mtime=0 | la hora que gzip guarda en su cabecera. Fijarla deja los bytes iguales en cada corrida
```

```salida
  lo que pesa el semestre entero, tres curvas por día, en KB por la red:
    puntos/día | acumulado | tramos | caracteres
            24 |      12.4 |    6.2 |          -
            48 |      20.8 |    8.4 |        7.0
            96 |      34.5 |   12.0 |        9.8
           144 |      44.8 |   14.3 |       11.7
           288 |      77.6 |   20.1 |       16.0
          1440 |     230.9 |   40.3 |       29.2
```

La columna de los caracteres no existe con un punto por hora: un tramo de una hora puede llevar
sesenta minutos de carga, y un solo carácter no llega a tanto.

### Paso 9. El navegador solo suma

```js
function camino(tramos, paso, techo) {
  var d = "M0 " + techo, total = 0;
  for (var k = 0; k < tramos.length; k++) {
    total += tramos[k];
    d += " L" + ((k + 1) * paso) + " " + (techo - total);
  }
  return d;
}
```

```anota
total += tramos[k] | la única cuenta del navegador: sumar los minutos de cada tramo para rehacer el acumulado
"M0 " + techo | el camino empieza abajo a la izquierda. En un SVG la altura crece hacia abajo, así que el cero está en el techo
" L" + ((k + 1) * paso) | una línea hasta el final de cada tramo, diez minutos más allá del anterior
```

La misma cuenta está escrita en Python en `render_panel.py`, que dibuja el día de partida sin
JavaScript. Dibujar sí se hace dos veces; decidir, una sola.

### Paso 10. La huella en la URL

```python
def huella(lang: str) -> str:
    return hashlib.sha256((PANEL_DIR / f"semestre.{lang}.json").read_bytes()).hexdigest()[:8]
```

```anota
hashlib.sha256(...) | la huella del módulo 5: cambia entera si cambia un solo byte del fichero
[:8] | con ocho caracteres basta para que cada versión tenga su propia dirección
```

La página pide `semestre.es.json?v=` seguido de esa huella. Si mañana cambia un día del veredicto,
cambian la huella y la dirección, así que ningún navegador puede quedarse con el fichero viejo.
Pasó de verdad en el módulo 24, con una perilla que dibujaba contra un techo que ya no era el suyo.

### Paso 11. Toca el panel

```panel
semestre
```

Arranca en el 5 de junio. Arrastra el cursor sobre la tira del semestre, o usa los botones para ir
a los días que cuentan la historia. La misma pieza vive en su [página propia](panel.html), que es
la que enlaza el portafolio.

## El resultado, medido

{{FIG:fig_m30_peso_del_semestre}}

**Qué esperábamos.** Que el peso lo decidiera la resolución. Un punto cada diez minutos son seis
veces más números que uno por hora, y era razonable esperar un fichero seis veces más grande.

**Qué salió.** Que manda más la manera de escribirlos. A la resolución del panel, el acumulado en
horas pesa **44,8 KB** y los minutos de cada tramo, **14,3 KB**: **3,1 veces menos**, con los
mismos datos. Y la raya punteada de la figura enseña lo más raro: los tramos a un punto por
minuto, **40,3 KB**, siguen pesando menos que el acumulado a diez minutos.

La razón es el ejemplo de juguete. El acumulado crece siempre, así que cada número es nuevo y lleva
sus decimales. Los tramos son números cortos que se repiten, sobre todo ceros de noche y dieces con
una fuga abierta, y la compresión vive de las repeticiones.

La tercera escritura, un carácter por tramo, ahorra **2,6 KB** más. A cambio pide un decodificador
propio que habría que escribir, probar y mantener, y no compensa: se quedan los tramos en JSON
corriente.

Con las curvas, las marcas y las frases, el fichero de un idioma pesa 284,4 KB en disco. Por la
red viajan **26,5 KB**, 10,7 veces menos, y esa es la cifra del módulo: **214 días en 26,5 KB**.
Para comparar, el motor de SQL de las consultas vivas pesa 8,12 MB, **314 veces más**.

**La cifra que prometía el temario era otra.** Pedía medir cuántos segundos tarda alguien que no
conoce el proyecto en entender qué pasa. Eso no lo mide un script: hacen falta personas y un
cronómetro, y todavía no las ha habido. Se cambió por una cifra que se mide sola. Y se dice aquí,
para no dar a entender que la pregunta desapareció.

**Qué significa.** Un panel que contesta al instante, se lee sin JavaScript y cuesta 26,5 KB no
necesita servidor. Lo que se pierde es preguntar algo que nadie calculó antes, y para eso ya están
las consultas vivas del curso. Cada herramienta donde toca: precalcular lo que se puede contar, y
llevar el motor adonde las preguntas no se pueden contar.

## Ojo

- **Precalcular solo sirve si las preguntas se pueden contar.** 214 días son 214 respuestas. Una
  consulta libre no se puede contar, y para ella hace falta un servidor o un motor en el navegador.
- **Redondear cada tramo por separado arrastra el error.** En este semestre llega a 72 minutos en
  un día. Se redondea el acumulado y se resta.
- **Pesa con la compresión de verdad.** En disco el fichero ocupa 284,4 KB y por la red 26,5.
  Decidir mirando el disco habría llevado a optimizar lo que no importa.
- **Un fichero de datos sin huella en la URL** se queda en la caché del lector mientras la página
  cambia. Entonces la página dibuja con datos viejos, y no avisa.
- **Precalcular congela.** Si cambian los datos, el panel no se entera hasta que alguien vuelve a
  correr `panel.py`. Por eso el script comprueba sus cuentas contra el veredicto cada vez.
- **Si la página decidiera, habría dos veredictos.** La frase de cada día se escribe en Python, una
  sola vez, y la página solo la enseña.

## Puente metalúrgico

Una báscula de banda no apunta lo que pasó en cada turno: lleva un **totalizador**, un contador
que solo sube. El tonelaje de un turno se saca restando la lectura del final menos la del
principio. Si cada turno se estimara y se redondeara por separado, el mes no cuadraría con el
contador; restando lecturas del totalizador, cuadra siempre. Es el paso 6 con cintas
transportadoras.

Y la pizarra de la sala de control es este panel. El balance del turno se calcula una vez, se
apunta, y cualquiera lo lee de un vistazo sin volver a hacer las cuentas. Cuando alguien trae una
pregunta nueva, como la recuperación sin contar la parada de las tres, eso ya no está en la
pizarra: se va al laboratorio con los datos. La pizarra es lo precalculado; el laboratorio, la
consulta viva.

## Repaso

### Por qué este panel no necesita un servidor

Porque todas sus preguntas se pueden contar: 214 días, una respuesta por día. Se calculan antes en
Python y viajan juntas en un fichero de 26,5 KB. Un servidor solo hace falta cuando las preguntas
no se pueden prever, y entonces hay que mantenerlo encendido, protegido y al día.

### Por qué los minutos de cada tramo pesan menos que el acumulado

Porque son números cortos que se repiten, y la compresión vive de las repeticiones. El acumulado
crece siempre, así que cada número es distinto y lleva decimales. A la resolución del panel son
14,3 KB contra 44,8, con los mismos datos.

### Qué pasa si se redondea cada tramo por separado

El error de cada tramo se suma al del siguiente y la curva se va apartando, hasta 72 minutos en el
peor día del semestre. Redondeando el acumulado y restando, ningún punto se aparta más de medio
minuto, porque cada uno se redondea contra la curva de verdad.

### Por qué la frase de cada día se escribe en Python y no en la página

Para que exista una sola definición de «día con alarma». Si la página decidiera, habría dos, y
podrían separarse sin que nadie lo viera. Además el script comprueba antes de escribir que sus
cuentas cuadran con el veredicto del módulo 28, día a día.

### Qué ve quien abre el panel sin JavaScript

El 5 de junio entero, dibujado en el servidor: las dos curvas, la zona sana, las marcas y la frase
del veredicto. Se eligió ese día porque cuenta la historia solo. A las 10:00 el residual pasa del
umbral, la misma hora a la que empieza el parte de avería.

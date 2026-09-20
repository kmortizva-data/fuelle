---
module: 31
---

## En 30 segundos

- El último entregable es **un folio**: la pregunta, el método en cinco líneas, la tabla del
  veredicto y **8 cosas que se romperían** en una planta de verdad.
- Ninguna cifra se teclea. El texto lleva huecos, un script los rellena desde `results/` y **se
  niega a escribir si algún número no sale de una corrida**.
- Es una página del propio curso impresa a PDF, no un documento de LaTeX: una sola identidad
  visual, y ninguna herramienta nueva que instalar.
- **Un folio es un folio.** El script cuenta las caras del PDF y falla con dos. Cupo quitando
  texto, no encogiendo la letra.
- El curso cierra por donde ha ido todo el rato: diciendo también lo que el gemelo no hace.

## Qué resuelve este módulo

Un trabajo que no se puede entregar no está terminado. Quien decide en una planta no va a leer
treinta y un módulos, ni a mover la perilla del panel: va a pedir una hoja.

Este módulo escribe esa hoja con la misma disciplina que el resto. Cada cifra sale de una corrida.
Y lo que el proyecto no hace se escribe en la misma cara, junto a lo que sí hace. Un entregable
que solo cuenta la mitad buena no es un entregable, es publicidad.

## El arco del proyecto

{{FIG:fig_m31_arco_del_proyecto}}

El fichero de la UCI son **208,2 MB** de texto. El bronce lo deja en **22,05 MB** sin perder una
lectura, la plata las pone en rejilla y pasa a **1.841.760** filas, y el oro las resume en nueve
nodos de dbt. Las mismas lecturas servidas desde PostgreSQL ocupan **267,8 MB**, doce veces más, y
a cambio traen restricciones, índices y una copia que se restaura.

Del otro lado está el gemelo. Cuatro números medidos en febrero describen la máquina, su
desacuerdo con ella es el residual, y el suelo de ruido de ese residual son **0,12 bar/min**. Con
el umbral que eligió el barrido, el veredicto es **4 de 4** averías con **1,5** falsas alarmas al
mes.

Y algo que el arco no enseña: entre la plata y el gemelo aparecieron doce días de marzo con la
máquina averiada y sin parte, encontrados al calibrar. El arco cuenta lo que queda de pie; el
curso, cómo se llegó hasta aquí.

## Glosario

- **Entregable.** Lo que queda cuando el trabajo termina. Otra persona tiene que poder usarlo sin
  preguntarte nada.
- **Folio.** Una cara de A4. No es un capricho de formato: es lo que alguien lee de pie, en una
  reunión, antes de decidir.
- **Plantilla con huecos.** Un texto con marcas como `{umbral}` donde irán las cifras, que un
  script rellena desde los resultados medidos.
- **Imprimir sin ventana.** Pedirle a un navegador que convierta una página en PDF sin abrirse,
  desde la línea de órdenes.
- **Límite declarado.** Una limitación escrita en el propio entregable, con su medida al lado.
- **Licencia.** El permiso con el que se publica algo. Aquí, MIT para el código y CC BY 4.0 para
  las lecciones y las figuras, con la cita del dataset.

## Paso a paso

### Paso 1. Escribir el folio sin cifras dentro

El texto vive en `lecciones/folio.md`, en español y en inglés, y donde iría un número hay un hueco
con nombre. Así el folio se escribe como prosa y se revisa como prosa, y pasa las mismas puertas
de escritura que una lección.

### Paso 2. Rellenar los huecos desde los resultados

Un mapa dice de qué fichero de `results/` sale cada hueco. El umbral y las cuentas del veredicto
se leen del barrido del módulo 28, no de una constante: si el barrido eligiera otro umbral, el
folio lo seguiría solo.

### Paso 3. Volver a leer lo escrito

El folio no es una lección, así que la puerta de los números no lo miraba. Se le aplica igual: el
script relee su propio texto y busca cifras que no existan en `results/`.

### Paso 4. Imprimir con el navegador, no con LaTeX

El plan decía Tectonic. Son 47 MB rechazados por la guarda de privacidad del repositorio, un
segundo sistema visual que mantener, y una herramienta más para quien clone esto. Una página
impresa por el navegador sale con la tipografía del curso y sin nada nuevo.

### Paso 5. Contar las caras

Un folio que se va a dos caras deja de ser un folio. El script cuenta las páginas del PDF que
acaba de escribir y falla si hay más de una.

## El código, por partes

### Paso 6. El hueco, y lo que lo llena

```python
def rellena(texto: str, valores: dict[str, str]) -> str:
    def cambia(m: re.Match) -> str:
        clave = m.group(1)
        if clave not in valores:
            raise SystemExit(f"El folio pide «{clave}» y no está entre las cifras medidas.")
        return valores[clave]

    return re.sub(r"\{([a-z_]+)\}", cambia, texto)
```

```anota
re.sub(r"\{([a-z_]+)\}", cambia, texto) | busca los huecos del texto, una palabra en minúsculas entre llaves, y llama a `cambia` con cada uno
clave not in valores | un hueco que nadie sabe rellenar para el folio entero, en vez de imprimir una llave dentro del PDF
valores[clave] | la cifra, ya escrita en el idioma de la página: 1,15 en español y 1.15 en inglés
```

### Paso 7. La puerta de los números, aplicada al folio

```python
for m in check_numbers.NUMBER.finditer(texto):
    valor = check_numbers.canonical(m.group(), lang)
    if valor is None or valor in conocidos:
        continue
    fuera.append(m.group())
```

```anota
check_numbers.NUMBER | la misma expresión que busca números en las lecciones. El folio no estrena reglas, hereda las que ya hay
canonical(...) | 1.516.948 y 1,516,948 son el mismo número: esto los deja en una sola forma antes de comparar
conocidos | todo número que algún script haya escrito en results/, leído justo antes de rellenar nada
fuera.append(...) | lo que no cuadra se nombra y el folio no se escribe
```

```salida
  folio.html       El veredicto, en un folio                       553 palabras
  folio.en.html    The verdict, on one page                        556 palabras
  8 cosas que se romperían, y 24 cifras, todas medidas
  escrito en results\m31_folio.json
```

### Paso 8. Contar las caras sin abrir el PDF

```python
def hojas(pdf: Path) -> int:
    crudo = pdf.read_bytes()
    return len(re.findall(rb"/Type\s*/Page[^s]", crudo)) or 1
```

```anota
pdf.read_bytes() | el PDF tal cual, sin instalar ninguna librería: por dentro es texto con objetos marcados
rb"/Type\s*/Page[^s]" | cada página se declara así. El `[^s]` es para no contar `/Pages`, que es el índice y saldría de más
or 1 | si un PDF no declarara ninguna, se cuenta una: la guarda está para cazar dos caras, no para caerse sola
```

```salida
  imprime con msedge.exe
  veredicto.pdf      59.4 KB   1 cara
  verdict.pdf        60.1 KB   1 cara
  apuntado en results\m31_folio.json
```

## El resultado, medido

**Qué esperábamos.** Que el folio cupiera a la primera.

**Qué salió.** Dos caras, y la guarda lo dijo antes que nadie. Sobraban unas tres líneas, medidas
en el navegador con el ancho y la letra de la impresión. Se arregló quitando texto en los dos
idiomas y apretando el aire entre secciones en la hoja de impresión. El tamaño de la letra no se
tocó: en un papel que alguien va a leer de pie, la letra es lo último que se encoge.

El folio publicado son **553** palabras, **24** cifras, todas medidas, y **8 cosas que se
romperían**. El PDF pesa **59,4** KB y ocupa una cara.

**Qué significa.** El proyecto entrega cuatro cosas, y cada una para un lector distinto. El curso,
para quien quiera aprender esto desde cero. El panel, para quien tenga dos minutos. El
repositorio, para quien quiera comprobarlo. Y el folio, para quien tenga que decidir algo con él
delante.

La última de las cuatro fue la más difícil de escribir, porque obliga a poner en una cara lo que
funciona y lo que no. El gemelo pilla las cuatro averías documentadas con una falsa alarma y media
al mes, y como predictor no sirve. Las dos frases van juntas, en el mismo folio, con el mismo
tamaño de letra.

## Ojo

- **Un folio que no cabe no se arregla con la letra.** Se quita texto. Encoger la tipografía para
  que entre es empeorar el entregable para salvar el formato.
- **Una cifra escrita a mano en el entregable vale menos que no tener entregable.** Es la última
  hoja que alguien va a leer, y la más fácil de contaminar copiando números.
- **Imprimir desde el sitio equivocado no escribe nada.** Lanzado desde Git Bash, este mismo
  navegador sale con código 0 y no deja PDF. Va desde PowerShell, y el script lo dice si falla.
- **El folio caduca.** Si cambia el veredicto, hay que volver a generarlo e imprimirlo. Por eso
  sus cifras salen de `results/` y no de la memoria de nadie.
- **Las limitaciones se escriben con su medida al lado.** «La máquina se degrada» no dice nada;
  «el consumo sano dobla entre febrero y agosto» sí.

## Puente metalúrgico

Un certificado de análisis lleva el resultado, el método y el límite de detección en la misma
hoja. Un laboratorio que da la ley sin decir su límite obliga a fiarse de él; con el límite
escrito, cualquiera sabe hasta dónde puede usar ese número.

El folio hace lo mismo. El veredicto va arriba y, en la misma cara, lo que el gemelo no ve. Una
sola máquina, cuatro averías, ninguna fuga de referencia, y un modelo que envejece si nadie lo
recalibra. Y como el informe de turno, cabe en una cara y se lee de pie.

## Repaso

### Por qué el folio no se escribe a mano

Porque es la hoja que más lejos viaja y la más fácil de contaminar copiando cifras. El texto lleva
huecos, un script los rellena desde los resultados, y después relee lo escrito para comprobar que
no se ha colado ningún número sin corrida detrás.

### Por qué el PDF sale de una página del curso y no de LaTeX

Por tres razones medidas. El compilador son 47 MB rechazados por la guarda del repositorio, sería
un segundo sistema visual que mantener, y quien clone el proyecto tendría que instalarlo. La
página ya existe, usa la tipografía del curso y cualquier navegador la convierte en PDF.

### Qué pasa si el folio no cabe en una cara

El script lo caza contando las páginas del PDF y no deja seguir. La respuesta es quitar texto o
apretar el aire entre secciones, nunca encoger la letra: un folio ilegible cumple el formato y
falla en lo único que importa.

### Por qué la lista de lo que se rompería va en el entregable

Porque quien lo lea va a decidir con eso delante, y cada límite cambia lo que puede hacer con el
resultado. Esconderlos no los quita: los deja para que los descubra la planta, que es el peor sitio
y el peor momento.

### Qué se entrega al final, y dónde vive cada cosa

Cuatro cosas. El curso y el panel viven dentro del portafolio. El código y las lecciones, en el
repositorio público, con licencia MIT y CC BY 4.0. Y el folio, en PDF y en los dos idiomas, lo
generan `src/entrega/folio.py` e `src/entrega/imprime.py`.

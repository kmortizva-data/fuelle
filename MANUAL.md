# Cómo se escribe una lección de Fuelle

> **Léelo antes de escribir una sola línea de contenido.**
>
> Este curso no inventa un método. Hereda el de Sílice, que a su vez heredó el de Concentra y le
> costó veintitrés rondas de corrección. Lo que cambia aquí es de qué va el material y quién lo
> lee: alguien que sabe de procesos y **no ha escrito nunca una consulta SQL**.

## La regla que ordena todo lo demás

En Sílice el proyecto ya había terminado y cada lección se escribía hacia atrás desde el
veredicto. Aquí no: **el experimento se corre a la vez que se escribe**. Eso obliga a una
disciplina distinta y más estricta.

`temario.json` fija **qué** se va a medir en cada módulo. No fija qué va a salir. Por eso casi
todas las cifras nacen como `por medir` y solo tres están escritas de entrada, porque están
verificadas contra el fichero. Cuando el experimento se corre, la cifra se rellena con lo que
salga, salga lo que salga.

**Si el resultado es malo, el resultado es malo y se publica.** El precedente está en Sílice, que
cierra diciendo que el machine learning no aporta valor operativo. Ese es el módulo que da
credibilidad a los otros trece.

## 1. Anatomía de una lección

Diez secciones, con estos nombres exactos, en este orden. `check_lesson.py` las verifica y falla
antes del commit.

| Sección | Qué va dentro |
|---|---|
| `## En 30 segundos` | Cinco viñetas como máximo: la cifra, la trampa y la decisión |
| `## Qué resuelve este módulo` | Tres frases: qué problema resuelve y por qué importa |
| `## Antes de la teoría: un ejemplo de juguete` | Cinco o seis números resueltos a mano, paso a paso |
| `## Glosario` | Cada término con su definición, formato `**Término.** Definición.` |
| `## Paso a paso` | `### Paso N` con prosa real, no viñetas densas |
| `## El código, por partes` | Bloques cortos, cada uno con su anotación y su salida real |
| `## El resultado, medido` | La cifra del módulo, su figura, y qué se esperaba frente a qué salió |
| `## Ojo` | Las trampas, en viñetas con la trampa en negrita |
| `## Hazlo tú` | **Obligatoria si el módulo declara `reto` en el temario.** El ejercicio que se resuelve en la propia página |
| `## Puente metalúrgico` | Analogía **solo** de metalurgia y beneficio de minerales |
| `## Repaso` | Cinco `### pregunta` tipo entrevista con su respuesta modelo debajo |

El módulo 35 entrega el proyecto en vez de enseñar una idea nueva, así que cambia el ejemplo de
juguete por `## El arco del proyecto`. Es la única excepción y el verificador la conoce.

### `Hazlo tú` es la sección que impide que esto sea un PDF

Veinte de los treinta y cinco módulos la llevan, y el temario declara cuál. La regla es simple:
**el lector escribe algo y la página le contesta si está bien**, contra los datos reales del
compresor. No es un cuestionario de opción múltiple, es la consulta corriendo de verdad.

Cada reto lleva tres cosas:

1. **El enunciado en una frase**, con la respuesta esperada bien definida (un número, una tabla
   corta), nunca «explora un poco».
2. **Un punto de partida**, que es la consulta del bloque de código de arriba. El lector nunca
   empieza desde una caja vacía.
3. **Una pista plegada y la solución plegada**, en ese orden. La solución se ve siempre: quien
   se atasca no se queda fuera del curso.

La comprobación se hace **contra el resultado, no contra el texto de la consulta**. Hay muchas
formas de escribir la misma pregunta y todas valen. Comparar cadenas de texto sería castigar por
no adivinar el estilo del autor.

### El ejemplo de juguete es obligatorio, va primero, y en SQL es literal

Antes de cualquier sintaxis, seis filas que se resuelvan a mano. En este curso eso significa
seis lecturas de un depósito de aire, con presiones redondas, sobre las que el lector contesta la
pregunta **antes** de ver una sola palabra en inglés de SQL.

Regla de diseño: **que los números salgan redondos a mano**. Si el lector no puede comprobarlo
con lápiz, el ejemplo no cumple su función. El vocabulario es de planta: depósitos, presiones,
caudales, turnos, paradas. Nunca alturas de personas ni notas de examen.

### La sección de código, en cinco partes por bloque

1. `### Paso N. Qué vamos a hacer`, con una frase de por qué.
2. El código, **corto**. Si pasa de ocho líneas, pártelo en dos pasos.
3. Un bloque `anota` con la forma `fragmento | explicación`, una línea por cada cosa que aparezca
   **por primera vez en el curso**.
4. Un bloque `salida` con la salida **real, ejecutada**.
5. Una frase de qué acaba de pasar.

**Qué se anota en SQL.** Aquí hay que anotar más que en Sílice, porque SQL es un idioma nuevo y
no se parece a Python. Se anota: que `SELECT` elige columnas y `FROM` elige de dónde, que el
punto y coma cierra, que `WHERE` filtra filas y `HAVING` filtra grupos, que las comillas simples
son para texto y las dobles para nombres de columna, que el orden en que se escribe una consulta
no es el orden en que se ejecuta, y por qué `SELECT *` es mala costumbre fuera de una exploración.

**Qué no se anota.** Lo ya explicado en un módulo anterior.

### La sección del resultado es la firma de este curso

`El resultado, medido` lleva tres cosas y en este orden:

1. **Qué esperábamos.** Una frase con la expectativa razonable antes de correr nada.
2. **Qué salió.** La cifra, con su figura, y la comparación contra la referencia que toque.
3. **Qué significa.** Sin inflar y sin disculparse.

En los módulos del gemelo, la referencia siempre es la misma pregunta: **qué habría dicho una
alarma de umbral corriente**. Si el gemelo no le gana a un umbral, hay que decirlo.

### El resumen va primero, y lo denso se pliega

La lección abre con `En 30 segundos`, que se lee entero de un vistazo. Van plegados y cerrados
por defecto el **glosario** y la **anotación línea por línea** de cada bloque de código.

## 2. Reglas de escritura

- **Cero rayas y cero guiones medios.** No se sustituyen por guiones: se reescribe la frase con
  coma, dos puntos, paréntesis o punto y seguido. `check_prose.py` lo verifica.
- **Cero emoji.**
- **Analogías solo de metalurgia.** En este curso la analogía es casi literal y conviene no
  desaprovecharla: el aire comprimido alimenta las columnas de flotación, así que una fuga en la
  red de aire es recuperación perdida. Nada de geología ni geoquímica.
- **Nada de muletillas.** «En el mundo de», «cabe destacar», «es importante mencionar».
- **Los números en español**: coma decimal en la prosa (`8,2 bar`), punto en el código y en las
  salidas, que es lo que imprime la máquina de verdad.

### Frases que no se enreden

`check_clarity.py` mide el nudo:

| Regla | Límite | Por qué |
|---|---|---|
| Una idea por frase | 32 palabras | Por encima de eso hay dos frases pegadas |
| Comas | 3 como máximo | Cuatro comas suelen ser dos frases fundidas en una |
| Subordinadas | 2 veces «que» como máximo | Tres es una pila de subordinadas |
| Párrafo | 6 frases | Más largo, y el lector pierde el hilo |

Tres cosas que el verificador no mide y hay que cuidar igual: **el término se define antes de
usarlo**, nunca en la misma frase; **el dato primero, la lectura después**; y **el número antes
que el adjetivo**.

### Los números, verificados antes de escribirlos

Ningún número se publica sin haberlo calculado corriendo su script. Los scripts viven en `src/`,
las cifras que producen se escriben en `results/*.json`, y `check_numbers.py` exige que toda
cifra de la prosa exista allí.

Solo hay tres excepciones, que son los datos verificados contra el fichero original y el PDF
oficial, y están listados en `temario.json` bajo `_hechos_verificados`.

**Si un número no cuadra con lo que se esperaba, se reporta, no se ajusta.**

### La fidelidad del original manda

Los partes de avería vienen con erratas de fábrica (dos filas numeradas `#1`, un mantenimiento
fechado un mes antes de su propia avería, mayúsculas inconsistentes). **No se corrigen.** Se
copian literales, se declaran, y se convierten en el material de los módulos 5 y 8. El detalle
está en `src/ingest/LEEME_failure_reports.md`.

## 3. Figuras

- **Cada figura nace en dos temas**, claro y oscuro, desde el mismo script, vía
  `figures_theme.py`. La geometría y los datos no se tocan: solo cambian los colores y el destino
  del `savefig`.
- **Nombre con huella del contenido**, `fig_m6_csv_vs_parquet.a3f2c1d0.png`. Mata la caché y, sobre
  todo, que la huella se mueva significa que el dibujo se movió.
- **Se miran una por una** después de generar. No se dan por buenas.
- Una figura ilegible se re-renderiza desde su script, no se disimula.

## 4. Página y diseño

El encargo de Kevin, textual (2026-08-29): **«no muy escandaloso, que parezca ingeniero, pero que
demuestres habilidades, que no seas un pdf que se lee de recorrido»**.

Eso se traduce en una regla que ordena todas las decisiones visuales: **la sobriedad va en la
superficie, la ambición va en lo que la página hace.** Nada de efectos que llamen la atención
sobre sí mismos. Todo el esfuerzo, en que se pueda tocar y responda de verdad.

El curso vive en **sala de control**: fondo grafito, rejilla de puntos discreta, nodos unidos por
líneas, números en monoespaciada de instrumento.

- **Los colores no se eligen a ojo.** `src/site/palette.py` los genera en OKLCH y mide el
  contraste de los treinta y cinco acentos sobre **los dos fondos** antes de dejarlos entrar en
  `temario.json`. El croma se mantiene bajo a propósito: son colores de instrumento, no neón.
- **Regla de forma, no negociable.** La serie medida va en línea continua y la simulada en
  discontinua. **El color nunca es la única pista.** La primera pareja de colores que probé
  medía 1,22 de contraste entre las dos líneas, o sea que en una impresión eran la misma; por eso
  el script mide ahora también la separación entre series, y falla si baja de 1,8.
- **Una sola gramática, tres instrumentos.** Misma rejilla, misma tipografía y los mismos dos
  colores en todo el curso. Cambia el instrumento, nunca el idioma visual.
- **Una lección no lleva más de un instrumento**, declarado en `temario.json`.
- **Dos bordes derechos como máximo.** La medida en píxeles, nunca en `ch`. Listas sangradas con
  `padding`, no con `margin`. Tablas al ancho que necesiten.

### El movimiento es el sospechoso, no el protagonista

Tres condiciones, sin excepción: **estado final visible sin JavaScript**, quietas con
`prefers-reduced-motion`, y sin librerías externas salvo DuckDB bajo demanda.

Y una prueba antes de añadir cualquiera: **si se quita, ¿se entiende peor?** Si la respuesta es
no, es decoración y se va. Con esa prueba ya cayeron dos ideas que parecían buenas: el punto que
viajaba por la tubería y la aguja que subía hasta la cifra. Las dos eran lucimiento.

Quedan tres, y las tres explican algo que en texto cuesta un párrafo: **las dos curvas
separándose** cuando empieza la fuga, **la perilla del caudal de fuga** que recalcula el ciclo del
compresor, y **el tramo del grafo que se ilumina** para situar qué construye cada lección.

### La consulta viva y el reto

Veintiuno de los treinta y cinco módulos traen interacción, y veinte de ellos un reto
comprobable. El motor SQL se descarga **solo cuando el lector lo pide**, nunca al cargar la
página, y la lección se lee entera sin tocarlo.

Esta es la parte que responde a «demuestra habilidades»: un curso de SQL donde las consultas se
ejecutan de verdad, contra los datos reales, y donde la página sabe si la respuesta es correcta.

## 5. Proceso

- **Un módulo por commit**, con aviso al cerrarlo. Nunca dos módulos en el mismo commit.
- **Cada módulo se termina entero** antes de empezar el siguiente.
- **Las discrepancias se reportan, no se ajustan.**
- **Verificar en el navegador**, no suponer.

## 6. El orden exacto para una lección nueva

1. Leer lo que `temario.json` le promete al módulo: título, cifra, instrumento, `reto`, scripts,
   figuras. Si declara `reto`, la lección lleva `## Hazlo tú` y no se cierra sin él.
2. Escribir y correr los scripts. **Guardar la salida real** y las cifras en `results/`.
3. Diseñar el ejemplo de juguete, con números que salgan redondos a mano.
4. Escribir la lección entera en español: las diez secciones, once si hay reto.
5. **Resolver el reto uno mismo y guardar su respuesta esperada** en `results/`, para que la
   página pueda comprobarla contra el resultado y no contra el texto de la consulta.
6. Escribir la gemela inglesa, con los mismos números y los mismos bloques de código.
7. Generar las figuras en los dos temas y **mirarlas una por una**.
8. Los verificadores en verde, con un solo comando que sí falla:
   `.venv\Scripts\python.exe src\site\check_all.py`. Correrlos en un bucle de shell no sirve,
   porque el bucle devuelve cero pase lo que pase.
9. Reconstruir el sitio y revisarlo en el navegador, en escritorio y en móvil.
10. Commit.

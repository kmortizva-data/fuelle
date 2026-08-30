# Fuelle: un gemelo digital y su lago de datos

> **Proyecto:** Fuelle (ES) / Bellows (EN) · **Carpeta:** `Documents\02_Personal\Portafolio\Fuelle`
> **Categoría:** personal (portafolio) · **Estado:** fase 0, nació el 2026-08-29
> Índice de todos los proyectos: `Documents\_INDICE\INDICE.md`
> Plan aprobado: `~/.claude/plans/proyecto-portafolio-data-lakes-iterative-volcano.md`

Kevin aprende ingeniería de datos desde cero (pipelines, lagos de datos, SQL, administración de
bases de datos) construyendo la columna vertebral de datos de un gemelo digital. El resultado se
cuenta como curso web bilingüe de **31 módulos**, con el método de Sílice.

**El hueco que cierra:** sus cuatro proyectos publicados (Froth, Sílice, Geoestadística,
Concentra) consumen datos que alguien ya dejó limpios en un CSV. Ninguno muestra de dónde salen.

**Nombre CERRADO el 2026-08-29:** Fuelle. La carpeta no se renombra.

**Sin tope de módulos, por decisión suya el 2026-08-29:** «no te limites en el número de módulos,
lo que importa es que se explique todo y que cada módulo dure lo que tenga que durar, pero que se
entienda, de esto no tengo ni las bases, es aprender haciendo». Por eso el temario pasó de 16 a
35, con una parte 1 de bases que antes se daba por supuesta.

**Recorte de SQL, 2026-08-30.** Kevin preguntó si SQL hacía falta de verdad. La respuesta honesta
que se le dio: **el gemelo no usa SQL en absoluto** (parte 6, Python puro), el lake tampoco lo
necesita para existir (se podría hacer todo con polars), pero dbt y PostgreSQL sí lo exigen, y
sobre todo lo exige el mercado, que filtra por SQL antes de mirar un portafolio.

Con eso delante eligió **recortar SQL a lo esencial**: de 10 módulos a 6. El curso pasó de 35 a
**31**, y el gemelo se adelantó del módulo 27 al **23**.

**Lo que NO se borró.** Los conceptos de los cuatro módulos que desaparecen se integraron en los
que quedan, y cada módulo declara en `absorbe` lo que tiene que caber. Las subconsultas eran
innegociables: la lección de agrupar ya usaba una para filtrar los días incompletos, así que
quitarlas habría dejado un agujero en una lección ya escrita y verificada.

## El mundo del proyecto

**MetroPT-3** (UCI, DOI 10.24432/C5VW3R, CC BY 4.0). Unidad de producción de aire comprimido de
un tren del Metro de Oporto. Citar siempre: Davari, Veloso, Ribeiro y Gama (2021).

**Por qué este y no el famoso de la NASA:** C-MAPSS son 33 MB en cuatro ficheros de texto (no
justifica un lago), está saturado de repos idénticos, y su física vive dentro del simulador
cerrado de la NASA, así que no admite un gemelo encima.

**Por qué encaja con Kevin:** en Sílice midió que el aire de las columnas era la variable que más
mandaba. El compresor es el equipo que entrega ese aire. Y se repite el hallazgo del módulo 14 de
Sílice: el lazo de control borra la señal en la variable controlada y la traslada a la manipulada.
**La firma de una fuga no está en la presión, está en el ciclo de trabajo.**

## Hechos verificados el 2026-08-29 (contra el fichero y el PDF oficial, no contra la web)

| Qué | Valor |
|---|---|
| Filas del CSV | **1.516.948** (contadas) |
| Columnas | índice sin nombre + `timestamp` + 15 señales |
| Analógicas (7) | TP2, TP3, H1, DV_pressure, Reservoirs, Oil_temperature, Motor_current |
| Digitales (8) | COMP, DV_eletric, Towers, MPG, LPS, Pressure_switch, Oil_level, Caudal_impulses |
| Periodo | `2020-02-01 00:00:00` a `2020-09-01 03:59:50` (llega a septiembre, no a agosto) |
| Muestreo | cada 10 s |
| Tamaño | CSV 209 MB, zip 209 MB |
| Averías | 4, todas fugas de aire, «High stress» |

**Física que el PDF regala y hace viable el gemelo:**
- **MPG arranca el compresor en carga cuando la presión de la APU baja de 8,2 bar.** Es el presostato.
- **LPS se activa por debajo de 7 bar.** Es la alarma de baja presión.
- **Motor_current:** unos 0 A parado, 4 A en vacío, 7 A en carga, 9 A al arrancar.
- **DV_pressure a cero indica compresor en carga.** `DV_eletric` activo también significa carga.
- **COMP activo significa que NO entra aire** (apagado o en vacío).
- **Caudal_impulses cuenta el aire que va de la APU a los depósitos.** Es el caudalímetro.
- **Reservoirs** debe parecerse a TP3.

### Dos hallazgos que van a las lecciones

1. **La ficha y el fichero no dicen lo mismo.** El PDF declara 15.169.480 puntos a 1 Hz; el CSV
   trae 1.516.948 filas cada 10 s, exactamente la décima parte, y su columna índice conserva la
   numeración original (0, 10, 20...). Lo publicado está submuestreado y la ficha describe la
   captura original. **Manda el fichero.** Va al módulo 1.
2. **Los partes de avería vienen con erratas de fábrica** y se conservan literales
   (`src/ingest/failure_reports.csv`, con su LEEME): numerados `#1`, `#1`, `#3`, `#4`; mezcla de
   `Air leak` y `Air Leak`; y la avería del 29 de mayo declara mantenimiento el **30 de abril**,
   un mes antes de sí misma. Material de los módulos 5 y 8.

También hay ruido de coma flotante en los decimales (`-0.0120000000000004`) y el muestreo no es
perfectamente regular (hay saltos de 9 s). Material del módulo 7.

## Referencia rápida (operativa)

| Qué | Cómo |
|---|---|
| Entorno | `.venv/` con **Python 3.12** (no 3.14: dbt tuvo fricción real con mashumaro) |
| Correr un script | `.venv\Scripts\python.exe src\<script>.py`, rutas vía `Path(__file__)` |
| El plan | `temario.json`. Congelado. Manda sobre las lecciones |
| El método | `MANUAL.md`. Anatomía de 10 secciones y reglas de escritura |
| La puerta | `.venv\Scripts\python.exe src\site\check_all.py`. **Nueve verificadores, falla de verdad.** Nunca en un bucle de shell: el bucle devuelve cero pase lo que pase |
| Datos crudos | `data/`, fuera de git, se re-descargan de UCI |
| El lago | `lake/`, fuera de git, se reconstruye entero con el pipeline |
| Git | Lo corre Claude. Un módulo por commit, mensajes en inglés, sin comillas dobles en `-m` (PowerShell 5.1) |
| Regla de oro | Ningún número se publica sin recalcularlo corriendo su script |

## Método (heredado de Sílice, no se reinventa)

Diez secciones exactas por lección: `En 30 segundos`, `Qué resuelve este módulo`, `Antes de la
teoría: un ejemplo de juguete`, `Glosario`, `Paso a paso`, `El código, por partes`, `El
resultado, medido`, `Ojo`, `Puente metalúrgico`, `Repaso`.

El ejemplo de juguete va primero y con números redondos. Cada bloque de código lleva su `anota`
línea por línea de lo que sale por primera vez (aquí importa el doble: SQL es idioma nuevo). Cero
rayas y cero emoji. Analogías solo de metalurgia. Bilingüe de nacimiento con puerta de paridad.

## Identidad visual: sala de control

Referencia: Webflow, con carta blanca de Kevin. **Su encargo, textual (2026-08-29): «no muy
escandaloso, que parezca ingeniero, pero que demuestres habilidades, que no seas un pdf que se lee
de recorrido».**

La regla que ordena todo lo visual: **la sobriedad va en la superficie, la ambición va en lo que
la página hace.** Fondo grafito, rejilla de puntos discreta, nodos unidos por líneas, números en
monoespaciada. Un pipeline es literalmente un grafo de nodos, así que la estética no es
decorativa, pero tampoco llama la atención sobre sí misma.

**Lo que queda vetado por repetido:** papel claro (Sílice, Geoestadística), scrollytelling de
panel pegajoso (Geoestadística), telón y Lenis (la portada), acento único por curso, y los cuatro
acentos ya usados (amber de Froth, iron de Sílice, mint de Concentra, gold de Geoestadística).

### La paleta se calcula, no se elige

`src/site/palette.py` genera los 31 acentos en OKLCH y **mide el contraste sobre los dos fondos**
antes de dejarlos entrar en `temario.json`. Croma bajo a propósito: colores de instrumento. Los
31 pasan AA en claro y en oscuro. Salida en `results/palette.json`.

**Bug cazado por el propio script (2026-08-29):** la primera pareja de colores para el gemelo
(`#8FA9B4` medido contra `#C08A4E` simulado) medía **1,22 de contraste entre las dos líneas**. En
la figura que remata el curso, alguien daltónico o mirando una impresión veía una sola curva. Se
rehízo separando los dos colores en luminosidad y por tema (ahora 2,21 en oscuro y 2,24 en claro),
y se añadió una regla dura: **la serie medida va en línea continua y la simulada en discontinua;
el color nunca es la única pista.** El script falla si la separación baja de 1,8.

### Una sola gramática, tres instrumentos

Misma rejilla, misma tipografía, mismos dos colores en todo el curso. **Una lección no lleva más
de un instrumento**, declarado en `temario.json`, y `check_motion.py` lo comprueba.

| Instrumento | Para qué | Módulos |
|---|---|---|
| Grafo de nodos | El linaje de los datos y qué construye cada lección | 13 |
| Carátula | La cifra del módulo | 15 |
| Doble trazo | La curva medida contra la simulada | 7 |

### El movimiento es el sospechoso, no el protagonista

Prueba antes de añadir cualquier animación: **si se quita, ¿se entiende peor?** Con esa prueba
cayeron dos que ya estaban en el plan (el punto viajando por la tubería y la aguja subiendo a la
cifra): eran lucimiento. Quedan tres: **las dos curvas separándose**, **la perilla del caudal de
fuga**, y **el tramo del grafo que se ilumina**.

Tres condiciones no negociables: estado final visible sin JavaScript, quietas con
`prefers-reduced-motion`, y sin librerías externas salvo DuckDB bajo demanda.

### Lo que impide que esto sea un PDF

**Los 6 módulos de SQL y otros varios traen interacción, y cada uno de los de SQL trae un reto comprobable.** El reto es una sección
obligatoria (`## Hazlo tú`) en los módulos que lo declaran: el lector escribe una consulta y **la
página la ejecuta contra los datos reales y le dice si acertó**, comparando el resultado, nunca el
texto de la consulta. Punto de partida siempre dado, pista y solución plegadas.

**La consulta viva:** DuckDB por WebAssembly, cargado solo cuando el lector lo pide (unos 3 MB la
primera vez). Quien solo lee no paga nada.

**Las figuras nacen en dos temas** (claro y oscuro) desde el mismo script, con el patrón que
Sílice ya usa para los dos idiomas (`figures_i18n.py`): un `figures_theme.py` hermano cambia solo
los colores y manda cada `savefig` a su fichero. La geometría y los datos no se tocan.

## Estado

### Fase 0: COMPLETA (2026-08-29)
- Carpeta, estructura y git en rama `master`.
- Entorno `.venv` con Python 3.12.10: duckdb 1.5.5, pandas 3.0.5, pyarrow 25.0.1, matplotlib 3.11.1.
- Dataset descargado y descomprimido (209 MB), **verificado contra el PDF oficial**.
- `temario.json`: **31 módulos en 7 partes**, con la parte de SQL recortada a 6 el 2026-08-30, cifras «por
  medir» salvo las seis verificadas.
- `src/site/palette.py` + `apply_palette.py`: los 31 acentos calculados y medidos en los dos temas.
- `src/ingest/failure_reports.csv` transcrito literal, con su LEEME de erratas.
- `src/ingest/inspect_raw.py` corriendo, escribe `results/m01_raw.json`.
- Alta en `_INDICE/projects.json` (y de paso se registró Geoestadística, que faltaba).

### Hallazgos de la fase 0,5 (2026-08-30), todos medidos

**1. Particionar por día, el consejo estándar, es la PEOR opción a esta escala.**
`src/transform/choose_partition.py` escribió las mismas 1.516.948 filas de cuatro formas:

| Disposición | Ficheros | Tamaño | Escribir | Leer un día |
|---|---|---|---|---|
| Un fichero | 1 | 16,84 MB | 1,18 s | 0,021 s |
| Por mes | 8 | 17,69 MB | 0,99 s | 0,020 s |
| Por semana | 32 | 17,79 MB | 3,10 s | 0,070 s |
| Por día | 212 | 22,09 MB | 4,28 s | **0,331 s** |

Por día ocupa un 31 % más y lee **16 veces más lento** justo el caso para el que se supone que
sirve. La razón: Parquet ya salta bloques con sus estadísticas internas, así que 212 ficheros
solo añaden sobrecarga de metadatos y de apertura. Las cuatro devuelven las mismas 8.716 filas
del 5 de junio, así que la comparación es válida. **Es el módulo 6 entero, medido.**

**Consecuencia pedagógica:** `bronze.py` se queda particionando por día a propósito, porque es
lo que hace todo el mundo. El módulo 6 lo mide, lo desmonta y lo corrige. El curso comete el
error estándar delante del lector en vez de contarlo ya resuelto.

**2. El ciclo de trabajo delata las averías antes de construir el gemelo.** Un día normal el
compresor carga **3,42 h** (media de 91 días completos). Los seis días de más carga del semestre:

| Día | Horas | % del día | Qué era |
|---|---|---|---|
| 2020-04-18 | **23,81** | 98,9 | avería #1 |
| 2020-06-05 | 15,41 | 63,6 | avería #3 |
| 2020-03-12 | 13,24 | 58,1 | **sin documentar** |
| 2020-07-15 | 11,57 | 48,1 | avería #4 |
| 2020-05-13 | 11,31 | 46,7 | **sin documentar** |
| 2020-05-30 | 8,06 | 33,7 | avería #1 (segunda) |

**Las cuatro averías documentadas que están completas en el fichero caen en el top 6.** Una
consulta de agrupar encuentra lo que el proyecto entero busca. Los dos días sin documentar se
dicen en voz alta: o son falsas alarmas, o son averías que nadie reportó. El gemelo tendrá que
ganarle a esto, no solo funcionar.

**3. Dos señales digitales se contradicen en 16.762 lecturas (1,1 %).** `DV_eletric` y `COMP`
deberían ser opuestas: 6.536 lecturas las tienen las dos activas (carga y sin admisión de aire a
la vez, imposible) y 10.226 las dos a cero. Material de los módulos 12 y 20.

**4. Solo 91 de 212 días están completos.** Un día lleno son 8.640 lecturas; la mediana es 7.435
(86 %). Cinco días por debajo del 10 %. El registro tiene huecos constantes, y cualquier media
diaria hay que calcularla solo sobre días completos o mentirá. Módulo 7.

**5. Un pico de la máquina, no del código.** La primera corrida de `bronze.py` tardó 3,5 horas
en escribir y 925 s en calcular una huella SHA256 de 208 MB. Remedido después: **0,21 s, unos
969 MB/s**. Fue el antivirus o el indexador escaneando una carpeta recién creada con 209 MB
nuevos. No cambiar el código por esto; si se repite, excluir la carpeta del antivirus.

### El escáner de JavaScript de esta máquina (2026-08-30, diagnóstico cerrado)

**Servir un fichero `.js` grande cuesta 19 segundos fijos en local, y eso rompe la carga del
motor SQL en el navegador.** Costó una tarde localizarlo, así que queda escrito.

La prueba que lo demuestra, con **el mismo fichero byte a byte** y tres extensiones:

| Nombre | Tiempo de servicio |
|---|---|
| `prueba_worker.txt` | **0,34 s** |
| `prueba_worker.mjs` | 18,99 s |
| `duckdb-browser-eh.worker.js` | 19,00 s |

Cincuenta y seis veces más lento por la extensión, comprimido o sin comprimir, en primera y en
segunda petición. Es un escáner local de JavaScript, de la misma familia que el Control de
aplicaciones que ya bloquea DLLs de pandas a mitad de import.

**La consecuencia:** el navegador **aborta el arranque de un Worker** que tarda tanto, y el
síntoma es un `ERROR: error` sin ningún detalle, que no apunta a nada. Con el fichero ya en
caché, el mismo worker arranca **en 1 ms**.

**No afecta a producción.** En GitHub Pages sirve el servidor de GitHub, sin antivirus de por
medio, y el fichero se cachea. Solo afecta al desarrollo en esta máquina.

`src/site/serve.py` existe por esto y hace tres cosas que `python -m http.server` no hace:
sirve en varios hilos, comprime como Pages (incluido `application/wasm`, verificado contra un
wasm real servido desde Pages), y **cachea el gzip**, porque comprimir 34 MB cuesta 2,9 s y sin
caché se pagaban en cada petición.

**VERIFICADO el 2026-08-30 por Kevin, en su Chrome:** el motor SQL carga y la consulta del
paso 5 devuelve su tabla de seis días. **La consulta viva funciona.** El bloqueo de los 19
segundos y el `ERROR: error` eran del panel del navegador de la herramienta, no del proyecto ni
del servidor. Para verificar cualquier cosa que dependa de DuckDB en el navegador, hay que
abrirlo en Chrome; el panel no sirve para eso.

**Lo que quedaba sin verificar antes de eso:** que el motor SQL ejecutase una consulta dentro del navegador. El
código llega hasta `instantiate` (import 0 ms, worker creado 1 ms, objeto creado 1 ms) y ahí se
queda esperando al wasm. El servidor entrega los 34,25 MB correctamente en 19,2 s medidos con
`curl`, así que **no es el código ni el servidor**. Falta probarlo en un navegador normal, fuera
del panel, o con la carpeta excluida del antivirus.

### El justificado y sus ríos, medidos (2026-08-30)

Kevin: «obvio el texto está sin justificar y se ve feo». Tenía razón: la regla de la casa dice
**justificado desde 33rem de columna y rasgado en móvil**, sin `hyphens`, y no se había aplicado.
Ya está, con el corte en 34rem.

**El coste, medido en el navegador** contando el estiramiento real de los espacios (río = línea
cuyo hueco medio supera 1,5 veces el espacio natural):

| Reparto de línea | Líneas con río | Peor estiramiento |
|---|---|---|
| **por defecto** | **20 %** | **2,39x** |
| `text-wrap: pretty` | 25,7 % | 2,52x |
| `text-wrap: balance` | 50 % | 17,9x |

**`pretty` y `balance` empeoran**, así que se queda el reparto por defecto. Ensanchar la columna
tampoco resuelve: de 646 px a 820 px solo baja del 20 % al 15,2 %, y 820 px ya es demasiado ancho
para leer cómodo.

Un 20 % de líneas con río es el precio de justificar en español sin partir palabras, y las dos
reglas que lo causan (justificado sí, guionado no) las fijó Kevin midiendo. Se deja así y se
declara; si algún día molesta, la única salida real es permitir el guionado.

### El doble trazo no puede dibujar la presión (2026-08-30)

Al construir la página de pruebas, el doble trazo dibujaba la presión del depósito y **al mover
la perilla de la fuga las dos curvas no se separaban**. Medido: 32 px de separación media con
5 l/min de fuga y 31 px con 40.

No era un fallo del código. Es la tesis del proyecto, cometida contra el propio instrumento: **la
presión es la variable controlada** y el control la sostiene entre 8,2 y 9,5 pase lo que pase.

Corregido con dos gráficos, y ahora el instrumento demuestra la tesis en vez de ilustrarla:

| Caudal de fuga | Separación en la presión | Separación en el trabajo acumulado |
|---|---|---|
| 0 l/min | 0 px | 0 px |
| 5 | 25,9 | 15,1 |
| 15 | 24,9 | 32,9 |
| 30 | 22,8 | 43,6 |
| 40 | 24,9 | **50,7** |

**Regla para el resto del curso: el doble trazo nunca dibuja una variable controlada.** Dibuja
trabajo, ciclo o consumo. Aplica a los módulos 23 a 28.

`src/site/build_probe.py` genera `out/prueba_visual.html` y **no se publica**: el espejado del
portafolio la deja fuera, como `prueba_scrolly.html` en Geoestadística. Se corre a mano.

### Fase 0,5 (siguiente, y es una puerta)
Maqueta visual de **una sola lección**, con el grafo, la carátula, la consulta viva y el reto
comprobable funcionando. **Kevin la aprueba antes de que se escriban las otras treinta.**
Existe porque descubrir en el módulo 9 que la dirección visual no convence costaría rehacer nueve
lecciones. Con 31 módulos, esta puerta sigue valiendo el doble que con dieciséis.

**Lección de muestra: el módulo 10 (GROUP BY), escrita y construida.** Era el 13 antes del
recorte. Es la que mejor enseña las piezas a la vez: cifra de cabecera, consulta viva y reto, y
su resultado (las horas de carga al día) es el número del que cuelga todo el gemelo.

**Error propio corregido el 2026-08-30:** la lección publicaba 8.435 lecturas para el 13 de mayo
y el valor real es 8.716. No fue un problema de datos: `results/` siempre dijo 8.716, fue un
fallo al copiar el número a la prosa. Es exactamente lo que `check_numbers.py` atraparía, y
todavía no está construido, así que **subirlo de prioridad**.

## Riesgos declarados

1. **1,5 millones de filas no son big data.** Es una tabla mediana. El curso lo dice en el módulo
   1 en vez de disimularlo. El volumen lo pone el gemelo con sus escenarios, siempre marcados
   como simulados.
2. **Solo hay cuatro averías.** No da para estadística. El módulo 14 presenta un estudio de
   casos y lo declara.
3. **El gemelo puede no detectar nada con antelación útil.** Se publica igual, como el veredicto
   de Sílice. «No detecta» también es resultado.
4. **PostgreSQL pide administrador** y deja un servicio corriendo. Docker no está instalado y en
   la red corporativa daría guerra, así que va el instalador oficial.
5. **Las figuras en dos temas doblan el trabajo de figuras.**
6. **CC BY 4.0 obliga a citar**, en el repo, en el curso y en la página del portafolio.
7. Red corporativa con SSL interceptado: inyectar `truststore` temprano. Consola cp1252: forzar
   UTF-8 en las salidas de Python.

## Decisiones ya cerradas por Kevin

| Cuándo | Qué |
|---|---|
| 2026-08-29 | **El nombre es Fuelle.** No se vuelve a preguntar |
| 2026-08-29 | **Sin tope de módulos.** Cada concepto dura lo que necesite; prima que se entienda |
| 2026-08-29 | **Dataset MetroPT-3**, con C-MAPSS descartado a sabiendas |
| 2026-08-29 | **Stack completo por fases**, incluido PostgreSQL con instalador oficial |
| 2026-08-29 | **Los cuatro entregables**: panel, curso en el portafolio, repo público, informe de un folio |
| 2026-08-29 | **Diseño sobrio de ingeniero**, con la ambición en la interacción y no en los efectos |

## Decisiones pendientes de Kevin

- El visto bueno a la maqueta de la fase 0,5, antes de escribir las 34 lecciones restantes.
- Si el repo público lleva también las lecciones o solo el código del pipeline.
- Con 31 módulos, si prefiere que el curso se publique **por partes según se cierren** (la parte 3
  ya es un curso de SQL entero y publicable) o de una vez al final. Recomendación: por partes.

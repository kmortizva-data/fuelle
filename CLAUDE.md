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
| La puerta | `.venv\Scripts\python.exe src\site\check_all.py`. **Diez verificadores, falla de verdad.** Nunca en un bucle de shell: el bucle devuelve cero pase lo que pase |
| Datos crudos | `data/`, fuera de git, se re-descargan de UCI |
| El lago | `lake/`, fuera de git, se reconstruye entero con el pipeline |
| Git | Lo corre Claude. Un módulo por commit, mensajes en inglés, sin comillas dobles en `-m` (PowerShell 5.1) |
| Regla de oro | Ningún número se publica sin recalcularlo corriendo su script |
| Antes de empujar al remoto público | `.venv\Scripts\python.exe src\site\check_history.py`. Mira **cada fichero de cada commit**, no el árbol de hoy: más de 10 MB, `data/`, `lake/`, claves, correos, teléfonos y rutas de esta máquina. Probada plantando las cinco cosas en una rama de usar y tirar |

### Reconstruir el lago desde cero, en orden

`data/` y `lake/` están fuera de git a propósito, así que en una máquina nueva hay que
regenerarlos. El orden importa: cada script depende de lo que dejó el anterior.

```
1. data/MetroPT3(AirCompressor).csv     se descarga de UCI (209 MB)
2. src/ingest/bronze.py                 el lago: 212 particiones, ~4 s
3. src/transform/benchmark_formats.py   deja lake/_formatos/todo.parquet
4. src/ingest/partition_profile.py      perfila lo que escribió el paso 2
5. src/transform/silver.py              la plata, en rejilla de 10 s
6. src/twin/model.py                    los cuatro numeros del gemelo
7. src/twin/simulate.py                 el paso de tiempo y las perillas
8. src/site/check_all.py                las diez puertas
```

La parte 4 añade cinco scripts más y una lista propia, al final de este fichero.

**El paso 3 no es opcional.** Las consultas publicadas del módulo 7 apuntan a ese fichero y
`check_sql` las ejecuta de verdad. Si falta, la puerta lo dice por su nombre y a quién llamar,
en vez de fallar con un «No files found» que no lleva a ningún sitio.

Los demás scripts (`donde_viven.py`, `choose_partition.py`, `fingerprint.py`, `m10_duty_cycle.py`)
se pueden correr en cualquier orden después del paso 2. Todos limpian su propio directorio de
trabajo al terminar.

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

**La consulta viva:** DuckDB por WebAssembly, cargado solo cuando el lector lo pide. **7,74 MB
comprimido, medido el 2026-09-01**, no los «unos 3 MB» que decía esta línea antes de pesarlo.
Quien solo lee no paga nada.

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

### Parte 2 cerrada (2026-08-31): módulos 4 a 7, y las ocho lecciones en los dos idiomas

**Ocho lecciones de 31, las ocho en español y en inglés.** Módulos 1 a 7 más el 10 de muestra.
Los ocho verificadores en verde, y cada uno probado rompiéndolo.

**`src/medir.py` es ahora la única forma de medir del proyecto.** `measure()` da la mediana de
siete corridas con su rango, y `distinguishable()` devuelve falso cuando dos rangos se solapan.
Los tres scripts que cronometran la usan. La regla que deja escrita: **cuando dos rangos se
pisan, no hay diferencia que contar**, por lejos que queden las medianas.

**Se ganó el sueldo el primer día.** Remedir el módulo 6 con ella tumbó lo que decía la corrida
única: por mes leía en 0,020 s contra 0,021 s de un fichero, así que los números viejos daban
ganador a particionar por mes. Con mediana de siete, por mes va de 0,016 a 0,085 y un fichero de
0,012 a 0,017: **se solapan, no se distinguen**. Y particionar por día, que sigue siendo el peor,
es 12,2 veces más lento y no 16.

**Números viejos que estaban mal y ya no:**

| Dónde | Decía | Dice |
|---|---|---|
| `bronze.json` escritura | 12.533,88 s (pico del antivirus) | 4,035 s |
| `bronze.json` huella | 925,2 s | 0,422 s, 494 MB/s |
| Módulo 6, leer un día | 0,021 contra 0,331 s | 0,014 contra 0,171 s |
| Módulo 3, entre extremos | 196 veces | 186 veces |

**Hallazgos de la parte 2, todos medidos:**

1. **Las 212 particiones no son 212 días iguales.** Un día lleno son 8.640 lecturas; la mediana
   es 7.437, solo 91 días pasan del 90 % y 5 no llegan al 10 %. La mayor pesa 16 veces la menor.
   Y hay **49 días que pasan de 8.640**, porque el muestreo real tiene saltos de nueve segundos.
2. **La ingesta ingenua triplica y nadie avisa.** Tres corridas dejan 4.550.844 filas donde hay
   1.516.948. La media aguanta igual, que es lo que hace el fallo invisible.
3. **Un byte cambiado mueve 126 de los 256 bits de la huella.** El 49,2 %, que es lo que se
   espera de una huella sana.
4. **El peso de un Parquet no está en las filas.** Las mismas 1.516.948 filas ocupan 16,83 MB con
   17 columnas y 0,03 MB con 2. `timestamp` es el 30,4 % del fichero él solo, con 1.516.948
   valores distintos; las ocho digitales juntas no llegan al 1 %.
5. **La contabilidad del fichero predice su tamaño.** Las cuatro columnas de la escalera suman
   3.969,4 KB según `parquet_metadata` y el fichero mide 4.095,0 KB. Un 3,1 %, que es la cabecera.

**Cifra retirada por inestable.** El factor de contar filas (CSV contra Parquet) dio 156, 141,
283 y 129 en cuatro corridas, porque Parquet contesta desde la cabecera sin leer un dato y la
medida está en el suelo del reloj. **No titula nada**; se publican las dos estables, 54 veces con
una columna y 25 con siete. Regla: cuanto más rápida es una medida, menos fiable es su factor.

**Bloque `diagrama` nuevo en el renderizador**, para esquemas conceptuales como las capas del
lago. Emite HTML y no SVG a propósito: un SVG tendría que llevar sus colores dentro (o dos
versiones, una por tema) y no se reordenaría en móvil. Con cajas de HTML el tema y el ancho los
resuelve el CSS. Medido a 375 px: se apilan y la flecha gira, sin desbordamiento.

**Dos bugs en los verificadores, los dos encontrados porque acusaban a una lección correcta:**

- `check_sql` leía el 2 de `avg(TP2)` y el 128 de `int128` como datos publicados. Ahora se salta
  la cabecera de las cajas de DuckDB, y no cuenta dígitos pegados a letras (el 3 de `TP3`).
- **`check_english` tenía el cuerpo del bucle vacío**: comparaba bloques de código y no decía
  nada, así que durante seis lecciones solo contó cuántos había. Ahora compara de verdad, y
  distingue lo que se traduce (las explicaciones de `anota`, la prosa de un `reto`) de lo que va
  literal (SQL, salidas, el punto de partida y la solución de un reto).

**Regla de escritura nueva, salida de `bronze.py`:** una afirmación sobre el código se comprueba
o se acota. `bronze.py` decía ser idempotente y lo es, pero por la vía barata, borrando la
carpeta antes de escribir. Eso no prueba nada sobre una tubería que añade, así que la afirmación
se acotó a lo que enseña y el experimento de verdad vive en `fingerprint.py`.

**Deuda saldada:** los módulos 2 y 3 ya tienen su gemela inglesa. Las ocho parejas pasan la
puerta de paridad.

### Parte 3 cerrada (2026-09-01): el curso de SQL entero, en los dos idiomas

**13 lecciones de 31, las 13 en español y en inglés.** Módulos 1 a 13 más nada pendiente de
traducir. **Nueve** verificadores en verde. La parte 3 es publicable por sí sola.

**La muestra dejó de ser una y pasó a ser cuatro**, porque cada módulo necesita columnas
distintas y una sola sería peso muerto en casi todas las páginas:

| Muestra | Peso | Módulos | Qué lleva |
|---|---|---|---|
| `sin_timestamp_ligera` | 64 KB | 10, 11 | day, DV_eletric, COMP |
| `sql` | 2.202 KB | 8, 9, 12 | y LPS, Motor_current, TP2 |
| `un_dia` | 43 KB | 13 | y timestamp, solo del 5 de junio |
| `averias` | 1 KB | 12 | los cuatro partes |

El módulo 13 se lleva un solo día porque **la hora exacta del lago entero cuesta 5,16 MB**, que
es el hallazgo del módulo 7 cobrado. El motor pesa 7,74 MB comprimido (no los «unos 3 MB» que
decía el riesgo 8, que ahora se corrige), así que la muestra más cara añade un 28 %.

**La consulta viva llevaba rota quién sabe cuánto.** `live.js` pedía `muestras/muestra.parquet`,
un nombre que **nunca ha existido en el repo**. Comprobado en el navegador: el viejo daba 404 y
el nuevo da 200. Ahora las tablas se declaran en `temario.json`, la página las emite en
`data-tablas` y los nombres no pueden volver a separarse.

**`check_muestras.py`, el noveno verificador**, existe por eso. `check_sql` ejecuta contra el
lago y **el navegador del lector no tiene lago**: tiene una muestra con menos columnas. Una
consulta con `TP3` pasaba `check_sql` y reventaba en la página. Ahora cada bloque ejecutable y
cada reto se corren contra **la muestra de su módulo** y se comparan con el lago fila a fila.

**Regla nueva que impone:** una muestra que recorta filas obliga a que todas las consultas de su
módulo nombren el día. Si no, la página diría una cosa y el lago otra.

**Hallazgos de la parte 3, todos medidos:**

1. **La alarma de baja presión no sirve de aviso.** Salta en 5.188 lecturas (0,342 %) pero
   repartidas en **95 de los 212 días**, casi uno de cada dos. Demasiado frecuente para mirarla.
2. **Faltan dos días enteros del calendario**, el 29 de febrero y el 26 de abril. Preguntar por
   ellos devuelve `count(*)` = 0 y `avg()` = NULL en la misma fila. Ese contraste es el módulo 8.
3. **`TP2 = 8.2` encuentra 107 filas y las que quieres son 5.237.** Encuentra el 2 %, y eso es
   peor que encontrar cero, porque 107 cabe en un informe. **Y la causa dominante aquí no es la
   binaria**: el sensor da tres decimales y la pantalla enseña dos.
4. **En DuckDB `0.1 + 0.2 = 0.3` es CIERTO**, porque los literales son DECIMAL. El fallo famoso
   solo aparece con `::DOUBLE`, que es el tipo de TP2. Publicar el ejemplo clásico sin comprobarlo
   habría enseñado algo falso de este motor.
5. **Los tres estados del motor: 54,6 / 30,1 / 15,2 %.** Los cortes en 1 y 5 A están en los valles
   de la distribución, y el **98,1 %** de lo que la regla llama carga lleva la marca de
   `DV_eletric`, una señal que no se usó para escribirla.
6. **`WITH` no cuesta nada.** Anidada 0,023 s y con WITH 0,021 s, **rangos solapados**. El precio
   entero son 3 líneas más.
7. **El JOIN malo no hubo que inventarlo.** `nr` no es clave: dos partes son `#1`, así que cruzar
   por él da **6 filas de 4**. La errata que el módulo 1 se negó a corregir es el ejemplo.
8. **Un día de avería arranca MENOS.** El 5 de junio el compresor arrancó **31 veces** contra una
   mediana de **58**, y a la vez estuvo **15,41 h en carga** contra 3,42. Con fuga no llega a
   parar. Contar sucesos sin su duración da la conclusión contraria.
9. **El hueco mayor dura 48 horas**, del 25 al 27 de abril, y explica el 26 de abril que faltaba.

**Cuatro fallos propios que cazaron las puertas, y ninguno se veía releyendo:**

- Tres salidas inventadas (módulos 8, 11 y 13). `check_sql` las tumbó las tres. **Dejar de
  escribir salidas de memoria: se generan.**
- Un `ORDER BY day LIMIT 5` que **no es reproducible**: 8 corridas sobre los mismos datos dieron
  2 resultados distintos. Está en la lección como hallazgo.
- La cifra del módulo 8 iban a ser segundos, y el manual prohíbe citar tiempos en prosa.
- El módulo 3 escribía «8,716» con coma inglesa en prosa española.

**Cinco agujeros en los propios verificadores**, todos encontrados porque acusaban a una lección
correcta: `check_english` tenía **el cuerpo del bucle vacío** (seis lecciones sin comparar código
de verdad); `check_numbers` adivinaba el separador decimal contando cifras, así que «8,198» se
leía como ocho mil; y `check_sql` no conocía las tablas de compañía, no miraba dentro de los
textos que devuelve una consulta, y tiraba la hora de una marca de tiempo.

**`figures_theme.es()`** existe porque formatear un número y hacer `.replace(",", ".")` sobre la
frase entera ya se había comido la coma de tres pies de figura.

### Parte 4, primera mitad (2026-09-01): módulos 14, 15 y 16

**16 lecciones de 31 en español, 13 en inglés.** Los nueve verificadores en verde. El inglés de la
parte 4 está en deuda, que es la cadencia acordada: se traduce al cerrar la parte.

**Se paró aquí a propósito** porque el 17 necesita `dbt-core` y `dbt-duckdb`, y el 18 necesita
`deltalake` o `pyiceberg`. Instalar librerías gordas en su entorno es de las tres cosas que se le
preguntan. Kevin dio luz verde el 2026-09-01 y el bloque siguió.

**Hallazgos de estos tres módulos:**

1. **El reloj del registro no se desplaza: camina.** Las lecturas se reparten por igual entre los
   diez restos de segundo posibles, porque cada hueco de 9 s mueve la fase. La primera versión de
   `silver.py` cruzaba con la rejilla por marca exacta y **conservó una de cada diez**. Lo cazó su
   propia comprobación de que la plata tiene que salir con todas las lecturas del bronce.
2. **La plata destapa 337.653 huecos** (18,3 %) que en bronce no existían como filas. Cuestan
   1,79 MB de más, y ese es el precio de poder contar lo que falta.
3. **El ruido de coma flotante es la norma, no la excepción**: toca el 85,5 % de TP2 y el 98,6 %
   de DV_pressure.
4. **La calle explica la temperatura del aceite mejor que la carga del compresor**, 0,529 contra
   0,432, y el aceite va 46 grados por encima. Un gemelo que ignore el clima se equivocará **más
   en verano**, y eso es una fábrica de falsas alarmas.
5. **El 5 de junio el aceite deja de ciclar y se queda en 75,7 grados justo a las 10:00**, la hora
   exacta en que empieza el parte. Es el hallazgo del módulo 13 por otro camino.
6. **El contrato de datos cazó 4 de 5 roturas con 7 promesas.** La que se escapó fue una columna
   nueva: la promesa comprobaba que estuvieran las acordadas, **no que no sobrara ninguna**. Con
   la promesa que faltaba, 8 promesas y 5 de 5.

**Las muestras ya son seis**, y dos son de otro grano (`horas` y `clima`, del módulo 15). Eso
obligó a tres cambios en la maquinaria: un módulo puede declarar sus vistas por nombre en
`temario.json`, `check_muestras` reconstruye las tablas derivadas **desde el lago** en vez de leer
la propia muestra, y si una muestra recorta filas ahora lo declara `make_sample` en vez de
deducirse del recuento.

**Y la lección que se repite:** tres veces he citado en prosa un número leído de mi propia figura
(7,2 y 10,5 bar en el 14, y 76 grados en el 15). `check_numbers` las cazó las tres. **Los números
de la prosa salen de `results/`, no del dibujo.**

### Parte 4 CERRADA (2026-09-02): módulos 17 y 18, y las 18 lecciones en los dos idiomas

**18 lecciones de 31, las 18 en español y en inglés.** Nueve verificadores en verde. Con esto el
hueco de ingeniería de datos del portafolio queda cerrado entero, aunque el gemelo llegue después.

**La instalación no rompió nada.** `requirements.lock.txt` se commiteó antes de tocar el entorno y
`check_all.py` pasó entero justo después de instalar. duckdb 1.5.5, pandas 3.0.5, pyarrow 25.0.1,
numpy 2.5.2 y matplotlib 3.11.1 siguen intactos. Las extensiones `delta` e `iceberg` de DuckDB
instalan y cargan sin pelea: el riesgo del SSL interceptado no se materializó.

**Módulo 17, oro con dbt.** Proyecto dbt sobre DuckDB en `dbt/`: tres vistas de preparación sobre
las tres fuentes, tres tablas de oro encima, once pruebas. `dbt build` en verde en 17 pasos, y el
grafo tiene **9 nodos y 8 dependencias, ninguna escrita a mano**.

- **La figura sale del `manifest.json` de dbt**, no de una lista. Es el argumento entero del
  módulo, así que dibujarla a mano lo destruiría. Columna = capa; altura dentro de la columna =
  profundidad en el grafo, que es el orden en que dbt construye.
- **Las once pruebas en verde se probaron rompiéndolas**, igual que el contrato del 16: se mete a
  propósito `unique` sobre el número de parte, que el módulo 12 ya midió que es mentira, y dbt lo
  caza con una fila culpable. El fichero se restaura pase lo que pase.
- **El reto cambió de forma, como estaba previsto.** El temario pedía «añadir un modelo y ver
  aparecer su nodo», que la maquinaria de retos no puede comprobar porque compara resultados de
  consultas. Ahora pide el SELECT de un modelo de oro nuevo, y la lección explica que guardarlo
  como fichero es lo que hace aparecer el nodo. **Cero bytes de muestra nuevos**: reutiliza las
  dos tablas horarias del módulo 15.

**Módulo 18, viaje en el tiempo, con los dos formatos.** Kevin pidió montar Delta **e** Iceberg y
compararlos, así que es un banco de pruebas como el 6. El historial no está inventado: es el fallo
real de la plata, que conservaba 151.657 de 1.516.948 lecturas.

| Qué | Delta | Iceberg |
|---|---|---|
| Montaje | nada, una carpeta vacía | un catálogo SQLite |
| En disco | 12,9 KB en 4 ficheros | 53,7 KB en 12, **4,2 veces más** |
| Escribir | unas 3 veces más rápido | |
| Leer, pagando la consulta al catálogo | | unas 2 veces más rápido |

**Nada empató**, que era el resultado más probable a esta escala. Y la cuarta medida existe para
no hacer trampa: las dos primeras lecturas de Iceberg parten de un puntero que ya sabemos dónde
está, así que se añadió una que paga la consulta al catálogo. Sigue ganando.

**Dos hallazgos técnicos que valen el módulo por sí solos:**

1. **`delta_scan` acepta carpeta y número de versión; `iceberg_scan` quiere el fichero de
   metadatos exacto**, cuyo nombre lleva un uuid, porque el puntero a la versión buena vive en el
   catálogo y no en la carpeta. Por eso el proyecto mantiene dos copias con nombre estable, y la
   lección dice que es un apaño y por qué hace falta.
2. **A pyiceberg hay que darle el almacén SIN esquema `file://`.** Con él escribe rutas
   `file://C:/...` dentro del metadato y DuckDB no las sabe abrir en Windows: falla buscando el
   manifiesto, no la tabla.

**La cifra del 18: 0,32 h contra 3,17 h.** Eso decía el panel de horas de carga al día antes de
encontrar el fallo. El 18 de abril, el peor día del semestre, aparecía con **2,36** horas en vez
de **23,6**. Ni un error, ni una alarma, ni un valor imposible: un compresor sospechosamente
tranquilo.

**Tres agujeros más en los propios verificadores, todos encontrados usándolos:**

- **`check_sql` no sabía de las columnas DECIMAL.** Un `DECIMAL(3,1)` llega como `decimal.Decimal`
  y no como `float`, así que un 14,0 publicado y el `Decimal('14.0')` devuelto se leían como
  valores distintos, y la puerta acusaba a una lección correcta. La temperatura del clima es
  `DECIMAL(3,1)`, o sea que pasaba de verdad. Comprobado rompiéndolo después: sigue cazando un
  número mal escrito.
- **`check_english` trataba un `diagrama` como código literal**, así que la única forma de pasar
  era publicar el diagrama en español dentro de la lección inglesa. Es lo que llevaban haciendo
  los módulos 4, 8 y 11 desde la parte 2 sin que nadie lo viera, porque la puerta daba verde.
  Ahora compara la forma (mismas filas, mismos campos, mismas cajas encendidas) y los números, y
  deja que las palabras cambien. Los tres diagramas ya están traducidos.
- **`check_muestras` pasó de segundos a minutos** al añadir las dos versiones del 18, porque
  recalculaba los bordes del bronce una vez por lección. Con caché, 25 s.

**Limitación conocida, y es decisión de Kevin, no un bug:** las figuras se generan **solo en
español**, así que la edición inglesa enseña ejes en español, y las `salida` del módulo 16 llevan
la transcripción española que imprime `contracts.py`. Hacer cualquiera de las dos cosas bilingüe
es un trabajo aparte que el plan no ha presupuestado (Sílice lo resuelve para las figuras con
`figures_i18n.py`).

**Lo que hay que correr para reconstruir la parte 4**, después de `silver.py`:

```
src/transform/contracts.py        el contrato y sus cinco roturas
src/transform/dbt_gold.py         dbt build + el manifest + la prueba que falla
src/figures_module17.py           el linaje, leído del manifest
src/transform/table_format.py     Delta e Iceberg, las dos versiones y las medidas
src/figures_module18.py           las dos figuras del 18
src/site/make_sample.py           regenera las muestras, incluidas antes y ahora
src/site/build_challenges.py      las respuestas de los retos
```

### Figuras bilingües (2026-09-02): la deuda que destapó el cierre de la parte 4

**Las 22 figuras existen en cuatro variantes**: dos temas por dos idiomas, 88 ficheros. Antes eran
dos, y la edición inglesa enseñaba los ejes en español. Mismo defecto que los bloques `diagrama` y
misma causa: ninguna puerta lo miraba.

**El enfoque es el de Sílice, no uno nuevo.** `src/figures_i18n.py` parchea `Text.set_text`,
`Artist.set_label` y `Figure.savefig`, así que **no se toca ninguno de los 16 scripts de figuras** y
la geometría ya validada no se mueve. Tiene que ser el parche y no un argumento de idioma en
`figura()`: **solo 6 de los 16 scripts pasan por `figura()`**, los otros 10 hacen su propio bucle de
temas y su propio `savefig`.

`src/figures_build_en.py` corre cada script en su propio proceso con `FIG_LANG=en` y **reporta toda
cadena visible sin traducir**, saliendo con ese número. Ese informe ES como se escribió la tabla:
la primera corrida con la tabla vacía nombró las 114 cadenas.

**Cuatro cosas que el informe cazó y leyendo no se habrían visto:**

1. **`es()` formateaba en español siempre**, así que «1.516.948» y «16,84» se colaban en las figuras
   inglesas. Ahora resuelve el idioma, y de paso arregló tres figuras ESPAÑOLAS que imprimían
   `0.558` y `1,516,948` con el separador equivocado porque se saltaban `es()`.
2. **El corte de longitud en 4 caracteres escondía «abr», «ago» y «oro».** Bajado a 3, salieron los
   tres.
3. **Neutralizar los meses españoles fue error mío** y dejó el eje del módulo 8 en español sin que
   la puerta dijera nada. Ahora solo son neutrales los meses ingleses.
4. **Poner entradas de identidad para los meses que no cambian** («feb» a «feb») parecía inofensivo
   y pasó a minúscula el eje del módulo 18, donde matplotlib escribe «Feb». **Una traducción que no
   cambia nada no es gratis.**

**`check_lesson` exige ahora 2 temas x 2 idiomas por figura prometida**, probado escondiendo una. Y
destapó que el temario prometía `fig_m10_ciclo_de_trabajo_diario`, que nunca se dibujó y que la
lección no usa. Se quitó la promesa, no se inventó la figura.

**Lo que NO se hizo, y es un cambio de criterio:** el plan decía que `contracts.py` pasaría a
imprimir en inglés. Su narración y los nombres de sus promesas son un solo texto, y traducir solo la
narración deja la transcripción del módulo 16 medio en inglés y medio en español, que se lee peor
que lo que sustituye. El problema de verdad eran las figuras y están arregladas.

### Parte 5 CERRADA (2026-09-02): PostgreSQL portable, módulos 19 a 22

**22 lecciones de 31, las 22 en los dos idiomas.** Nueve verificadores en verde.

**PostgreSQL va portable y sin administrador.** Binarios oficiales en zip descomprimidos en
`~/tools/pgsql`, como Tectonic y ffmpeg. **330 MB, medidos a 9,1 MB/s: 36 segundos.** El clúster
vive en `lake/pg`, que ya estaba fuera de git, en el **puerto 5433** para no chocar con una
instalación de verdad, escuchando **solo en localhost**, que es lo único que hace defendible la
autenticación `trust`. Y `lc_messages = 'C'` para que los errores que publica el módulo 20 digan lo
mismo en las dos ediciones.

`src/db/servidor.py` es el único sitio que lo arranca y lo para, **y para solo lo que arrancó él**.
Dos cosas de Windows costaron tiempo y quedan escritas ahí:

- **`pg_ctl start` se cuelga para siempre si se le captura la salida**, porque `postgres.exe` hereda
  la tubería y no la cierra nunca. Va a DEVNULL.
- **`pg_ctl status` dice que sí mientras la base todavía se está recuperando.** La sonda buena es
  `pg_isready`.

**Los cuatro hallazgos, todos medidos:**

1. **Un servidor no vende velocidad.** La misma pregunta analítica **no se distingue** entre DuckDB
   y PostgreSQL: rangos solapados en siete corridas. Lo que sí cambia es cargar (**unos 20 s** para
   1.841.760 filas) y el disco: **23,8 MB en Parquet contra 267,8 en el servidor, 11,2 veces**.
2. **El esquema rechaza 6 de 6 escrituras imposibles**, cada una por una guarda distinta. Y el
   tropiezo enseña más: la prueba del 29 de febrero la rechazó **la clave primaria y no la
   foránea**, porque ese día SÍ existe en la plata como filas vacías desde que el módulo 14 puso el
   dato en rejilla. Por eso `dias` tiene **214** días donde el 19 contaba 212.
3. **El factor de un índice no se puede publicar.** Cuatro repeticiones en la misma corrida dieron
   **107,5, 114,3, 58,1 y 82,9** veces. Se publica la horquilla y se apoya en **el plan**, que pasa
   de `Parallel Seq Scan` a `Index Scan` y no se mueve. La factura: **12,3 MB** y la escritura al
   doble.
4. **La copia pesa 22,2 MB**, menos que el Parquet del que salió, porque no guarda ni el registro de
   transacciones ni los índices. Y **restaura idéntica**, comprobado por recuento, suma, días
   distintos y **el número de guardas**, que es la fila que casi nadie mira.

**Máquina nueva de la parte 5:**

- **Bloque ` ```postgres `** que `check_sql` ejecuta **contra el servidor vivo**, arrancándolo si
  hace falta y fallando con nombre si no puede. Probado cambiando un 8588 por 8500.
- **`solo_datos()` recorta el «(5 rows)» de psql**, que se leía como dato publicado. Mismo defecto
  que tenía la cabecera de las cajas de DuckDB.
- **Restricciones con nombre puesto a mano.** Sin nombre PostgreSQL inventa uno y le pega sufijos al
  recrear la tabla, así que el nombre publicado caducaría solo. Y el nombre es lo único que lee
  quien mira el error a las tres de la mañana.
- **`schema.py` se puede correr dos veces.** Costó dos intentos: renombrar la tabla se lleva sus
  guardas y deja sus nombres ocupados. Copia con `CREATE TABLE AS SELECT`, que no arrastra ninguna.

**Y la lección que se repite por cuarta vez:** publiqué 70,31 de aceite medio y son **70,57**.
`check_sql` lo cazó. Los números salen de una corrida, nunca de la memoria. `check_numbers` cazó
además dos cifras inestables en el módulo 19 (una mediana de consulta y el tamaño del clúster) que
se mueven entre corridas: fuera de la prosa, dentro de la figura.

**Para reconstruir la parte 5**, después de `silver.py`:

```
1. ~/tools/pgsql             binarios portables, si no estan
2. src/db/servidor.py        arranca
3. src/db/load_silver.py     la plata al servidor, y la comparacion del modulo 19
4. src/db/schema.py          el esquema con sus guardas y las seis imposibles
5. src/db/indexes.py         el indice, lo que da y lo que cobra
6. src/db/backup.py          la copia, la restauracion y su comprobacion
7. src/figures_module19.py a src/figures_module22.py
8. src/figures_build_en.py   las figuras inglesas
```

### Parte 6a (2026-09-03): el gemelo existe, y los módulos 23 a 25

**25 lecciones de 31 en español, 22 en inglés.** **Diez** verificadores en verde. La parte 6 se
partió en dos por decisión de Kevin: 6a es la maquinaria más los módulos 23 a 25, y 6b serán el 26,
27, 28 y la tanda de inglés.

**El gemelo son cuatro números y cuatro líneas, y ninguno está inventado.** `src/twin/model.py` los
mide del lago y **se niega a publicar** si no se sostienen. Sale así:

| Qué | Medido | La ficha |
|---|---|---|
| Arranca | **8,06 bar** | 8,2 |
| Para | **10,12 bar** | no lo dice |
| Sube por minuto cargando | **0,6735 bar/min** | no lo dice |
| Consumo | **0,0806 bar/min** | no lo dice |

**El balance de aire cuadra al 0,8 %** en seis semanas, y con eso los dos parámetros predicen una
carga de **0,1069** cuando la máquina hizo **0,1076**. Ninguno se ajustó a ella.

**Medir bien costó tres intentos, y los tres errores están en las lecciones:**

1. **Filtrar tramos cortos tiraba casi todas las cargas.** Duran 1,8 min y los vacíos 22, así que un
   mínimo de 120 s se llevaba unas y no otras. El balance salía descuadrado por 2,3 y la culpa era
   del filtro.
2. **La mediana instantánea de llenado engaña un 53 %.** El compresor arranca despacio (0,516
   bar/min los primeros diez segundos, la corriente de 9 A de la ficha), pica en 1,5 y **decae**
   según se llena. Un modelo montado sobre la mediana predice **32,7 % por debajo**.
3. **La rampa se medía sobre el registro entero** mientras todo lo demás salía de la ventana sana.

**Y el paso de tiempo se mide con los ciclos, no con la carga.** Con paso de 30 s el error del ciclo
de trabajo es **el más pequeño de la tabla** y ya se han perdido **2 ciclos de 16**: sus errores se
compensan porque cada arranque perdido alarga un vacío y acorta una carga. Contando arranques la
degradación es monótona, y el paso más grande que aún vale es **10 s, el ritmo del propio registro**.

**Tres señales más que no aportan nada**, del mismo género que el hallazgo del módulo 1:
`Caudal_impulses` es **binaria** en el fichero y la ficha la describe como caudalímetro;
`Reservoirs` correlaciona **1,0** con TP3; y `MPG` es el inverso de `DV_eletric`.

**El listón del gemelo, medido.** Un día sano y completo: la máquina 140,0 min de carga, el gemelo
152,0, **12 minutos**. El 18 de abril: la máquina 1.416,2 y el gemelo los mismos 152,0, o sea
**1.264,2 de hueco**. **105,4 veces más**, así que el error del gemelo queda dos órdenes de magnitud
por debajo de la señal.

### La perilla, y por qué va precalculada

**El doble trazo ya sale en una lección**, con el bloque ` ```perilla `. La física se simula **una
sola vez, en Python**, para cada posición del mando, y la página solo cambia de serie.

Es una decisión, no una comodidad: escribirla otra vez en JavaScript dejaría dos implementaciones
que se pueden separar, y **en esta máquina no hay node, ni deno, ni bun** con los que compararlas.
Una sola implementación no se contradice. Cuesta unos 27 KB por lección.

Se dibuja **en el servidor**, así que sin JavaScript se ven los dos trazos igual. El mando arranca
en la posición más cercana a la máquina de verdad, y los números llevan el separador decimal de la
página, que viaja en `data-decimal`.

### `check_motion`, la décima puerta

La prometía el plan desde el principio y **nunca se construyó**. Durante 22 lecciones nadie
comprobó el estado final sin JavaScript, ni `prefers-reduced-motion`, ni la regla de un instrumento
por lección. El campo `instrumento` de `temario.json` estaba declarado en los 31 módulos y **no lo
leía nadie**.

**Dos falsos verdes propios, cazados al probarla:**

- La primera versión contaba la consulta viva y los bloques `diagrama` como instrumentos, y **acusó
  a catorce lecciones correctas**. No lo son: la consulta viva es la capa interactiva, que el
  temario declara aparte, y un `diagrama` es contenido. Los tres instrumentos son el grafo, la
  carátula y el doble trazo, y **solo el tercero deja rastro en el Markdown**.
- La segunda **daba verde con `prefers-reduced-motion` borrado del código**, porque la frase seguía
  escrita en un comentario de al lado. Ahora quita los comentarios antes de mirar.

Comprueba además que lo que el temario promete de interacción esté: una lección declarada
interactiva tiene que traer consulta viva, reto o perilla, y un bloque de reto tiene que estar
anunciado. Eso no lo miraba nadie.

**`un_dia` se lleva ahora TP3**, en vez de publicar otra muestra: un día de presión son unos 9 KB y
un fichero nuevo repetiría el `timestamp`, que es la columna cara. Pasa de 43 a 61 KB.

### Hallazgo grande de la parte 6b (2026-09-03): la ventana sana no estaba sana

Calibrar el gemelo en el módulo 26 destapó tres cosas encadenadas, y las tres cambian números ya
publicados en los módulos 23, 24 y 25. El orden en que salieron importa, porque cada una tapaba
a la siguiente.

**1. Los huecos del registro se contaban como tiempo de compresor.** `_crea_tramos` medía la
duración de cada tramo con `date_diff` de la primera lectura a la última, y el registro tiene
huecos: 35 de más de una hora solo en la ventana vieja, casi todos de madrugada. Un tramo que
salta un hueco se llevaba las horas del hueco. **92 tramos se tragaban 4.906 minutos**, o sea 82
horas de compresor que nunca existieron. En la ventana nueva, febrero solo, son **28 tramos y
3.129 minutos**, que es la cifra que publica el módulo 24. Eso hundía las dos velocidades por igual.

**Y el guardián que había no podía verlo.** Comparaba el ciclo de trabajo predicho contra el
observado, y el ciclo de trabajo es un cociente: si las dos duraciones se inflan por el mismo
factor, no se mueve. Por eso ahora hay un guardián más, **los arranques por hora**, que se cuentan
contra el reloj y sí lo ven. Con los parámetros viejos fallaba un 15,4 % y nadie miraba.

**2. Del 1 al 12 de marzo de 2020 la máquina está averiada, y no está documentado.** Al arreglar
lo anterior los parámetros seguían sin cuadrar, y mirando día a día salió esto:

| | 20 al 28 de febrero | 1 al 12 de marzo | 16 al 20 de marzo |
|---|---|---|---|
| carga | 0,049 a 0,067 | 0,116 a **0,581** | 0,068 a 0,077 |
| arranques por hora | 1,66 a 2,21 | 2,71 a **5,00** | 1,96 a 2,40 |
| aceite | 54 a 57 °C | 61 a **69 °C** | 53 a 57 °C |
| corriente del motor | 1,05 a 1,37 A | 1,78 a **3,91 A** | 1,23 a 1,38 A |
| alarma LPS | 0 | salta el 11 y el 12 | ~0 |

Cuatro señales independientes, y el 13 vuelve todo a lo de antes. **La ventana de calibración del
proyecto (1 de febrero al 15 de marzo) llevaba doce días de avería dentro.** Elegir la ventana por
fecha, que es lo que se hizo para no escoger a conveniencia, protege de una cosa pero no de esta.

**La ventana sana pasa a ser febrero entero, y solo febrero.** `SANO = ("2020-02-01",
"2020-02-29")`, y el evento de marzo se publica como hallazgo del curso.

**3. La resolución de TP3 no es 0,01 bar, es 0,001**, medida y no supuesta. El módulo 24 publicaba
que la mediana instantánea de consumo caía «en la resolución del sensor» (0,060 contra 0,06).
Caía, pero de casualidad: el escalón de verdad es diez veces más fino. La mediana sí se queda
corta, un **32 %** por debajo de la media, y la razón es otra: **el consumo va a ráfagas**, así que
la mitad de los pasos de diez segundos son más tranquilos que la media.

**Los parámetros, antes y después:**

| | Publicado en 6a | Medido ahora | Por qué cambia |
|---|---|---|---|
| arranca / para | 8,06 / 10,12 bar | 8,05 / 10,10 bar | solo la ventana |
| sube por minuto cargando | 0,6735 | **1,1796** | los huecos y marzo |
| consumo | 0,0806 | **0,0711** | los huecos y marzo |
| entrega | 0,7541 | **1,2507** | |
| descuadre del balance | 0,8 % | 0,7 % | sigue cuadrando |
| carga predicha contra observada | 0,1069 / 0,1076 | 0,0568 / 0,0572 | |
| arranques por hora, predichos / observados | 2,00 / 2,363 (15,4 %) | 1,833 / 2,031 (9,7 %) | el guardián nuevo |
| lo que engaña la mediana de llenado | 53 % | **6 %** | era casi todo el fallo de los huecos |
| paso más grande que aún vale (módulo 25) | 10 s | **5 s** | la máquina llena más rápido |

**Y el día sano del módulo 23 ha cambiado dos veces**, las dos por no mirar lo que se elegía:
primero el 2 de marzo (le faltan tres horas), después el 8 de marzo (completo, pero dentro de la
avería de marzo y el más cargado de los candidatos, 140 min contra 81 de mediana). Ahora es el
**18 de febrero**, el día completo más cercano a la mediana de febrero.

**Ojo con el cociente del módulo 23.** Con el día de la mediana el hueco sale de 0,2 min y el
cociente contra el 18 de abril se dispara a 6.677, que es un artefacto de dividir por casi cero.
El suelo de ruido tiene que salir del **reparto de los días sanos**, no de un día elegido.

### Módulo 26 cerrado (2026-09-03)

**El resultado:** medir y ajustar coinciden dentro de un **7,8 %** (1,1796 contra 1,272 bar/min), y
sobre una semana sana los dos gemelos se llevan **8,2 minutos de 497,2**. El ajuste no mejora, que
es lo que el plan esperaba. Lo que sí hizo fue destapar los dos fallos de arriba.

**La lección de identificabilidad, medida:** ajustando solo la carga hay **4 puntos empatados** con
entregas de 0,72 a 1,08; solo los arranques, **40 empatados** de punta a punta de la rejilla; las
dos cosas, **uno**. La perilla recorre el valle: la carga se queda en 5,5-5,6 % y los arranques van
de 10 a 21.

**Piezas nuevas:** `src/twin/ventana_sana.py` (comprueba que una ventana de calibración sea una
máquina en un estado, y se niega si febrero pasa su propio listón), `src/figures_module26.py` con
tres figuras, la perilla `m26_valle` y el reto `m26_los_dos_observables`.

**Y un fallo de producción encontrado moviendo la perilla:** las figuras llevan huella de contenido
en la URL y los datos de la perilla no. El techo del eje va en el HTML y las series las trae un
`fetch`, así que un JSON viejo en caché dibuja contra otro techo: **seis de las veintiuna
posiciones del módulo 24 se salían del marco**. Arreglado, y `check_motion` tiene una quinta regla
que lo caza (probada rompiéndola).

### Parte 6 cerrada en español (2026-09-03): módulos 27 y 28

**Módulo 27, el residual.** Sale de una identidad y no de un ajuste, y tiene una propiedad que le da
sentido a la perilla: **con una fuga de f bar/min el residual vale exactamente f**. Se nota a partir
de **0,12 bar/min**, que es cuando pasa el suelo de ruido.

| Qué | Medido |
|---|---|
| Suelo de ruido (579 horas de febrero) | mediana 0,0053, p95 0,0505, **máximo 0,1165** |
| Techo, que es `llena` | **1,1796**, o sea 10,1 veces el suelo |
| Horas topadas en el registro | 156 de 3.924 |
| La #1b por días contra por horas | **1,09× el suelo** contra **7,47×** |
| La segunda ruta el 18 de abril y el 6 de junio | **no contesta**: ni un tramo de vacío |
| La segunda ruta el 15 de julio | **0,349 bar/min**, donde el residual está topado |

**La deriva obligó a los dos indicadores** (decisión de Kevin del 2026-09-03): el consumo sube de
0,0711 a más del doble entre febrero y agosto, así que el congelado marca 24 de 31 días en agosto.
El móvil (contra los 14 días previos) devuelve los partes al primer plano: +1,0631 el 18 de abril,
+0,8182 el 5 de junio, +1,0169 el 15 de julio, +0,5368 el 29 de mayo, contra 0,0052 de un día
corriente. **El gemelo sigue congelado; lo que se mueve es la referencia.**

**Módulo 28, el veredicto.** Con umbral 1,15 bar/min:

| | El gemelo | La alarma LPS instalada |
|---|---|---|
| Averías detectadas | **4 de 4** | 2 de 4 |
| Días con alarma | 18 | 94 |
| Falsas alarmas al mes | **1,5** | **11,4** |

Con marzo como quinta avería: **5 de 5 con 1,2 falsas al mes**. Las dos cuentas van publicadas.

**Como predictor no sirve**: solo el 15 de julio avisa antes, un día, en una racha de dos. Los otros
tres levantan la alarma el mismo día del parte. La antelación se mide **desde que se encendió la
racha**, no desde cualquier alarma previa, y eso es lo que baja el resultado de «7 a 13 días» (que
es lo que sale con la definición floja) a «uno de cuatro».

**Y el rival hay que juzgarlo en sus términos.** La primera versión contaba la LPS sobre las mismas
horas completas que usa el gemelo y daba 28 días y 3,1 falsas al mes. Pero la LPS no promedia nada y
salta sobre todo en horas incompletas: **101 de sus 136 horas**. Con el filtro del gemelo se le
quitaban tres cuartas partes de sus disparos. Sobre lecturas crudas son 94 días y 11,4 al mes.

**El rival trivial se comprueba, no se afirma:** con parámetros congelados el residual es función
creciente de la carga, así que un umbral sobre cualquiera de los dos **ordena los 207 días igual**.
El script lo verifica y falla si deja de ser cierto. El gemelo no gana en detección; gana en
unidades físicas, en no necesitar historial y en poder preguntar por una fuga que no ha pasado.

**Verificado a mano** contra el lago, sin código del proyecto: 4 de 4 y 12 días falsos en 8 meses,
idéntico a lo que dice el script.

### Parte 6 CERRADA en los dos idiomas (2026-09-03)

**28 lecciones de 31, las 28 en español y en inglés.** Solo queda la parte 7 (módulos 29, 30 y 31).

**Tres fallos que las diez puertas no veían**, encontrados al traducir:

- El bloque `sql` del módulo 24 seguía consultando hasta el 15 de marzo y su salida enseñaba 8.06 y
  10.12. `check_sql` daba verde porque **la salida es correcta para esa consulta**: lo caducado era
  la consulta, y la prosa de al lado ya citaba los números de febrero.
- El puente del módulo 24 seguía diciendo que el aire cuadraba al 0,8 %. `check_numbers` daba verde
  porque 0.8 existe en otro fichero de resultados. **Lo cazó la puerta de paridad inglesa**, que es
  para lo que sirve que las puertas se solapen.
- El módulo 25 seguía llamando al paso de 5 s «el ritmo del propio registro» y diciendo 2 ciclos de
  16. Las dos cosas eran ciertas con los parámetros viejos.

**Y una convención que se estaba torciendo:** la clave de `anota` tiene que ser **el fragmento de
código** que se anota, no prosa, o la edición inglesa tiene que repetir el español. Once claves de
los módulos 23, 26, 27 y 28 son ahora fragmentos de verdad.

**Regla que sale de esto:** un bloque `sql` publicado puede quedarse caducado sin que ninguna puerta
lo note, porque su salida sigue siendo cierta para su propia consulta. Al cambiar una ventana de
análisis hay que **buscar las fechas a mano** en las lecciones, no fiarse de los verificadores.

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
8. **El motor SQL del navegador pesa 7,74 MB comprimido**, medido el 2026-09-01 sobre los ficheros
   que se sirven de verdad. El plan decía «unos 3 MB» a ojo. Se descarga solo al pulsar y se
   cachea, así que el que solo lee no paga nada, pero en móvil con datos son 7,74 MB reales. La
   muestra más cara del curso, la de la parte 3, añade 2,14 MB encima.

## Decisiones ya cerradas por Kevin

| Cuándo | Qué |
|---|---|
| 2026-08-29 | **El nombre es Fuelle.** No se vuelve a preguntar |
| 2026-08-29 | **Sin tope de módulos.** Cada concepto dura lo que necesite; prima que se entienda |
| 2026-08-29 | **Dataset MetroPT-3**, con C-MAPSS descartado a sabiendas |
| 2026-08-29 | **Stack completo por fases**, incluido PostgreSQL con instalador oficial |
| 2026-08-29 | **Los cuatro entregables**: panel, curso en el portafolio, repo público, informe de un folio |
| 2026-08-29 | **Diseño sobrio de ingeniero**, con la ambición en la interacción y no en los efectos |
| 2026-09-02 | **PostgreSQL portable** en `~/tools/pgsql`, sin administrador. Corrige la fila del instalador |
| 2026-09-02 | **Figuras bilingües ya**, antes de la parte 5 |
| 2026-09-02 | **El residual en bar/min**, no en litros: la ficha no da el volumen del depósito |
| 2026-09-02 | **La parte 6 en dos bloques**, 6a y 6b |
| 2026-09-03 | **El veredicto lleva dos cuentas**, detector y predictor, por separado |
| 2026-09-03 | **Los días de residual alto sin parte cuentan como falsas alarmas**, con la duda declarada |
| 2026-09-03 | **La ventana sana es febrero solo** |
| 2026-09-03 | **El residual con dos indicadores**, congelado contra febrero y móvil contra 14 días |
| 2026-09-03 | **Marzo lleva las dos cuentas** en el módulo 28, con y sin él como acierto |
| 2026-09-18 | **Se instala Dagster** (dagster, dagster-webserver, dagster-dbt, dagster-duckdb) para el módulo 29. Comprobado antes contra PyPI: protobuf 6.33.6 sirve a dbt, Dagster y Streamlit, y no baja nada |
| 2026-09-18 | **El panel del 30 es una página estática** con la maquinaria de las perillas, enlazada desde el portafolio. Sin Streamlit |
| 2026-09-18 | **El repo público lleva código y lecciones**, con todo el historial y la cita CC BY 4.0 |
| 2026-09-18 | **Las partes 1 a 6 se publican ya** en el portafolio; 29 a 31 se añaden al cerrarse |

## Decisiones pendientes de Kevin

- **El nombre del repo público.** Propuesta: `fuelle`.
- **El visto bueno antes de cada empuje público**: la ficha y el curso en el portafolio, y el repo.
- **Medir la cifra del módulo 30**, «segundos hasta entender qué pasa»: enseñar el panel a una o dos
  personas que no conozcan el proyecto y cronometrar. Si no se puede, la cifra se cambia por una
  que se mida sola, y se dice en la lección.

## Parte 7, el plan (2026-09-18)

El plan entero está en `~/.claude/plans/proyecto-portafolio-data-lakes-iterative-volcano.md`,
sección «Parte 7». En corto, cinco pasos del hito 8:

| Paso | Qué |
|---|---|
| 8.1 | Publicar 1 a 6: ficha en `sitio/content/site.json`, el curso en `EMBEDDED` de `sitio/src/build.py` (con `out`, `figuras` y `assets`), repo público con guarda de privacidad sobre **todo el historial** |
| 8.2 | Módulo 29: Dagster. `lake/` pasa a `lake_antes/`, se reconstruye todo, se compara **tabla a tabla por huella** y se pasan las diez puertas contra el lago nuevo. PostgreSQL cronometrado aparte |
| 8.3 | Módulo 30: `src/twin/panel.py` precalcula, `panel.html` estático con huella en la URL |
| 8.4 | Módulo 31: folio PDF bilingüe con Tectonic, «qué se rompería», figura del arco |
| 8.5 | Inglés de 29 a 31 y republicar |

**Medido antes de planear:** Fuelle pesaría unos 49 MB en el portafolio (el motor SQL son 34,3 de
un solo fichero, `duckdb-eh.wasm`). El repo tiene 372 ficheros, el mayor de 2,2 MB, y **ninguno
contiene correos, claves, teléfonos ni rutas de la máquina**. Datos, lago, `out/` y el motor ya
quedan fuera por `.gitignore`; el motor se baja con `src/site/vendor_duckdb.py`.

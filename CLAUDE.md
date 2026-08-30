# Fuelle: un gemelo digital y su lago de datos

> **Proyecto:** Fuelle (ES) / Bellows (EN) · **Carpeta:** `Documents\02_Personal\Portafolio\Fuelle`
> **Categoría:** personal (portafolio) · **Estado:** fase 0, nació el 2026-08-29
> Índice de todos los proyectos: `Documents\_INDICE\INDICE.md`
> Plan aprobado: `~/.claude/plans/proyecto-portafolio-data-lakes-iterative-volcano.md`

Kevin aprende ingeniería de datos desde cero (pipelines, lagos de datos, SQL, administración de
bases de datos) construyendo la columna vertebral de datos de un gemelo digital. El resultado se
cuenta como curso web bilingüe de **35 módulos**, con el método de Sílice.

**El hueco que cierra:** sus cuatro proyectos publicados (Froth, Sílice, Geoestadística,
Concentra) consumen datos que alguien ya dejó limpios en un CSV. Ninguno muestra de dónde salen.

**Nombre CERRADO el 2026-08-29:** Fuelle. La carpeta no se renombra.

**Sin tope de módulos, por decisión suya el 2026-08-29:** «no te limites en el número de módulos,
lo que importa es que se explique todo y que cada módulo dure lo que tenga que durar, pero que se
entienda, de esto no tengo ni las bases, es aprender haciendo». Por eso el temario pasó de 16 a
35: SQL creció de 2 módulos a 10, y entró una parte 1 de bases que antes se daba por supuesta
(qué es una tabla, un tipo, dónde viven los datos). **Si un concepto necesita su propio módulo,
lo tiene.**

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

`src/site/palette.py` genera los 35 acentos en OKLCH y **mide el contraste sobre los dos fondos**
antes de dejarlos entrar en `temario.json`. Croma bajo a propósito: colores de instrumento. Los
35 pasan AA en claro y en oscuro. Salida en `results/palette.json`.

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

**21 de 35 módulos traen interacción y 20 traen un reto comprobable.** El reto es una sección
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
- `temario.json` congelado: **35 módulos en 7 partes**, 21 interactivos, 20 con reto, cifras «por
  medir» salvo las seis verificadas.
- `src/site/palette.py`: los 35 acentos calculados y medidos en los dos temas.
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

### Fase 0,5 (siguiente, y es una puerta)
Maqueta visual de **una sola lección**, con el grafo, la carátula, la consulta viva y el reto
comprobable funcionando. **Kevin la aprueba antes de que se escriban las otras treinta y cuatro.**
Existe porque descubrir en el módulo 9 que la dirección visual no convence costaría rehacer nueve
lecciones. Con 35 módulos, esta puerta vale el doble que antes.

**Candidato a lección de muestra: el módulo 13 (GROUP BY).** Es el que mejor enseña las cuatro
piezas a la vez: tiene cifra de cabecera, grafo, consulta viva y reto, y su resultado (las horas
de carga al día) es el número del que cuelga todo el gemelo.

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
- Con 35 módulos, si prefiere que el curso se publique **por partes según se cierren** (la parte 3
  ya es un curso de SQL entero y publicable) o de una vez al final. Recomendación: por partes.

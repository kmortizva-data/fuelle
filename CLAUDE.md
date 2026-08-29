# Fuelle: un gemelo digital y su lago de datos

> **Proyecto:** Fuelle (ES) / Bellows (EN) · **Carpeta:** `Documents\02_Personal\Portafolio\Fuelle`
> **Categoría:** personal (portafolio) · **Estado:** fase 0, nació el 2026-08-29
> Índice de todos los proyectos: `Documents\_INDICE\INDICE.md`
> Plan aprobado: `~/.claude/plans/proyecto-portafolio-data-lakes-iterative-volcano.md`

Kevin aprende ingeniería de datos desde cero (pipelines, lagos de datos, SQL, administración de
bases de datos) construyendo la columna vertebral de datos de un gemelo digital. El resultado se
cuenta como curso web bilingüe de 16 módulos, con el método de Sílice.

**El hueco que cierra:** sus cuatro proyectos publicados (Froth, Sílice, Geoestadística,
Concentra) consumen datos que alguien ya dejó limpios en un CSV. Ninguno muestra de dónde salen.

**El nombre es provisional.** Fuelle, o «Depósito / Reservoir», o el suyo. Decide Kevin.
Renombrar la carpeta después de crear el entorno rompe rutas, así que se decide antes de la fase 1.

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

Referencia: Webflow, con carta blanca de Kevin. Fondo oscuro, rejilla de puntos, nodos unidos por
líneas, tipografía grande, números en monoespaciada. **Un pipeline es literalmente un grafo de
nodos**, así que la estética no es decorativa.

**Lo que queda vetado por repetido:** papel claro (Sílice, Geoestadística), scrollytelling de
panel pegajoso (Geoestadística), telón y Lenis (la portada), acento único por curso, y los cuatro
acentos ya usados (amber de Froth, iron de Sílice, mint de Concentra, gold de Geoestadística).

**Una sola gramática, tres instrumentos.** Misma rejilla, misma tipografía, mismos dos colores en
todo el curso. Cambia el instrumento, nunca el idioma visual. **Una lección no lleva más de un
instrumento** y `check_motion.py` lo comprueba.

| Parte | Instrumento | En el temario |
|---|---|---|
| Lago (1 y 2) | Grafo de nodos | 8 módulos |
| Gemelo (3) | Doble trazo, con el área entre las curvas pintada | 3 módulos |
| Cifra de cabecera | Carátula de instrumento | 5 módulos |

**Cinco animaciones, cada una explica algo:** el dato viajando por la tubería, el doble trazo
separándose, la perilla de la fuga, la consulta viva, y la aguja llegando a la cifra. Las tres
condiciones no negociables: estado final visible sin JavaScript, quietas con
`prefers-reduced-motion`, y sin librerías externas salvo DuckDB bajo demanda.

**La consulta viva:** DuckDB por WebAssembly, cargado solo al pulsar «pruébalo» (unos 3 MB la
primera vez). Quien solo lee no paga nada. Siete módulos la llevan: 3, 4, 5, 9, 10, 13 y 14.

**Las figuras nacen en dos temas** (claro y oscuro) desde el mismo script, con el patrón que
Sílice ya usa para los dos idiomas (`figures_i18n.py`): un `figures_theme.py` hermano cambia solo
los colores y manda cada `savefig` a su fichero. La geometría y los datos no se tocan.

## Estado

### Fase 0 (en curso)
- Carpeta, estructura y git en rama `master`.
- Dataset descargado y descomprimido (209 MB), y **verificado contra el PDF oficial**.
- `temario.json` congelado: 16 módulos, 4 partes, 7 interactivos, cifras «por medir» salvo tres.
- `src/ingest/failure_reports.csv` transcrito literal, con su LEEME de erratas.
- Pendiente: `MANUAL.md`, entorno 3.12, alta en `_INDICE/projects.json`.

### Fase 0,5 (siguiente, y es una puerta)
Maqueta visual de **una sola lección**, con el grafo, la carátula y la consulta viva funcionando.
**Kevin la aprueba antes de que se escriban las otras quince.** Existe porque descubrir en el
módulo 9 que la dirección visual no convence costaría rehacer nueve lecciones.

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

## Decisiones pendientes de Kevin

- **El nombre** (Fuelle / Depósito / el suyo), antes de la fase 1.
- 16 módulos, o 14 fundiendo 12 con 13 y 15 con 16.
- Si el repo público lleva también las lecciones o solo el código del pipeline.
- El visto bueno a la maqueta de la fase 0,5.

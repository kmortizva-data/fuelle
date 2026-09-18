# Fuelle: un lago de datos y un gemelo digital, desde cero

*In English: [README.md](README.md)*

Un curso bilingüe que construye un lago de datos y un gemelo digital desde la nada, sobre
1.516.948 lecturas del compresor de aire de un tren del Metro de Oporto. Cada número sale de la
corrida de un script, y diez comprobaciones se ponen entre una lección y un commit.

## Por dónde empezar

El curso está publicado en **https://kmortizva-data.github.io/fuelle/curso/index.html**, con la
edición inglesa al lado como `index.en.html`. Hay escritos veintiocho de sus treinta y un módulos,
en los dos idiomas.

Las lecciones de SQL corren un motor de base de datos dentro de tu navegador, contra datos reales
del compresor, y comprueban tu respuesta por su resultado, no por su texto. El motor solo se
descarga cuando lo pides.

## El resultado

El gemelo son cuatro números medidos del lago: la presión a la que el presostato arranca el
compresor, la presión a la que lo para, lo rápido que se llena el depósito y cuánto aire gasta la
planta. Ninguno se ajustó. El balance de aire cierra al 0,7 %, y con esos cuatro números el gemelo
predice un ciclo de trabajo de 0,0568 donde la máquina hizo 0,0572.

Contra las cuatro fugas de aire que documenta el dataset:

| | El gemelo | La alarma de baja presión que la máquina ya lleva |
|---|---|---|
| Fugas detectadas | **4 de 4** | 2 de 4 |
| Falsas alarmas al mes | **1,5** | 11,4 |

Como detector funciona. **Como predictor no**: avisa antes en una fuga de cuatro, y con un solo
día. El curso publica las dos notas por separado, y también la parte incómoda: con sus parámetros
congelados, el gemelo ordena los días exactamente igual que un umbral sobre el ciclo de trabajo. El
código lo comprueba en vez de suponerlo.

## El hallazgo

Buscar los parámetros del gemelo no coincidía con medirlos, y persiguiendo por qué salieron dos
fallos. Los huecos del registro se estaban contando como tiempo de compresor. Y del 1 al 12 de
marzo de 2020 la máquina estaba averiada sin ningún parte que lo dijera: el ciclo de trabajo sube
de 0,06 a 0,58, el aceite se calienta diez grados y la alarma de baja presión salta por primera
vez en todo el registro.

Esos doce días estaban dentro de la ventana con la que se calibraba el gemelo. Se recalibró con
febrero solo, y se reescribieron tres módulos ya publicados.

## Los datos

MetroPT-3, la unidad de producción de aire de un tren del Metro de Oporto, del 1 de febrero al 1
de septiembre de 2020: 1.516.948 lecturas, una cada diez segundos, en 15 señales, con cuatro
averías documentadas, todas fugas de aire.

> Davari, N., Veloso, B., Ribeiro, R., & Gama, J. (2021). MetroPT-3 Dataset. UCI Machine Learning
> Repository. https://doi.org/10.24432/C5VW3R

Con licencia CC BY 4.0. El CSV (208 MB) no está en este repositorio: se descarga desde el DOI de
arriba a `data/`.

## Cómo correrlo

Python 3.12, no 3.14, porque dbt todavía no se lleva bien con 3.14.

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Después se reconstruye el lago en orden, porque cada script lee lo que escribió el anterior:

| Etapa | Scripts, en `src/` |
|---|---|
| El lago | `ingest/bronze.py`, `transform/benchmark_formats.py`, `ingest/partition_profile.py`, `transform/silver.py` |
| Oro y calidad | `transform/contracts.py`, `transform/dbt_gold.py`, `transform/table_format.py` |
| El servidor, opcional | `db/load_silver.py`, `db/schema.py`, `db/indexes.py`, `db/backup.py`. Necesitan PostgreSQL portable descomprimido en `~/tools/pgsql`, y `db/servidor.py` lo arranca y lo para |
| El gemelo | `twin/model.py`, `twin/simulate.py`, `twin/ventana_sana.py`, `twin/calibrate.py`, `twin/residual.py`, `twin/evaluate.py` |
| El sitio | `site/make_sample.py`, `site/build_challenges.py`, los scripts `figures_module*.py`, `figures_build_en.py`, `site/vendor_duckdb.py`, `site/build_site.py` |

`src/site/check_all.py` corre las diez comprobaciones, y `src/site/serve.py 8531` sirve el
resultado en http://localhost:8531/out/index.html, comprimiendo los ficheros como lo hace GitHub
Pages.

## Qué hay en cada carpeta

| Carpeta | Qué |
|---|---|
| `lecciones/` | las lecciones, el español arriba y el inglés en `en/` |
| `temario.json` | el temario: título, cifra de cabecera, figuras y scripts de cada módulo |
| `src/ingest`, `src/transform` | bronce, plata y oro |
| `src/db` | PostgreSQL, portable |
| `src/twin` | el gemelo: física, simulación, calibración, residual y veredicto |
| `src/site` | el generador del sitio y las diez comprobaciones |
| `dbt/` | el proyecto dbt de la capa de oro |
| `results/` | cada número medido, en JSON, escrito solo por scripts |
| `figuras/` | cada figura, en dos temas y dos idiomas |
| `assets/` | fuentes, series de las perillas y muestras de SQL; el motor del navegador llega con `vendor_duckdb.py` |
| `data/`, `lake/`, `out/` | fuera de git: el CSV crudo, el lago y el sitio construido |

`CLAUDE.md` y `MANUAL.md` son la memoria de trabajo del proyecto y su método de escritura.

## Licencia

MIT, ver [LICENSE](LICENSE). El dataset no está cubierto por ella: pertenece a sus autores bajo
CC BY 4.0, citado arriba. El motor SQL del navegador y sus tres dependencias conservan sus propias
licencias, que `vendor_duckdb.py` descarga a su lado, en `assets/duckdb-wasm/licenses/`.

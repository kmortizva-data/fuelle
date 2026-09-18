# Bellows: a data lake and a digital twin, built from zero

*En español: [LEEME.md](LEEME.md)*

A bilingual course that builds a data lake and a digital twin from nothing, on 1,516,948 readings
from the air compressor of a Porto Metro train. Every number in it comes out of a script run, and
ten checks stand between a lesson and a commit.

## Start here

The course is published at **https://kmortizva-data.github.io/fuelle/curso/index.en.html**, and
the Spanish edition sits next to it as `index.html`. Twenty eight of its thirty one modules are
written, in both languages.

The SQL lessons run a database engine inside your browser, against real compressor data, and check
your answer by its result rather than its text. The engine only downloads when you ask for it.

## The result

The twin is four numbers measured from the lake: the pressure at which the switch starts the
compressor, the pressure at which it stops it, how fast the receiver fills, and how much air the
plant draws. None of them was fitted. The air balance closes to 0.7 %, and with those four numbers
the twin predicts a duty cycle of 0.0568 where the machine did 0.0572.

Against the four air leaks documented in the dataset:

| | The twin | The low pressure alarm the machine already has |
|---|---|---|
| Leaks detected | **4 of 4** | 2 of 4 |
| False alarms per month | **1.5** | 11.4 |

As a detector it works. **As a predictor it does not**: it warns ahead of one leak in four, and by
a single day. The course publishes both marks separately, and the uncomfortable part too: with its
parameters frozen, the twin orders the days exactly like a threshold on the duty cycle. The code
checks that rather than assuming it.

## The finding

Searching for the twin's parameters disagreed with measuring them, and chasing why turned up two
faults. Gaps in the record were being counted as compressor time. And from 1 to 12 March 2020 the
machine was broken with no report saying so: the duty cycle climbs from 0.06 to 0.58, the oil runs
ten degrees hotter and the low pressure alarm fires for the first time in the record.

Those twelve days sat inside the window the twin was calibrated on. It was recalibrated on February
alone, and three published modules were rewritten.

## The data

MetroPT-3, the air production unit of a Porto Metro train, from 1 February to 1 September 2020:
1,516,948 readings, one every ten seconds, across 15 signals, with four documented failures, all of
them air leaks.

> Davari, N., Veloso, B., Ribeiro, R., & Gama, J. (2021). MetroPT-3 Dataset. UCI Machine Learning
> Repository. https://doi.org/10.24432/C5VW3R

Licensed CC BY 4.0. The CSV (208 MB) is not in this repository: download it from the DOI above
into `data/`.

## Running it

Python 3.12, not 3.14, because dbt does not get along with 3.14 yet.

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then rebuild the lake in order, since each script reads what the one before it wrote:

| Stage | Scripts, in `src/` |
|---|---|
| The lake | `ingest/bronze.py`, `transform/benchmark_formats.py`, `ingest/partition_profile.py`, `transform/silver.py` |
| Gold and quality | `transform/contracts.py`, `transform/dbt_gold.py`, `transform/table_format.py` |
| The server, optional | `db/load_silver.py`, `db/schema.py`, `db/indexes.py`, `db/backup.py`. They need portable PostgreSQL unzipped in `~/tools/pgsql`, and `db/servidor.py` starts and stops it |
| The twin | `twin/model.py`, `twin/simulate.py`, `twin/ventana_sana.py`, `twin/calibrate.py`, `twin/residual.py`, `twin/evaluate.py` |
| The site | `site/make_sample.py`, `site/build_challenges.py`, the `figures_module*.py` scripts, `figures_build_en.py`, `site/vendor_duckdb.py`, `site/build_site.py` |

`src/site/check_all.py` runs the ten checks, and `src/site/serve.py 8531` serves the result at
http://localhost:8531/out/index.en.html, compressing files the way GitHub Pages does.

## Layout

| Folder | What |
|---|---|
| `lecciones/` | the lessons, Spanish at the top and English in `en/` |
| `temario.json` | the syllabus: each module's title, headline figure, figures and scripts |
| `src/ingest`, `src/transform` | bronze, silver and gold |
| `src/db` | PostgreSQL, portable |
| `src/twin` | the twin: physics, simulation, calibration, residual and verdict |
| `src/site` | the site builder and the ten checks |
| `dbt/` | the dbt project for the gold layer |
| `results/` | every measured number, as JSON, written only by scripts |
| `figuras/` | every figure, in two themes and two languages |
| `assets/` | fonts, knob series and SQL samples; the browser engine arrives with `vendor_duckdb.py` |
| `data/`, `lake/`, `out/` | not versioned: the raw CSV, the lake and the built site |

`CLAUDE.md` and `MANUAL.md`, in Spanish, are the project's working memory and its writing method.

## License

MIT, see [LICENSE](LICENSE). The dataset is not covered by it: it belongs to its authors under
CC BY 4.0, cited above. The browser SQL engine and its three dependencies keep their own licences,
which `vendor_duckdb.py` downloads next to them, into `assets/duckdb-wasm/licenses/`.

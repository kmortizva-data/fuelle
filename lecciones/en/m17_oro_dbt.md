---
module: 17
---

## In 30 seconds

- The **gold** layer is the tables that answer questions, and they are written in the SQL you know.
- **dbt** is the tool that builds them: every model is **a file with a SELECT inside**.
- You never write the previous table's name, you write `ref()`. From that dbt **works out the order**.
- And the map comes from there: **9 nodes** and **8 dependencies**, not one placed by hand.
- Module 16's tests fit in **11 lines of YAML**, and one that cannot fail is worth nothing.

## What this module solves

The lake already has three sources, a clean silver layer and a contract watching it. What it does
not have is **the tables somebody will actually query**.

Nobody opens a dashboard to look at 1,841,760 readings. You open it to ask how many hours the
compressor worked yesterday, or what happened on the failure days. Those answers are small tables,
computed once and queried many times, and that is the gold layer.

Writing them is not the problem: they are queries like part 3's. The problem shows up at the third
table, when one leans on another. It stops being clear **in what order to build**, or **what
breaks** if you change the one underneath.

## Before the theory: a toy example

A small plant has three tables:

| Table | Where it comes from |
|---|---|
| `tonelaje` | from the weighbridge |
| `recuperacion` | from `tonelaje` and the laboratory assays |
| `informe` | from `recuperacion` |

Two arrows. You hold it in your head effortlessly, and if somebody changes `tonelaje` you know at
once that the other two have to be redone, in that order.

Now draw it on a whiteboard and let Monday arrive. A colleague adds a fourth table, `costes`, which
also comes from `tonelaje`. They write their query, leave it running and **do not touch the
whiteboard**.

The whiteboard still shows three boxes and two arrows. It is not incomplete in any visible way: it
is **lying perfectly calmly**, and the day somebody changes `tonelaje` they will look at the
drawing, see two things to redo, and leave `costes` computing with stale data.

The fix is not remembering to update the whiteboard. The fix is that **the map gets read from the
code**, because the code is always current: if `costes` did not read `tonelaje`, it would not work.
The dependency is already written in the query. All that is missing is something to read it and
draw it.

That is dbt in one sentence.

## Glossary

- **Model.** A file with a `SELECT` inside. Its filename is the name of the table it produces. It
  carries no `CREATE TABLE`: the tool adds that.
- **Materialise.** Decide whether a model is stored as a table (computed, taking disk) or as a view
  (recomputed on every query, taking nothing).
- **`ref()`.** How you name another model. You write `ref('otro_modelo')` instead of the table name,
  and that is what creates the arrow on the map.
- **`source()`.** The same for what comes in from outside and dbt does not build: the lake's files.
- **Lineage.** The map of what depends on what. Here it is generated, not drawn.
- **Directed acyclic graph.** The formal name for that map: arrows with a direction and no loops.
  No loops because a table cannot depend on itself, nor on anything that depends on it.
- **`manifest.json`.** The file where dbt leaves everything it knows about the project after
  compiling it. This module's figure comes from there.
- **Data test.** The same thing as a module 16 promise, under the name the industry uses.

## Step by step

### Step 1. Declare where the data comes in

The lake's three sources get declared once, with the path to their Parquet. From then on no model
writes a path again.

That pays for itself: the day the lake moves, you change one file rather than six.

### Step 2. Write each table as a SELECT and nothing more

No `CREATE TABLE`, no `DROP`, no `INSERT`. The file `oro_horas.sql` holds the query that produces
`oro_horas`, full stop. Where it gets stored and under what name is decided by configuration.

### Step 3. Name the others with `ref()`

This is the module's only genuinely new rule. Instead of writing the previous table's name, you
write `ref('prep_telemetria')`.

In exchange for that inconvenience, **the tool finds out about the dependency**. Three things come
free from there: the build order, the map, and knowing what to redo when something upstream
changes.

### Step 4. Put module 16's promises alongside

The four tests dbt ships with (`unique`, `not_null`, `accepted_values`, `relationships`) are the
contract's promises under another name. They get declared in YAML, and the ones that do not fit in
those four get written by hand as a zero row SQL file, which is exactly module 16's shape.

### Step 5. Run a single command

`dbt build` builds and tests in the same step, in the order the graph says, and **stops the moment
a test fails**. A model whose test breaks does not publish its table, and whatever depended on it
is not even attempted.

## The code, in parts

### Step 6. The sources, declared once

```yaml
sources:
  - name: lago
    tables:
      - name: plata
        meta:
          external_location: "read_parquet('../lake/silver/telemetry/**/*.parquet')"
```

```anota
sources | what comes in from outside and dbt does not build. It is the edge of the map
name: lago | the group's name, so you can write source('lago', 'plata')
external_location | dbt pastes that text behind the FROM, so the source is the lake's Parquet read in place, with no copy and no import
```

### Step 7. A preparation model

```modelo
SELECT
    timestamp,
    day,
    medido,
    dudoso,
    lecturas,
    TP2,
    Oil_temperature,
    DV_eletric
FROM {{ source('lago', 'plata') }}
```

```anota
{{ source('lago', 'plata') }} | the source declared in the previous step. The double braces mark something dbt substitutes before executing
sin CREATE TABLE | the file is called prep_telemetria.sql, so the table will be called prep_telemetria. The filename is the name
```

This model is a **view**: it does not copy silver's 1,841,760 rows, it only names them.
Materialising it as a table would duplicate the lake for no gain.

### Step 8. A gold model crossing two

```modelo
WITH por_hora AS (
    SELECT
        time_bucket(INTERVAL 1 HOUR, timestamp) AS hora,
        round(avg(Oil_temperature), 2)          AS aceite,
        count(*)                                AS lecturas
    FROM {{ ref('prep_telemetria') }}
    WHERE medido
    GROUP BY hora
)
SELECT h.hora, h.aceite, c.temperatura AS calle
FROM por_hora h
JOIN {{ ref('prep_clima') }} c ON c.hora = h.hora
```

```anota
{{ ref('prep_telemetria') }} | another model, named by its model name and not by its table's. This line is an arrow on the map
dos ref en el mismo fichero | two arrows coming into this node. Nobody declares them separately
WITH ... AS | module 11's steps, in here. A model is ordinary SQL
```

When dbt compiles it, every `ref()` is replaced by the real table name:

```salida
FROM "fuelle"."main"."prep_telemetria"
...
JOIN "fuelle"."main"."prep_clima" c ON c.hora = h.hora
```

And that is all the marker does: **swap one name for another, and point the arrow while it is at
it**.

### Step 9. The promises, in YAML

```yaml
  - name: oro_ciclo_diario
    columns:
      - name: dia
        data_tests: [unique, not_null]
      - name: dia_completo
        data_tests:
          - accepted_values:
              arguments:
                values: [true, false]
```

```anota
data_tests | the list of promises for that column. Each one becomes a query
unique | no two rows hold the same value. It is module 16's promise that the timestamp does not repeat
not_null | no empty cell
accepted_values | only these values and no others. It is the promise about the digital signals, which are only ever zero or one
```

The `unique` test turns into this, which dbt writes by itself:

```salida
select
    dia as unique_field,
    count(*) as n_records
from "fuelle"."main"."oro_ciclo_diario"
where dia is not null
group by dia
having count(*) > 1
```

It is **the same query we wrote by hand in module 16**: look for the offenders and demand zero
rows. The only change is that there we wrote it and here we name it.

### Step 10. Build and test in one go

```python
proceso = subprocess.run([DBT_EXE, "build", "--profiles-dir", "."], cwd=DBT)
```

```anota
build | build and test in the same command. Plain run would build without checking anything
cwd=DBT | dbt runs from its own folder, which is where the project lives
```

```salida
Concurrency: 4 threads (target='dev')

1 of 17 START sql view model main.prep_averias ................. [RUN]
2 of 17 START sql view model main.prep_clima ................... [RUN]
3 of 17 START sql view model main.prep_telemetria .............. [RUN]
4 of 17 START sql table model main.oro_ciclo_diario ........... [RUN]
5 of 17 START sql table model main.oro_horas .................. [RUN]
8 of 17 PASS not_null_oro_ciclo_diario_dia .................... [PASS]
14 of 17 START sql table model main.oro_averias ............... [RUN]
15 of 17 PASS clave_de_averias ............................... [PASS]

Done. PASS=17 WARN=0 ERROR=0 SKIP=0 NO-OP=0 REUSED=0 TOTAL=17
```

Look at the order, because I did not choose it. The three preparation models start together, and
`oro_averias` is last **because it leans on `oro_ciclo_diario`**, which in turn has to be built
first. That chain is written in a `ref()` inside a file, and nowhere else.

### Step 11. The gold table you can touch

This is the query inside `oro_horas`, with the two prepared tables. It is a whole gold model,
running in your browser:

```sql-vivo
SELECT h.hora,
       h.aceite,
       c.temperatura                      AS calle,
       round(h.aceite - c.temperatura, 2) AS aceite_sobre_calle
FROM horas h
JOIN clima c ON c.hora = h.hora
ORDER BY h.hora
LIMIT 6;
```

```salida
┌─────────────────────┬────────┬──────────────┬────────────────────┐
│        hora         │ aceite │    calle     │ aceite_sobre_calle │
│      timestamp      │ double │ decimal(3,1) │       double       │
├─────────────────────┼────────┼──────────────┼────────────────────┤
│ 2020-02-01 00:00:00 │   51.9 │         14.2 │               37.7 │
│ 2020-02-01 01:00:00 │  51.91 │         14.4 │              37.51 │
│ 2020-02-01 02:00:00 │  51.71 │         14.3 │              37.41 │
│ 2020-02-01 03:00:00 │   51.4 │         14.4 │               37.0 │
│ 2020-02-01 04:00:00 │  52.17 │         14.5 │              37.67 │
│ 2020-02-01 05:00:00 │  52.91 │         14.0 │              38.91 │
└─────────────────────┴────────┴──────────────┴────────────────────┘
```

## The result, measured

{{FIG:fig_m17_linaje_dbt}}

**What we expected.** A dependency map much like the one I would draw by hand.

**What came out.** **9 nodes** and **8 dependencies**, and the difference from drawing it by hand
is that I wrote neither number. The figure above is generated by reading `manifest.json`, which
dbt writes when it compiles, which in turn comes from the `ref()` and `source()` inside the SQL.

The split: **3 sources**, **3 preparation models** and **3 gold ones**. And the three gold tables
are what 1,841,760 silver readings amount to once a concrete question is asked of them:

| Gold table | Rows | One row is |
|---|---|---|
| `oro_ciclo_diario` | 212 | a day |
| `oro_horas` | 4,416 | an hour |
| `oro_averias` | 4 | a failure report |

**The whole build is 17 steps**: 6 models and **11 tests**, run in graph order by a single
command.

**And the 11 green tests prove nothing on their own.** It is module 16's rule again, and here
there is an extra reason to be suspicious. Declaring a promise costs one line of YAML, so it is
extremely easy to fill the file with promises incapable of failing and feel reassured.

So a promise destined to fail gets added on purpose. The chosen one: the report number is unique.
Module 12 already measured that this is a lie, because two of the four reports are called `#1`.

```salida
1 of 4 START test clave_de_averias .............................. [RUN]
4 of 4 START test unique_oro_averias_nr ......................... [RUN]
1 of 4 PASS clave_de_averias .................................... [PASS]
4 of 4 FAIL 1 unique_oro_averias_nr ............................. [FAIL]

Completed with 1 error, 0 partial successes, and 0 warnings:

[ERROR]: in test unique_oro_averias_nr (models\oro\_oro.yml)
  Got 1 result, configured to fail if != 0
```

It catches it, and shows the other half along the way: the `clave_de_averias` test, the one saying
the key is the **pair** of number and date, passes in the same run. Both look at the same column
and only one of them is true.

**What it means.** The map is not documentation, it is a **reading of the code**. It can go stale
exactly as far as the code can be wrong, which means that if the map lies it is because the
project lies, and that is no longer a map problem.

## Watch out

- **`ref()` is not decoration.** If you write the table name directly, the query works just the
  same and **the arrow disappears from the map**. It is the worst possible failure here, because it
  throws no error: it produces an incomplete map that looks complete. It is the toy example's
  whiteboard.
- **View or table is a decision, not a setting.** The preparation ones are views because they gain
  nothing by copying; the gold ones are tables because they are queried often and computed rarely.
- **A test that cannot fail is worse than none.** It costs one line to declare and it gives
  reassurance for free. The only way to know whether it is any use is to see it fail once.
- **The four built in tests do not cover everything.** This project's composite key does not fit in
  `unique`, so it gets written by hand as a zero row SQL. A tool not shipping a promise is no
  reason not to demand it.
- **dbt is not an orchestrator.** It knows the order of its models and nothing else. It cannot
  download the CSV or ask an API for the weather: that is module 29.
- **Gold is not "the good data".** It is an answer to a concrete question. Every gold table has a
  declared grain, a day or an hour or a report, and if you cannot say it in one sentence it is
  probably not a gold table.

## Metallurgical bridge

A plant flowsheet has been doing this same thing for decades. Grinding, rougher flotation,
cleaning and thickening. Every unit carries its declared incoming stream.

What is interesting is not the drawing, it is what the drawing allows: when the mill drops
tonnage, nobody has to guess what happens to the thickener. You read it off the flowsheet,
downstream.

And now the uncomfortable part, which anyone who has worked in a plant recognises. **The diagram
hanging in the control room is not the plant.** It is the plant of whenever somebody drew it,
minus the pump swapped out in March, plus the reagent nobody uses any more.

A dbt model is that diagram with one difference: **it is generated from the pipes**, not from the
memory of whoever installed them. It cannot go stale, because there is no copy to maintain.

## Do it yourself

```reto
pregunta: Write the SELECT of a new gold model, `oro_meses`, with one month per row. Return `mes`, `horas` with the hours the record carries, `aceite` with the mean oil temperature and `calle` with the street's, both rounded to one decimal. Eight rows.
inicio: SELECT count(*)                      AS horas,
       round(avg(h.aceite), 1)       AS aceite,
       round(avg(c.temperatura), 1)  AS calle
FROM horas h
JOIN clima c ON c.hora = h.hora;
esperado: m17_oro_por_mes
pista: The join in the starting point is already right, and so are the three number columns. What is missing is the grouping column, and it comes from the hour with `strftime(h.hora, '%Y-%m')`, which keeps the year and the month. Then you group by it and order by it.
solucion: SELECT strftime(h.hora, '%Y-%m')     AS mes,
       count(*)                      AS horas,
       round(avg(h.aceite), 1)       AS aceite,
       round(avg(c.temperatura), 1)  AS calle
FROM horas h
JOIN clima c ON c.hora = h.hora
GROUP BY mes
ORDER BY mes;
```

What you just wrote **is** a gold model. Save that SELECT in a file called `oro_meses.sql`. Inside
it, swap `horas` for `ref('prep_telemetria')` and `clima` for `ref('prep_clima')`. That makes a
tenth node appear on the map above, with its two arrows, and nothing drawn.

## Review

### What a model gains by writing `ref()` instead of the table name

Three things, and none has to be asked for: the build order, the dependency map, and knowing what
to redo when something upstream changes. The cost is six extra characters. If you put the name in
directly the query works just the same, and that is why the failure is dangerous: it gives no
warning.

### Why the preparation models are views and the gold ones are tables

A view stores nothing, it is recomputed when queried. The preparation ones only rename and select
columns from a Parquet that already exists, so materialising them would copy the lake for nothing.
The gold ones aggregate heavily and get queried often, so there it does pay to compute once.

### How this module resembles module 16 and how it differs

It is the same contract: promises written as queries that must return zero rows. The difference is
that the four commonest ones come ready made and are named in one line, instead of written. What
does not change is where their value comes from: having seen them fail once.

### The map says 9 nodes. What if somebody adds a model and does not draw it

Nothing, because there is nothing to draw. The map is read from `manifest.json`, which is
regenerated on compile, so a new model appears by the mere fact of existing. The map can only lie
if a model names its parents without `ref()`, and then the liar is the model.

### Your `dbt build` fails a test halfway through. What is left in the lake

What was there before, intact. The table whose test failed does not get published, and what sits
downstream of it is not even attempted. It is module 16's decision again: better a stale dashboard
than one with bad data. The rest of the graph's branches, the ones not passing through the failure,
do get built.

---
module: 29
---

## In 30 seconds

- Up to here the lake was built **by hand**, script by script, in an order that was only written
  down in a table in the README.
- An **orchestrator** knows the order on its own, because each piece declares what it comes from:
  **27 assets and 31 arrows**, and not one of them drawn by hand.
- The test is to delete the whole lake and ask for all of it. **The first time it did not come out
  the same**, and what that found corrected four already published lessons.
- Once fixed, it comes out **14 of 14**: every table identical, and every Parquet file identical
  **byte for byte**.
- The rule of the whole module: **what the orchestrator runs has to give the same result every
  time**. That is why the stopwatch stays outside.

## What this module solves

Every piece of the lake exists and has been checked, from the ingest to the twin's verdict. But
they exist on this machine, and they were built by running scripts by hand in an order you had to
know.

That holds up while nothing breaks. Three situations break it, and all three happen in any plant:

- **A new machine.** Somebody clones the repository and has to rebuild the lake. In what order? The
  README says so, if it is up to date.
- **A network failure at three in the morning.** The weather is asked for from somebody else's API.
  If it does not answer that night, somebody has to remember to ask again.
- **A day that arrives broken.** If 5 June goes bad, redoing the whole lake to fix one day means
  throwing away almost all the work.

An orchestrator solves all three: **it knows the order, it retries what fails and it backfills**.
And with it comes the only honest proof that the lake can be rebuilt: deleting it and looking.

## Before the theory: a toy example

A concentrator closes each day with four tasks:

| Task | Needs first |
|---|---|
| weigh the ore | nothing, it comes from the scale |
| sample | nothing, it comes from the sampler |
| assay the grade | the sample |
| close the balance | the weight and the grade |

**Three arrows.** Nobody has to write down "first this, then that": the order comes out of the
arrows. Weighing and sampling can go at the same time, the assay goes after sampling, and the
balance goes last because it needs the other two.

Now, three bad nights in a 30 day month:

1. **The laboratory analyser fails at three in the morning.** Almost always it is a stumble: you
   retry ten minutes later and it works. Nobody should be woken up for that.
2. **Tuesday's sample arrived contaminated.** Tuesday's assay and Tuesday's balance get repeated.
   **One day out of 30**, not the whole month.
3. **The month's balance book gets lost.** If it can be redone whole from the weights and the
   grades, and comes out the same, the procedure is really written down. If it does not come out
   the same, something depended on somebody's memory.

All three things have a name: **retry, backfill and rebuild**. This module does them with the lake,
and the third one was the one that gave the surprise.

## Glossary

- **Orchestrator.** The program that knows what has to be built, in what order, and what to do when
  something fails. Here it is **Dagster**.
- **Asset.** Something that should exist: a folder of Parquet, a table, a results file. Each one
  declares what it is built from.
- **Materialise.** Build an asset and leave a note of when and with what result.
- **Dependency.** The "is built from" arrow. It is the same idea as module 17's `ref()`, for the
  whole project and not just for the gold.
- **Partition.** A piece of an asset that can be built separately. Here, one day of the bronze.
- **Backfill.** Rebuilding a stretch of past partitions without touching the others. That is the
  word Dagster uses for exactly this.
- **Retry policy.** How many times a failing step is repeated and how long it waits between one
  attempt and the next.
- **Asset check.** A test that runs right after an asset is built. It is module 16's contract under
  another name.
- **Deterministic.** Giving always the same result with the same inputs, down to the last byte. A
  stopwatch is not, and a parallel writer turned out not to be either.
- **Thread.** Each of the tasks a program runs at the same time. DuckDB uses as many as the machine
  has cores, and that has a price this module measures.
- **Content fingerprint.** How many rows a table has and the sum of a number taken from each one.
  Module 5's fingerprint looked at the bytes of the file; this one looks at what they say.

## Step by step

### Step 1. Declare each piece, and what it comes from

Each asset carries a name and the list of what it needs. With that Dagster draws the graph, decides
the order and knows what goes stale when something changes upstream.

### Step 2. Declare what nobody builds too

The CSV from UCI, the weather API and the failure reports are not built by anybody here. **They get
declared all the same**, because the graph has to start where it really starts. They cannot be
materialised, and in the figure they carry a dashed border.

### Step 3. Split by day what arrives by days

The bronze had been in a folder per day since module 4. Now Dagster knows it, and that lets it redo
a single day or a stretch of days without touching the rest.

### Step 4. Retry only where there is a network

Only one piece talks to the outside: the weather download. **It is the only one with retries.**
Putting retries on everything hides real failures behind repetitions that are never going to work.

### Step 5. Hang the tests that already existed off each asset

Module 16's contract goes on to watch the silver, module 17's eleven dbt tests come in by
themselves, and module 22's restore watches the backup. None of them is rewritten: they are hung.

### Step 6. Separate building from timing

The scripts of the lessons did two things at once: build, and measure how long they took to build,
with the median of seven runs.

**An orchestrator cannot time things.** The stopwatch does not give the same answer twice, so every
rebuild would rewrite the figures the lessons publish. The rule ended up like this: what the
orchestrator runs has to give the same result every time. **Six scripts were split in two**, and
their measuring half is still there, to be run by hand.

## The code, in parts

### Step 7. An asset that calls what was already there

```python
@dg.asset(key=["lago", "plata"], deps=[bronce], group_name="lago")
def plata() -> dg.MaterializeResult:
    from transform import silver

    hecho = _corre(silver.construye)
    return dg.MaterializeResult(metadata=hecho)
```

```anota
@dg.asset | turns the function into an asset: something Dagster knows how to build
key=["lago", "plata"] | its name in the graph, with the group in front like a folder
deps=[bronce] | the arrow: the silver is built from the bronze. The order comes from here
silver.construye | module 14's function: the orchestrator works nothing new out
_corre | turns a script's "I refuse to go on" into a failure of the asset, with the same message
MaterializeResult | what gets noted down about this build: rows, readings and gaps
```

Not a line of the silver is rewritten here. **The orchestrator provides the order, not the
arithmetic.**

### Step 8. The bronze, day by day

```python
DIAS = dg.DailyPartitionsDefinition(start_date="2020-02-01", end_date="2020-09-02")

@dg.asset(key=["lago", "bronce"], deps=[CSV], partitions_def=DIAS,
          backfill_policy=dg.BackfillPolicy.single_run())
def bronce(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    tramo = context.partition_key_range
    dias = (tramo.start, tramo.end)
    bronze.clear(dias)
    bronze.write(con, dias)
```

```anota
DailyPartitionsDefinition | one partition per calendar day. The last one does not go in, which is why 2 September is written
partitions_def=DIAS | the bronze ends up split by days: it can be built whole or in pieces
BackfillPolicy.single_run() | a stretch of days goes in a single run and not one per day: reading the whole CSV every time would be absurd
partition_key_range | the stretch to be built: from the first day to the last, or a single day
bronze.clear(dias) | deletes only the folders of that stretch. The rest are not even opened
```

The calendar has **214 days** and the bronze, **212 folders**. The two missing ones are 29 February
and 26 April, the days without a single reading that module 8 found. **The orchestrator knows the
calendar; the data does not.** Those two days get built all the same and come out empty.

### Step 9. The weather, with retries

```python
@dg.asset(key=["lago", "clima"], deps=[OPEN_METEO],
          retry_policy=dg.RetryPolicy(max_retries=3, delay=10,
                                      backoff=dg.Backoff.EXPONENTIAL))
def clima() -> dg.MaterializeResult:
```

```anota
retry_policy | what to do if the step fails: repeat it instead of giving up
max_retries=3 | up to three more attempts after the first
delay=10 | it waits ten seconds before the first retry
Backoff.EXPONENTIAL | and each wait doubles the one before: ten, twenty and forty
```

Waiting longer each time is not a whim. If the API is saturated, retrying straight away saturates it
more, and four attempts in a row inside one second all fail for the same reason.

### Step 10. The gold, without rewriting dbt

```python
@dbt_assets(manifest=DBT.manifest_path, project=DBT)
def oro(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()
```

```anota
@dbt_assets | reads module 17's manifest and turns every model into an asset
manifest=DBT.manifest_path | the same file module 17's map came out of
dbt.cli(["build"]) | the same order as always: build and test in the order of the graph
.stream() | every finished model gets noted down in Dagster, and every dbt test, as a check
```

The sources of the dbt project are called `lago.plata`, `lago.clima` and `lago.averias`. The assets
of the previous steps are called the same, so **the arrows between Dagster and dbt place
themselves**.

### Step 11. A table's fingerprint, in one query

The test compares each table by what it contains, not by its bytes. Delta and Iceberg write dates
and random names into their own log, so two identical tables never have the same bytes. What gets
compared is this:

```sql
SELECT count(*) AS filas, sum(hash(t)::HUGEINT) AS huella
FROM read_parquet('lake/bronze/failures/failures.parquet') t;
```

```anota
hash(t) | a number taken from the whole row. Two rows with a single different value give different numbers
::HUGEINT | an enormous integer, so that the sum of millions of rows does not overflow
sum(...) | adding does not depend on the order of the rows, and a repeated row does move the sum
```

```salida
┌───────┬──────────────────────┐
│ filas │        huella        │
│ int64 │        int128        │
├───────┼──────────────────────┤
│     4 │ 41458351517739629285 │
└───────┴──────────────────────┘
```

A duplicated row, a changed value or a missing row moves the fingerprint. A table written in another
order, or split into other files, does not. And that second half is the one that almost hid the
finding of the module.

### Step 12. Move the whole lake aside and ask for all of it

```python
LAGO.rename(ANTES)
for grupo, que, seleccion, extra in pasos:
    tardo, r = materializa(seleccion, **extra)
```

```anota
LAGO.rename(ANTES) | the whole lake moves to another folder. From here on, there is no lake
materializa(seleccion) | it asks Dagster for a whole group, and Dagster decides the order inside it
```

This is the last run, the one that came out the same. The times are from this run and do not repeat;
what repeats is each "identical".

```salida
  el grafo: 27 activos, 24 que se pueden construir, 31 dependencias y 13 comprobaciones
  1. las huellas del lago de ahora, tabla a tabla
     14 tablas y versiones, 642 ficheros Parquet
  2. el lago entero pasa a lake_antes/: desde aquí, no hay lago
  3. Dagster lo construye todo, con los mismos pasos que construye.py
     bien  el bronce, los 214 días en una corrida       26.0 s
     bien  el resto del lago, con el oro de dbt         51.4 s
     bien  lo que consultan las lecciones                5.3 s
     bien  el gemelo, de la física al veredicto         45.0 s
     bien  PostgreSQL, desde initdb                    146.2 s
  4. las huellas del lago nuevo, y la comparación
     igual    lago/bronce                          1,516,948 filas
     igual    lago/clima                               5,136 filas
     igual    lago/averias                                 4 filas
     igual    lago/plata                           1,841,760 filas
     igual    lago/historia, Delta, versión 0            212 filas
     igual    lago/historia, Delta, versión 1            212 filas
     igual    lago/historia, Iceberg, versión 0          212 filas
     igual    lago/historia, Iceberg, versión 1          212 filas
     igual    lecciones/todo_en_un_parquet         1,516,948 filas
     igual    lago/oro_averias                             4 filas
     igual    lago/oro_ciclo_diario                      212 filas
     igual    lago/oro_horas                           4,416 filas
     igual    servidor/lecturas                    1,841,760 filas
     igual    servidor/dias                              214 filas
     igual    el servidor: 12 guardas, 3 índices, roles fuelle, mirona
     iguales  642 de 642 ficheros Parquet byte a byte (642 ahora)
     0 ficheros versionados distintos en results/ y assets/
     13 de 13 comprobaciones de Dagster en verde
  5. las diez puertas, contra el lago nuevo
     10 en verde, salida 0
  6. rellenar hacia atrás: se estropea el 2020-06-05 y se rehace solo ese día
     igual    el día rehecho, byte a byte
     211 de 211 ficheros de los otros días, sin tocar
  todo igual: lake_antes/ borrado
  4.6 minutos en total
```

### Step 13. Write with a single thread

```python
@contextlib.contextmanager
def un_solo_hilo(con):
    antes = con.sql("SELECT current_setting('threads')").fetchone()[0]
    con.execute("SET threads = 1")
    try:
        yield
    finally:
        con.execute(f"SET threads = {antes}")
```

```anota
current_setting('threads') | how many threads DuckDB is using now, so as to leave it the same at the end
SET threads = 1 | a single task writing, so the rows always come out in the same order and in the same files
finally | whatever happens inside, the connection goes back to how it was
```

And the silver, on top of that, is written in time order: an `ORDER BY r.timestamp` at the end of
its query. Neither of the two things was in the plan. They came out of the first rebuild, and they
are what the result is about.

## The result, measured

{{FIG:fig_m29_grafo_de_activos}}

**What we expected.** That Dagster would rebuild the lake and that it would come out the same. All
the scripts had been checked already, so the test looked like a formality.

**What came out the first time.** **13 of 14** tables identical, the ten gates with one in red, and
three things nobody had seen in 28 modules:

1. **A hidden dependency.** The weather script reads the silver for module 15's correlations, and
   the graph did not say so. Dagster ran it before the silver existed, and the script, instead of
   refusing, **wrote `null` into seven published figures**. By hand it never happened, because 15
   was always run after 14.
2. **The same rows, other files.** The bronze and the silver came back with exactly the same
   content, but spread over other files and in another order. DuckDB writes with several threads at
   once, and each run spreads it out its own way.
3. **And that moved numbers.** A floating point average added up in another order changes in its
   last decimal, and when it falls right in the middle of a rounding, it jumps. In `oro_horas`,
   **five hours out of 4,416 changed by a hundredth**. And the column weights module 7 publishes, by
   a few bytes.

To find out what was causing it, an experiment writes each layer twice in each way. The ways are
two: with DuckDB's threads or with a single one. The silver, on top of that, unordered or in time
order. Then it compares the files of the two writes and the hourly averages of each one.

```salida
  bronce varios hilos              213 y  213 ficheros,  198 idénticos,  22.06 MB
  bronce un hilo                   212 y  212 ficheros,  212 idénticos,  22.05 MB
  plata  varios hilos, sin orden   402 y  405 ficheros,    1 idénticos,  24.12 MB, 2 de 4416 medias horarias distintas
  plata  un hilo, sin orden        400 y  400 ficheros,  400 idénticos,  22.08 MB, 0 de 4416 medias horarias distintas
  plata  varios hilos, en orden    214 y  214 ficheros,  207 idénticos,  21.88 MB, 0 de 4416 medias horarias distintas
  plata  un hilo, en orden         214 y  214 ficheros,  214 idénticos,  21.88 MB, 0 de 4416 medias horarias distintas
```

**There were two causes, and each one fixes a different thing.** The order of the rows fixes the
averages. The silver used to come out in a jumbled order, different on every run, and sorting it by
time leaves the averages still even with several threads. The single thread fixes the bytes: with
several, even if the rows go in order, some file comes out different every time. The lake uses both
things, and that is step 13.

**The fix for the weather** was splitting its script: the orchestrator only downloads it and writes
it, and module 15's analysis refuses if there is no silver.

**And the fix uncovered the worst of it.** Written in order, the silver takes **21.88 MB**, when
before it came out around 24: the disorder was inflating it, spread over some four hundred jumbled
files. Three published lessons leaned on that inflated size and were corrected, each one saying what
it used to say:

| Module | Said | Says now |
|---|---|---|
| 14 | the gaps cost almost two megabytes | **1.38 MB**, measured by writing the silver without them |
| 19 | the server takes eleven times more | **12.2 times**: 21.9 MB against 267.8 |
| 22 | the backup weighs less than the Parquet | it weighs a little more: 22.2 against 21.9 |
| 7 | the weights of a file written from the jumbled bronze | **16.84 MB**, and the factor of seven columns drops from 25 to 22 |

**What came out the last time.** With both fixes, the third rebuild came out identical in
everything:

- **14 of 14** tables identical by their content.
- **642 of 642** Parquet files identical byte for byte.
- Not one published result different.
- The 13 checks and the ten gates, green.

And the backfill: 5 June was deleted from the bronze, as if it had arrived corrupted, and Dagster
redid that day and only that day. It came back identical byte for byte, and the other **211** files
of the bronze were not touched.

**What it means.** That the test was worth it for what already exists. The 28 previous modules had
been checked one by one, by ten gates. Even so, three of their figures depended on something no
check was looking at: **that writing the same thing twice gave the same bytes**. It only shows up by
rebuilding, because only then are there two versions to compare.

## Watch out

- **Reproducible is not correct.** If a script had a bug, Dagster would rebuild it just as badly and
  the comparison would come out perfect. This test says the lake **can be redone**; whether it tells
  the truth is said by the ten gates and the previous modules.
- **A content fingerprint does not see the order, on purpose.** That is why the first rebuild gave
  the bronze and the silver as identical while their files were other ones. Both comparisons are
  needed: the content for the tables, the bytes for what gets written the same way.
- **A script that writes `null` instead of refusing is worse than a failure.** The weather failure
  gave no error: it left seven holes in published figures, and only the numbers gate caught it.
- **The stopwatch stays outside, and not for convenience.** An orchestrator that measured times
  would rewrite on every run the figures the lessons publish.
- **The rebuild did not touch `data/`.** The CSV and the downloaded weather are the input, not the
  lake. That is why the weather did not talk to the network, and **the retry never had to act**.
- **An empty partition is not an error.** 29 February and 26 April get materialised without a single
  reading. Dagster does not know there was no data that day: the data knows that.
- **Dagster's interface is for looking.** The test runs without it, from Python. If you open it, do
  it with `src/orchestration/abre.py`, which fixes the configuration folder. Without it, Dagster
  sends usage statistics to its authors.

## Metallurgical bridge

The start up of a grinding and flotation circuit has worked this way for decades. Nobody starts the
cells before the pumps that feed them, nor the mill before its lubrication. And nobody knows it by
heart: **the control system prevents it with interlocks**, because every piece of equipment has
declared what it needs upstream.

An orchestrator is that start up sequence for data. And the reconciled metallurgical balance shows
the same thing as the backfill: when the laboratory corrects one shift's assay, that shift's balance
gets recalculated. **Not the year's.**

The thread business has its plant version too. Two samplers cutting the same stream at a different
rhythm give the same average grade and **a different grade in each sample**. If a report publishes
the grade of one particular sample, it depends on which sampler did the cutting.

## Review

### What Dagster knows that the README did not know already

The same thing, but read from the code instead of written by hand. The README had a table with the
order of the scripts, and it was missing two: the weather one and the failure reports one. Dagster's
graph comes out of what each asset declares, so it cannot forget anybody. What it can do is trust an
incomplete declaration, and that is what happened with the weather.

### Why the stopwatch cannot go into the orchestrator

Because an orchestrator runs the same thing many times, and every time it has to give the same
result. A measured time never repeats, so every rebuild would rewrite the published figures.
Building is orchestrated; measuring stays in the lessons' scripts, to be run by hand.

### Why the test compares content and bytes as well

Because each comparison sees what the other one does not. The content can be compared in any table,
including in Delta, Iceberg and PostgreSQL, which never repeat their bytes. But it does not see the
order of the rows. The bytes do see it, and they were the ones that uncovered the jumbled rows.

### 5 June arrives corrupted. What gets redone and what does not

That day's partition of the bronze gets redone, and nothing else of the bronze: the test did it and
the other files were not touched. Afterwards what hangs off it has to be redone, and there the whole
silver comes in: in Dagster the silver is not split by days.

### A check green after rebuilding. What does it guarantee

That what that check promised holds on the new lake, and nothing else. The eleven dbt tests
and module 16's contract passed on the first rebuild, and even so there were seven figures set to
`null`. A check watches what it was told to watch.

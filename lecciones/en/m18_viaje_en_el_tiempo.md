---
module: 18
---

## In 30 seconds

- A Parquet folder **forgets**. Overwrite it and yesterday no longer exists.
- An **open table format** keeps the old versions and points at the current one.
- This module's history is not invented: it is **silver's real bug**.
- The old table said **0.32 h against 3.17 h** of load a day. A factor of ten, with no warning.
- Both formats get built and measured. Delta takes **4.2 times** less room, Iceberg reads faster.

## What this module solves

Everything this course has built overwrites. `bronze.py` deletes the folder and writes it again;
`dbt build` replaces the gold table. That is normal, and it works.

Until somebody asks what the dashboard said last week.

And it is not an idle question. This project had a real bug in the silver layer. The first version
joined the readings to the grid on an exact timestamp, and kept **151,657 of 1,516,948**, one in
ten. The bug was found and fixed.

What there is no way to answer is what the dashboard was showing meanwhile, because that table no
longer exists. It was overwritten.

## Before the theory: a toy example

The laboratory sends you the grades of three batches:

| batch | grade |
|---|---|
| L1 | 1.0 |
| L2 | 1.2 |
| L3 | 0.8 |

You work out the mean, **1.0 %**, and send it to the client.

On Tuesday the laboratory recalibrates and resends the file with corrected grades. You save it
over the previous one, recompute and send **1.3 %**.

On Thursday the client calls: why did you tell them 1.0 on Monday.

And you cannot answer. It is not that you do not remember: **Monday's data is gone**. You know what
today's file says and nothing else.

The obvious fix is keeping a copy with the date in the name. It works until there are three tables
and forty days, and then nobody knows which was the good one at any given moment.

The good fix is another. The old files **do not get deleted**, and beside them a notebook gets
written with one line per change: "from today, the table is these files". To read Monday you read
the notebook down to Monday's line.

That is an open table format, and it is no more than that: the same old Parquet, plus a notebook.

## Glossary

- **Open table format.** A convention for treating a folder of Parquet as a table with history.
  Delta Lake and Iceberg are the two that work without Spark.
- **Version, or snapshot.** The state of the table after a change. They are numbered.
- **Transaction log.** The example's notebook. In Delta it is a `_delta_log` folder inside the
  table itself.
- **Metadata.** In Iceberg, the files saying which files each version is made of.
- **Catalog.** Whoever knows where each table is and which is its current version. Iceberg demands
  one; Delta does not.
- **Time travel.** Querying a version that is no longer the current one.

## Step by step

### Step 1. Manufacture the history, which already existed

There is no need to invent two versions. The gold table gets computed twice: once over the buggy
silver and once over the fixed one. The first is **version 0** and the second **1**.

Reproducing the bug does not require digging out the old script. The bug fitted in a `JOIN`, so
joining on an exact timestamp again is enough.

### Step 2. Delta: write into an empty folder

You point it at a folder and write. Two writes in a row leave two versions, and the `_delta_log`
keeps track of which is which.

### Step 3. Iceberg: mount a catalog first

Iceberg does not start without somebody keeping the list of tables. The cheapest one with no server
is **SQLite in a file**, and that file is the whole setup.

This difference needs no stopwatch and it is the first one to appear.

### Step 4. Ask for the latest and for the old one

Both are read from DuckDB with the `delta` and `iceberg` extensions. The normal query asks for the
latest version. Time travel is the same query with one more piece.

### Step 5. Measure, median of seven

Like module 6, and with its rule: if two measurements' ranges overlap, **there is no difference to
report**. `distinguishable()` decides, not the medians.

## The code, in parts

### Step 6. Both versions in Delta

```python
write_deltalake(str(DELTA), v0, mode="overwrite")
write_deltalake(str(DELTA), v1, mode="overwrite")
```

```anota
mode="overwrite" | replaces the table's content. The previous version is NOT deleted: it stays in the folder and the log points at the new one
dos llamadas | two versions. There is nothing else to do, and no folder to prepare
```

### Step 7. Both versions in Iceberg

```python
cat = catalogo_iceberg()
cat.create_namespace_if_not_exists("oro")
tabla = cat.create_table("oro.ciclo_diario", schema=v0.schema)
tabla.append(v0)
tabla.overwrite(v1)
```

```anota
catalogo_iceberg() | opens the SQLite catalog. Without it there is no table at all
create_namespace | Iceberg groups tables into namespaces, like a database's schemas
create_table | the schema has to be declared up front. Delta works it out from the data
append y overwrite | two changes, two snapshots
```

Four lines against two, and one of them mounts a database. It is the same table.

### Step 8. The latest version, in Delta

```sql
SELECT count(*) AS dias, round(avg(horas_de_carga), 2) AS horas
FROM delta_scan('lake/_formatos_de_tabla/delta');
```

```anota
delta_scan | reads a Delta table. First you need INSTALL delta and LOAD delta, once
la ruta | the table's folder, nothing more. The log lives inside
```

```salida
┌───────┬────────┐
│ dias  │ horas  │
│ int64 │ double │
├───────┼────────┤
│   212 │   3.17 │
└───────┴────────┘
```

### Step 9. And now the old one

```sql
SELECT count(*) AS dias, round(avg(horas_de_carga), 2) AS horas
FROM delta_scan('lake/_formatos_de_tabla/delta', version = 0);
```

```anota
version = 0 | the first version. It is all that separates a normal query from time travel
```

```salida
┌───────┬────────┐
│ dias  │ horas  │
│ int64 │ double │
├───────┼────────┤
│   212 │   0.32 │
└───────┴────────┘
```

The same **212** days, and a tenth of the loaded hours. That is what the dashboard was showing, and
it throws no error at all: it is a compressor that looks comfortably underworked.

### Step 10. The same in Iceberg, and what it costs

```sql
SELECT count(*) AS dias, round(avg(horas_de_carga), 2) AS horas
FROM iceberg_scan('lake/_formatos_de_tabla/iceberg_ultima.metadata.json');
```

```anota
iceberg_scan | reads an Iceberg table, and it wants the exact metadata file, not the folder
iceberg_ultima.metadata.json | a workaround of this project's, and the lesson explains it right below
```

```salida
┌───────┬────────┐
│ dias  │ horas  │
│ int64 │ double │
├───────┼────────┤
│   212 │   3.17 │
└───────┴────────┘
```

That filename is a copy this project maintains by hand. The real one is called
`00002-d4a1ce7d-...metadata.json`, with an identifier that changes on every run.

And it is not a whim of the tool. **Whoever knows which is the current version of an Iceberg table
is the catalog, not the folder.** DuckDB refuses to guess it by looking at the files, and rightly
so: it could read something half written. Delta does not have this problem because its log sits
inside the table itself.

### Step 11. The two versions, side by side

```sql-vivo
SELECT a.dia,
       a.horas_de_carga                               AS antes,
       b.horas_de_carga                               AS ahora,
       round(b.horas_de_carga - a.horas_de_carga, 2)  AS diferencia
FROM antes a
JOIN ahora b ON b.dia = a.dia
WHERE a.dia = DATE '2020-04-18';
```

```salida
┌────────────┬────────┬────────┬────────────┐
│    dia     │ antes  │ ahora  │ diferencia │
│    date    │ double │ double │   double   │
├────────────┼────────┼────────┼────────────┤
│ 2020-04-18 │   2.36 │   23.6 │      21.24 │
└────────────┴────────┴────────┴────────────┘
```

18 April is failure number one, the worst day of the half year. The old table put it at **2.36**
loaded hours, a quietish day. It is **23.6**.

## The result, measured

{{FIG:fig_m18_historial_de_versiones}}

**What we expected.** That the old version would look like the good one with some noise on top.

**What came out.** An almost flat line. The buggy version is not offset: it is **flattened**, and
the failure peaks vanish inside the thickness of the line.

That is the module's argument, drawn. A dashboard fed by that table would not have thrown a single
error, nor an alarm, nor an impossible value. It would have shown a quiet compressor for months.

### The two formats, measured

{{FIG:fig_m18_delta_contra_iceberg}}

And there is no tie here, which was the likeliest outcome at this scale. The two separate, and in
opposite directions:

| What | Delta | Iceberg |
|---|---|---|
| Setup | nothing, an empty folder | a SQLite catalog |
| On disk | 12.9 KB | 53.7 KB |
| Files | 4 | 12 |
| Writing both versions | about 3 times faster | |
| Reading, even asking the catalog | | about 2 times faster |

**Iceberg takes 4.2 times more disk** to hold exactly the same table, and leaves **12** files where
Delta leaves **4**. The reason is what each of them counts as metadata. Delta notes one line per
version in its log; Iceberg writes three things on every change, a metadata file, a manifest list
and a manifest.

**And there is a point of bookkeeping worth a look.** Delta keeps **2** versions, which are the two
writes. Iceberg leaves **3** metadata files, because creating the empty table is already a change
with its own snapshot.

**A piece of honesty about the read measurement.** Iceberg's first two reads start from a metadata
file we already know the location of, and that skips the step a real query cannot skip. That is
why there is a fourth measurement, "leer preguntando primero", which pays for the catalog lookup.
It still reads faster, so the advantage is real and not a gift from the method.

**What it means.** Neither of them wins. Delta is cheaper to set up, to write and to store.
Iceberg reads faster, and brings a catalog that with a few tables stops being in the way and
becomes what you were after. For this project, with one gold table and no server, **Delta is the
choice**, and that is now a conclusion rather than a preference.

## Watch out

- **Keeping history is not free.** The old files take room and do not clean themselves. Both
  formats ship a command to throw away what came before, and using it erases the time travel.
- **This is not a backup.** It protects you from a bad calculation, not from a broken disk. Lose
  the folder and you lose every version at once.
- **Time travel does not fix the bug, it explains it.** It answers what was shown and since when.
  Fixing the data is still separate work.
- **The DuckDB extension only reads.** Writing needs each format's Python package. That is enough
  for a lake like this one and it is worth knowing before designing on top of it.
- **This page's browser has neither extension.** That is why the challenge below does not time
  travel: it downloads both versions already extracted and crosses them, which is the skill that
  actually gets used afterwards.
- **Without a catalog, Iceberg outside its own tooling is awkward.** You have to tell the query the
  exact metadata file, and only the catalog knows that name.

## Metallurgical bridge

A laboratory does not delete Monday's result when it recalibrates the instrument. It issues a new
certificate, with its number and its date, and the old one stays in the archive marked superseded.

Nobody does this out of nostalgia. Monday's ore was already sold with that number in front of it,
and the day somebody disputes the invoice you have to show what the decision rested on.

An open table format is that certificate archive. And the question it answers is the same one: not
what the grade is, but **what the grade was in front of us when we decided**.

## Do it yourself

```reto
pregunta: Cross the two versions of the table and pull out the five days where they contradict each other most. Return `dia`, `antes`, `ahora` and `diferencia` with the hours between one and the other, rounded to two decimals, ordered from largest down. Five rows.
inicio: SELECT a.dia,
       a.horas_de_carga  AS antes,
       b.horas_de_carga  AS ahora
FROM antes a
JOIN ahora b ON b.dia = a.dia;
esperado: m18_donde_mentia
pista: The join is already done and so are the two columns. What is missing is the subtraction, which is `ahora` minus `antes` wrapped in a `round(..., 2)`, and then ordering by it downwards and keeping five. Both columns of the subtraction have to be written out in full, `b.horas_de_carga - a.horas_de_carga`, because the short name does not exist yet while it is being computed.
solucion: SELECT a.dia,
       a.horas_de_carga                               AS antes,
       b.horas_de_carga                               AS ahora,
       round(b.horas_de_carga - a.horas_de_carga, 2)  AS diferencia
FROM antes a
JOIN ahora b ON b.dia = a.dia
ORDER BY diferencia DESC
LIMIT 5;
```

The five rows that come out are five days of failure or heavy work, and they are exactly the ones
the old version was hiding. The bug did not spread its error evenly: it ate more the more there
was to see.

## Review

### Why a Parquet folder cannot answer what the dashboard said yesterday

Because it keeps nothing from yesterday. Overwriting a file leaves a single state, the last one,
and the previous one is nowhere. The folder knows what it holds, and does not know what it held.

### What an open table format adds to that same folder

A notebook beside it. The data is still ordinary Parquet, and what is new is a log with one line
per change, saying which files the table is made of from that moment. Reading an old version means
reading the notebook down to that line.

### The difference between Delta and Iceberg you notice before measuring anything

The setup. Delta writes into an empty folder and asks for nothing else. Iceberg needs a catalog
before it will accept a single row, and here that was a SQLite file. With one table that is pure
nuisance, and with forty it is exactly what you need.

### Your table has been written daily for a year and takes ten times what it should

That is the history, and it is the announced price. Every write leaves the old files where they
were. Both formats ship a command to throw away what is older than a given age, and that age has
to be chosen knowing it erases the time travel up to there.

### You find a calculation bug from a month ago. What does this give you that you did not have

The answer to what was shown and since when, which is what whoever made decisions with those
numbers is going to ask. Here the old version gave 0.32 loaded hours a day and the good one gives
3.17, and 18 April, the worst day of the half year, showed up as a quiet day.

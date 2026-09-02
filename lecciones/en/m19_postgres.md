---
module: 19
---

## In 30 seconds

- Until now the database was **a file**. Now it is **a service** you have to start.
- Handing it the **1,841,760** readings costs **about 20 s**. The file already had them.
- And the surprise: answering **does not get faster**. The ranges overlap, so they do not differ.
- What does change is disk: **23.8 MB** in Parquet against **267.8** in the server.
- The table we just created accepts any nonsense. That is module 20.

## What this module solves

Everything this course has done fitted in one process. DuckDB opens the file, answers and closes,
and meanwhile nobody else can touch it.

That ends the moment there are two people. Or a dashboard querying while the ingestion writes. Or
somebody who needs read permission and nothing else.

A database server exists for that: a process that stays up, serves several clients at once and
decides who may do what. **PostgreSQL** is the one the job adverts ask for and the one with thirty
years of head start at that task.

What this module measures is what the change costs, because it is not free.

## Before the theory: a toy example

The laboratory notebook is on your desk. You write down each batch's grade and look it up whenever
you like. It is fast, it is yours, and nobody has to give you permission.

Now three more people turn up:

| Who | What they need |
|---|---|
| the shift supervisor | to read the last batch's grade |
| the laboratory | to write the next one |
| the client | to read, and only to read |

With the notebook on your desk there are three problems and none is about speed. **They cannot
look at it at once**, because the notebook is where you are. **There is no way to let the client
read without being able to write**, because a notebook cannot tell them apart. And if two people
write at once, **the last one to close wins** and the other never finds out.

The answer is not a faster notebook. It is putting the notebook on a counter, with somebody behind
it serving in turn who knows who everyone is.

That is a database server. And notice what has **not** improved: looking up a grade still costs the
same. What has been bought is the counter, not the speed.

## Glossary

- **Server.** A process that stays up waiting for requests. If it is not started, there is no
  database at all.
- **Client.** Anybody asking it: `psql`, a Python script, a dashboard.
- **Port.** The number you talk to it on. PostgreSQL's standard is 5432; this course uses **5433**
  so it never clashes with a real install.
- **Cluster.** The folder holding all the server's files, here `lake/pg`. Confusingly, it has
  nothing to do with several machines.
- **`initdb`.** The program that creates that folder the first time.
- **`COPY`.** PostgreSQL's bulk load command. It brings in millions of rows without going through
  `INSERT` one at a time.
- **OLTP and OLAP.** Two ways of using a database: many small operations (OLTP), or few questions
  that sweep everything (OLAP). PostgreSQL was born for the first and DuckDB for the second.

## Step by step

### Step 1. Get PostgreSQL without being an administrator

The official installer wants administrator rights and leaves a Windows service running. The same
binaries are also published as a zip, and that one **unzips wherever you like and runs as it is**.

It is what this project already does with Tectonic and with ffmpeg. Part 5 stops depending on
anybody having permissions for anything.

### Step 2. Create the cluster

`initdb` prepares the data folder: the system database, the configuration and the log files. It is
done once and never touched again.

It goes inside `lake/`, which this project already keeps out of git. The database gets rebuilt like
the rest of the lake, and not one byte of it goes to the repository.

### Step 3. Start it on a port that is not everybody's

Two decisions, both visible in `postgresql.conf` and both worth explaining:

- **Port 5433**, not 5432, so a real PostgreSQL installed here tomorrow can live alongside this one
  without either of them noticing.
- **`listen_addresses = 'localhost'`**, so the instance is not reachable from the network.
  Authentication is `trust`, meaning no password, and **that is only defensible because of that
  line**: nothing outside this machine can open a connection. Module 22 replaces it with users that
  mean something.

### Step 4. Hand it the rows

Here is the difference a file never charges for. The Parquet was already on disk: DuckDB reads it
where it lies. The server **does not have the data until you give it**, row by row, over a
connection.

### Step 5. Ask both the same question

And compare them by measuring, not by opining. The question is the project's: how many hours a day
the compressor spends loaded.

## The code, in parts

### Step 6. The three commands that set the server up

```consola
initdb  -D lake/pg -U fuelle --encoding=UTF8 --locale=C --auth=trust
pg_ctl  -D lake/pg -l lake/pg/servidor.log start
psql    -h localhost -p 5433 -U fuelle -d fuelle
```

```anota
initdb | creates the cluster folder. Only the first time
--locale=C | sorting and messages independent of the system language, so the result does not change from one machine to another
pg_ctl start | brings the server up. Without this, everything else says «connection refused»
psql | the command line client PostgreSQL ships with
```

None of the three asks for administrator, and when you are done no service is left installed: it
stops with `pg_ctl stop` and it is gone.

### Step 7. The table, deliberately naive

```postgres
SELECT count(*) AS filas, min(day) AS desde, max(day) AS hasta
FROM lecturas;
```

```anota
FROM lecturas | the table that has just received silver. Twenty columns, no key and no constraints
```

```salida
  filas  |   desde    |   hasta
---------+------------+------------
 1841760 | 2020-02-01 | 2020-09-01
(1 row)
```

No primary key, no `NOT NULL`, nothing at all. **This is not an oversight, it is module 20's
starting line.** Right now this database would accept two readings with the same timestamp, or a
pressure of minus a thousand bar, just as the Parquet did.

### Step 8. Give it the rows

```python
with pg.cursor() as cur, cur.copy(
        "COPY lecturas FROM STDIN WITH (FORMAT csv, HEADER)") as copia:
    with io.open(CSV, "rb") as fh:
        while bloque := fh.read(1 << 20):
            copia.write(bloque)
```

```anota
COPY ... FROM STDIN | bulk load over the connection. One INSERT per row would take hours
STDIN y no una ruta | reading a file from the server's disk requires the file to be on its machine and permission to read it. Over the connection it always works, including with the server somewhere else
fh.read(1 << 20) | it goes a megabyte at a time, so 190 MB never sit in memory
```

```salida
  1,841,760 filas, 190.0 MB de CSV
  1,841,760 filas en el servidor
```

The intermediate CSV weighs **190.0 MB** for data that takes 23.8 in Parquet. It is module 7 again:
text compresses badly, and here you pay for it twice, on disk and in what has to be pushed down the
connection.

### Step 9. The project's question, against the server

```postgres
SELECT day,
       count(*) AS lecturas,
       round((sum(CASE WHEN dv_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0)::numeric, 2) AS horas
FROM lecturas
WHERE medido
GROUP BY day
ORDER BY horas DESC
LIMIT 5;
```

```anota
::numeric | PostgreSQL is fussier about types than DuckDB: round with two decimals wants numeric, not a floating point number
el resto | identical to what you have been writing since module 10
```

```salida
    day     | lecturas | horas
------------+----------+-------
 2020-04-18 |     8588 | 23.60
 2020-06-06 |     7279 | 20.22
 2020-05-20 |     7398 | 20.02
 2020-03-29 |     7136 | 19.82
 2020-06-24 |     7162 | 15.91
(5 rows)
```

The same days and the same hours module 18 produced. **The SQL you learned works here**, which is
half the module solved: changing engine does not change the language.

## The result, measured

{{FIG:fig_m19_fichero_vs_servicio}}

**What we expected.** That a columnar engine like DuckDB would beat a row store hands down on an
analytical question. It is what module 7's theory says and it is what I took for granted.

**What came out.** That **they do not differ**. Their ranges over seven runs overlap, so by module
6's rule there is no difference to report. At 1.8 million rows both sweep the table and neither
breaks a sweat.

The exact medians are in the figure and not here on purpose: **they move from one run to the next**,
like anything measured in tenths of a second. What does not move is that the ranges overlap.

What does separate, and by a lot, is everything else:

| What | A file | A service |
|---|---|---|
| Having it ready | it already was | **about 20 s** of loading |
| On disk | 23.8 MB | **267.8 MB** |
| Starting it | nothing | a process kept up |
| Several at once | no | yes |
| Per user permissions | no | yes |

**Eleven times more disk.** **11.2** to be exact, for the very same readings. And the whole cluster
folder goes past the gigabyte, because besides the table it keeps the write ahead log that lets it
lose nothing when the power goes.

**What it means.** That the question "which is faster" was the wrong question. **A server does not
sell you speed: it sells concurrency, permissions and guarantees.** And they are paid for in disk,
in loading, and in having a process running.

For the work of this course so far, a file was the right choice and still is. What a file cannot do
is let three people in with different permissions. And that will be needed when module 30's
dashboard queries while the ingestion writes.

## Watch out

- **A stopped server is not a database.** It is the number one mistake with PostgreSQL: everything
  says "connection refused" and it is not the network, it is that nobody started it. That is why in
  this project a single file starts and stops it.
- **`trust` is only acceptable because it listens on localhost.** With no password and open to the
  network it would be giving the database away. The two decisions travel together or not at all.
- **Port 5432 is left free on purpose.** Occupying the standard one with a toy instance is the
  fastest way to break somebody's real one.
- **Load with `COPY`, never with `INSERT` row by row.** The difference between twenty seconds and
  an afternoon.
- **The intermediate CSV gets deleted.** It is 190 MB that contribute nothing once loaded, and
  leaving it there is the kind of litter that fills a disk with nobody knowing why.
- **This table promises nothing yet.** It would take a duplicate or an impossible pressure without
  blinking. Module 20 fixes that, and until then the server is no safer than the file.

## Metallurgical bridge

A small laboratory keeps its results in a spreadsheet. It works while there is one person.

As soon as the plant grows a LIMS arrives, meaning a database with its server behind it. And the
first thing everybody notices: **it does not analyse any faster**. The test takes what it takes.

What changes is something else. The night shift queries without calling anybody. The client sees
their own certificates and not somebody else's. Two technicians load results at once without
overwriting each other. And when somebody asks who changed a grade, there is an answer.

Nobody buys a LIMS for speed. It gets bought for the same reasons as a database server, and it
costs the same: more disk, more maintenance, and something switched on around the clock.

## Review

### What a database server gains over a file

Serving several clients at once, telling them apart and knowing what each may do, and guaranteeing
two simultaneous writes do not overwrite each other. It does not gain speed: here the same question
takes the same in both, with overlapping ranges.

### Why loading costs twenty seconds if the data was already on disk

Because it was on disk but not inside the server. A file gets read where it lies. A server has to
be handed every row over a connection, and it writes each one again in its own format and in its
write ahead log. Those twenty seconds are the price of delivery.

### What it means that the two measurements have overlapping ranges

That the difference between their medians cannot be defended. It is module 6's rule: if over seven
runs the worst case of one falls inside the other's range, what is being measured is the machine's
noise. Publishing a winner there would be inventing a result.

### Why the table is created with no primary key and no constraints

Because the module starts where the reader was: with a Parquet that accepted anything. Creating the
table already armoured would hide module 20's lesson, that a database protects against nothing
until you tell it what is impossible. It is module 4's criterion, which partitions by day knowing
full well it is the worst option.

### The server takes eleven times more for the same data. In exchange for what

For being able to recover. Much of that weight is the write ahead log, which notes every change
before applying it so a power cut does not leave the table half written. A Parquet offers nothing
like it: if the write is cut off, the file is broken and has to be redone.

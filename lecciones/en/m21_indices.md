---
module: 21
---

## In 30 seconds

- An index is an ordered copy of a column, so the whole table need not be read.
- Module 6's question, one specific day, goes from sweeping **1,841,760** rows to jumping.
- It runs **between 58.1 and 114.3 times** faster depending on the repetition, and that spread is the result.
- What is stable: the index takes **12.3 MB** and puts writing at **double**.
- The proof it works is not the stopwatch, it is **the plan** the database shows you.

## What this module solves

Module 6 asked a Parquet this same question: give me one day. There the answer was how to spread
the files on disk, and the conclusion was a surprise, because splitting by day was the worst
option.

Here the question is the same and the tool is different. A database does not spread files: it
builds **indexes**, a separate structure whose only job is finding things quickly.

And like everything you add, you have to know what it costs. An index is not free and this module
measures it from both sides.

## Before the theory: a toy example

A filing cabinet with the cards of a thousand batches, filed in arrival order. You are asked for the
ones from 5 June.

There is nothing for it but to **look at them all**, because the date could be anywhere. A thousand
cards, one by one. That is a sequential scan.

Now somebody sets up a card index beside it with the dates in order, and each card says which
drawer its record is in:

| date | drawer |
|---|---|
| 4 June | 812 |
| 5 June | 813 |
| 5 June | 814 |
| 6 June | 815 |

Now the answer is: go to the card index, which is ordered, and with two jumps land on the 5 June
cards. **From a thousand looks to a handful.**

The card index is the index. And it brings three bills nobody mentions when selling it:

1. **It takes room.** It is a copy of the date column.
2. **It has to be maintained.** Every new record forces writing its card too, in its place.
3. **It only helps with what it orders.** Ordered by date, it is no help searching by batch number.

## Glossary

- **Index.** An ordered structure, separate from the table, saying where each value lives.
- **Sequential scan.** Reading the whole table. `Seq Scan`, and it is what the database does when
  it has nothing better.
- **Index scan.** Using the index to go straight there. `Index Scan`.
- **Execution plan.** What the database has decided to do with your query. Asked for with
  `EXPLAIN`.
- **Selectivity.** What proportion of the table a filter returns. An index helps when it is low.
- **`ANALYZE`.** Refreshes the statistics the planner uses to decide.

## Step by step

### Step 1. Ask without an index, and look at the plan

Before touching anything, see what the database does. `EXPLAIN` describes its plan without running
it, and there is the phrase that matters: `Seq Scan`, meaning it is going to read the whole table.

### Step 2. Measure, with the usual rule

Median of seven runs and its range, like module 6 and module 18. And `distinguishable()` deciding
whether there is a difference to report.

### Step 3. Create the index and look at the plan again

The plan first, the stopwatch second. **The plan goes from `Seq Scan` to `Index Scan`, and there is
the proof the index is being used.** It does not depend on how busy the machine is.

### Step 4. `ANALYZE`, or the index may sit there watching

The planner decides with statistics. If they are stale it may keep preferring the full scan even
though the index exists, and then the measurement would be comparing the same thing twice.

### Step 5. Measure what it costs

An index charges in disk and in every write. It gets measured by writing **200,000 rows** into a
throwaway table, with the index and without.

It is done on a separate table on purpose: measuring writes against the good one would leave it
with extra rows afterwards.

## The code, in parts

### Step 6. The plan without an index

```postgres
SELECT count(*) AS lecturas,
       round(avg(oil_temperature)::numeric, 2) AS aceite
FROM lecturas
WHERE day = DATE '2020-06-05';
```

```anota
WHERE day = ... | the filter. Of 1,841,760 rows, this day has 8,640
la pregunta | it is module 6's, on purpose: there it was solved by spreading files and here with an index
```

```salida
 lecturas | aceite
----------+--------
     8640 |  70.57
(1 row)
```

And this is what the database says it will do to answer it:

```salida
Finalize Aggregate
  ->  Gather
        Workers Planned: 2
        ->  Partial Aggregate
              ->  Parallel Seq Scan on lecturas
                    Filter: (day = '2020-06-05'::date)
```

**`Seq Scan`**: sequential scan. It will read all 1,841,760 rows and keep the 8,640 that match. And
it is already using two parallel workers, which is the database doing what it can with a bad hand.

### Step 7. The index, and the plan again

```postgres
SELECT count(*) AS indices
FROM pg_indexes
WHERE tablename = 'lecturas';
```

```anota
pg_indexes | another catalogue view, like module 20's pg_constraint
```

```salida
 indices
---------
       2
(1 row)
```

Two: the primary key's, which PostgreSQL created by itself in module 20, and ours on `day`. With
it, the plan for the same query is another:

```salida
Aggregate
  ->  Index Scan using lecturas_por_dia on lecturas
        Index Cond: (day = '2020-06-05'::date)
```

The full scan is gone and so are the parallel workers: **there is no longer any work to share out**.

### Step 8. And what it costs

```python
escritura_sin = measure(escribe, setup=vacia_sin_indice)
escritura_con = measure(escribe, setup=vacia_con_indice)
peaje = times_slower(escritura_con, escritura_sin)
```

```anota
setup= | prepares the table before each repetition, and that work is NOT timed
las dos medidas | the same write, with the only difference being whether there is an index to maintain
times_slower | it only returns a factor when the ranges do not overlap
```

```salida
  lo que cuesta mantenerlo, escribiendo:
    sin índice  0.494 s
    con índice  1.208 s
    2.45 veces más lento
```

## The result, measured

{{FIG:fig_m21_indice_antes_despues}}

**What we expected.** A clean factor to publish, along the lines of "the index makes the query N
times faster".

**What came out.** That the factor **does not exist**. The pair of measurements was repeated four
times inside the same run and gave **107.5**, **114.3**, **58.1** and **82.9** times. The index
wins every time and by an enormous margin, but the actual number is half noise.

Module 7 already wrote down the reason: **the faster a measurement, the less its factor can be
trusted**. With the indexed read at three thousandths of a second, anything the machine does takes
half the result with it.

So the spread gets published, **between 58.1 and 114.3 times**. And separately, what is firm:

| What | Without an index | With an index |
|---|---|---|
| The plan | `Parallel Seq Scan` | `Index Scan` |
| Reading one day | 0.2925 s | 0.0027 s |
| Writing 200,000 rows | 0.494 s | 1.208 s |
| On disk | nothing | **12.3 MB** |

**The plan is the real proof.** It does not move between runs, it does not depend on whether the
antivirus is looking, and it says explicitly that the database has stopped sweeping the table. When
somebody asks whether an index is being used, the answer is `EXPLAIN`, not a stopwatch.

**And the bill.** Writing goes to double, **2.45 times** in this run, and the index takes 12.3 MB,
which is half of what the entire silver layer takes in Parquet. For a table read a lot and written
once a day, the trade is obvious. For one taking writes all the time, it needs thinking about.

## Watch out

- **An index nobody uses is all cost.** It takes room and slows writes while giving nothing.
  `EXPLAIN` is the only way to know whether yours is used.
- **It does not serve every filter.** If the query returns half the table, the database ignores the
  index on purpose, and rightly: jumping about costs more than reading straight through.
- **Order matters.** An index on `(day, tp2)` serves filtering by `day`, and also by `day` and
  `tp2` together. For filtering by `tp2` alone, no.
- **After a big load, `ANALYZE`.** Without fresh statistics the planner decides blind and can
  ignore a perfectly good index.
- **Do not measure an index once.** Here the same experiment gave 58.1 and 114.3 in the same run.
  Publishing the first would have been inventing a datum.
- **A primary key already brings an index.** PostgreSQL creates it by itself, so module 20 left one
  in place without saying so. Counting indexes before creating another avoids duplicating it.

## Metallurgical bridge

The core sample store is a table with no index. Boxes stacked in arrival order, and finding a
particular interval means walking the aisle reading labels.

The register book is the index: hole, depth, and shelf number. With it you go straight there, and
that is why every serious store has one.

And it has the same three bills. It takes a cupboard. **It gets updated with every box that comes
in**, and if somebody stops doing it for a month the book lies and is worse than not having one.
And it is ordered by hole: for the question "which intervals did such and such a laboratory assay"
it is no use at all, and you walk the aisle anyway.

## Review

### What an index is and why it speeds a query up

An ordered structure, separate from the table, saying where each value of a column lives. Without
it the database has to read the whole table to know which rows match a filter. With it, it jumps
straight to the matching ones, and here that is the difference between looking at 1,841,760 rows
and looking at 8,640.

### How you check an index is being used

With `EXPLAIN`, which shows the plan without running the query. If it says `Seq Scan`, the database
is still sweeping the table. If it says `Index Scan`, it is using it. It is better proof than the
clock because it does not depend on how busy the machine is.

### Why this module does not publish a speedup factor

Because it is not reproducible. The same pair of measurements gave 107.5, 114.3, 58.1 and 82.9
times over four repetitions. With the fast read in thousandths of a second, the factor is largely
clock noise. The honest thing is to publish the spread and lean on the plan, which does not move.

### What an index charges

Disk and writes. This one takes 12.3 MB and doubles the time to insert 200,000 rows, because every
new row forces placing its index entry too. On a table of heavy reads and light writes it pays for
itself. On one written continuously, it has to be measured.

### You have a slow query. You create an index and nothing improves. What is going on

Three suspects, and `EXPLAIN` rules them out. The filter returning too much of the table, in which
case the database prefers the full scan on purpose. Stale statistics, needing `ANALYZE`. Or the
index being on another column, or in an order that does not serve that filter.

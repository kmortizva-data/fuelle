---
module: 12
---

## In 30 seconds

- A `JOIN` puts two tables together by something they share.
- The good join **does not change the row count**: 1,516,948 readings stay 1,516,948.
- The bad one multiplies without warning: the 4 failure reports become **6 rows**.
- A real erratum is to blame: **two reports are numbered `#1`**.
- Joined properly, **54,354 readings** fall inside a documented failure, 3.58 %.

## What this module solves

The telemetry says what the compressor was doing. The failure reports say when it was broken.
Separately they answer nothing interesting; together they are the material for the rest of the
project.

Putting them together is a `JOIN`, and it is the operation most people get wrong without
noticing, because when it goes wrong it throws no error: it gives extra rows.

## Before the theory: a toy example

Two tables from a day in the plant. The shifts, with what each one processed:

| shift | tonnes |
|---|---|
| T1 | 100 |
| T2 | 200 |

And the incidents recorded:

| shift | incident |
|---|---|
| T1 | mill stoppage |
| T1 | belt jam |
| T2 | pump vibration |

**How much was processed that day.** You add the first table: 100 plus 200, **300 tonnes**. That
is the correct answer and you know it before touching anything.

Now join them by shift, so you can look at tonnes and incidents together:

| shift | tonnes | incident |
|---|---|---|
| T1 | 100 | mill stoppage |
| T1 | 100 | belt jam |
| T2 | 200 | pump vibration |

And add that table's tonnes again: 100 plus 100 plus 200, **400**.

A hundred tonnes out of nowhere. And notice the table is not wrong: every row is true. What is
wrong is summing a column that now repeats.

It happened because **T1 had two incidents**, so its shift row got copied twice to pair with each
one. The shift did not change grain; the table did.

That is the module's whole trap: **joining on something that is not unique multiplies rows**, and
afterwards everything summed or counted is inflated.

## Glossary

- **`JOIN`.** Putting two tables together by pairing rows that meet a condition.
- **Key.** The column, or group of columns, that identifies a row without repeating. If it
  repeats, it is not a key.
- **`INNER JOIN`.** Keeps only the rows that find a partner. The rest disappear.
- **`LEFT JOIN`.** Keeps **all** of the left ones, with a partner or without. Those that find none
  come out with NULL in the right hand columns.
- **`CROSS JOIN`.** Pairs each row with every row of the other table. It is the join without a
  condition and it grows very fast.
- **Grain.** What one row corresponds to, from module 2. A `JOIN` can change it without warning,
  and that is where the trouble starts.

## Step by step

### Step 1. Look at the small table before joining anything

Four rows. They read in ten seconds and save hours, because almost everything that can go wrong
with this join is visible in them.

### Step 2. Convert the dates, which arrive as text

The reports carry `4/18/2020 0:00` written as text. Comparing text with dates does not work, or
worse, works badly. It has to be converted first, and that is what module 9 said.

### Step 3. Choose the join condition

There is no shared column between the two tables here: the telemetry has a day and the report has
an interval. So the condition is not an equality, it is a membership.

### Step 4. Count before and count after

And this is the habit to pick up. Before joining you count the rows, afterwards you count them
again, and if the number moved without meaning to, the join is wrong.

## The code, in parts

### Step 5. The small table, whole

```sql-vivo
SELECT nr, start_time, end_time, failure, report
FROM averias;
```

```anota
FROM averias | the other table your browser brought: the four failure reports
```

```salida
┌─────────┬─────────────────┬─────────────────┬──────────┬───────────────────────────────┐
│   nr    │   start_time    │    end_time     │ failure  │            report             │
├─────────┼─────────────────┼─────────────────┼──────────┼───────────────────────────────┤
│ #1      │ 4/18/2020 0:00  │ 4/18/2020 23:59 │ Air leak │ NULL                          │
│ #1      │ 5/29/2020 23:30 │ 5/30/2020 6:00  │ Air Leak │ Maintenance on 30Apr at 12:00 │
│ #3      │ 6/5/2020 10:00  │ 6/7/2020 14:30  │ Air Leak │ Maintenance on 8Jun at 16:00  │
│ #4      │ 7/15/2020 14:30 │ 7/15/2020 19:00 │ Air Leak │ Maintenance on 16Jul at 00:00 │
└─────────┴─────────────────┴─────────────────┴──────────┴───────────────────────────────┘
```

Four rows and three things to note, all true and none corrected:

**There are two reports numbered `#1` and no `#2` at all.** That number looks like an identifier
and it is not.

**`Air leak` and `Air Leak`.** The same failure written two ways. Grouping by that column would
give two groups where there is one.

**The 29 May report says the maintenance was on 30 April**, a month before the failure itself. It
is an erratum of the original and it stays as it is.

### Step 6. Join properly, and check the count

```sql-vivo
SELECT count(*) AS filas,
       count(a.nr) AS dentro_de_una_averia
FROM telemetria t
LEFT JOIN (
    SELECT nr,
           CAST(strptime(start_time, '%-m/%-d/%Y %-H:%M') AS DATE) AS desde,
           CAST(strptime(end_time,   '%-m/%-d/%Y %-H:%M') AS DATE) AS hasta
    FROM averias
) a ON t.day BETWEEN a.desde AND a.hasta;
```

```anota
LEFT JOIN | keeps every reading, whether it finds a failure or not
strptime(texto, formato) | converts text to a date by saying what format it is written in
%-m/%-d/%Y %-H:%M | that format: month, day, year and time, with no leading zeros
ON t.day BETWEEN a.desde AND a.hasta | the join condition; not an equality, but falling inside the interval
count(a.nr) | counts only the rows where that column is NOT NULL, that is the ones that found a failure
```

```salida
┌─────────┬──────────────────────┐
│  filas  │ dentro_de_una_averia │
├─────────┼──────────────────────┤
│ 1516948 │                54354 │
└─────────┴──────────────────────┘
```

The rows are still 1,516,948, exactly the ones there were before joining. That number is the
proof the join invented nothing.

And notice the difference between the two columns: `count(*)` counts rows and `count(a.nr)`
counts the ones with a value. It is module 8 again, now with a practical use.

### Step 7. The join that multiplies

```sql
SELECT count(*) AS filas
FROM averias a
JOIN averias b ON a.nr = b.nr;
```

```anota
JOIN | without the word LEFT in front, it is an INNER JOIN: only the rows with a partner
a.nr = b.nr | joining by the report number, which looks like it identifies a failure
a, b | two short names for the same table, because it is joined to itself
```

```salida
┌───────┐
│ filas │
├───────┤
│     6 │
└───────┘
```

Six rows from a table of four. Each `#1` report finds two partners, its own and the other `#1`'s,
so those two rows turn into four.

No error, no warning. Just two extra rows.

## The result, measured

{{FIG:fig_m12_tipos_de_join}}

**What we expected.** That joining the telemetry with the reports would mark the failed readings
without touching the row count.

**What came out.** That, with the `LEFT JOIN`: **1,516,948 rows before and 1,516,948 after**, and
**54,354** of them inside a documented failure, **3.58 %** of the record.

The figure shows the three ways of writing the same join. The `INNER JOIN` returns **54,354**,
which are only the readings with a failure. The `CROSS JOIN`, which carries no condition, returns
**6,067,792**: each reading paired with each of the four reports.

Split by failure, the four come out like this:

| Report | From | To | Readings | Loaded hours |
|---|---|---|---|---|
| #1 | 2020-04-18 | 2020-04-18 | 8,663 | 23.8 |
| #1 | 2020-05-29 | 2020-05-30 | 16,083 | 11.3 |
| #3 | 2020-06-05 | 2020-06-07 | 20,947 | 49.4 |
| #4 | 2020-07-15 | 2020-07-15 | 8,661 | 11.6 |

{{FIG:fig_m12_join_que_multiplica}}

**And the join that lies.** Joining the four reports by their number goes **from 4 rows to 6**. In
the figure you can see why: the two thick lines are the two `#1` reports, and each one pairs with
both.

Joining by the pair that does identify a report, the number and the start time, gives **4**,
which is correct.

**What it means.** The erratum module 1 recorded and left uncorrected has turned into a real
fault here. It is not a laboratory example: it is the project's only source of truth, with a
numbering that does not number.

And out of that comes the habit to take away: **count the rows before and after joining**. It is
not paranoia, it is the only way to find out, because a join that multiplies throws no error.

## Watch out

- **A `JOIN` can change the table's grain.** If the right hand one has several rows for each of
  the left's, the left gets copied. Afterwards, any sum is inflated.
- **Count before and count after.** It is the cheapest check there is and it catches almost every
  badly made join.
- **A column named like an identifier is not thereby a key.** Here `nr` has two rows with the same
  value. It gets checked with a `GROUP BY nr HAVING count(*) > 1`.
- **`INNER JOIN` deletes rows in silence.** The readings without a failure, which are 96 %, would
  disappear without a word. When you want to keep them all, `LEFT JOIN`.
- **The report dates are text.** Comparing text with dates can work by chance and fail the moment
  the format changes. You convert first, always.
- **`Air leak` and `Air Leak` are different groups** for a `GROUP BY`. The original data does not
  get touched, so the normalisation happens at query time, not on ingestion.

## Metallurgical bridge

In a plant balance there are two records crossed daily: the trucks tipping into the hopper and
the laboratory assays. They get crossed by lot number.

The day a lot is sampled twice, because the first assay came out odd, that number stops
identifying a row. Joining by it, that lot's truck appears twice, and its tonnage gets counted
twice in the month's balance.

Nobody notices by looking at the result, because the balance still closes. The person who notices
is whoever compares the joined tonnage with the weighbridge tonnage, which is exactly counting
before and after.

## Do it yourself

```reto
pregunta: Mark each failure with how many compressor readings fall inside it. Return three columns, `nr`, `desde` and `lecturas`, one row per report. Four rows, ordered by date.
inicio: SELECT count(*) AS filas,
       count(a.nr) AS dentro_de_una_averia
FROM telemetria t
LEFT JOIN (
    SELECT nr,
           CAST(strptime(start_time, '%-m/%-d/%Y %-H:%M') AS DATE) AS desde,
           CAST(strptime(end_time,   '%-m/%-d/%Y %-H:%M') AS DATE) AS hasta
    FROM averias
) a ON t.day BETWEEN a.desde AND a.hasta;
esperado: m12_lecturas_por_averia
pista: The starting point's join is already the right one, but it faces the wrong way for what the challenge asks: the reports have to go on the left and the telemetry on the right, so that one row comes out per report. After that it is a `GROUP BY` on `a.nr` and `a.desde`, counting with `count(t.day)`, which does not count the absent readings.
solucion: SELECT a.nr, a.desde, count(t.day) AS lecturas
FROM (
    SELECT nr,
           CAST(strptime(start_time, '%-m/%-d/%Y %-H:%M') AS DATE) AS desde,
           CAST(strptime(end_time,   '%-m/%-d/%Y %-H:%M') AS DATE) AS hasta
    FROM averias
) a
LEFT JOIN telemetria t ON t.day BETWEEN a.desde AND a.hasta
GROUP BY a.nr, a.desde
ORDER BY a.desde;
```

## Review

### The difference between INNER JOIN and LEFT JOIN

The `INNER` keeps only the rows that find a partner, and the rest disappear without a word. The
`LEFT` keeps all of the left hand ones and fills the right hand columns with NULL when there is
no partner. Here the difference is enormous: 54,354 rows against 1,516,948.

### How do you know a join went wrong

By counting rows before and after. If the left table had 1,516,948 and after the join there are
more, some row got duplicated by having several partners. It is the cheapest check there is and
almost nobody does it, because a badly made join throws no error.

### Why can you not join by the report number

Because two of the four reports are `#1`. That number looks like an identifier, and joining by it
each `#1` pairs with both, so four rows come out six. The real key here is the pair of number and
start time, which does identify a row.

### The reports carry errata. Why not correct them before joining

Because they are the project's only source of truth and they are not mine. Correcting the
numbering would be inventing a datum nobody measured. The course's rule is that the raw stays
literal, and the corrections happen at query time, where they stay visible and can be revised.

### You sum tonnes after joining with an incidents table. What do you check

That the join has not changed the grain. If a shift has two incidents, its row gets copied twice
and its tonnage counted twice. You check by counting rows before and after, or by summing before
joining and comparing with the sum afterwards.

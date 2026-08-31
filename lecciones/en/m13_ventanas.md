---
module: 13
---

## In 30 seconds

- Grouping joins rows. A **window function** leaves them loose and shows each one its neighbour.
- The gap between two readings **is not a column**: it exists only as a difference between rows.
- The lake holds **179,426** gaps that do not respect the ten seconds, 11.8 %.
- The largest lasts **48 hours**, from 25 to 27 April, and explains a day that was missing.
- A start is not a datum either: it is a row saying loaded behind one that did not.

## What this module solves

Everything so far crushed rows. `GROUP BY` takes a thousand readings and returns one. It serves
to summarise, and for that very reason it serves nothing that depends on order.

This module does the opposite: it keeps every row and shows each one its neighbours. Without that
there are no time series, and without time series there is no twin.

## Before the theory: a toy example

Six readings from a morning, with the compressor's state:

| time | load |
|---|---|
| 08:00 | 0 |
| 08:10 | 0 |
| 08:20 | 1 |
| 08:30 | 1 |
| 08:40 | 0 |
| 09:00 | 0 |

**Question one: how much time passed between each reading and the previous one?**

Look at the table and subtract: 10, 10, 10, 10 and **20 minutes**. The last is twice the others,
and a reading is missing there.

Notice something. That 20 **is written nowhere in the table**. It is not a column, it is not any
row's value. It is born from subtracting two rows, and that is why until now it could not be
asked for.

**Question two: how many times did the compressor start?**

You look for where the load goes from 0 to 1. It happens once, at 08:20. **One start.**

And again the same: looking at one row alone you cannot tell whether it is a start. The 08:20 one
says 1, just like the 08:30 one, and yet only one of the two is a start. The difference is in what
the previous one said.

That is a window function: **each row can look at its neighbours without ceasing to be a row.**

## Glossary

- **Window function.** A function that computes something for each row by looking at a set of rows
  around it, without grouping them.
- **`OVER`.** The word that turns a normal function into a window function. It defines which rows
  each one sees.
- **`lag(column)`.** That column's value in the previous row. If there is no previous, NULL.
- **`lead(column)`.** The same with the following row.
- **`ORDER BY` inside `OVER`.** What "previous" means. Without it there is no previous, because
  there is no order.
- **`PARTITION BY`.** Restarts the window in each group. With `PARTITION BY day`, each day's first
  reading has no previous.
- **Gap.** The seconds between a reading and the previous one. In this file they should be ten.

## Step by step

### Step 1. Look at the previous row

`lag()` brings the value from the row above. With that, each row gets two versions of the same
column: its own and the previous one, on the same row and side by side.

From there, subtracting or comparing them is ordinary SQL.

### Step 2. Say what "previous" means

And this is not optional. The previous row exists only if there is an order, so `OVER` always
carries an `ORDER BY` inside. Here it is the timestamp.

It is module 8's warning again, now with worse consequences: there a missing order gave different
rows, and here it would give invented gaps.

### Step 3. Measure the gap

Subtract the previous row's timestamp from your own. Where ten comes out, all normal. Where
something else comes out, something is missing or the clock moved.

### Step 4. Count starts

A start is a row with load one whose previous had load zero. You filter by that pair of
conditions and count.

## The code, in parts

### Step 5. The previous row, beside your own

```sql-vivo
SELECT timestamp,
       DV_eletric,
       lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
FROM telemetria
WHERE day = DATE '2020-06-05'
ORDER BY timestamp
LIMIT 5;
```

```anota
lag(DV_eletric) | the value that column had in the row above
OVER (...) | turns lag into a window function; the window's definition goes inside
ORDER BY timestamp | what "the row above" means: the previous one in time
AS antes | the new column's name, so it can be compared with the row's own
```

```salida
┌─────────────────────┬────────────┬────────┐
│      timestamp      │ DV_eletric │ antes  │
│      timestamp      │   double   │ double │
├─────────────────────┼────────────┼────────┤
│ 2020-06-05 00:00:02 │        0.0 │   NULL │
│ 2020-06-05 00:00:12 │        0.0 │    0.0 │
│ 2020-06-05 00:00:22 │        0.0 │    0.0 │
│ 2020-06-05 00:00:32 │        0.0 │    0.0 │
│ 2020-06-05 00:00:42 │        0.0 │    0.0 │
└─────────────────────┴────────────┴────────┘
```

The first row has NULL in `antes`, and that is correct: there is no previous row. It is module 8's
emptiness turning up where it should.

And notice the seconds, which run in tens starting from 02. The day does not begin on the hour.
The compressor has been measuring since before, so those are the readings it happened to take and
not a clock set to zero.

### Step 6. The gap between readings

```sql-vivo
SELECT hueco, count(*) AS veces
FROM (
    SELECT date_diff('second',
                     lag(timestamp) OVER (ORDER BY timestamp),
                     timestamp) AS hueco
    FROM telemetria
    WHERE day = DATE '2020-06-05'
)
WHERE hueco IS NOT NULL
GROUP BY hueco
ORDER BY veces DESC;
```

```anota
date_diff('second', a, b) | how many seconds lie between two timestamps
WHERE hueco IS NOT NULL | drops the first row, the one with no previous
```

```salida
┌───────┬───────┐
│ hueco │ veces │
├───────┼───────┤
│    10 │  7953 │
│     9 │   762 │
└───────┴───────┘
```

That day the sampling has two rhythms: 7,953 times of ten seconds and 762 of nine. The datasheet
promised ten always.

And notice the query's shape: the window gets computed inside and the `GROUP BY` goes outside.
You cannot group by something still being computed, so two steps are needed. It is module 11
again.

### Step 7. The starts

```sql-vivo
SELECT count(*) AS arranques
FROM (
    SELECT DV_eletric,
           lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
    FROM telemetria
    WHERE day = DATE '2020-06-05'
)
WHERE antes = 0 AND DV_eletric = 1;
```

```anota
WHERE antes = 0 AND DV_eletric = 1 | the definition of a start: it was not loading before and now it is
```

```salida
┌───────────┐
│ arranques │
├───────────┤
│        31 │
└───────────┘
```

Thirty one starts that day. Keep that number, because the module's result depends on comparing it
with something.

## The result, measured

{{FIG:fig_m13_lag_y_hueco}}

**What we expected.** More starts than usual on a failure day, because the compressor has to
replace the air escaping.

**What came out.** The opposite. On 5 June, the first day of failure **#3**, the compressor
started **31 times**. The median across the 208 days with starts is **58**, and the maximum is
**1,257** starts on 23 June.

So a failure day has **half the starts** of a normal one.

**What it means.** And here is the good part, because that same day the compressor spent **15.41
hours loaded**, against 3.42 on an ordinary day. It started less and worked four times more.

They do not contradict each other: **they explain each other**. With a large leak, the compressor
never gets to stop. Instead of starting and stopping sixty times, it starts thirty and stays in.
Counting starts without looking at how long they last would have given exactly the opposite
conclusion to the true one.

It is module 5's trap with means, in another place: **the number that is easiest to count is not
always the one telling the truth.**

**And the module's figure.** In the whole lake there are **179,426** gaps that are not ten
seconds, **11.8 %**. The largest measures **48 hours**, from **25 to 27 April**. That explains the
26 April missing in module 8: it is not one absent row, it is two consecutive days.

## Watch out

- **Without `ORDER BY` inside `OVER` there is no previous row.** The result comes out anyway, and
  it is anything. It is module 8's worst case: there the order changed, here the datum changes.
- **The first row always has NULL.** There is no previous. Filtering it with `IS NOT NULL` is part
  of the query, not a patch.
- **`PARTITION BY day` changes the result, and sometimes that is right.** Without it, a day's last
  reading gets compared with the next day's first, and that gap crosses midnight.
- **The window gets computed before it can be grouped.** That is why these queries come in two
  steps, with the window inside and the `GROUP BY` outside.
- **Counting events is not enough.** Thirty one starts look like fewer than fifty eight until you
  look at how long each one lasts. An event without its duration is half a measurement.
- **This lesson runs over one single day.** The sample your browser downloads is 5 June's, because
  carrying the exact clock for the whole lake would cost 5.16 MB, and module 7 measured why. That
  is why every query carries its `WHERE day = DATE '2020-06-05'`.

## Metallurgical bridge

In a SAG mill, the datum that really matters is not the instantaneous power: it is how it
changes. A sustained rise over twenty minutes means the charge is growing, and that shows by
comparing each reading with one from a while back, not by looking at the number now.

That is why control rooms do not show figures: they show trends. An experienced operator does not
tell you how many kilowatts it reads, they tell you it is going up.

`lag()` is that backward glance written in SQL. And the module's warning holds equally in the
control room: counting how many times an alarm went off says far less than counting how long it
stayed off.

## Do it yourself

```reto
pregunta: Count how many times the compressor **stopped** that day, that is the rows where the load goes from 1 to 0. Return one single column called `paradas`.
inicio: SELECT count(*) AS arranques
FROM (
    SELECT DV_eletric,
           lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
    FROM telemetria
    WHERE day = DATE '2020-06-05'
)
WHERE antes = 0 AND DV_eletric = 1;
esperado: m13_paradas_del_dia
pista: It is step 7's state change, the other way round. Where the start asks that before was 0 and now 1, the stop asks that before was 1 and now 0. You only have to flip the two conditions of the `WHERE` and change the column's name.
solucion: SELECT count(*) AS paradas
FROM (
    SELECT DV_eletric,
           lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
    FROM telemetria
    WHERE day = DATE '2020-06-05'
)
WHERE antes = 1 AND DV_eletric = 0;
```

## Review

### The difference between GROUP BY and a window function

`GROUP BY` crushes: it takes many rows and returns one per group. A window function keeps every
row and adds to each one a calculation made by looking at its neighbours. You use one or the
other depending on whether the answer has one row per group or one row per reading.

### Why the gap between readings cannot be got with what came before

Because it is in no row. It is the difference between two, and until now every tool in the course
looked at one row at a time or a whole group at once. `lag()` is the first thing that puts two
rows within reach of the same expression.

### What happens if you forget the ORDER BY inside the OVER

The query works and the result means nothing. "The previous row" stops being defined, so the
engine returns some row, and the gaps that come out will be invented. It is worse than an error,
because an error can be seen.

### A failure day had fewer starts than a normal one. How do you explain that

Because with a large leak the compressor never gets to stop. That day it started 31 times against
a median of 58, and at the same time spent 15.41 hours loaded against 3.42. It started half as
often and worked four times more, because each start lasted very much longer. Counting events
without measuring their duration leads straight to the opposite conclusion.

### What use is all this to the digital twin

Being able to compare. A twin predicts what should be happening now, and "now" only makes sense
with the previous instant beside it. The gaps have to be known so that two readings 48 hours
apart do not get treated as consecutive, and the start cycle is the signal where this project
expects to see the leak.

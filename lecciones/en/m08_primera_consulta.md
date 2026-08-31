---
module: 8
---

## In 30 seconds

- A query has five pieces and they always come in the same order.
- `SELECT` picks columns, `WHERE` picks rows. Not the same thing, and easily confused.
- The low pressure alarm fired in **5,188 readings**, on 95 of the 212 days.
- The period holds **214 days** of calendar and the record only **212**.
- And those two missing days teach what no definition teaches: **empty is not zero**.

## What this module solves

Here you write your first whole query, and you write it against the real compressor.

There are five pieces and they need no memorising: you understand them by watching what each one
does. What does need understanding first time is the difference between having no value and
having the value zero. Confusing them gives results that look correct.

## Before the theory: a toy example

A shift leaves six readings of the receiver, with its pressure and whether the alarm sounded:

| time | pressure | alarm |
|---|---|---|
| 06:00 | 9 | 0 |
| 06:10 | 8 | 0 |
| 06:20 | 7 | 1 |
| 06:30 | 6 | 1 |
| 06:40 | 8 | 0 |
| 06:50 | 9 | 0 |

Now, without SQL, answer three questions by looking at the table:

**Show me only the time and the pressure.** You cover the third column. Still six rows, just
narrower. **That is `SELECT`: it picks columns.**

**Show me only when the alarm sounded.** You cross out four rows and two are left, 06:20 and
06:30. Still three columns, just fewer rows. **That is `WHERE`: it picks rows.**

**Lowest pressure first, and only the worst one.** You order and keep the first: 06:30, at 6 bar.
**Those are `ORDER BY` and `LIMIT`.**

Picking columns and picking rows are different things done with different words. That is ninety
per cent of the confusion of anyone starting out.

And now the fourth question, which is this module's. **What was the mean pressure at 07:00?**

It is not zero. There is no 07:00 reading. Nobody measured, so there is nothing to average, and
the correct answer is "unknown". If your system answers zero, it is lying to you with apparent
confidence.

## Glossary

- **Query.** A question written in SQL. It reads almost like an English sentence.
- **Clause.** Each of a query's pieces. There are five and all of them appear here.
- **`SELECT`.** Picks which **columns** come out in the result.
- **`FROM`.** Says which table they come from.
- **`WHERE`.** Picks which **rows** pass the filter. The rest never reach the result.
- **`ORDER BY`.** Orders the result. Without it, the order is not guaranteed.
- **`LIMIT`.** Cuts and leaves only the first rows.
- **NULL.** The absence of a value. Not zero, not an empty string, and not equal to anything, not
  even to another NULL.
- **Alias.** The name you give a result column, with `AS`.

## Step by step

### Step 1. The five pieces, and the order they are written in

A query is always written in the same order, and that order is not negotiable. Putting the
`WHERE` before the `FROM` is not ugly: it does not work.

### Step 2. Ask about the low pressure alarm

The dataset's datasheet says `LPS` activates below 7 bar. It is the closest thing to an alarm in
the file, so it is a good place for a first filter.

### Step 3. Order and cut, so as not to read five thousand rows

Filtering by the alarm leaves thousands of readings, which fit on no screen and serve nothing in
a row. Ordered by pressure and cut to five, the answer fits at a glance.

### Step 4. Ask about a day that does not exist

The record runs from 1 February to 1 September. That is 214 calendar days, and the file only has
212. Two are missing, and asking the system about one of them is the best way to understand what
NULL is.

## The code, in parts

### Step 5. The anatomy of a query

```diagrama
SELECT | qué columnas | y con qué nombre
FROM | de qué tabla | aquí, telemetria
WHERE | qué filas pasan | el filtro
ORDER BY | en qué orden | salen
LIMIT | cuántas | quiero ver
```

It is always written in that order. And a warning that saves grief: **it is not the order it gets
executed in**. The database applies the `FROM` first, then the `WHERE`, and the `SELECT` almost
last. Module 10 comes back to this when it starts to matter.

### Step 6. Your first whole query

```sql-vivo
SELECT day, TP2, LPS
FROM telemetria
WHERE LPS = 1
ORDER BY TP2 DESC
LIMIT 5;
```

```anota
SELECT day, TP2, LPS | asks for three columns in that order; what is not named does not come out
FROM telemetria | from the compressor's table, the one your browser brought
WHERE LPS = 1 | only the rows where the alarm was active; the rest get discarded
= | comparing, not assigning: in SQL a single equals is already a comparison
ORDER BY TP2 DESC | orders by pressure from high to low; DESC is descending
LIMIT 5 | and of all those, show me only the first five
; | closes the query
```

```salida
┌────────────┬────────┬────────┐
│    day     │  TP2   │  LPS   │
│    date    │ double │ double │
├────────────┼────────┼────────┤
│ 2020-07-17 │  8.132 │    1.0 │
│ 2020-07-25 │  8.124 │    1.0 │
│ 2020-07-08 │  8.108 │    1.0 │
│ 2020-07-12 │  8.106 │    1.0 │
│ 2020-07-15 │  8.104 │    1.0 │
└────────────┴────────┴────────┘
```

Try it. Remove the `WHERE` and rows where `LPS` is zero will arrive. Change the `LIMIT` to 20.
Replace `DESC` with nothing and the lowest pressures come out.

Look at the dates: four of the five are July, and one is the 15th, which is the date of the
fourth failure.

### Step 7. Where the alarm fires most

```sql
SELECT day, count(*) AS lecturas
FROM telemetria
WHERE LPS = 1
GROUP BY day
ORDER BY lecturas DESC
LIMIT 5;
```

```anota
count(*) AS lecturas | counts each group's rows and calls the result "lecturas"
GROUP BY day | joins every row of the same day into one; module 10 is entirely about this
DESC | high to low; without that word it orders low to high
```

```salida
┌────────────┬──────────┐
│    day     │ lecturas │
├────────────┼──────────┤
│ 2020-07-15 │      534 │
│ 2020-07-17 │      414 │
│ 2020-06-08 │      312 │
│ 2020-05-19 │      272 │
│ 2020-07-31 │      247 │
└────────────┴──────────┘
```

The first on the list, 15 July, is the date of the fourth documented failure.

### Step 8. Ask about the day that is not there

```sql
SELECT count(*) AS cuantas,
       avg(TP2) AS presion_media,
       sum(LPS) AS alarmas
FROM telemetria
WHERE day = DATE '2020-02-29';
```

```anota
avg(TP2) | the mean of that column over the rows that passed the filter
sum(LPS) | the sum of that column
DATE '2020-02-29' | a literal date; without the word DATE in front SQL would read it as text
```

```salida
┌─────────┬───────────────┬──────────┐
│ cuantas │ presion_media │ alarmas  │
├─────────┼───────────────┼──────────┤
│       0 │          NULL │     NULL │
└─────────┴───────────────┴──────────┘
```

Look at that row carefully, because it is the whole module. **The same query, over the same zero
rows, returns 0 in one column and NULL in the other two.**

Counting how many things there are when there are none is zero, and it is a correct number.
Calculating the mean of nothing is not zero: there is no answer. And summing nothing is the same,
for the same reason.

## The result, measured

{{FIG:fig_m08_null_no_es_cero}}

**What we expected.** That the low pressure alarm would be a rare event concentrated around the
failures.

**What came out.** Rare, yes: **5,188 readings** out of 1,516,948, **0.342 %**. Concentrated, no.
Those readings spread over **95 of the 212 days**, that is **45 %** of the days. The alarm goes
off on nearly every other day.

The day it fires most is **15 July**, with **534 readings**, and that is the date of the fourth
failure. But none of the other four on the podium carry a failure report.

**And the finding we were not looking for.** The period covers **214** calendar days and the
record has **212**. Two are missing entirely: **29 February** and **26 April**. In the figure they
are the two crosses.

A missing 29 February has a certain charm, because it is the day a badly written program skips on
its own. There is no way to tell from here whether that was it or whether the unit was down.

**What it means.** An alarm that fires on 45 % of days warns of nothing. It is too frequent for
anyone to look at. That is exactly the problem this project wants to solve: the twin has to warn
better.

And on the two absent days, the practical lesson. If somebody plots alarms per day and those two
come out at zero, the chart will say they were quiet days. They were not: **it is unknown what
they were.** That is why in the figure they carry a cross and not a blank gap.

## Watch out

- **`SELECT` picks columns and `WHERE` picks rows.** It is confusion number one at the start. One
  narrows the table, the other shortens it.
- **NULL is not equal to anything, not even to another NULL.** Writing `WHERE x = NULL` does not
  return the empty rows: it returns **none**. You ask with `WHERE x IS NULL`.
- **`count(*)` and `avg()` do not treat nothing the same way.** Counting nothing is zero;
  averaging nothing is NULL. Both are correct, and that is why you have to know which you asked.
- **Without `ORDER BY` there is no order.** It may come out ordered by chance, and change tomorrow
  with nobody touching anything. If the order matters, ask for it.
- **And an `ORDER BY` with ties does not fully order either.** This lesson was going to publish
  `ORDER BY day LIMIT 5`, which asks for five rows out of the thousands sharing a day without
  saying which. Running it **8 times over the same data gave 2 different results**. Ordering by
  pressure, which barely ties, gave **1**. With a `LIMIT`, the `ORDER BY` has to break ties all
  the way down or the result is not reproducible.
- **This file holds not one single NULL.** The emptiness is not in the cells, it is in the rows
  that do not exist, and those cannot be seen by looking at the table.

## Metallurgical bridge

On a shift sheet there are two boxes that look alike and do not mean the same thing: **zero
tonnes processed** and **the blank box**.

Zero tonnes is information: the plant was down and somebody checked. The blank box is the absence
of information. It might have been down, nobody might have come round to write it, the whole
shift might have gone unrecorded.

Putting that sheet into a spreadsheet turns both into a zero. By month end the plant availability
comes out lower than it was. The error is not in the calculation: it is in having translated
"unknown" as "zero" on the way in.

SQL, for the better, refuses to make that translation on its own.

## Do it yourself

```reto
pregunta: Return the readings where the alarm was active **and** the compressor pressure was above 6 bar, with the columns `day`, `TP2` and `LPS`, ordered by pressure from high to low. Show me only the first 10.
inicio: SELECT day, TP2, LPS
FROM telemetria
WHERE LPS = 1
ORDER BY TP2 DESC
LIMIT 5;
esperado: m08_alarma_con_presion
pista: The starting point already orders and cuts the way it needs to. All it is missing is a second condition in the same `WHERE`, joined to the first by the word `AND`. And the `LIMIT` goes from 5 to 10.
solucion: SELECT day, TP2, LPS
FROM telemetria
WHERE LPS = 1 AND TP2 > 6
ORDER BY TP2 DESC
LIMIT 10;
```

## Review

### The difference between SELECT and WHERE

`SELECT` picks columns and `WHERE` picks rows. With `SELECT` the result table gets narrower; with
`WHERE` it gets shorter. They can be used together and they are independent: you can filter by a
column you then do not show.

### Why WHERE x = NULL does not return the empty rows

Because NULL is not a value, it is the absence of one, and it cannot be compared with equals. The
question "is this gap equal to a gap?" has no answer, so SQL replies that it does not know and
the row does not pass the filter. To ask about absence there is `IS NULL`.

### The same query returns 0 in one column and NULL in another. Is it broken

No, and both answers are correct. Over zero rows, `count(*)` is zero because counting nothing
gives zero. `avg()` and `sum()` give NULL because averaging and summing nothing has no result.
The difference matters: a zero can go into a chart and a NULL warns that there is no datum there.

### Two days are missing from the record. Would you fill them with zeros

No. Filling with zeros turns "unknown" into "nothing happened", and that is inventing a datum.
The right thing is to leave them absent, so that any calculation over them returns NULL. If a
chart needs a box for that day, it gets drawn differently, like the cross in the figure.

### The alarm fires on 45 % of days. Does it work as a failure warning

No, and that is the module's result. An alarm that sounds nearly every other day stops being
looked at a week after installation. It correctly detects that the pressure dropped, but pressure
drops constantly in a compressor's normal operation. To warn of a failure you have to look at
something else, and that is what the rest of the course is about.

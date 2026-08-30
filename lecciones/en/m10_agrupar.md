---
module: 10
---

## In 30 seconds

- A normal compressor on this train runs loaded **3.42 hours a day**.
- On April 18th it ran **23.81 hours out of 24**. There was a failure that day.
- Grouping is going from 1,516,948 readings to a seven month table that fits on screen.
- The trap: only **91 of the 212 days** are complete. Averaging them all would give a false number.
- The four documented failure days are among the six busiest of the half year.

## What this module solves

Until now every query returned rows: many of them, one per reading. None answered an operations
question, because operations questions are not about single readings.

Nobody asks what the sensor read at 04:31:20. They ask how hard the machine worked yesterday.

`GROUP BY` is what turns the first into the second. It is the verb that makes a large table
useful, and it is half the SQL anyone writes in a real job.

## Before the theory: a toy example

Forget the million and a half rows. Look at one shift of six readings, one every ten minutes.

| reading | time | loaded |
|---|---|---|
| 1 | 08:00 | yes |
| 2 | 08:10 | yes |
| 3 | 08:20 | no |
| 4 | 08:30 | no |
| 5 | 08:40 | yes |
| 6 | 08:50 | no |

**Count by hand.** There are six readings. Three say yes. Three say no.

**Turn it into time.** Each reading stands for ten minutes, so three loaded readings are thirty
minutes. The compressor worked **half of that hour**.

That number, thirty minutes, is called loaded time. And the sum you just did has exactly three
steps: split into groups, count inside each group, and multiply by how long one reading lasts.

`GROUP BY` does the first step. The aggregates do the second. The arithmetic is yours.

Now change two things and you have the real case: the groups are days instead of hours, and each
reading lasts ten seconds instead of ten minutes.

## Glossary

- **Grouping.** Sorting rows into piles by the value of a column. Every reading from April 18th
  goes into the April 18th pile.
- **Aggregate.** A function that takes a whole pile and returns a single number. Counting, summing
  and averaging are the three used constantly.
- **Grain.** What one row corresponds to. Before grouping, the grain is a reading. Afterwards, the
  grain is a day. Changing the grain is what `GROUP BY` does.
- **Duty cycle.** The fraction of time a machine spends actually working. Here, the hours the
  compressor spends loaded.
- **Loaded.** The compressor actually compressing air. The opposite is running offloaded, which
  draws current and fills nothing.

## Step by step

### Step 1. Decide what one result row is

Before writing anything, answer this: what do you want each row of the final table to be.

Here the answer is a day. That already tells you what goes after `GROUP BY`.

It is the most important decision in the module and the one most often skipped. Get the grain
wrong and the query works while the number is wrong, which is the worst possible combination.

### Step 2. Choose the signal that says it is working

The file carries fifteen signals and three of them talk about the same thing. The official
datasheet says `DV_eletric` is active when the compressor runs loaded, that `COMP` is active when
air is **not** coming in, and that the motor current sits around 7 A under load.

Three sources for one fact ask to be checked against each other. That happens in step 4.

### Step 3. Turn readings into time

Counting readings is not measuring time. They look so alike that they are easy to confuse.

One reading every ten seconds means each loaded reading is worth ten seconds of work. Dividing by
3,600 gives hours. That `× 10 / 3600` is all the physics in this lesson.

## The code, in parts

### Step 4. Check the signals agree

Before trusting `DV_eletric`, look at what the other two say when it says yes.

```sql
SELECT DV_eletric, COMP, count(*) AS lecturas,
       round(avg(Motor_current), 2) AS corriente_media
FROM telemetria
GROUP BY DV_eletric, COMP
ORDER BY lecturas DESC;
```

```anota
SELECT | picks which columns you want to see in the result
count(*) | counts the rows in each pile, without looking at any column
AS lecturas | names the calculated column so you can read it
avg(...) | averages the values in the pile
GROUP BY a, b | makes one pile per distinct combination of a and b
ORDER BY lecturas DESC | sorts high to low, DESC meaning descending
```

```salida
DV_eletric  COMP    lecturas    corriente_media
         0     1   1,263,084               1.34
         1     0     237,102               5.73
         0     0      10,226               2.69
         1     1       6,536               3.91
```

The first two rows are the expected ones: when one signal says yes the other says no, and the
current agrees. The last two should not exist.

**16,762 readings, 1.1 %, have both signals saying the same thing.** Six thousand of them claim
the compressor is loaded and taking in no air at the same time, which is impossible. It gets
noted and left: module 16 deals with it. For counting hours, 1.1 % does not change the answer.

### Step 5. Group by day

Now the real query. Each result row will be a day.

You can run this one yourself: the button brings a database engine into the browser and runs it
against the compressor's real data. Change it and press again.

```sql-vivo
SELECT day,
       count(*) AS lecturas,
       sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas_de_carga
FROM telemetria
GROUP BY day
ORDER BY horas_de_carga DESC
LIMIT 6;
```

```anota
sum(CASE WHEN ... THEN 1 ELSE 0 END) | counts only the rows meeting the condition, putting a 1 where they do and a 0 where they do not
* 10 | each reading is worth ten seconds
/ 3600.0 | seconds to hours; the point forces division with decimals
LIMIT 6 | cuts the result to six rows, after sorting it
```

```salida
day          lecturas   horas_de_carga
2020-04-18       8663            23.81
2020-06-05       8716            15.41
2020-03-12       8202            13.24
2020-07-15       8661            11.57
2020-05-13       8716            11.31
2020-05-30       8617             8.06
```

Six days. And four of them are documented failure dates.

### Step 6. The average, over complete days only

To know what is normal you need an average, and here is where the trap of this module appears.

```sql
SELECT round(avg(horas_de_carga), 2) AS media,
       min(horas_de_carga) AS minimo,
       max(horas_de_carga) AS maximo
FROM (
    SELECT day,
           count(*) AS lecturas,
           sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas_de_carga
    FROM telemetria GROUP BY day
)
WHERE lecturas > 0.9 * 8640;
```

```anota
FROM ( ... ) | a query can drink from another query; the inner one resolves first
8640 | the readings that fit in a whole day: 24 hours by 360 readings each hour
WHERE lecturas > 0.9 * 8640 | keeps only days holding at least 90 % of their readings
```

```salida
media   minimo   maximo
 3.42     1.11    23.81
```

### Step 7. Filtering groups with HAVING, and the order SQL works in

In step 5 the query came out without filtering incomplete days. If you try adding a `WHERE` to
keep only the complete ones, it does not work.

The reason is the order. **SQL does not run in the order you write it.** First it takes the rows
(`FROM`), then filters them one by one (`WHERE`), then sorts them into piles (`GROUP BY`), and
only then does something called "how many readings this day has" exist.

`WHERE` arrives too early: when it acts, the piles do not exist yet. Filtering piles takes
another word.

```sql
SELECT day,
       count(*) AS lecturas,
       round(sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0, 2) AS horas_de_carga
FROM telemetria
GROUP BY day
HAVING count(*) > 0.9 * 8640
ORDER BY horas_de_carga DESC
LIMIT 6;
```

```anota
HAVING | filters piles, not rows; only usable after GROUP BY
count(*) > 0.9 * 8640 | the same condition as step 6, without needing the inner query
```

```salida
day          lecturas   horas_de_carga
2020-04-18       8663            23.81
2020-06-05       8716            15.41
2020-03-12       8202            13.24
2020-07-15       8661            11.57
2020-05-13       8716            11.31
2020-05-30       8617             8.06
```

Same result as step 5, but now with the guarantee that no partial day slipped in. And shorter
than step 6, which needed a query inside another.

So why did step 6 use that nested query? Because there the average was computed **over a value
that was already the result of grouping**. That is a second level, and `HAVING` does not reach
it: you have to group once, keep the result, and group again on top. Module 11 is about that.

## The result, measured

**What we expected.** A service compressor on a train should spend considerably more time stopped
than working. Somewhere between two and five hours a day would be reasonable.

**What came out.** **3.42 loaded hours a day**, averaged over the 91 complete days. The range runs
from 1.11 to 23.81. Month by month:

| month | complete days | loaded hours |
|---|---|---|
| 2020-02 | 11 | 1.45 |
| 2020-03 | 15 | 3.58 |
| 2020-04 | 11 | 4.27 |
| 2020-05 | 13 | 3.61 |
| 2020-06 | 16 | 4.02 |
| 2020-07 | 13 | 3.78 |
| 2020-08 | 12 | 2.81 |

**What it means.** The average falls inside what is reasonable, so the chosen signal behaves as it
should. The interesting part is not the average, it is what departs from it.

On April 18th the compressor was loaded **98.9 %** of the day. That is seven times normal, and
that date is the first documented failure in the file. The line pressure did not move: the system
held it. What moved was the effort needed to hold it.

There sits the idea the rest of the course rests on, and it turned up with a grouping query, long
before building any model.

Two warnings, so as not to oversell it. Two of those six days, March 12th and May 13th, **appear
in no failure report**. Either they are false alarms, or they are failures nobody reported. It is
not known, and it gets said.

## Watch out

- **Averaging incomplete days lies.** Only 91 of the 212 days hold 90 % of their readings. The
  median day has 7,435 readings, where 8,640 fit. Without the filter, a day with two hours of
  record enters the average as though it were a whole day.
- **Counting readings is not measuring time.** They are the same thing only if sampling is
  regular, and here it is not entirely: module 1 measured 179,426 irregular gaps.
- **`count(*)` counts rows; `count(column)` counts values present.** They look alike and diverge
  the moment there is a hole.
- **A column not in `GROUP BY` cannot appear in `SELECT`** without saying how it is summarised. It
  is the commonest beginner error, and the message the database returns explains it well.
- **`WHERE` cannot filter an average.** The real order is `FROM`, `WHERE`, `GROUP BY`, `HAVING`,
  `SELECT`, `ORDER BY`, `LIMIT`. When `WHERE` acts, the piles do not exist yet. Understanding that
  order fixes half of a beginner's errors.
- **The grain changes under your feet.** After grouping by day, one row is no longer one reading.
  Everything you write from there has to account for that.

## Do it yourself

The query below works and groups by day. Change it so it groups by month.

```reto
pregunta: Return two columns, `mes` and `horas_de_carga`, with the average loaded hours of each month, counting only complete days. Seven rows, from `2020-02` to `2020-08`.
inicio: SELECT day,
       round(sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0, 2) AS horas
FROM telemetria
GROUP BY day
ORDER BY day;
esperado: m10_horas_por_mes
pista: You have to group twice. First by day, to get each day's hours, and then by month to average them. The inner query goes in parentheses after FROM, as in step 6. To pull the month out of a date, `strftime(day, '%Y-%m')`.
solucion: SELECT strftime(day, '%Y-%m') AS mes,
       round(avg(horas), 2) AS horas_de_carga
FROM (
    SELECT day,
           count(*) AS lecturas,
           sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas
    FROM telemetria
    GROUP BY day
)
WHERE lecturas > 0.9 * 8640
GROUP BY mes
ORDER BY mes;
```

## Metallurgical bridge

In a flotation cell, concentrate grade is held up by the control loop. If the feed gets dirtier,
the operator raises the collector dosage and the grade holds. Anyone watching only the grade will
say nothing happened.

What happened shows in the reagent consumption, not in the grade.

The same thing occurs here on another machine. Line pressure is the grade: the control holds it
and it does not move. Duty cycle is the dosage: it is what rises when something goes wrong. That
is why this module measures loaded hours and not mean pressure.

It is the same lesson the causal reading of the silica project left, on a different machine:
**watch the manipulated variable, because the controlled one will lie to you.**

## Review

### Why group by day and not by hour, when the data comes every ten seconds

Because the grain is decided by the question, not by the data. The question is how hard the
machine works in a shift, so each result row has to be a day. The ten second data is still down
there, and grouping by hour would be another query for another question.

### What exactly does `sum(CASE WHEN condition THEN 1 ELSE 0 END)` do

It counts only the rows meeting the condition. It puts a one where they do and a zero where they
do not, and adds them up. It is the portable way of counting with a condition, and it works in
any database.

### Why filter out incomplete days, and why at 90 %

Because a day with two hours of record would enter the average as a whole day and drag it down.
The 90 % is not sacred: it is the cut that excludes plainly broken days without throwing away
those missing only a small gap. With another threshold the average barely moves, and that is
worth checking before defending it.

### The busiest day was 23.81 hours. How do you know it is not a sensor fault

I do not know from the query alone, and that is the point. What I know is that the date coincides
with a failure documented by the company, and that three other failure dates are also among the
six busiest. Four matches out of four do not prove causation, but they rule out sensor
coincidence.

### Somebody tells you the fleet's mean duty cycle is 3.4 hours. What do you ask

Which days it is computed over. An average without its denominator means nothing. In this very
file, the mean over all 212 days and the mean over the 91 complete ones are two different
numbers, and only one of them answers the question that was asked.

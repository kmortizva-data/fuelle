---
module: 14
---

## In 30 seconds

- Bronze refused to decide. Silver decides, and **every decision leaves a column or a number**.
- Floating point noise touches **85.5 %** of TP2's values. They get rounded to 3 decimals.
- The **16,762** contradictory readings get **flagged**, not deleted.
- The clock sits on no grid: it walks. Once snapped, **12,841** readings share a slot.
- And **337,653 holes** appear that did not exist as rows in bronze.

## What this module solves

Module 4 left a rule: bronze does not clean. That turns cleaning into a postponed problem, and
this module is where the deadline falls due.

Here is where a good datum gets defined. What matters is not the particular decision, it is that
it **ends up written in code with its price measured**, rather than in the head of whoever made
it.

## Before the theory: a toy example

Four readings from a shift, straight off the sensor:

| time | pressure | valve open | compressor taking air |
|---|---|---|---|
| 06:00:02 | 8.200000000000001 | 1 | 0 |
| 06:00:12 | 8.4 | 1 | 1 |
| 06:00:31 | 8.6 | 0 | 1 |
| 06:00:41 | 8.8 | 0 | 1 |

There are three problems in there, and each one calls for a different decision.

**One: the 8.200000000000001.** The gauge has three decimals, so the next twelve are not
measurement, they are floating point litter. **Round it.** Nothing is lost.

**Two: the second row says the valve is open and the compressor is taking air at once.** The two
signals are opposites by design, so one of them is lying and nobody knows which. Deleting the row
would hide a broken sensor. **Flag it** with a column saying that row is suspect, and whoever
uses it will decide.

**Three: the 06:00:22 reading is missing.** 19 seconds pass between the second row and the
third, not 10. Filling in an invented pressure would be lying. **Create the empty row**, with
NULL inside. That is exactly what module 8 said a hole should look like.

Notice the pattern: **rounding removes, flagging adds a column, and the grid adds rows.** All
three are decisions and none is obvious. What separates them from a bodge is that they are
written down and their cost is known.

## Glossary

- **Silver.** The lake's second layer. Clean, typed, ready to work with, and with the decisions
  taken and recorded.
- **Resample.** Take measurements captured at one rhythm and put them on another. Here, on a
  regular ten second grid.
- **Grid.** One row every exact ten seconds, reading or no reading.
- **Slot.** Each of those ten second gaps in the grid.
- **Snap.** Put every reading in the slot it belongs to. Also called bucketing.
- **Collision.** Two readings landing in the same slot.
- **Flag.** A column that is not a datum, it is a judgement about the datum. Here, `dudoso`.

## Step by step

### Step 1. Measure what each decision will cost, before taking it

Before rounding anything it helps to know how many values will be touched. If it were four,
rounding is a detail. If it is one million three hundred thousand, it is the kind of decision you
declare.

### Step 2. Round to the precision the sensor really has

The file shows three decimals. Everything below that was put there by the computer when it stored
the number in binary, and module 9 measured what leaving it costs.

### Step 3. Flag the contradictions instead of deleting them

`DV_eletric` and `COMP` are opposites by design. When they agree, something is wrong with the
instrumentation and that information is worth keeping. A `dudoso` column preserves it.

### Step 4. Snap the clock to a grid, and find that it walks

And here is the part that did not come out first time. The first version of this script joined
each reading to the grid on an exact timestamp match, and **kept one in ten**.

The reason is that **this clock is not on any fixed grid**. Every nine second gap shifts its phase
by one, so the readings spread evenly across all ten possible remainders. There is no reference
instant.

## The code, in parts

### Step 5. What it will cost, counted first

```sql
SELECT
  sum(CASE WHEN TP2 <> round(TP2, 3) THEN 1 ELSE 0 END) AS tp2_con_ruido,
  sum(CASE WHEN DV_eletric = COMP THEN 1 ELSE 0 END)    AS contradictorias,
  count(*) AS filas
FROM telemetria;
```

```anota
TP2 <> round(TP2, 3) | the value is not equal to itself rounded, meaning it carries extra decimals
<> | different from; also written as !=
DV_eletric = COMP | the two signals hold the same value, and they are opposites by design
```

```salida
┌───────────────┬─────────────────┬─────────┐
│ tp2_con_ruido │ contradictorias │  filas  │
├───────────────┼─────────────────┼─────────┤
│       1296720 │           16762 │ 1516948 │
└───────────────┴─────────────────┴─────────┘
```

One million two hundred and ninety six thousand out of one million five hundred and sixteen
thousand. **The noise is not the exception, it is the rule.**

### Step 6. Snap each reading to its slot

```sql
SELECT count(*) AS lecturas,
       count(DISTINCT casilla) AS casillas_ocupadas,
       count(*) - count(DISTINCT casilla) AS colisiones
FROM (SELECT time_bucket(INTERVAL 10 SECOND, timestamp) AS casilla FROM telemetria);
```

```anota
time_bucket(INTERVAL 10 SECOND, x) | trims the timestamp back to the ten second slot it belongs to
count(DISTINCT casilla) | how many slots end up occupied, which is not the same as how many readings there are
```

```salida
┌──────────┬───────────────────┬────────────┐
│ lecturas │ casillas_ocupadas │ colisiones │
├──────────┼───────────────────┼────────────┤
│  1516948 │           1504107 │      12841 │
└──────────┴───────────────────┴────────────┘
```

Twelve thousand eight hundred and forty one readings land in a slot that is already taken.
Something has to be decided about them, and throwing one of the two away is not an option on this
course.

### Step 7. Merge without losing anything

```sql
SELECT casilla,
       count(*)                 AS lecturas,
       round(avg(TP2), 3)       AS TP2,
       max(DV_eletric)          AS DV_eletric
FROM (SELECT time_bucket(INTERVAL 10 SECOND, timestamp) AS casilla, *
      FROM telemetria)
GROUP BY casilla
ORDER BY lecturas DESC
LIMIT 3;
```

```anota
avg(TP2) | the mean of the readings that fell in that slot; with only one, it is that one
max(DV_eletric) | the maximum of a zero and one signal: if it was open at any point, it counts as open
count(*) AS lecturas | how many readings were merged there, kept as a column so it shows
```

Analogue signals get averaged and digital ones take the maximum, because a valve open at any
point in those ten seconds was open. And `lecturas` leaves the merge in plain sight rather than
hiding it.

### Step 8. The whole grid, holes included

```sql
SELECT timestamp, medido, lecturas, TP2
FROM plata
WHERE timestamp BETWEEN TIMESTAMP '2020-06-12 00:54:30'
                    AND TIMESTAMP '2020-06-12 00:55:30'
ORDER BY timestamp;
```

```anota
FROM plata | the new layer, which is no longer the raw telemetry
medido | a new column: true when that slot has a reading behind it
```

```salida
┌─────────────────────┬─────────┬──────────┬────────┐
│      timestamp      │ medido  │ lecturas │  TP2   │
├─────────────────────┼─────────┼──────────┼────────┤
│ 2020-06-12 00:54:30 │ false   │        0 │   NULL │
│ 2020-06-12 00:54:40 │ false   │        0 │   NULL │
│ 2020-06-12 00:54:50 │ false   │        0 │   NULL │
│ 2020-06-12 00:55:00 │ true    │        1 │  7.212 │
│ 2020-06-12 00:55:10 │ true    │        1 │  7.422 │
│ 2020-06-12 00:55:20 │ true    │        1 │  7.576 │
│ 2020-06-12 00:55:30 │ true    │        1 │   7.79 │
└─────────────────────┴─────────┴──────────┴────────┘
```

There is the real change of this module. **A hole has gone from being a missing row to being a
row that says there is nothing here.** In bronze nobody could see it without subtracting
timestamps.

## The result, measured

{{FIG:fig_m14_huecos}}

**What we expected.** To clean a few odd values and leave the data tidier.

**What came out.** That the odd values were nearly all of them. Floating point noise touches
**85.5 %** of TP2 and 98.6 % of `DV_pressure`. Rounding to three decimals is not a touch up: it
is over a million values.

And above all, the grid uncovered what was hidden. The **1,841,760 slots** of ten seconds that
fit between the first and the last reading hold only **1,504,107** occupied ones. The other
**337,653** are holes, **18.3 %**.

The figure shows they are not spread evenly. April loses 24 % and February 15 %.

{{FIG:fig_m14_remuestreo}}

The zoom shows an ordinary hole: ninety slots in a row with nothing in them, and then the
compressor starting. The first four readings after the hole are the ones from step 8, with
pressure climbing from 7.212 to 7.79 bar in four slots.

**What it means.** Bronze looked complete because it had no way to show what it was missing.
Putting the data on a grid adds no information: it **turns an absence into something countable**,
and counting it has a price. The same silver written without its empty slots takes 20.49 MB
instead of 21.88: **the holes cost 1.38 MB**.

This lesson used to say they cost nearly two megabytes, and it measured that by subtracting bronze
from silver. That subtraction does not measure the holes, because silver changes several things at
once: it rounds, it merges readings and it drops the original index column. And the silver of
back then came out inflated, because DuckDB wrote it with several threads at once and in no order at all. Module 29 found
that out by deleting the lake and rebuilding it. Today the whole of silver weighs less than
bronze: 21.88 MB against 22.05.

In exchange for that price, comparing a row with the previous one stops depending on whether the
clock jumped, and that is all the twin will ever do.

**And the check that matters.** Silver holds bronze's **1,516,948** readings, not one fewer,
spread across its 1,504,107 slots. The script refuses to finish if that count does not come out,
and that refusal is what caught the first version, which dropped nine in ten along the way.

## Watch out

- **Cleaning is not throwing away.** Silver keeps every reading bronze had. What changes is the
  shape and what gets added, never what disappears.
- **A flag beats a delete.** `dudoso` leaves the 16,762 contradictions in plain sight. Whoever
  runs a calculation decides whether they want them, and that decision stays in their query.
- **A record's clock is not where you think.** Here it walks, and joining on an exact timestamp
  kept one reading in ten. You check that by counting, not by assuming.
- **Merging two readings is a decision and it has to show.** The `lecturas` column says how many
  sit behind each slot, so nobody meets an average without knowing.
- **A hole in the grid is not a zero.** It is NULL, and any mean crossing it returns NULL, which
  is correct. Module 8 said so and here it is structural.
- **Filling the holes is tempting and does not happen here.** Interpolating would invent 337,653
  measurements nobody took. If some module of the twin needs them, it will invent them itself and
  say so.

## Metallurgical bridge

A laboratory does not hand over the assay the instrument measured. It hands over the assay with
its significant figures, its date, and a note when the test came out of control.

That note is the `dudoso` column. The laboratory does not delete the odd test: it delivers it
flagged, and whoever does the balance decides whether to use it. Deleting it would leave a
cleaner balance and hide an instrument drifting out of calibration.

And significant figures are the rounding. A spectrometer spitting out 0.4987654321 is not
measuring ten figures: it is measuring four and padding the rest. Publishing them all is not more
precision, it is less honesty.

## Review

### What silver does that bronze refused to do

Decide. Bronze keeps what arrived without touching it, and that leaves the problems intact and
postponed. Silver rounds the noise, flags the suspect and puts the data on a regular grid. What
separates it from any old cleanup is that every decision is in the code and its cost is measured.

### Why flag the contradictions instead of deleting them

Because they are 16,762 readings where two signals that should be opposites agree, and that is
information about the instrumentation. Deleting them would leave a cleaner table and hide a
failing sensor. Flagged, anyone can exclude them in their query, and the decision stays visible
rather than buried in the ingestion.

### What resampling is, and why a timestamp join was not enough here

Resampling is putting measurements on a regular rhythm. A join was not enough because the
record's clock walks. Every nine second gap shifts its phase, so the readings fall evenly across
all ten possible second remainders. An exact equality join kept one in ten, and each reading has
to be snapped to its slot.

### Two readings land in the same ten second slot. What do you do

Merge them and leave a trace. Analogue signals get averaged and digital ones take the maximum,
because a valve open at any instant of those ten seconds was open. And a column keeps how many
readings there were, so nobody meets an average thinking it is a measurement.

### The holes take up space. What are they for, then

For them to exist. Bronze looked complete because it had no rows where data was missing, and only
subtracting timestamps could tell you. Silver has 337,653 rows saying "nothing here", and they cost
1.38 MB, measured by writing the same silver without them. That is the price of being able
to count what is missing.

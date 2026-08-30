---
module: 1
---

## In 30 seconds

- A compressor from a Porto Metro train, logged for seven months.
- The official datasheet promises **15,169,480 measurements**. The file holds **1,516,948**.
- Four real failures, with dates and maintenance reports, and all four are air leaks.
- The reports arrive with factory errata and **they are not corrected**.
- The question the whole course turns on: what signal gives a leak away, if pressure does not drop.

## What this module solves

Before touching a single tool you have to know what is in front of you. This module opens the
archive, counts what is inside, and compares it against what its documentation claims is there.

They disagree. That is the first lesson of the course, and it is not about data: it is about
trust.

A data file always arrives with a story somebody wrote. The story helps, but **the file decides**.

## Before the theory: a toy example

Imagine you receive the log of a belt weigher. The sheet that comes with it says:

> Continuous logging, one weighing per second, 3,600 weighings over the test hour.

You open the file and count the rows. There are **360**.

**Divide.** 3,600 over 360 is 10. For every ten weighings the sheet promises, the file holds one.

**Look at the first column.** The row numbers run 0, 10, 20, 30. Not 0, 1, 2, 3.

There is the explanation, and it is not that data is missing. The weigher did weigh 3,600 times.
What you were handed is **one in every ten**, keeping the original numbering. The sheet describes
the capture; the file is what they published.

That one line division is the whole method of this module. What changes with the compressor is
the scale: instead of 3,600 and 360, it is 15,169,480 and 1,516,948.

## Glossary

- **Telemetry.** The record a machine leaves of itself while running. Here, fifteen signals noted
  every ten seconds for seven months.
- **Analogue signal.** One measuring a magnitude with all its decimals: a pressure, a temperature,
  a current.
- **Digital signal.** One that only says yes or no. That a valve is open, that an alarm is active.
- **Sampling.** How often a reading is written down. Here every ten seconds, though not always.
- **Downsampling.** Keeping one reading in every N and discarding the rest. It shrinks the file
  and loses detail, and it is what was done to this one before publishing.
- **Failure report.** What the company writes when something breaks. Here there are four, and they
  are the only ground truth this project has.

## Step by step

### Step 1. The machine

An air compressor feeds the brakes, the doors and the suspension of a train. If it stops, the
train stops. That is why it carries sensors.

Its job is simple to describe: keep a receiver full of air. When pressure drops below a threshold,
it starts and compresses. When it reaches the top, it stops. And round again.

{{FIG:fig_m1_anatomia_del_compresor}}

There is the whole machine over two hours of an ordinary Tuesday. Pressure falls slowly, because
the train keeps consuming air. It touches the threshold, the compressor starts, and pressure rises
almost vertically. Afterwards the motor keeps turning a while without compressing anything, which
is what the datasheet calls running offloaded, and that is why the current sits around 4 A instead
of dropping to zero.

Three cycles in two hours. That rhythm is what the whole course watches.

### Step 2. What the datasheet promises

The zip from the University of California carries, besides the file, a description PDF. It says
two things worth keeping:

> Number of Instances: 15169480

> The data were logged at 1Hz by an onboard embedded device.

Fifteen million measurements, one per second. And it describes the fifteen signals one by one,
with details that turn out to be gold later: that the compressor starts when pressure drops below
**8.2 bar**, that an alarm fires below **7 bar**, and that the motor draws about 7 A loaded and
about 4 A offloaded.

### Step 3. What the file holds

Count the rows and look at the dates. It is the first thing anyone should do with any archive,
and almost nobody does.

## The code, in parts

### Step 4. Count what is there

```python
import duckdb

con = duckdb.connect()
src = "read_csv_auto('data/MetroPT3(AirCompressor).csv')"
print(con.sql(f"SELECT count(*), min(timestamp), max(timestamp) FROM {src}").fetchone())
```

```anota
import duckdb | brings in the tool that knows how to read and query data files
con = duckdb.connect() | opens a database in memory; it creates no file
read_csv_auto(...) | reads the CSV working out each column's type by itself
f"..." | a string with holes: what sits in braces is replaced by its value
count(*) | counts the rows
min / max | the smallest and largest value of a column
.fetchone() | brings the first result row back into Python
```

```salida
(1516948, datetime.datetime(2020, 2, 1, 0, 0), datetime.datetime(2020, 9, 1, 3, 59, 50))
```

A million and a half rows, from 1 February to 1 September 2020.

First mismatch, and a small one: the repository's page says the data runs "from February to
August". It reaches 1 September.

### Step 5. Measure the sampling instead of assuming it

The datasheet says 1 Hz. Rather than believe it, measure the distance between consecutive
readings.

```python
con.sql(f"""
    SELECT gap, count(*) AS veces
    FROM (SELECT date_diff('second', lag(timestamp) OVER (ORDER BY timestamp),
                           timestamp) AS gap
          FROM {src})
    WHERE gap IS NOT NULL
    GROUP BY gap ORDER BY veces DESC LIMIT 3
""").show()
```

```anota
lag(timestamp) OVER (ORDER BY timestamp) | looks at the previous row's value, ordering by date
date_diff('second', a, b) | how many seconds lie between two timestamps
IS NOT NULL | drops the first row, which has no previous one
```

```salida
┌───────┬──────────┐
│  gap  │  veces   │
├───────┼──────────┤
│    10 │  1337521 │
│     9 │   128277 │
│    12 │    38321 │
└───────┴──────────┘
```

**Every ten seconds, not every second.** And not always: 179,426 readings arrive on a different
interval. The commonest is nine seconds, 128,277 times, and next is twelve, 38,321.

### Step 6. The division that explains it

```python
print(15_169_480 / 1_516_948)
```

```salida
10.0
```

Exactly ten, with no stray decimals. That does not happen by chance.

And the first column of the CSV, the one with no name, runs 0, 10, 20, 30. It keeps the original
record's numbering.

## The result, measured

**What we expected.** That the file would hold what its datasheet declares, or something close.

**What came out.** The datasheet declares **15,169,480** measurements at 1 Hz. The file holds
**1,516,948** readings every 10 s. The ratio is **10.0000**, and the index column keeps the
original numbering.

**What it means.** The original record really was one datum per second. What was published is
**one reading in every ten**. The datasheet does not lie: it describes the capture, not the file.
But anyone coding on the assumption of 1 Hz will get every time calculation ten times wrong.

And the four failures, which are this project's ground truth:

{{FIG:fig_m1_las_cuatro_averias}}

Each dot is a day. The height is the hours the compressor spent actually working. The dotted line
is the mean, **3.42 hours**. The four rings are the days carrying a failure report, and all four
sit high, far above the mean.

That drawing is the whole project. The rest of the course is about building what it takes to see
it without knowing in advance where to look.

## Watch out

- **The datasheet describes the capture, not the file.** That is this module's mismatch, and it is
  ordinary in public data. You check it by counting, not by reading.
- **The failure reports carry errata and are not corrected.** They are numbered `#1`, `#1`, `#3`
  and `#4`: two ones and no two. One writes `Air leak` and another `Air Leak`. And the 29 May
  failure declares maintenance on **30 April**, a month before itself. They are copied literally
  and explained, because that is how real reports arrive.
- **Sampling is not regular.** 179,426 readings, 11.8 %, do not respect the ten seconds. Counting
  rows and measuring time will not be the same thing.
- **Four failures are not statistics.** With four events you do a case study and you say so. Any
  percentage computed over four things is an anecdote with decimals.
- **The decimals carry litter.** The file holds values like `-0.0120000000000004`. That is nobody's
  error: it is how a computer stores numbers with a point. Module 14 deals with it.

## Metallurgical bridge

When a laboratory certificate arrives with a lot's grade, the first thing a metallurgist with
craft does is not use the number. It is to look at how many aliquots back it, what date they are,
and whether the declared method is the one that was used.

A certificate reading 64.03 % iron for thirty three days running is not a stable grade: it is an
assay that stopped being updated. The number looks fine until somebody asks where it came from.

This module is that, with a file. The datasheet is the certificate, the CSV is the pulp, and
counting the rows is weighing the aliquot before trusting the paper.

## Review

### You are handed a data file and its documentation. Where do you start

By counting. Rows, columns, first and last date, and how often a reading arrives. That is four
queries and they come before anything else. The documentation gets read afterwards, to explain
what you counted, not to replace it.

### The datasheet said 15 million and the file holds 1.5. Is that a repository error

No. The ratio is exactly ten and the index column keeps the original numbering, so what was
published is a downsample of the original record. The datasheet describes the machine's capture.
It is loose wording, not lost data.

### Why not fix the errata in the failure reports

Because they are the project's only ground truth and they are not mine. If I correct the numbering
or the maintenance date, I am inventing a datum I never measured. They are kept literal, declared
in a README beside the file, and explained in whichever lesson they get in the way.

### What makes you think the leak will show anywhere, if pressure does not drop

The figure at the end. The four days carrying a failure report are days the compressor worked far
more than usual, up to 23.81 hours out of 24 against a mean of 3.42. The control loop holds the
pressure; what spikes is the effort of holding it.

### A compressor is not a flotation plant. What is this doing in your portfolio

It is doing this: compressed air is what feeds the flotation columns, and a leak in the air line
is lost recovery with no alarm noticing. The machine changes, the problem does not: the variable
being controlled gives nothing away, and the one working to control it does.

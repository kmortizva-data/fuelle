---
module: 6
---

## In 30 seconds

- Partitioning is splitting a table into folders so a question reads only one.
- The advice repeated everywhere is to split by day. Here it gets measured.
- Reading one day takes **0.014 s against 0.171 s** between not partitioning and splitting by day.
- Splitting by day comes out **12.2 times slower** and takes **31 %** more. It is the worst of the four.
- Splitting by month and not splitting **do not separate**: their ranges overlap.

## What this module solves

Module 4 left the lake split into 212 folders, one per day, because it is what everybody does.
This module checks whether that was a good idea.

It turns out it was not, and the reason teaches more about how a columnar format works than any
explanation.

## Before the theory: a toy example

You have 120 shift reports from a year and somebody asks for June's. Three ways of storing them:

| Where | How many folders | For June you open | Sheets you look at |
|---|---|---|---|
| One box | 1 | the box | 120 |
| Twelve folders, one per month | 12 | 1 folder | 10 |
| Three hundred and sixty five, one per day | 365 | 30 folders | 10 |

The last two make you look at the same ten sheets. The difference is in **how many folders you
have to open and close** to reach them: one against thirty.

Opening a folder costs. Little, but it costs, and that cost does not depend on how many sheets
are inside. If the folders are many and small, a point arrives where more time is spent opening
folders than reading sheets.

That point is what this module hunts with the stopwatch. The question is not whether partitioning
helps, it is **at what size**.

## Glossary

- **Partition.** To split a table into several files according to the value of a column, normally
  the date. Each distinct value is a folder.
- **Partition pruning.** The engine discarding whole folders without opening them, looking only
  at the name. It is what makes partitioning useful.
- **File statistics.** The minimum and maximum values Parquet stores for each block of rows, so
  it can skip the block whole without reading it.
- **Overhead.** The fixed cost of each file, independent of its content: opening it, reading its
  header, closing it.
- **Small files.** The problem of having a great many tiny files. It has a name of its own
  because it is a data lake classic.

## Step by step

### Step 1. Write the same thing four ways

The same 1,516,948 rows and the same content, spread four ways. In one single file, by month, by
week and by day. The only thing that changes is the split.

### Step 2. Ask all four the same question

How many readings there are for 5 June. Partitioning by date exists to answer exactly that, so it
is where splitting by day ought to shine.

### Step 3. Time seven times and keep the range

Here is this module's most important correction. The first version of this script timed each
split **one single time**, and with those numbers the conclusion was another.

With one measurement, splitting by month came out faster than not splitting. With seven
measurements and their ranges, the two overlap: **they do not separate**. The first version was
going to publish a winner that does not exist.

### Step 4. Check that the four answer the same

Before comparing times, the four layouts have to return the same number of rows. Otherwise the
split is not what is being measured: a writing error is.

## The code, in parts

### Step 5. Write one split

```sql
COPY (
    SELECT *, date_trunc('month', timestamp) AS part
    FROM read_parquet('lake/bronze/telemetry/**/*.parquet')
)
TO 'lake/_bench/by_month'
(FORMAT PARQUET, PARTITION_BY (part), OVERWRITE_OR_IGNORE, COMPRESSION ZSTD);
```

```anota
date_trunc('month', timestamp) | trims the date back to the start of its month: 5 June becomes 1 June
AS part | the column to split by; the name does not matter, what matters is that it exists
PARTITION_BY (part) | one folder per distinct value of part, that is one per month
```

Swapping `month` for `week` or for the whole day gives the other splits. The rest of the code is
identical, which is what makes the comparison fair.

### Step 6. Measure reading one day, seven times

```python
read = measure(lambda: con.sql(
    f"SELECT count(*) FROM read_parquet('{glob}') "
    f"WHERE CAST(timestamp AS DATE) = DATE '{ONE_DAY}'"
).fetchone()[0])
```

```anota
measure(...) | the function from src/medir.py: runs whatever it is given seven times and returns the median with its range
lambda: ... | a function with no name, written on one line; it serves to pass "this thing to do" as if it were a datum
DATE '2020-06-05' | a literal date in SQL; without the word DATE in front it would be text
```

```salida
Writing single_file, 7 times...
     1 files    16.84 MB  write     0.99 s  read one day 0.014 s (0.012 to 0.017)
Writing by_month, 7 times...
     8 files    17.64 MB  write     0.94 s  read one day 0.019 s (0.016 to 0.085)
Writing by_week, 7 times...
    32 files    17.79 MB  write     2.51 s  read one day 0.039 s (0.026 to 0.053)
Writing by_day, 7 times...
   212 files    22.09 MB  write     3.18 s  read one day 0.171 s (0.154 to 0.201)
```

### Step 7. Decide with the ranges, not with the medians

```python
row["read_distinguishable_from_fastest"] = (
    False if row["layout"] == fastest_name
    else distinguishable(reads[fastest_name], other))
```

```anota
distinguishable(a, b) | from src/medir.py: returns false if the two ranges tread on each other
False if ... else ... | a condition written on one line: if it is the fastest, it is not compared against itself
```

```salida
  All layouts return the same 8,716 rows for 2020-06-05: True
  fastest read: single_file
  by_month reads the same as single_file: the ranges overlap, so there is no difference to report
```

Nobody wrote that last line: the script decided it by comparing the ranges.

## The result, measured

{{FIG:fig_m6_curva_de_particion}}

**What we expected.** That partitioning by day would win. It is the standard advice and the
question is for exactly one day. The logic looks solid: with the day's data in its own folder,
there is no need to look at the other two hundred and eleven.

**What came out.** The opposite, with room to spare. Reading one day takes **0.014 s against
0.171 s** between not partitioning and splitting by day. Splitting by day is **12.2 times
slower** in exactly the case it is supposed to serve, and it takes **31 %** more, 212 files
against one.

The left panel of the figure shows the curve rising with the number of files, and the right one
shows the size doing the same.

**What it means.** Parquet already knows how to skip what it does not need. Every file stores,
for each block of rows, the minimum and maximum value of each column. Asking for one day, the
engine reads those statistics and discards the blocks that cannot contain it, without reading
them.

So the pruning was already happening **inside** the file. Splitting into 212 folders adds no new
capability: it adds 212 headers to open, read and close. The overhead is paid in full and the
benefit was already collected.

And the second result, the one that only appears by measuring properly. **Splitting by month and
not splitting do not separate**: one range overlaps the other, so there is no difference to
report. The first version of this script, with one measurement, gave splitting by month as the
winner.

## Watch out

- **This holds at this scale and on this machine.** With a billion rows and several disks in
  parallel the answer changes, because then the folders get read at once. The conclusion that
  travels is not "do not partition", it is **measure before splitting**.
- **The number of files is the knob, not the date.** Splitting by day is a way of saying "212
  files". What decides is how many come out and how much each weighs, not whether the column is a
  date.
- **Writing by day also comes out dearer**, and that gets paid every night. A bad split does not
  just slow reads down.
- **Medians are not enough to rank.** Two splits with overlapping ranges are the same split as
  far as this machine goes. Ranking by median would have invented a winner.
- **`bronze.py` still partitions by day.** It is left on purpose: module 4 makes the ordinary
  mistake and this one measures it. Changing it early would have erased the lesson.

## Metallurgical bridge

A ball mill has an optimum ball size, and it is neither the largest nor the smallest. Large balls
break the coarse well and waste energy on the fines. Small balls do the opposite.

Nobody picks a ball charge by copying another plant's. It gets picked by looking at the size
distribution of the feed and the product being sought, because with another ore the answer is
another.

Partition size is exactly that. Partitioning by day is a default ball charge, and here the feed
was asking for another.

## Review

### What is partitioning and what is it supposed to be for

Splitting a table into folders according to the value of a column, almost always a date. It
serves so that a narrow question opens only the folders it needs and saves the rest. It is true
when each folder is large, and it stops being true when they are many and small.

### Why did partitioning by day come out worse than not partitioning

Because Parquet was already skipping what it did not need. It stores the minimum and maximum per
block of rows, so it discards what cannot hold the requested day without opening it. Splitting
into 212 files added no pruning, it added 212 headers to open.

### How do you choose the partition size then

By measuring, with the real question and on the real machine. Several splits get written, the
same query gets timed on all of them, and you look at where the curve starts to rise. Copying a
value from a blog post is choosing without data.

### Two splits give different medians. Can you say which is better now

Not if their ranges overlap. That happened here with not partitioning and partitioning by month,
and that is why the script says so instead of ranking them. A difference that does not survive
repeating the measurement is not a difference.

### If the lake held a billion rows tomorrow, would this conclusion hold

Not necessarily, and that is the important part. At that scale a single file stops fitting
comfortably and folders can be read in parallel, so the overhead gets shared out. What does
travel is the method: write several splits, time them with the real question, and look at the
ranges before declaring a winner.

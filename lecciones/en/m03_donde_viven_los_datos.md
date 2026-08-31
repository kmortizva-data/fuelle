---
module: 3
---

## In 30 seconds

- "File", "database", "lake" and "warehouse" are not synonyms, however they get used.
- The same question, in all four places: from **0.558 s to 0.003 s**. Nearly two hundred times.
- The text file is the biggest and the slowest. Both at once, and that is no coincidence.
- The lake takes **22.08 MB** against **208.19**: nearly ten times less with the same data inside.
- And a surprise: **the warehouse index sped up nothing** and cost 18.0 MB.

## What this module solves

These four words appear in every job ad in the field and almost nobody tells them apart.
Explaining them with definitions does not work: the definitions look far too alike.

So here we do the opposite. Take a simple question, store the same data four ways, and time it.
The differences show on their own.

## Before the theory: a toy example

You have a year of shift reports in the plant office, and somebody asks how many stoppages there
were on 5 June.

**Place one: a box of loose sheets.** They are all there, unordered. To answer you have to pull
them out and look at them one by one to the end, because until the last one you do not know
whether another 5 June sheet is left.

**Place two: twelve folders, one per month.** You go to June and look only at that one. You do
not touch the other eleven months. The box weighed the same, but the question now costs a twelfth.

**Place three: a cabinet with cards ordered by date.** You go straight to 5 June. You do not even
open the whole folder.

**Place four: a notebook where somebody already wrote down, each night, how many stoppages there
were that day.** You read one line.

Those four places are, in that same order: **a file, a lake, a database and a warehouse**. And
all of them hold exactly the same information.

What changes is not the data. It is how much work it takes to ask it something.

## Glossary

- **File.** A loose archive with the data inside, usually text. It knows nothing about itself: to
  answer anything you have to read it whole.
- **Columnar format.** Storing all the values of one column together, instead of grouping rows.
  It lets you read only the columns you need and it compresses far better.
- **Data lake.** Files in folders, usually in columnar format and split by date. Cheap, and it
  gets queried without loading anything into any server.
- **Database.** A program that stores the data in its own format and answers questions. It knows
  what is inside, so it can skip what it does not need.
- **Data warehouse.** A database prepared for the questions that repeat: columns precomputed,
  tables presummarised, indexes where they help.
- **Index.** A separate structure pointing at where each value lives, so it need not be searched
  for. It speeds some questions up, takes space, and slows writes down.

## Step by step

### Step 1. Pick a question and do not change it

How many readings there are for 5 June. It is about as simple as they come, and that is why it
works: what gets measured is the place, not the question.

### Step 2. Store the same data four ways

The original CSV exactly as it arrived. The lake of Parquet partitioned by day. A database with
the table inside. And a warehouse, which is that same database with the date precomputed in its
own column and an index on top.

### Step 3. Time each one seven times and keep the median

One measurement is not a measurement. The first version of this script timed once, and two
consecutive runs of the same code reported 203.7 and 143.8 times between the extremes. The coarse
conclusion held, but the number about to be published did not.

So it gets measured seven times and the median is what gets published, so that one isolated spike
does not move the result. And with it the minimum and the maximum: hiding the variability would
be faking a precision that does not exist.

## The code, in parts

### Step 4. The same question, changing only the place

```python
def measure(action, runs=7):
    times = []
    for _ in range(runs):
        started = time.perf_counter()
        result = action()
        times.append(time.perf_counter() - started)
    times.sort()
    return Measurement(median=times[len(times) // 2],
                       minimum=times[0], maximum=times[-1],
                       runs=runs, result=result)
```

```anota
def measure(action, runs=7) | defines a function called measure taking something to do and how many times to do it
action | not a datum, an action: the query to be timed is passed in and called here with action()
time.perf_counter() | Python's most precise stopwatch, in seconds
times.sort() | orders the list from smallest to largest, which is what the median needs
times[len(times) // 2] | the middle one once ordered, that is the median
result | what the last run returned, which is what lets you check that the four places answer the same
```

That function lives in `src/medir.py` and every script in the course that times anything uses it.
It gets written once instead of three copies that drift apart over time.

```salida
median of 7 runs per place
place                 format                   size  median     min     max
un fichero de texto   CSV                     208.19 MB   0.558   0.551   0.628
un lago de ficheros   Parquet particionado     22.08 MB   0.216   0.174   0.225
una base de datos     DuckDB                   49.76 MB   0.003   0.002   0.005
un almacén            DuckDB con índice        67.76 MB   0.004   0.003   0.005
```

### Step 5. Check that the four say the same thing

Before comparing times you have to check that the four answers match. Otherwise you are not
measuring the place: you are measuring a mistake.

```salida
all four return 8,716 rows for 2020-06-05: True
slowest over fastest: 186.0x
index vs no index distinguishable: False (plain 0.003 s (from 0.002 to 0.005), indexed 0.004 s (from 0.003 to 0.005))
```

## The result, measured

{{FIG:fig_m3_cuatro_sitios}}

**What we expected.** That the text file would be the slowest and the database the fastest. And
that the warehouse, with its index, would be faster still.

**What came out.** The first part yes, by a mile: the text file takes **0.558 s** and the
database **0.003 s**. That is **186 times**.

**The index sped up nothing.** The warehouse and the database give medians of
0.004 and 0.003 seconds, and **their ranges overlap**. When two ranges tread on each
other there is no difference to show, however unequal the medians look. The only thing the index
achieved for certain was taking up **18.0 MB
more**.

That last sentence is not decided by whoever writes it: the script decides it. `medir.py` carries
a function called `distinguishable` that compares the two ranges and returns false when they
overlap, and it is that function which prints the line in the output above. So the verdict comes
out of a run, just like the numbers.

**What it means.** An index exists so you need not look at everything. But this database is
columnar and already stores, for each block of rows, the minimum and maximum value. Asking for
one day, it skips in one go the blocks that cannot contain it. The index arrives late to a job
already done.

Careful with the fine reading: at the scale of thousandths of a second the times bounce, and that
is why they get measured seven times and published with their range. **The exact times in the
block above are from one concrete run and yours will come out similar but not equal.** What holds
between runs is the negative conclusion: the index brings no improvement you can see. Module 21
comes back to this with PostgreSQL, which is not columnar, and there the answer is different.

And the fact that will repeat most in this course: **the same content goes from 208.19 MB to
22.08 MB** purely by changing format. That is module 7 whole, and it is already showing here.

## Watch out

- **The biggest is also the slowest, and that is no coincidence.** The CSV is text: every number
  has to be interpreted character by character on the way in. Taking more space is reading more.
- **One measurement is not a measurement.** Timing once, two runs of the same code reported 203.7
  and 143.8 times between the extremes. With seven repetitions and the median, the number sits
  still. If a difference does not survive repeating the measurement, it does not exist.
- **An index is not free.** It takes disk, it has to be maintained on every write, and it only
  pays when the engine had no other way of skipping what it does not need.
- **The times bounce, and proportionally the one that bounces most is the fastest.** The database
  runs from 0.002 to 0.005 seconds depending on the run: it sits at the floor of what the clock
  resolves, so any spike doubles the measurement. The lake runs from 0.174 to 0.225, and with 212
  folders to open and close that variation is the filesystem, not the data. That is why a
  difference only counts when the two ranges do not touch.
- **None of the four is "the best".** The file is what arrived and it does not get touched. The
  lake is cheap and needs no server. The database is fast and needs somebody to look after it.
  The warehouse is for questions that repeat a great deal.

## Metallurgical bridge

A pulp sample can be kept four ways, and all of them hold the same mineral.

In an unlabelled drum, which is the file: it is all there, and to know anything you have to assay
it whole again. In trays labelled by shift, which is the lake: you go to the shift you care
about. In the laboratory register, which is the database: you look up the sample number and there
it is. And in the monthly grade report, which is the warehouse: somebody already worked out the
averages that get asked for every month.

Nobody throws the trays away because the report exists. Each place answers a different question,
and the report can be rebuilt from the trays, but not the other way round.

## Review

### The difference between a data lake and a data warehouse

The lake keeps the data as it arrived, in files, and serves questions you do not yet know you
will ask. The warehouse keeps the data already prepared for concrete questions that repeat. The
lake is cheap and flexible; the warehouse is fast and rigid. In a serious project they coexist,
and the warehouse gets rebuilt from the lake.

### Why the CSV is at once the biggest and the slowest

Because it is text. The number 8,716 takes five characters and has to be converted to a number
every time it is read. In columnar format it takes a few bytes and is read as is. More size means
more disk reading, and with interpretation work on top of it.

### You put an index in and it did not speed anything up. Was it on the wrong column

No, it was on the right column. It happens that the database is columnar and stores the minimum
and maximum of each block, so it was already skipping the unnecessary part. The
index repeated a job already done and took 18.0 MB on top. In a row based database, like
PostgreSQL, the answer would have been another, and that gets measured in module 21.

### You have 208 MB. Is it worth standing up a database

For 208 MB, almost never. The Parquet lake answers in two tenths of a second with nothing to
install and nothing to maintain. A database starts paying off when several people are writing at
once, or when you need guarantees that two things either both happen or neither does. On speed
alone, at this scale, no.

### Somebody says "we have a data lake" and you see a folder of CSVs. What do you ask

Whether they are in columnar format, whether they are split by some date or key, and who decides
what goes in. A folder of loose CSVs is a box of sheets with an English name on it.

Two things turn a folder into a lake: that questions cost little, and that somebody knows what is
inside.

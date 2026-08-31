---
module: 2
---

## In 30 seconds

- A **table** is a grid: each row a moment, each column a signal.
- A **type** is the promise of what kind of value fits in a column.
- Seven signals on this compressor measure magnitudes. Eight only say yes or no.
- That split is not read off the datasheet: it is counted. A signal with two values is digital.
- Counted, it matches what the datasheet declares. **This time the paper is right.**

## What this module solves

The previous module opened the archive and counted the rows. This one looks inside one.

It sounds elementary and it is not. Almost everything that breaks later is born of an assumption
about what a column holds.

A number written as text. A yes or no treated as a quantity. A date sorted alphabetically.

Three words and that is it: datum, table and type.

## Before the theory: a toy example

One shift of three readings from a flotation cell, jotted in a notebook:

| time | pH | frother | alarm |
|---|---|---|---|
| 08:00 | 10.4 | 12 | no |
| 08:30 | 10.1 | 14 | no |
| 09:00 | 9.8 | 14 | yes |

**That is a table.** Three rows, four columns. Each row is a moment and each column something
measured at all of them.

**Every column has its type**, and looking at it is enough to tell:

- `time` is a **time**. It sorts and subtracts. 09:00 comes after 08:30.
- `pH` is a **number with decimals**. It averages: 10.1.
- `frother` is a **whole number**, in grams per tonne.
- `alarm` only says **yes or no**. It has no decimals and no average. The only thing you can do
  with it is count how many times it said yes.

**Count the distinct values of each column.** `pH` has three, `frother` two, `alarm` two.

And there is the trap this module teaches you to dodge: **`frother` and `alarm` both have two
distinct values, and they are not the same kind of thing**. The frother could have been 13 or 15;
it is a quantity that happened to take two values this shift. The alarm can never be 13.

With three rows, counting distinct values is not enough. With a million and a half, it is.

## Glossary

- **Datum.** A single value. The 10.4 in the first row.
- **Row.** Everything measured at one same instant. Here, one moment of the compressor.
- **Column.** The same signal along time. Also called a field, or a variable.
- **Table.** Rows and columns together, with the promise that every row has the same columns.
- **Type.** What kind of value fits in a column. Text, integer, decimal, date, or yes and no. The
  database uses it to know which operations make sense.
- **Grain.** What one row corresponds to. Here, one ten second reading. It is the question to
  answer before touching any table.
- **Distinct values.** How many different values appear in a column. It is the fastest way to
  guess what type something is when nobody has told you.

## Step by step

### Step 1. Look at a whole row

The compressor leaves one row every ten seconds. That row holds fifteen signals, and all of them
were measured at the same instant.

That last part is not a detail: it is what makes a table a table and not fifteen loose lists. If
the pressure and the current in one row came from different moments, comparing them would mean
nothing.

### Step 2. Ask what kind of thing each column is

The official datasheet says so: seven analogue and eight digital, names and all.

And in the previous module that same datasheet got the number of measurements wrong. So it gets
counted.

### Step 3. Count distinct values

A signal measuring a pressure takes thousands of different values over seven months. A valve that
can only be open or shut takes two. Nothing more is needed to tell them apart.

## The code, in parts

### Step 4. How many distinct values each signal takes

```python
for señal in FICHA:
    distintos, minimo, maximo = con.sql(
        f'SELECT count(DISTINCT "{señal}"), min("{señal}"), max("{señal}") FROM t'
    ).fetchone()
    medido = "digital" if distintos <= 2 else "analógica"
```

```anota
for señal in FICHA | repeats what is inside once per signal in the list
count(DISTINCT col) | counts different values, not rows: if 8 repeats a thousand times, it counts once
f'...' con comillas dobles dentro | the double quotes protect the column name in SQL
distintos <= 2 | the whole rule: two values or fewer, digital
```

```salida
señal              distintos        min        max   ficha       dato
TP2                   5,257      -0.03      10.68   analógica  analógica
TP3                   3,683       0.73      10.30   analógica  analógica
H1                    2,665      -0.04      10.29   analógica  analógica
DV_pressure           2,257      -0.03       9.84   analógica  analógica
Reservoirs            3,682       0.71      10.30   analógica  analógica
Oil_temperature       2,462      15.40      89.05   analógica  analógica
Motor_current         1,809       0.02       9.29   analógica  analógica
COMP                      2       0.00       1.00   digital    digital
DV_eletric                2       0.00       1.00   digital    digital
Towers                    2       0.00       1.00   digital    digital
MPG                       2       0.00       1.00   digital    digital
LPS                       2       0.00       1.00   digital    digital
Pressure_switch           2       0.00       1.00   digital    digital
Oil_level                 2       0.00       1.00   digital    digital
Caudal_impulses           2       0.00       1.00   digital    digital
```

There is no middle ground. The first seven take between one thousand eight hundred and five
thousand values. The last eight take exactly two.

### Step 5. See the difference drawn

{{FIG:fig_m02_analogica_vs_digital}}

The same hour, two signals. Above, the panel pressure, falling slowly, rising sharply when the
compressor starts, and falling again. Below, the intake valve, which only knows how to sit at
zero or at one.

The lower one is drawn in steps and not in straight lines on purpose. A valve does not pass
through the intermediate values: it jumps. Joining it with a ramp would be drawing something the
machine never did.

And there is something you only see by putting them together: **the valve drops to zero exactly
when the pressure rises**. They are the same story told by two sensors.

## The result, measured

**What we expected.** That the measured split would match the datasheet. Or that some signal
would turn up halfway, one of those the documentation calls digital and is really a counter.

**What came out.** **Seven analogue and eight digital**, exactly what the datasheet declares.
Zero mismatches. The digital ones take two values dead on, zero and one, without a single odd
case in 1,516,948 rows.

**What it means.** This time the paper is right, and that deserves saying as plainly as it was
said that module 1's paper was wrong. Checking is not distrusting on principle: it is knowing
what what you are handed is worth. That datasheet is worth more now, because a part of it was
tested and held.

The ranges come out consistent with the machine too. The oil temperature runs from 15.4 to 89.05
degrees, which is a cold start and a hot regime. The motor current reaches 9.29 A, which is the
starting peak the datasheet announced.

## Watch out

- **Counting distinct values is a shortcut, not a definition.** It works with a million and a
  half rows and fails with three, as in the notebook example. A counter that took only two values
  over the measured period would look digital without being it.
- **Zero and one do not always mean the same thing.** In `COMP`, active means air is **not**
  coming in. Reading a one as "on" gets the sense backwards, and no data type catches that error.
- **A yes or no does not average.** The mean of `LPS` is a number that comes out and means
  nothing. What makes sense is counting how many times it said yes, or how long it kept saying it.
- **Grain rules over everything else.** A row here is a ten second reading. As soon as it gets
  grouped by day, a row will be a day, and everything written afterwards has to account for that.
- **`Caudal_impulses` is called a counter and takes two values.** It does not count by
  accumulating: it marks each pulse of air with a one. The name suggests one thing and the data
  does another.

## Metallurgical bridge

A laboratory certificate and a shift sheet are the two tables, and they do not read alike.

On the certificate, the copper grade is a number with decimals: it averages, it compares against
the previous lot, it gets a deviation calculated. On the shift sheet, "mill down" is a yes or a
no: it has no mean, it has accumulated hours and a number of times.

Confusing them is the classic mistake of someone starting with plant data. Asking what the mean
of "mill down" was is not a hard question: it is a question that means nothing, and the database
will hand you a number anyway.

## Review

### What is the grain of a table and why do you always ask for it

It is what one row corresponds to. Here, one ten second reading of every signal at once. You ask
first because it decides which operations make sense: counting rows is counting readings, not
minutes and not failures. When the grain changes, the meaning of everything else changes.

### How do you tell an analogue signal from a digital one with nobody telling you

By counting distinct values. With 1,516,948 rows in front of you, a pressure takes thousands and
a valve takes two. Here the split was clean: from 1,809 values down to 2, with nothing in
between. With few rows the shortcut is worthless, because a quantity may have taken only two
values by chance.

### The datasheet said seven and eight, and seven and eight came out. You wasted your time

No. I know something I did not know before: that in this part the datasheet is reliable. In
module 1 that same datasheet got the number of measurements wrong, so this was not a check for
form's sake. Checking and being right changes what you can rest on that paper later.

### Somebody hands you a CSV where the pH arrives as text. What happens if you do not convert it

It sorts alphabetically and compares wrongly. The text "10.4" goes before "9.8", because one goes
before nine.

Averages will fail or throw an error. And worse: a bad ordering throws no error at all, only a
wrong result with a good face on it.

### On this compressor, a one in COMP means the compressor is working

No, it means the opposite. `COMP` marks the intake valve and it is active when air is **not**
coming in, that is with the compressor stopped or turning offloaded. It is the example of why the
data type is not enough: I know it is a yes or no, and I can still read what it says backwards.

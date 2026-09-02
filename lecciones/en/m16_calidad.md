---
module: 16
---

## In 30 seconds

- A data contract is a list of promises **written as code that runs**.
- You test it by breaking it: five failures of the kind that arrive on any Monday.
- The first version, with **7 promises**, caught **4 of 5**. One got past it entirely.
- With the missing promise there are **8**, and it catches **5 of 5**.
- The missing one: it checked whether the agreed columns were there, not whether one was extra.

## What this module solves

The lake already has three sources and two layers. From here the problem stops being building it
and becomes keeping it working on Monday.

A contract is what turns "this should arrive like so" into something that notices when it stops
arriving like so. And like every gate on this course, **it is worth nothing until you have seen it
fail**.

## Before the theory: a toy example

A laboratory sends you a file every day with the copper grade of each batch:

| batch | grade |
|---|---|
| L1 | 0.8 |
| L2 | 1.2 |
| L3 | 1.0 |

You work out the day's copper by multiplying by the tonnes. **Mean of 1.0 %.**

One Monday this arrives:

| batch | grade |
|---|---|
| L1 | 800 |
| L2 | 1200 |
| L3 | 1000 |

The laboratory changed instrument and now delivers **parts per million** instead of per cent. The
file is perfectly valid: three rows, two columns, correct numbers. Nothing throws an error.

And your report says the ore has a mean grade of **1,000 %**.

Now imagine three promises written before that happened:

1. **The file brings the columns `batch` and `grade`, and no others.**
2. **`grade` is between 0 and 5.**
3. **`batch` does not repeat.**

The second would have broken that Monday and the file would not have come in. That is a contract:
not documentation, but **a condition that blocks the way**.

Look closely at the first promise, because it has a catch and this module tripped over it. It says
two things: that the columns are there, and that there are no others. Checking only half is easy,
and it lets through the day a new column shows up.

## Glossary

- **Data contract.** The set of promises a table keeps, written as code and executed on every run.
- **Promise.** A concrete, checkable condition. "Pressure is in bar" is not one; "TP2 is between
  -2 and 15" is.
- **Data test.** Each individual check in the contract.
- **Schema.** A table's list of columns, with their names and their types.
- **Schema drift.** A schema change with no warning: a column that leaves, another that arrives,
  another renamed.
- **False green.** A check that always passes, even when it should fail. It is worse than having
  none, because it gives confidence.

## Step by step

### Step 1. Write the promises as queries that return zero rows

The trick of shape that makes a contract useful: every promise is a query looking for **the
offenders**. If it returns zero rows, the promise holds.

That way the error message already carries the guilty data inside, instead of a "something is
wrong" that forces you to investigate from scratch.

### Step 2. Run it against the layer of record

Over module 14's silver, the contract has to pass in full. If it does not, the problem is not the
contract's: it is the layer's, and that has to be fixed before going on.

### Step 3. Break it on purpose, five times

And here is what separates this module from a list of good intentions. You take the layer, spoil
it in five different ways, and see how many the contract catches.

All five are real failures of the kind that arrive on a Monday: a renamed column, a changed unit,
a new column, an ingestion that ran twice, and an impossible value.

### Step 4. Look at the one that gets away

Because one did, and that is the lesson of the module.

## The code, in parts

### Step 5. One promise, written

```sql
SELECT timestamp, count(*) AS veces
FROM plata
GROUP BY timestamp
HAVING count(*) > 1;
```

```anota
HAVING count(*) > 1 | keeps the groups with more than one row, meaning the repeated timestamps
```

```salida
┌───────────┬───────┐
│ timestamp │ veces │
├───────────┴───────┤
│      0 filas      │
└───────────────────┘
```

Zero rows means the promise holds. And if one day it returns something, what it returns is
exactly the list of duplicated timestamps, ready to investigate.

### Step 6. The whole contract, and the five breakages

```python
for rotura, sql in ROTURAS.items():
    roto = duckdb.connect()
    roto.execute(f"CREATE VIEW datos AS {sql}")
    cazada = revisa(roto, completo)
```

```anota
ROTURAS | a dictionary of failure name and the query that causes it over a copy
CREATE VIEW datos AS ... | the spoiled copy takes the same name as the good one, so the contract does not change
revisa(roto, completo) | runs the eight promises against that copy and returns the ones that break
```

```salida
  el contrato tiene 8 promesas
  sobre la plata de verdad se incumplen: 0

  y ahora, rompiéndolo a propósito:
    la caza    una columna llega con otro nombre
    la caza    la presion llega en milibares
    la caza    aparece una columna que nadie anuncio   (la primera versión la dejaba pasar)
    la caza    la ingesta corrio dos veces
    la caza    un recuento de lecturas negativo
```

### Step 7. What the incomplete promise said

```sql
SELECT column_name
FROM (DESCRIBE SELECT * FROM plata)
WHERE column_name IN ('timestamp', 'day', 'lecturas', 'medido', 'dudoso');
```

```anota
DESCRIBE SELECT * FROM plata | returns one row per column, with its name and its type
column_name IN (...) | keeps the ones on the agreed list
```

That query counts how many of the agreed columns are present. And there is the hole: **if one
extra column arrives, there are still twenty agreed ones and the count comes out right.**

### Step 8. The missing promise

```sql
SELECT column_name
FROM (DESCRIBE SELECT * FROM plata)
WHERE column_name NOT IN ('timestamp', 'day', 'lecturas', 'medido', 'dudoso');
```

```anota
NOT IN (...) | the other way round: it keeps the ones NOT on the list, meaning the extra ones
```

It is the same query with the condition flipped, and it is what was missing. One looks at what
should be there and the other at what should not.

## The result, measured

{{FIG:fig_m16_contrato_roto}}

**What we expected.** That the contract would catch the five breakages. They were chosen by me,
knowing what the contract checked.

**What came out.** It caught **4 of 5** with its initial **7 promises**. The new column got away.

And the reason is exactly the one the toy example saw coming. The promise said the twenty agreed
columns had to be present, and with one extra column **the twenty are still there**. The check
passes, and the schema has changed.

With the missing promise, "no extra columns arrive", the contract has **8 promises** and catches
**5 of 5**.

The figure shows it at a glance. The column for the "new column" breakage has a single cell lit,
and it is the bottom promise, the one that was not there.

**What it means.** An incomplete contract is not half a contract: it is a **false green**. It
gives the all clear daily and therefore builds confidence, and the day schema drift comes in
through the gap it does not cover, nobody looks.

Hence the rule this project already applies to its own verifiers, now applied to the data: **a
promise nobody has seen fail protects against nothing.** The only way to know whether a contract
is any use is to break the data on purpose and check that it notices.

Look also at the top row of the figure. The renamed column breakage lights four promises, not
one: two because they detect the change and **two because they cannot even run any more**. A query
asking for `TP2` when `TP2` no longer exists does not give a bad result: it gives an error. That
error is contract information too, and that is why it counts as a broken promise rather than
knocking over the whole check.

## Watch out

- **Checking that the columns are there is not checking the schema.** Both halves are needed: what
  is required and what is forbidden.
- **A vague promise is not a promise.** "Pressure is reasonable" cannot be executed. "TP2 is
  between -2 and 15" can, and the range is chosen by looking at the data, like module 9's cuts.
- **The contract is tested by breaking the data, not by rereading it.** It is the same rule as
  this course's verifiers, and it arrived by the same road: one of them had an empty loop and gave
  a green without comparing anything.
- **A promise that cannot run counts as broken.** When a column disappears, the query asking for
  it fails, and that is precisely the news.
- **A contract that is too strict is also a problem.** If it fires every week over things that do
  not matter, somebody will switch it off, and we are back to module 8: an alarm that always
  sounds is not an alarm.
- **The contract lives in the repository, with the code.** A schema document in a shared folder
  goes stale in the first month and nobody notices.

## Metallurgical bridge

A serious laboratory does not deliver a result without its controls. In every batch it puts a
reference sample of known grade, a duplicate of a real sample, and a blank.

If the reference does not land where it should, the whole batch is repeated. The result is not
delivered with a note saying the control came out odd: **it is not delivered**.

That is a data contract, and it has been mandatory in a laboratory for decades while in data
people still argue about whether it is needed. And look at the blank, the sample with nothing in
it: it is there to detect contamination, meaning to catch **what should not appear**. It is
exactly the promise the first version of this contract was missing.

## Review

### What a data contract is and how it differs from documentation

It is a set of checkable conditions that run on every pass and can stop the data getting through.
Documentation describes what should happen and never notices when it stops happening; the
contract fails and halts the process. The practical difference is that one has an exit code and
the other does not.

### Why every promise is written as a query that returns zero rows

Because that way the error carries the evidence inside. A promise returning true or false forces
you to investigate from scratch when it fails; one returning the guilty rows has already told you
which they are. And the shape is always the same, so adding a promise means writing one more
query.

### Your contract has passed every day for a year. Good sign

Not necessarily. The data may be fine, or the contract may check nothing capable of failing. The
only way to tell them apart is to break the data on purpose and see whether it notices. Here, the
first version calmly passed one breakage out of five.

### The missing promise looked trivial. Why did it get away

Because it checked half a condition. It verified the presence of the twenty agreed columns, and
an extra column removes none of the twenty. It is a failure by omission, the kind you do not see
by rereading: what is written is correct, and what is missing is written nowhere.

### What do you do if the contract fails at three in the morning

Nothing automatic. The contract halts the process and leaves the previous data intact, which is
what matters: better a stale dashboard than a dashboard with bad data. Afterwards somebody looks
at which promise broke and which rows were guilty, both of which the contract itself wrote down.

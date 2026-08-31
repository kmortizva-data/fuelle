---
module: 7
---

## In 30 seconds

- CSV stores row after row. Parquet stores each column apart, and that changes everything.
- Asking for one column comes out **54 times** faster in Parquet than in the CSV.
- The advantage **shrinks** when the question uses more columns: from 54 times to **25**.
- A Parquet's weight is not in the rows: the `timestamp` column is **30.4 %** of the file.
- The same 1,516,948 rows take **16.83 MB with 17 columns and 0.03 MB with 2**.

## What this module solves

The previous modules used Parquet without explaining it. Time to justify why, and to do it with
the stopwatch instead of with a list of advantages.

Along the way the rule that decides how much a data file takes shows up, and it is not the one
almost everybody assumes.

## Before the theory: a toy example

Four shifts, with three data each:

| Shift | Tonnes | Grade | Operator |
|---|---|---|---|
| T1 | 100 | 20 | Ana |
| T2 | 200 | 20 | Ana |
| T3 | 300 | 20 | Luis |
| T4 | 400 | 20 | Luis |

**Stored by rows**, which is what a CSV does, the file says:

```
T1,100,20,Ana
T2,200,20,Ana
T3,300,20,Luis
T4,400,20,Luis
```

**Stored by columns**, which is what Parquet does, the same content groups like this:

```
turnos:      T1,T2,T3,T4
toneladas:   100,200,300,400
leyes:       20,20,20,20
operarios:   Ana,Ana,Luis,Luis
```

Now ask: **how many tonnes were processed in total**.

By rows you have to walk the four whole lines and pull the second value out of each. Twelve data
read to use four.

By columns you read only the tonnes line. Four data to use four.

And look at the grades line, which is the same twenty four times over. Stored together, it can be
written as **"twenty, four times"**. Stored by rows, that twenty is spread across four lines and
there is no way to group it.

There are the two advantages of the columnar format. They are the same thing seen twice: **what
sits together gets skipped whole, and what repeats gets written once**.

## Glossary

- **Row format.** Stores one complete record after another. CSV, JSON lines and most traditional
  databases.
- **Columnar format.** Stores all the values of one column together. Parquet, ORC, DuckDB
  internally.
- **Parquet.** The most used columnar format. It is a binary file carrying its own index of what
  is inside and where.
- **Metadata.** Data about the data. In Parquet it includes how much each column takes, how many
  values it has and what its minimum and maximum are.
- **Cardinality.** How many distinct values a column has. It is what decides whether it
  compresses well or badly.
- **Dictionary.** The technique of storing each distinct value once and then only references to
  it. It works well with few distinct values and badly with many.

## Step by step

### Step 1. Ask the same question three times, each with more columns

Three questions, chosen so that only the number of columns needed changes: counting rows, which
needs none; the mean of one column; and the mean of the seven analogue signals.

If the columnar format does what it says, Parquet's advantage has to **shrink** as more columns
get asked for. That slope is what gets measured, and it says far more than a plain "Parquet wins".

### Step 2. Ask the file how much each column weighs

Nothing has to be estimated here. Parquet carries its own accounting written inside, and DuckDB
lets it be queried like one more table.

So the file can be interrogated about itself: how much each column takes, compressed and
uncompressed. That turns an explanation into a measurement.

### Step 3. Remove columns and see what happens to the size

And the experiment that finishes the module. The same number of rows gets written four times,
with fewer columns each time, and the size of the file gets looked at.

## The code, in parts

### Step 4. The same question, in both formats

```sql
SELECT avg(TP2) FROM read_parquet('lake/_formatos/todo.parquet');
```

```anota
avg(TP2) | the mean of the TP2 column, which is the compressor pressure
read_parquet | reads a columnar file, which already carries the types written inside
```

```salida
┌────────────────────┐
│      avg(TP2)      │
│       double       │
├────────────────────┤
│ 1.3678259663489851 │
└────────────────────┘
```

The same question against the CSV is written by changing one word, `read_parquet` for
`read_csv_auto`, and it returns exactly the same number. The only difference is where the data
comes from, and that is precisely what we want to time.

With that question and two others, the benchmark prints this:

```salida
Three questions, two formats, median of 7 runs each.
  question                 CSV   Parquet    factor
  contar_filas          0.552s   0.0043s    128.7x
  una_columna           0.594s   0.0111s     53.6x
  siete_columnas        0.680s   0.0274s     24.8x
```

Look at the CSV column: its three times are nearly equal. It makes no difference what you ask,
because the whole file has to be read and decoded either way.

### Step 5. Ask the file what each column weighs

```sql
SELECT path_in_schema AS columna,
       sum(total_compressed_size)   AS comprimido,
       sum(total_uncompressed_size) AS sin_comprimir
FROM parquet_metadata('lake/_formatos/todo.parquet')
GROUP BY columna
ORDER BY comprimido DESC;
```

```anota
parquet_metadata('...') | opens the file's metadata as if it were a table, without reading the data
path_in_schema | the name of the column inside the file
total_compressed_size | the bytes that column takes already compressed, that is what it really weighs
sum(...) | adds them up, because the file stores one figure per block of rows
ORDER BY comprimido DESC | largest to smallest; DESC is descending
```

```salida
┌─────────────────┬────────────┬───────────────┐
│     columna     │ comprimido │ sin_comprimir │
│     varchar     │   int128   │    int128     │
├─────────────────┼────────────┼───────────────┤
│ timestamp       │    5284726 │      12135987 │
│ Oil_temperature │    1971125 │       2147372 │
│ TP3             │    1944693 │       2223233 │
│ Reservoirs      │    1942403 │       2222913 │
│ H1              │    1804798 │       2162780 │
│ source_index    │    1651898 │      12135987 │
└─────────────────┴────────────┴───────────────┘
```

The file answers in bytes. The script does the division to kilobytes, works out the percentage
and counts the distinct values of each column:

```salida
  column                    KB   % file   distinct
  timestamp             5160.9     30.4  1,516,948
  Oil_temperature       1924.9     11.3      2,462
  TP3                   1899.1     11.2      3,683
  source_index          1613.2      9.5  1,516,948
  Motor_current         1154.1      6.8      1,809
  TP2                    887.5      5.2      5,257
  Towers                  42.3      0.2          2
  COMP                    28.7      0.2          2
  LPS                      1.7      0.0          2
```

That table is the whole module. The two columns that repeat no value are right at the top, and
the digital ones, which are only zero or one, are at the bottom weighing almost nothing.

Look at `timestamp` and `source_index` in the output above. Uncompressed they take the same,
12,135,987 bytes, because both store one number per row. Compressed they are still the two
heaviest, and for the same reason: there is nothing that repeats.

### Step 6. The same rows with fewer columns

```sql
COPY (SELECT CAST(timestamp AS DATE) AS day, COMP FROM read_parquet('...'))
TO 'cols_3.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);
```

```anota
SELECT CAST(timestamp AS DATE) AS day, COMP | keeps two columns: the day and one digital signal
```

```salida
  las 17 columns ->  16.83 MB   la contabilidad predecia 16,985.4 KB, midio 17,235.4 KB
       5 columns ->   9.04 MB   la contabilidad predecia 9,130.3 KB, midio 9,257.0 KB
       4 columns ->   4.00 MB   la contabilidad predecia 3,969.4 KB, midio 4,095.0 KB
       2 columns ->   0.03 MB   la contabilidad predecia 28.7 KB, midio 34.4 KB
```

The number of rows does not change in any of the four. It is always 1,516,948.

## The result, measured

{{FIG:fig_m7_csv_vs_parquet}}

**What we expected.** That Parquet would beat the CSV, and that the advantage would be similar
across the three questions.

**What came out.** It won, and the advantage is **not** similar. With one column it is **54
times**, and with seven it drops to **25 times**. The module's figure is the first, because
asking for a single column is the normal case.

That slope is the definition of columnar, measured. The more columns the question asks for, the
more Parquet resembles reading the whole file, and the less it wins. With all seventeen the
advantage would keep falling.

**And counting rows is left out of that comparison on purpose.** Parquet reads not one datum to
answer it: the number of rows is written in the file's header. So what is compared there is not
two ways of reading, it is reading 208 MB against reading nothing. The factor comes out enormous
and it also **bounces a great deal between runs**: in this one it was **129 times** and in
another it was more than double that. Parquet's side sits at the floor of what the clock
resolves, so that number heads nothing.

**And the result nobody expected.** The same **1,516,948 rows** take **16.83 MB with the 17
columns and 0.03 MB with 2**. Five hundred and sixty one times less, without removing a single
row.

{{FIG:fig_m7_filas_vs_columnas}}

**What it means.** The weight of a data file is not in how many rows it has. It is in **how much
the values of its columns repeat**, and the figure shows it in both its panels at once.

On the left, what each column weighs. On the right, how many distinct values it has. They are
practically the same drawing, and there is the rule.

The `timestamp` column repeats no value: it has 1,516,948 distinct ones in 1,516,948 rows. There
is nothing to group, so they all get stored and it takes **30.4 %** of the file on its own.
`source_index` is in the same position.

The eight digital ones are at the opposite extreme. They are only zero or one, so the file stores
those two values once and then references. `LPS` in full weighs less than two kilobytes.

And a check that this accounting is trustworthy. The script adds up what the four columns of the
ladder's third row weigh and gets **3,969.4 KB**, while that file measures **4,095.0 KB**. The
deviation is **3.1 %** and it is the file's own header. Put another way: the split by columns
predicts the size before writing it.

## Watch out

- **Parquet is not always better.** For appending one row at the end, a CSV is unbeatable.
  Parquet is meant for writing once and reading many times, which is what a lake does.
- **A CSV opens with anything and a Parquet does not.** A tool that reads it is needed. In
  exchange, the CSV does not know what type each column has and it has to be guessed on every
  read.
- **Removing columns is not a compression technique.** It is throwing data away. The lesson's
  ladder serves to understand where the weight comes from, not to publish mutilated files.
- **Cardinality rules over type.** A text column with two distinct values compresses better than
  a number column with a million. What matters is how much it repeats, not whether it is text.
- **The times in the output are from one concrete run.** On another machine they will come out
  different. What holds is the slope: Parquet's advantage shrinks as more columns get asked for.
- **The faster a measurement, the less reliable its factor.** The counting rows one more than
  doubled between runs, because it measures something so short that the machine's noise dominates.
  The other two barely moved.

## Metallurgical bridge

An ore sample can be kept two ways in the core store. Hole by hole, with all its intervals in one
box in order. Or by variable, with all the copper grades of every hole together in one register.

To reconstruct a given hole, the first is convenient. To work out the deposit's mean copper
grade, the second saves you opening every box.

And there is a detail that resembles the digital columns. In a lithology log, the same unit
repeats metre after metre, so it gets noted once with its interval. Nobody writes "schist" four
hundred times in a row. That is exactly what a dictionary does in Parquet.

## Review

### What is the difference between storing by rows and storing by columns

By rows, each record goes complete and the next one follows. By columns, all the values of one
column go together and then the next column starts. The content is the same and what changes is
what has to be read to answer a question.

### Why does Parquet's advantage drop from 54 times to 25

Because the advantage consists of not reading the columns that are not asked for. With a single
column, one seventeenth of the file gets read. Asking for seven of seventeen means reading nearly
half of it already, and the advantage shrinks to what the binary format contributes over text.

### The same rows take 16.83 MB or 0.03 MB. How can that be

Because the weight comes from repetition, not from the row count. The two column version stores
the day and a signal that is only zero or one, and both repeat a great deal, so they compress to
almost nothing. The seventeen column one drags the `timestamp` along, which repeats not one value
and cannot be compressed.

### How do you know what a column weighs without trying things out

By asking the file. Parquet writes its own accounting inside, with the compressed size of each
column in each block, and DuckDB exposes it with `parquet_metadata`. It is not an estimate: it is
the file describing itself.

### If you had to cut the weight of a table, where would you start

By looking at the cardinality of its columns before touching anything. The one that repeats no
values is the one paying for the file, and it is almost always a timestamp or an identifier. From
there the options are concrete: store it with less precision, move it to another table, or keep
it and accept what it costs.

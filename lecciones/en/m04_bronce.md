---
module: 4
---

## In 30 seconds

- The lake is ordered in three layers: **bronze, silver and gold**. This lesson builds the first.
- The bronze rule is one single rule: **it does not clean, it does not fix and it does not interpret**.
- In go 208.19 MB of text and out come **22.05 MB** in 212 folders, one per day.
- The 212 folders are not 212 equal days: the median is **7,437 readings** out of 8,640.
- The only things added are the day column and a receipt of what came in.

## What this module solves

The raw file is untouchable and awkward at the same time: 208 MB of text that has to be read
whole for any question. A copy you can work with, without losing the original, is needed.

That copy is the bronze layer, and its value lies in what it does **not** do.

## Before the theory: a toy example

A shift leaves six pressure readings of the receiver, one every ten minutes:

| Time | Pressure |
|---|---|
| 06:00 | 9.0 |
| 06:10 | 9.0 |
| 06:20 | 8.0 |
| 06:30 | 8.0 |
| 06:40 | 6.0 |
| 06:50 | **-10.0** |

The last one is impossible. A receiver has no negative pressure, let alone ten bar below zero. It
is a sensor that disconnected and wrote its warning value.

**The mean with that reading in is 5.0 bar.** Add the six, thirty, and divide by six.

**The mean without it is 8.0 bar.** Add the five good ones, forty, and divide by five.

Eight is the real pressure of the shift and five is nothing. So the temptation is obvious: delete
the bad row before saving. And there is the mistake this module is about.

If you delete it on the way in, there are three questions you will never be able to answer:

1. **How often that sensor drops out.** You cannot count what you have deleted.
2. **Whether it always drops out at the same hour.** Here it went at the end of the shift. With a
   month of data you would know whether that is chance.
3. **Whether somebody had already fixed it before you.** And in what way.

Bronze keeps the **-10.0**. Silver marks it as missing data and notes why. Gold publishes the
mean of 8.0. Each layer does one thing, and all three go on existing.

## Glossary

- **Layer.** A copy of the data at a different level of treatment. It does not replace the
  previous one: it lives alongside it.
- **Bronze.** The first copy. The data exactly as it arrived, in a workable format.
- **Silver.** The clean data, with the right types and joined to other sources.
- **Gold.** The tables that answer concrete questions, already summarised.
- **Medallion architecture.** The name of this three layer split. It is called that after the
  metals, and it is the usual way of organising a lake.
- **Partition.** Each piece a table is split into, normally one folder per date.
- **Manifest.** A small file beside the data saying what came in and from where.
- **Compression.** Storing the same thing in less space, exploiting what repeats.

## Step by step

### Step 1. Decide what does not get touched

Before writing code it helps to fix the rule, because it is the one that gets broken later out of
convenience. In bronze no decimals get corrected, no gaps get filled and no row gets thrown away.

The odd values of module 1 are still there: the noisy decimals like `-0.0120000000000004` and the
readings every nine seconds. They are a nuisance, and they stay.

### Step 2. Add the minimum needed to work

Bronze adds two things, and only two.

The first is a column with the day, taken from the timestamp. It is not new information: it is
the same date in its own column, and it serves to split the data into folders.

The second is the manifest: a receipt with the name of the source file, its fingerprint and how
many rows it brought. It is what will let module 5 know whether a fresh ingestion is needed.

### Step 3. Store in folders by day

One folder per date, with its file inside. It is the split everybody does, and that is why it
gets done here too.

Worth saying up front: **module 6 measures this split and it turns out to be the worst of the
ones tested.** It is left as is on purpose. First the ordinary mistake gets made and then it gets
measured, which is different from telling it already solved.

## The code, in parts

### Step 4. The three layers, to get your bearings

```diagrama
*CRUDO | El CSV de UCI | 208,19 MB, intocable
*BRONCE | Parquet por día | 22,05 MB, nada se limpia
PLATA | Tipado y unido | aquí sí se arregla, módulo 14
ORO | Tablas de respuesta | listas para preguntar, módulo 17
```

The two lit ones are those that exist by the end of this lesson. The other two arrive in part 4,
and the same diagram will light up as they get built.

### Step 5. Copy the CSV to Parquet, split by day

```sql
COPY (
    SELECT
        "column00" AS source_index,
        * EXCLUDE ("column00"),
        CAST(timestamp AS DATE) AS day
    FROM read_csv_auto('data/MetroPT3(AirCompressor).csv', header = true)
)
TO 'lake/bronze/telemetry'
(FORMAT PARQUET, PARTITION_BY (day), OVERWRITE_OR_IGNORE, COMPRESSION ZSTD);
```

```anota
COPY (...) TO '...' | writes the result of a query into files, instead of showing it on screen
"column00" | the name DuckDB invents for the file's first column, which arrived with no name
AS source_index | gives it a name: it is the original row number, and module 1 used it as the proof of the downsampling
* EXCLUDE ("column00") | every other column but that one, so it does not get repeated
CAST(timestamp AS DATE) AS day | keeps the day part and stores it in its own column
FORMAT PARQUET | the columnar format; module 7 measures why
PARTITION_BY (day) | creates one folder per distinct value of day
OVERWRITE_OR_IGNORE | allows writing over whatever was there
COMPRESSION ZSTD | the algorithm that compresses each column as it is stored
```

A single instruction reads 208 MB of text and leaves 212 folders written.

### Step 6. Check what was left

```sql
SELECT count(*) AS filas,
       count(DISTINCT day) AS carpetas,
       min(day) AS primera,
       max(day) AS ultima
FROM read_parquet('lake/bronze/telemetry/**/*.parquet');
```

```anota
read_parquet('.../**/*.parquet') | reads every file that matches; the two asterisks mean "and in the subfolders"
count(DISTINCT day) | counts distinct values, not rows: how many different days there are
AS filas | names the result column, so it reads better
```

```salida
┌─────────┬──────────┬────────────┬────────────┐
│  filas  │ carpetas │  primera   │   ultima   │
├─────────┼──────────┼────────────┼────────────┤
│ 1516948 │      212 │ 2020-02-01 │ 2020-09-01 │
└─────────┴──────────┴────────────┴────────────┘
```

The same 1,516,948 rows module 1 counted. Not one more and not one less, and that is exactly what
had to happen.

### Step 7. The receipt of what came in

```python
manifest = {
    "source_file": RAW_CSV.name,
    "source_sha256": source_hash,
    "source_bytes": RAW_CSV.stat().st_size,
    "rows": stats["rows"],
    "partitions": stats["partitions"],
}
```

```anota
manifest | a Python dictionary: pairs of name and value, saved as a JSON file
source_sha256 | the fingerprint of the source file, which module 5 explains in full
.stat().st_size | the size of the file in bytes, asked of the system
```

That dictionary gets saved next to the data, not in the code. A fact about the data that travels
in the code is lost the moment somebody copies the folder elsewhere.

## The result, measured

{{FIG:fig_m04_bronce_particiones}}

**What we expected.** A smaller copy and 212 folders of roughly the same size.

**What came out.** The first yes, and then some: **208.19 MB of text get stored in 22.05 MB**
spread over **212 partitions**, that is 9.44 times less with the same content inside.

The second, no. A full day is 8,640 readings, six a minute for twenty four hours. The median of
the 212 folders is **7,437 readings**, 86.1 % of a day. Only **91 days** get past 90 % and there
are **5 days** that do not reach 10 %. The largest folder weighs **16 times** what the smallest
does.

**What it means.** The record has gaps everywhere, and they are not one isolated accident: the
figure shows drops spread across the seven months. That has a practical consequence which will
come back in module 10: **any daily average computed over the 212 days will lie**, because it
mixes whole days with two hour days.

And a design consequence that shows better here than anywhere. Had the ingestion "fixed" the gaps
by filling them, this figure would not exist and nobody would know the problem is there.

## Watch out

- **Bronze is not a backup.** The original is still the original. Bronze is a workable copy, and
  if it gets lost it is regenerated from the CSV.
- **A full day is 8,640 readings in theory, and there are 49 days that pass that figure.** The
  sampling is not exact: module 1 measured nine second gaps, and with them more readings fit into
  a day. A percentage of a day can go past one hundred.
- **The day column is not new data.** It comes from the timestamp that was already there. Adding
  a derived column is allowed in bronze; changing a value that arrived is not.
- **The name of the first column is a detail of the program, not of the file.** DuckDB calls it
  `column00` today and could call it something else tomorrow, so the code reads it instead of
  writing it by hand.
- **Splitting by day is what everybody does and here it comes out badly.** Module 6 measures it.
  It stays this way until then.

## Metallurgical bridge

In a plant laboratory, the head sample is split and a witness portion is kept before anything is
done to it. That witness is not crushed, not dried and not assayed. It is labelled and filed.

It looks like waste until the day a grade does not add up. Then the witness is the only thing
that lets you tell a sampling error from a preparation error from an assay error. Without it, the
argument gets settled by seniority.

Bronze is the witness. The temptation to clean on the way in is the same temptation as drying the
sample before weighing it, and it gets paid for just as late.

## Review

### Why keep dirty data if it has to be cleaned anyway

Because cleaning is a decision and decisions get revised. If the cleaning happens on the way in,
the decision is buried and nobody can revise it or count how many times it was applied. Keeping
the raw data turns cleaning into a visible step that can be changed without asking for the data
again.

### What is the bronze layer allowed to add

Columns derived from what is already there, like the day taken from the timestamp, and metadata
alongside, like the manifest. What is not allowed is changing a value that arrived, filling a gap
or discarding a row.

### The CSV takes 208.19 MB and bronze 22.05. Has something been lost on the way

No. Both forms hold the same 1,516,948 rows and it gets checked by counting. The difference is
the format. Text writes each number as characters and repeats the day's name in every row. The
columnar format stores each column together and compresses what repeats, and module 7 measures it
column by column.

### The folders are not the same size. Is that an ingestion fault

No, it is what is in the source. The ingestion writes one folder for each day appearing in the
file, and the days arrive with gaps. The median is 7,437 readings against the 8,640 of a full
day. That the ingestion respects it is the proof that it is doing its job.

### If the whole lake had to be rebuilt from scratch, what would it take

The original CSV and this script. Nothing else, and that is the proof the layer is well made. If
rebuilding bronze needed something that only exists inside bronze, there would be a datum with no
origin and the lake would stop being reproducible.

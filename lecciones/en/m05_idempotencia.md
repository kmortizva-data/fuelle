---
module: 5
---

## In 30 seconds

- Running the same ingestion three times left **4,550,844 rows** where there were only 1,516,948.
- Nobody warned. No error, no warning, nothing odd in the data.
- The cure is a **fingerprint** of the source, stored beside the data.
- With it, of three runs only **one** did any work, and the count did not move.
- **One byte** of the source was changed and the fingerprint changed in **126 of its 256 bits**.

## What this module solves

An ingestion is going to run twice. Through a retry, through a badly set cron job, because
somebody launched it by hand not knowing it was already launched. It is a matter of time.

This module measures what happens then, and builds the piece that prevents it.

## Before the theory: a toy example

The morning shift leaves three samples with their iron grade:

| Sample | Grade |
|---|---|
| M1 | 10 |
| M2 | 20 |
| M3 | 30 |

You load them into the register. You are not sure it saved, so you load them again. The register
now holds six rows, the three from before and the three repeated.

Look at what happens to each number:

| What you ask | Before | After | Does it show? |
|---|---|---|---|
| How many samples | 3 | 6 | Yes |
| Sum of the grades | 60 | 120 | Yes |
| **Mean grade** | **20** | **20** | **No** |

The mean does not move. Add the six, one hundred and twenty, divide by six, and out comes twenty
again.

That row of the table is the whole module. **The number people look at most is exactly the one
that does not give the duplication away.** You can hold twice the data there is, look at the mean
grade every day, and never find out.

What does blow up is everything that adds. Were those three samples three tonnes processed, the
report would say six. The shift's production would have been doubled without anyone pressing a
key twice on purpose.

## Glossary

- **Idempotent.** Repeatable without changing the result. Pressing a lift button is idempotent:
  the second press does not call it twice.
- **Fingerprint.** A short number computed from a whole file. If the file changes, the
  fingerprint changes. Also called a hash or a digest.
- **SHA-256.** The concrete way of computing that fingerprint used here. It always returns 256
  bits, that is 64 characters, whatever the file measures.
- **Bit.** The smallest unit of information: it is zero or one. A byte is eight bits.
- **Byte.** Roughly what one character of text takes. This course's file has 218,300,507 of them.
- **Manifest.** The small file where the fingerprint is stored beside the data, so it can be
  compared on the next run.
- **Incremental ingestion.** The kind that only brings what is missing, instead of bringing it
  all every time.

## Step by step

### Step 1. Write the naive version on purpose

The first version of any ingestion writes what it reads and asks nothing. It is not badly
written: it is incomplete, and the difference only shows the second time it runs.

Here it gets written that way on purpose, run three times, and counted. Without seeing the fault
happen, this module's rule would be one more warning of the kind that gets read and forgotten.

### Step 2. Count after each run

Three runs of the same ingestion over the same source, counting after each. Were the ingestion
idempotent, the three counts would be equal.

### Step 3. Store the source fingerprint and ask before working

The guarded version asks one question before moving a single datum: **is the source the same as
last time?** It computes the file's fingerprint, compares it with the one it left stored, and if
they match it does nothing.

That fingerprint lives in a file beside the data, not in memory. So the answer survives the end
of the process, the reboot of the machine and the change of computer.

### Step 4. Check that the fingerprint can change

And here is the step almost nobody takes. A fingerprint never seen changing proves nothing: it
could be returning the same value always and the result would be identical.

So the source file gets copied, **one single byte** gets swapped for another, and it gets
computed again. It is the same idea behind this course's verifiers: **a guard never seen failing
does not count**.

## The code, in parts

### Step 5. The naive ingestion, run three times

```python
for run in range(1, 4):
    naive_ingest(con, naive_dir, run)
    print(count(con, naive_dir))
```

```anota
range(1, 4) | the numbers 1, 2 and 3; the last one is not included
naive_ingest(...) | writes the data read into a new file, without looking at whether anything was there
count(...) | counts the rows in the destination folder
```

```salida
  naive    run 1:  1,516,948 rows
  naive    run 2:  3,033,896 rows
  naive    run 3:  4,550,844 rows
```

Three runs, three times the data. And not one error anywhere.

### Step 6. The same ingestion, asking first

```python
def guarded_ingest(con, target, part, source, manifest):
    current = sha256_of(source)
    if manifest.exists():
        seen = json.loads(io.open(manifest, encoding="utf-8").read())
        if seen.get("source_sha256") == current:
            return False
    naive_ingest(con, target, part)
    ...
    return True
```

```anota
sha256_of(source) | computes the fingerprint of the source file, reading it whole
if manifest.exists() | there is only something to compare against if a previous run happened
seen.get("source_sha256") | the fingerprint the previous run left stored
== current | if they are equal, the source has not changed
return False | it leaves without ingesting anything, and reports that it did no work
```

```salida
  guarded  run 1:  1,516,948 rows   ingested
  guarded  run 2:  1,516,948 rows   skipped, source unchanged
  guarded  run 3:  1,516,948 rows   skipped, source unchanged
```

The three runs leave the same count, and the last two did not even open the data.

### Step 7. One byte, and the fingerprint has to notice

```python
with io.open(copy, "r+b") as fh:
    fh.seek(position)
    original_byte = fh.read(1)
    new_byte = b"7" if original_byte != b"7" else b"3"
    fh.seek(position)
    fh.write(new_byte)
```

```anota
"r+b" | opens the file to read and write, in binary mode: raw bytes, not text
fh.seek(position) | places the cursor at that exact position in the file
fh.read(1) | reads a single byte, the one under the cursor
b"7" | a byte with the character 7 inside; the b in front means binary and not text
fh.write(new_byte) | writes over it, without moving anything around it
```

One digit gets swapped for another so the file stays a valid CSV. That is the hard case: a change
no program reading the file would notice.

```salida
  byte 109,150,253 of 218,300,507: '6' -> '7'
  before  db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24
  after   2dd4fd02dd3ae1bcd82933a9ed224952493821edfd368076c0c90466f1681be6
  126 of 256 bits in the hash changed
  the guarded pipeline ingests again: True
```

The two fingerprints look nothing alike, and that is exactly what one is asked for.

## The result, measured

{{FIG:fig_m05_idempotencia}}

**What we expected.** That the naive ingestion would duplicate and that the fingerprint would
prevent it. Both were predictable, and that is why the experiment is worth running: had either
come out differently, there would be a fault to find.

**What came out.** The module's figure is **4,550,844 against 1,516,948**. Three runs of the
unguarded ingestion leave the first number where the source holds the second, that is **3.0
times** the data. With the fingerprint in front, the same three runs leave **1,516,948 rows**,
and only **1 of the 3** did any work.

And the part that makes the above mean something. Changing **one byte** of the file's
**218,300,507**, the fingerprint changed in **126 of its 256 bits**, **49.2 %**. After that
change the guarded ingestion went back to work, and that is what it had to do.

**What it means.** Close to half the bits is exactly what is expected of a healthy fingerprint.
Were a small change to move the fingerprint little, two similar files would have similar
fingerprints, and comparing fingerprints would stop serving as a decision. That one digit changed
midway through a file rewrites half the result is the property that makes all of this useful.

On the cost, which is the reasonable objection: reading 208 MB to compute a fingerprint looks
expensive against not doing it.

```salida
Fingerprinting the source, 7 times...
  sha256 db30ccb4ea402e3c...  0.422 s (from 0.376 to 0.447)  (494 MB/s)
```

Compared with what the whole ingestion costs, the guard does not show. And it avoids reprocessing
everything when there is no need, so most of the time it comes out ahead.

## Watch out

- **Duplication does not catch the eye.** The mean holds, as in the three sample example. What
  breaks is everything that adds or counts, and that tends to be the report, not the dashboard.
- **The fingerprint says whether the file changed, not what changed.** For the what, the data has
  to be compared. Module 18 comes back to this with time travel.
- **Deleting and rewriting is idempotent too**, and it is what `bronze.py` does. It is the
  simplest option and here it is the right one. It stops being right when the data no longer fits
  into a full rewrite, and then this guard is needed.
- **A fingerprint never seen changing proves nothing.** It is the half of the experiment that is
  almost always missing, and it is the half that turns a claim into a check.
- **The fingerprint is stored beside the data, not in the code.** A fact about the data that
  lives in the code disappears the moment somebody copies the folder.

## Metallurgical bridge

In a flotation circuit, the metallurgical balance closes by comparing what goes in with what
comes out. If a shift records the same feed charge twice, the balance throws no error: it simply
gives an impossible recovery, or a perfectly believable and wrong one.

That is why charges are identified by a lot number and not by their content. Two trucks with the
same grade are not the same truck, and the same truck weighed twice is not two trucks. The lot is
what tells one from the other.

The file's fingerprint is that lot number. Without it, the system has no way of knowing whether
what is coming in already came in.

## Review

### What does it mean for a process to be idempotent

That running it several times leaves the same result as running it once. It does not mean
standing still the second time: it means leaving the same thing behind. Deleting and rewriting
meets the definition, and so does skipping the work when the source has not changed.

### How do you detect that a table has duplicate data

By counting, not by averaging. The mean is the first thing looked at and the last to find out,
because duplicating every row leaves the mean exactly as it was. What gives it away are the
counts, the sums and the repeated rows with the same key.

### Why is it not enough to compute the fingerprint and compare it in memory

Because the process ends. The next run is a new process, often on another machine and days later,
and it remembers nothing of the previous one. Storing the fingerprint in a file beside the data
is what makes the comparison still possible tomorrow.

### One byte changed and the fingerprint changed in 126 of 256 bits. Why is that what you want

Because it means the fingerprint keeps no resemblances. Were a small change to produce a similar
fingerprint, two different files could give nearly equal fingerprints and the comparison would
stop being reliable. Close to half the bits changed is what a healthy fingerprint is expected to
do.

### Your ingestion runs nightly over a file that almost never changes. What do you do

Store the fingerprint and compare before working. The ingestion goes on to do nothing most
nights, which is correct when there is nothing new, and it still reacts on the day the file
really changes. The check costs reading the file, and that is a fraction of what processing it
costs.

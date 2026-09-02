---
module: 20
---

## In 30 seconds

- Module 16 wrote promises a script checked. Here the engine enforces them.
- The difference: a contract that **warns** against one that **will not let you write**.
- **12 guards** in place, tested the same way: by attempting **6** impossible writes.
- The database rejects **6 of 6**, each by a different guard and each with its error.
- And before adding a constraint you count who breaks it. That is the challenge.

## What this module solves

Module 19's table accepted anything. Two readings with the same timestamp, a pressure of minus nine
hundred bar, a digital signal holding 2. It all went in without a complaint, exactly as it went
into the Parquet.

Module 16's contract detected those things, but **afterwards**, by running a script. Between the
bad datum arriving and somebody looking, the dashboard has already shown it.

A database can do something a file cannot: **refuse**. This module is how you tell it what is
impossible, and above all how you check that it really refuses.

## Before the theory: a toy example

A weighing book with three columns:

| batch | tonnes | shift |
|---|---|---|
| L1 | 20 | morning |
| L2 | 30 | afternoon |
| L3 | 25 | morning |

Four things should never be writable, and each needs a different guard:

| The impossible | The guard |
|---|---|
| two rows with batch `L1` | the batch is **unique** |
| a row with no tonnes | tonnes **cannot be missing** |
| `-5` tonnes | tonnes are **between 0 and 500** |
| the shift `night`, which does not exist | the shift **comes from the list of shifts** |

Notice that none of the four can be deduced from the data. That tonnes cannot be negative **is not
in the book**: it is in your head, or in the head of whoever installed the weighbridge. Writing the
schema is taking it out of there and putting it where the machine can enforce it.

And there is an order that matters. **Before demanding tonnes be between 0 and 500, look at whether
some row already falls outside.** If there is one at 600, the database will refuse to add the rule
and it will be right: the problem is not the rule, it is the data already inside.

## Glossary

- **Constraint.** A condition the table forces to hold. A write that breaks it does not get in.
- **Primary key.** The column identifying a row. Unique and never empty.
- **Foreign key.** A column that only accepts values existing in another table.
- **`NOT NULL`.** This cell cannot be left empty.
- **`CHECK`.** Any condition at all on the values of the row.
- **Catalogue.** The internal tables where the database keeps what it knows about itself.
  `pg_constraint` and `information_schema` are part of it.
- **Referential integrity.** The formal name for what a foreign key does: no references left
  pointing at something that is not there.

## Step by step

### Step 1. Decide what is impossible

Not what is odd: what is **impossible**. A pressure of 14 bar is odd and can happen; one of minus
nine hundred is not a measurement, it is a fault. The line gets drawn by looking at the data, like
module 9's cuts and module 16's contract ranges.

### Step 2. Write it into the table, with a name

Every guard is named by hand. This is not cosmetic: **the guard's name is the only thing the person
looking at the error at three in the morning will see.** `tp2_en_rango` explains what happened and
`lecturas_tp2_check1` explains nothing.

### Step 3. Add the missing table

A foreign key needs something to point at. `dias` appears, one row per day, and the readings point
at it: **a reading from a day that does not exist stops being writable**.

### Step 4. Attempt six absurdities

And here is the only part that turns this into something checked. Six impossible writes get
attempted, one per kind of guard, and the rejections get counted.

Without this, twelve constraints in the catalogue are twelve good intentions. It is module 16's
rule again, and module 17's, and this course's own verifiers'.

## The code, in parts

### Step 5. The guards, counted by the database itself

```postgres
SELECT conname AS guarda, pg_get_constraintdef(oid) AS dice
FROM pg_constraint
WHERE conrelid = 'lecturas'::regclass AND contype IN ('p', 'f')
ORDER BY conname;
```

```anota
pg_constraint | one of the catalogue tables: what the database knows about its own rules
conrelid = 'lecturas'::regclass | keep the ones belonging to this table
contype IN ('p', 'f') | p for primary key, f for foreign key. There are more letters: c for CHECK
```

```salida
            guarda            |                  dice
------------------------------+------------------------------------------
 el_dia_esta_en_el_calendario | FOREIGN KEY (day) REFERENCES dias(dia)
 lecturas_pk                  | PRIMARY KEY ("timestamp")
(2 rows)
```

I did not tell it: **I asked it**. It is what module 17 does with dbt's map, and for the same
reason: if a tool can describe itself, let it talk.

### Step 6. The schema, where it has authority

```postgres
SELECT count(*) AS guardas
FROM pg_constraint
WHERE conrelid IN ('lecturas'::regclass, 'dias'::regclass);
```

```anota
count(*) | how many guards are in place between the two tables
```

```salida
 guardas
---------
      12
(1 row)
```

Twelve, spread over **13** columns, and **8** of those columns also refuse to be empty.

None of them is new. TP2's range is module 16's contract range, and that the digital signals are
only ever zero or one was module 2's finding.

### Step 7. The six impossible ones

```python
for que, sql in IMPOSIBLES.items():
    try:
        pg.execute(sql)
        pg.commit()
    except psycopg.errors.Error as e:
        pg.rollback()
        resultados.append({"que": que, "guarda": e.diag.constraint_name})
```

```anota
try / except | the write is attempted expecting it to fail. If it does not, the guard is useless
pg.rollback() | essential: in PostgreSQL an error aborts the whole transaction, and without undoing it the next write would fail because of the previous one
e.diag.constraint_name | the name of the guard that fired, which the database returns inside the error
```

```salida
  y ahora, seis escrituras imposibles:
    la rechaza     la misma marca de tiempo dos veces
                   duplicate key value violates unique constraint "lecturas_pk"
    la rechaza     una presion de -900 bar
                   new row for relation "lecturas" violates check constraint "tp2_en_rango"
    la rechaza     una casilla sin decir si se midio
                   null value in column "medido" of relation "lecturas" violates not-null constraint
    la rechaza     una digital que vale 2
                   new row for relation "lecturas" violates check constraint "comp_es_binaria"
    la rechaza     una lectura de un dia que no existe
                   insert or update on table "lecturas" violates foreign key constraint "el_dia_esta_en_el_calendario"
    la rechaza     un dia con 30 horas de carga
                   new row for relation "dias" violates check constraint "horas_de_un_dia"
```

Six attempts, six doors in the face, **and each one says why**. Compare that with module 16, where
the same bad datum went in and a script found it later.

### Step 8. What to do before adding a rule

```sql-vivo
SELECT count(*) AS incumplen,
       round(count(*) * 100.0 / (SELECT count(*) FROM telemetria), 2) AS por_ciento
FROM telemetria
WHERE DV_eletric = COMP;
```

```anota
DV_eletric = COMP | the two signals are opposites by design, so here they hold the same value and that is impossible
la subconsulta | the total number of readings, so the percentage can be worked out. It is module 11's
```

```salida
┌───────────┬────────────┐
│ incumplen │ por_ciento │
│   int64   │   double   │
├───────────┼────────────┤
│     16762 │        1.1 │
└───────────┴────────────┘
```

**16,762 readings would break a constraint saying those two signals are opposites.** So that
constraint cannot be added, and the database would be right to refuse. Module 14 chose to flag them
with the `dudoso` column instead of deleting them, and this is the consequence of that decision.

## The result, measured

{{FIG:fig_m20_esquema}}

**What we expected.** That the database would reject all six, because I chose all six knowing which
guards I had put in.

**What came out.** It rejects **6 of 6**, and along the way there was a stumble that teaches more
than the result. The fifth write was a reading dated **29 February 2020**, a day module 13 reported
missing. It was rejected by **the primary key rather than the foreign key**.

Which means that day does exist in silver. And of course it does: module 14 put the data on a
regular grid, and **the grid created rows for the holes**. In bronze 29 February was absent; in
silver it is there, with `medido` false and everything else empty.

That is also why the `dias` table has **214** days where module 19 counted 212: that one counted
only days with real readings. The fifth test's absurdity had to move to 2019, which really is
outside the record.

The figure shows the spread, and it is not drawn by hand: it comes from `pg_constraint` and
`information_schema`, meaning from what the database says about itself.

**What it means.** A schema is not documentation or decoration: it is the only layer that can say
no.

Module 16's contract is still needed, because there are promises that do not fit in a constraint.
But whatever does fit **belongs** here, where it does not depend on somebody remembering to run a
script.

## Watch out

- **A guard nobody has seen refuse anything protects nothing.** Twelve constraints in the catalogue
  are twelve assertions until something impossible is attempted.
- **Name every one of them.** With no name, PostgreSQL invents one and appends suffixes when the
  table is recreated. And in the error, the name is all anybody reads.
- **Before adding a constraint, count who breaks it.** If rows already fail it, the database will
  refuse to add it. That count is the challenge below.
- **A `CHECK` cannot look at other rows.** It only sees the row being written. "The timestamp does
  not repeat" needs a key, not a `CHECK`.
- **A foreign key demands the table it points at goes first.** That is why `dias` is filled first,
  and why deleting it forces deleting what points at it.
- **Constraints cost on write.** Every row gets checked. It does not matter on a daily load and it
  shows when millions of rows are inserted one at a time.

## Metallurgical bridge

A truck weighbridge has stops. Not a sign saying how much a truck weighs: **physical stops**, a
load cell range outside which it gives no reading, a minimum tare, a maximum that raises an alarm.

Nobody reads that as distrust of the operator. It is that a truck of minus five tonnes is not a
badly weighed truck: it is a broken sensor, and accepting that number contaminates the whole
month's balance.

And there is something else, which is the uncomfortable part. When those stops get installed in a
plant that has been running for years, **they almost always fire on historical data**. That is when
somebody discovers impossible weighings have been coming in for a year and nobody had looked.

## Do it yourself

```reto
pregunta: Before adding a constraint you have to know who would break it. Return the five days with the most readings where `DV_eletric` and `COMP` hold the same value, with `day` and `lecturas`, largest first. Five rows.
inicio: SELECT day, count(*) AS lecturas
FROM telemetria
GROUP BY day;
esperado: m20_quien_la_rompe
pista: The starting point is missing the filter and the ordering. The filter is the impossible condition, `DV_eletric = COMP`, and it goes in a `WHERE` before grouping. Then you order by the count downwards and ask for five.
solucion: SELECT day, count(*) AS lecturas
FROM telemetria
WHERE DV_eletric = COMP
GROUP BY day
ORDER BY lecturas DESC
LIMIT 5;
```

One day takes nearly a third of all the violations. That is not noise spread evenly: it is a
specific episode, and it is a better lead than the total. Before deciding what to do with those
readings, it is worth going to look at what happened that day.

## Review

### How this differs from module 16's contract

In who enforces it and when. The contract is a script that looks at the data after it is written
and warns. The schema is the engine refusing to write it. One detects and the other prevents, and
both are needed: some promises do not fit in a constraint.

### Why every constraint gets a name

Because the name travels inside the error message, and that message is what the person on call
sees. With no name PostgreSQL generates one and also appends suffixes when the table is recreated,
so the one showing up in an alert may not be last week's.

### What to check before adding a constraint to a table that already has data

How many rows already break it. The database scans the whole table before accepting the rule and
refuses if it finds a single one that does not fit. Here, demanding `DV_eletric` and `COMP` be
opposites would collide with 16,762 readings.

### The dias table has 214 days and module 19 counted 212. Which one is lying

Neither. Module 19 counted days with real readings, and `dias` counts every calendar day silver
covers. The difference is the two days with no record, which exist as empty rows ever since module
14 put the data on a regular grid.

### Your foreign key rejects a row you believe is correct. What do you look at first

The table it points at, not the one you are writing. A foreign key only fails when the value does
not exist on the other side. The question is not whether the datum is right: it is whether the day,
the machine or the batch it points at was ever registered. Almost always the row above is missing,
rather than the row below being wrong.

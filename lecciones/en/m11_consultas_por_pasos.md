---
module: 11
---

## In 30 seconds

- A query with a query inside reads from the inside out, and that costs.
- `WITH` gives **each step a name** and the query reads top to bottom.
- Module 10's splits into **2 named steps**: days, and complete days.
- Both versions return the **same 7 rows**, checked row by row.
- And they take the same time: **their ranges overlap**. Writing it readably costs nothing.

## What this module solves

Module 10 ended with a query that has another one inside. It works, and it has to be read from
the inside out, which is not how anybody reads.

This module rewrites it to read in the order it is thought, and checks that the rewrite changes
neither the result nor the time.

## Before the theory: a toy example

Work out a circuit's recovery from this data:

| Stream | Tonnes | Copper grade |
|---|---|---|
| Feed | 100 | 2 % |
| Concentrate | 10 | 18 % |

Do it two ways.

**All at once**, the way a subquery gets written:

> Recovery is ten times eighteen over a hundred divided by a hundred times two over a hundred,
> times a hundred.

Read that sentence again. It is correct and it is unreadable, and checking it means unpicking it
from the middle outwards.

**Step by step, with names:**

1. **Copper in** = 100 × 2 % = **2 t**
2. **Copper out** = 10 × 18 % = **1.8 t**
3. **Recovery** = 1.8 / 2 = **90 %**

The same calculation, the same numbers and the same result. The only thing that changed is that
each step now has a name and can be checked on its own.

If somebody doubts the 90 %, in the second version you can ask about step 1 and look at it. In
the first you have to redo the whole thing.

That is exactly what `WITH` does to a query.

## Glossary

- **Subquery.** A query written inside another, in parentheses. The inner one resolves first and
  the outer one works on its result.
- **`WITH`.** How you pull those queries out and put them first, each with a name.
- **CTE.** The technical name for each step of a `WITH`, from "common table expression". It comes
  up a lot in job ads and it means that: a named step.
- **Chaining.** When one step of the `WITH` uses the previous one, like a calculation that
  accumulates.
- **Execution plan.** What the database actually decides to do to answer. It need not resemble
  how the query is written.

## Step by step

### Step 1. Look at module 10's query and see where it splits

That query did two things: first work out each day's loaded hours, then average them by month
keeping only the complete days.

Two things, two steps. There is the cut.

### Step 2. Pull each step out and name it

What was in parentheses after the `FROM` moves up top, with `WITH`, and with a name saying what
it is. Then the main query uses it like one more table.

### Step 3. Check it says the same thing

And this is not eyeballed. Both get run, the rows get compared one by one, and only then does the
old version get thrown away.

### Step 4. Check it does not cost more

The standing objection to `WITH` is speed: it looks like it stores intermediate results, so it
ought to come out slower. Both get timed with the median of seven and the ranges get compared.

## The code, in parts

### Step 5. Module 10's version, with the query inside

```sql
SELECT strftime(day, '%Y-%m') AS mes,
       round(avg(horas), 2)   AS horas_de_carga
FROM (
    SELECT day,
           count(*) AS lecturas,
           sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas
    FROM telemetria
    GROUP BY day
)
WHERE lecturas > 0.9 * 8640
GROUP BY mes
ORDER BY mes;
```

```anota
FROM ( ... ) | instead of a table, a whole query goes in parentheses
strftime(day, '%Y-%m') | takes the year and month out of a date, as text
lecturas > 0.9 * 8640 | keeps the days holding at least 90 % of a full day's readings
```

To understand it you have to start at the parenthesis, on line four, and then come back up. And
the `lecturas` column the `WHERE` filters on is declared nowhere visible: it is born inside the
parenthesis.

### Step 6. The same question, in steps

```sql-vivo
WITH por_dia AS (
    SELECT day,
           count(*) AS lecturas,
           sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas
    FROM telemetria
    GROUP BY day
),
dias_completos AS (
    SELECT * FROM por_dia WHERE lecturas > 0.9 * 8640
)
SELECT strftime(day, '%Y-%m') AS mes,
       round(avg(horas), 2)   AS horas_de_carga
FROM dias_completos
GROUP BY mes
ORDER BY mes;
```

```anota
WITH nombre AS ( ... ) | defines a named step, usable further down like a table
, | separates one step from the next; the last one carries no comma
FROM por_dia | the second step uses the first by name, without repeating its code
FROM dias_completos | and the final query uses the second
```

```salida
┌─────────┬────────────────┐
│   mes   │ horas_de_carga │
├─────────┼────────────────┤
│ 2020-02 │           1.45 │
│ 2020-03 │           3.58 │
│ 2020-04 │           4.27 │
│ 2020-05 │           3.61 │
│ 2020-06 │           4.02 │
│ 2020-07 │           3.78 │
│ 2020-08 │           2.81 │
└─────────┴────────────────┘
```

Now it reads top to bottom: first per day, then only the complete days, then the monthly average.
It is the order the question was thought in.

### Step 7. The two steps, drawn

```diagrama
*POR_DIA | Las horas de carga de cada día | 212 filas, una por día
*DIAS_COMPLETOS | Solo los que pasan del 90 % | 91 filas
CONSULTA FINAL | El promedio de cada mes | 7 filas
```

Each box can be queried on its own while writing, by swapping the final `SELECT` for
`SELECT * FROM por_dia`. That is what turns writing SQL into something debuggable.

## The result, measured

**What we expected.** That both versions would give the same thing, and that the `WITH` one would
be somewhat slower for storing intermediate results.

**What came out.** The same, yes: both return **7 rows**, identical, compared one by one and not
at a glance.

And the second, no. The two versions **do not separate in time**: their ranges overlap, so as far
as this machine goes they take the same.

```salida
  las dos devuelven 7 filas y son iguales: True
  anidada:   0.023 s (from 0.019 to 0.031)
  con WITH:  0.021 s (from 0.019 to 0.022)
  ¿se distinguen en tiempo? False
  la version con WITH define 2 pasos con nombre
  lineas: 12 anidada contra 15 con WITH
```

**What it means.** The reason everybody gives for not using `WITH` is speed. It does not lose any
here, and the reason is that **the database does not execute the query as written**. It reads it
whole, decides its own plan, and arrives at the same place by both routes.

So choosing between one form and the other is not a performance decision. It is a decision about
who is going to read that in six months.

The real cost is **3 more lines**, from 12 to 15. That is the entire price.

## Watch out

- **`WITH` is not a temporary table.** It stores nothing on disk and leaves no trace. It is a name
  for a step, and it disappears when the query ends.
- **A step can use the previous one, not the other way round.** They read in order, top to bottom,
  the way they are written.
- **The comma goes between steps and not after the last one.** It is the commonest syntax error
  when starting with `WITH`, and the error message helps not at all.
- **That it costs nothing here does not mean it never costs.** With large volumes and a step used
  several times, some engines recompute it each time. The way to know is the usual one: measure
  with the ranges, do not assume.
- **Name the steps by what they hold, not by what they do.** `dias_completos` says what is inside;
  `paso2` says nothing and `filtrar_datos` says even less.

## Metallurgical bridge

A metallurgical balance never gets handed over as one giant formula. It gets handed over as a
table with its rows: feed, concentrate, tailings, and then the recoveries worked out from them.

That is not for looks. It is because when the balance does not close, you have to be able to
point at which row the problem is in. With a single formula all you can say is that the result
looks odd.

`WITH` is that table of intermediate rows. And as with the balance, what you gain is not speed:
it is being able to point at where the fault is when there is one.

## Do it yourself

```reto
pregunta: Rewrite step 5's nested query with `WITH`, in two named steps, and check it returns the same 7 rows with the columns `mes` and `horas_de_carga`.
inicio: SELECT strftime(day, '%Y-%m') AS mes,
       round(avg(horas), 2)   AS horas_de_carga
FROM (
    SELECT day,
           count(*) AS lecturas,
           sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas
    FROM telemetria
    GROUP BY day
)
WHERE lecturas > 0.9 * 8640
GROUP BY mes
ORDER BY mes;
esperado: m11_con_with
pista: What sits in parentheses after the `FROM` is the first step: pull it up top with `WITH por_dia AS ( ... )`. The `WHERE` that came after the parenthesis is the second step: `dias_completos AS (SELECT * FROM por_dia WHERE ...)`. And the final query keeps the `SELECT` from the top, swapping the parenthesis for `FROM dias_completos`.
solucion: WITH por_dia AS (
    SELECT day,
           count(*) AS lecturas,
           sum(CASE WHEN DV_eletric = 1 THEN 1 ELSE 0 END) * 10 / 3600.0 AS horas
    FROM telemetria
    GROUP BY day
),
dias_completos AS (
    SELECT * FROM por_dia WHERE lecturas > 0.9 * 8640
)
SELECT strftime(day, '%Y-%m') AS mes,
       round(avg(horas), 2)   AS horas_de_carga
FROM dias_completos
GROUP BY mes
ORDER BY mes;
```

## Review

### What a CTE is and why it appears in so many job ads

It is a named step inside a query, what gets written with `WITH`. It appears in the ads because
it marks the difference between a query another person can maintain and one that has to be
rewritten from scratch. In teams where more people read the SQL than wrote it, that is worth more
than any performance trick.

### Is using WITH slower than nesting subqueries

Not here, and it is measured: the two versions' ranges overlap, so they do not separate. The
reason is that the database does not execute what is written but its own plan, and for both forms
it reaches the same one. In other engines and at larger volumes it may not be so, and then you
measure it the way it was measured here.

### Then why rewrite it, if the result and the time are the same

Because it reads in the order it is thought. The nested version forces you to start in the middle
and work outwards, and it hides the `lecturas` column, which is born inside the parenthesis and
used outside it. The stepped version reads top to bottom and each step can be queried on its own
while writing.

### How do you debug a long query giving an odd result

By splitting it into named steps and looking at each. With `WITH`, swapping the final `SELECT`
for `SELECT * FROM whichever_step` shows what comes out of there. With nested subqueries you have
to dismantle the query by hand to get the same.

### What names do you give the steps

The ones that say what is inside, not what the step does. `dias_completos` says the complete days
are in there, and that is what the reader of the line below needs to know. `paso2` and
`datos_filtrados` force you to go up and read the code to understand the main query.

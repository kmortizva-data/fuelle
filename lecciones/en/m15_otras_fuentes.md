---
module: 15
---

## In 30 seconds

- The compressor takes air from the street, so the weather is part of its physics.
- Three sources with three rhythms: every **10 s**, every **hour** and **when something breaks**.
- Crossing them forces everything down to the slowest rhythm, losing detail on purpose.
- The street explains oil temperature with **0.529**, and compressor load with **0.432**.
- Which means **the weather outside weighs more than the machine's own work**. Nobody expected that.

## What this module solves

Until now the lake had a single big table. A lake with one table is not a lake: it is a file with
pretensions.

This module brings in the other two sources and, above all, solves the problem they carry: **they
do not beat at the same rhythm**. And along the way it answers whether the weather adds anything
or is decoration.

## Before the theory: a toy example

Two records from the same morning. The plant's, every ten minutes:

| time | tonnes |
|---|---|
| 08:00 | 20 |
| 08:10 | 30 |
| 08:20 | 40 |
| 08:30 | 30 |

And the laboratory's, which assays a sample every half hour:

| time | grade |
|---|---|
| 08:00 | 2 |
| 08:30 | 4 |

**Question: how much copper came in between 08:00 and 08:30.**

You have four weighings and two grades. They cannot be multiplied row by row because there are
not the same rows. A decision is needed, and there are three defensible answers:

**One: the 08:00 grade holds for the whole half hour.** That gives 90 tonnes at 2 %, so **1.8 t of
copper**. It is what a laboratory does: the sample represents the period it starts.

**Two: average the two grades.** 90 tonnes at 3 %, **2.7 t**. It sounds fairer and it assumes the
grade changed smoothly, which may be false.

**Three: bring everything up to the half hour.** 90 tonnes at a mean grade of 3 %, which is the
same as two but having thrown away the detail of the weighings on purpose.

None is the right one. **The right one is the one you declare.** Crossing sources of different
rhythms always forces a decision like this, and the mistake is not choosing badly: it is choosing
without noticing.

## Glossary

- **Source.** A data origin with its own owner, its own format and its own rhythm.
- **Frequency.** How often a datum arrives. There are three here: ten seconds, one hour, and per
  event.
- **Grain.** What one row corresponds to, from module 2. Crossing two sources means deciding which
  grain you work at.
- **Bring down to the common grain.** Summarise the fast source to the slow one's rhythm. Detail
  is lost, and that is why it is a decision.
- **API.** An internet address that returns data instead of a page. The weather one is free and
  asks for no key.
- **UTC.** Universal time, with no seasonal changes. Everything is asked for and stored that way.

## Step by step

### Step 1. Fetch Porto's weather, once

Open-Meteo's historical archive is free, asks for no key and carries the same licence as the
compressor. You ask for the whole period, save the JSON, and later runs read the file.

Asking again every time would be rude to somebody else's service and fragile for the project: the
result would depend on it being up today.

### Step 2. Ask for everything in UTC

The compressor's telemetry comes in UTC. If the weather arrived in Porto local time, the join
would be an hour off in summer and neither file would say so.

### Step 3. Bring in the four failure reports with their errata

The third source is four hand written rows. The text dates get turned into real dates and the
duration gets computed, which is all bronze may do. The two `#1`, the `Air leak` against `Air
Leak` and the maintenance dated a month early all stay exactly as they are.

### Step 4. Bring the telemetry down to the weather's rhythm

And here is the module's decision. Telemetry gives 360 readings an hour and the weather gives
one. To cross them, the telemetry gets summarised into hourly means.

Everything that happens inside the hour is lost, the compressor's cycles included. It is done
knowingly, because the question being asked is an hourly one, not a per second one.

## The code, in parts

### Step 5. The three sources, and what each one gives

```diagrama
*TELEMETRY | Every 10 seconds | 1,516,948 rows
*WEATHER | Every hour | 5,136 rows
*FAILURES | When something breaks | 4 rows
```

Three hundred and twenty thousand times more rows in the first than in the last. That
disproportion is normal and it is what makes crossing them a problem.

### Step 6. The two tables, before touching them

```sql-vivo
SELECT * FROM clima ORDER BY hora LIMIT 3;
```

```anota
FROM clima | the Porto weather table, one row per hour
```

```salida
┌─────────────────────┬──────────────┬─────────┬──────────────┐
│        hora         │ temperatura  │ humedad │    lluvia    │
│      timestamp      │ decimal(3,1) │  int32  │ decimal(2,1) │
├─────────────────────┼──────────────┼─────────┼──────────────┤
│ 2020-02-01 00:00:00 │         14.2 │      96 │          0.5 │
│ 2020-02-01 01:00:00 │         14.4 │      97 │          0.5 │
│ 2020-02-01 02:00:00 │         14.3 │      98 │          0.3 │
└─────────────────────┴──────────────┴─────────┴──────────────┘
```

Look at `temperatura`'s type: **decimal**, not double. The API delivers an exact decimal, so
module 9's trap does not apply here. Every source brings its own types.

### Step 7. The telemetry, already brought down to the hour

```sql-vivo
SELECT * FROM horas ORDER BY hora LIMIT 3;
```

```anota
FROM horas | the telemetry summarised into hourly means, with 360 readings behind each row
carga | the fraction of the hour the compressor spent loaded, from 0 to 1
lecturas | how many readings that hour had, so you do not trust a mean built from four
```

```salida
┌─────────────────────┬────────┬────────┬──────────┐
│        hora         │ aceite │ carga  │ lecturas │
│      timestamp      │ double │ double │  int64   │
├─────────────────────┼────────┼────────┼──────────┤
│ 2020-02-01 00:00:00 │   51.9 │ 0.0583 │      360 │
│ 2020-02-01 01:00:00 │  51.91 │ 0.0278 │      360 │
│ 2020-02-01 02:00:00 │  51.71 │ 0.0556 │      360 │
└─────────────────────┴────────┴────────┴──────────┘
```

The `lecturas` column is not decoration. An hour with 360 readings and one with 12 both give a
mean, and only one of the two deserves trust.

### Step 8. Cross them, and ask who explains the oil

```sql-vivo
SELECT count(*) AS horas,
       round(corr(c.temperatura, h.aceite), 3) AS calle_aceite,
       round(corr(h.carga, h.aceite), 3)       AS carga_aceite,
       round(avg(h.aceite - c.temperatura), 1) AS grados_por_encima
FROM horas h
JOIN clima c ON c.hora = h.hora;
```

```anota
corr(a, b) | the correlation between two columns: 1 means they move together completely, 0 means they have nothing to do with each other
ON c.hora = h.hora | now it really is an equality, because both tables are at the same grain
avg(h.aceite - c.temperatura) | how many degrees separate the oil from the street on average
```

```salida
┌───────┬──────────────┬──────────────┬───────────────────┐
│ horas │ calle_aceite │ carga_aceite │ grados_por_encima │
├───────┼──────────────┼──────────────┼───────────────────┤
│  4416 │        0.529 │        0.432 │              46.0 │
└───────┴──────────────┴──────────────┴───────────────────┘
```

## The result, measured

{{FIG:fig_m15_tres_frecuencias}}

**What we expected.** That the weather would be context, nice to have and not very informative. A
compressor's oil temperature is set by the compressor.

**What came out.** The opposite. Street temperature explains the oil with a correlation of
**0.529**, and the compressor's own load with **0.432**. **The weather outside weighs more than
the machine's work.**

The oil runs **46.0 degrees** above the street on average, and that jump is the compressor. What
governs the rest is where it starts from.

The figure shows the day of failure #3 with all three sources at once. And there is something in
it I was not looking for. **The oil stops cycling and goes flat exactly at 10:00**, at a mean of
75.7 degrees, and that is the exact hour the report begins.

That is the same thing module 13 measured by another route. With the leak, the compressor never
gets to stop, so the oil does not cool between cycles.

**What it means.** A twin predicting oil temperature without looking at the street thermometer
will be wrong systematically, and worse: it will be **more wrong in summer**. It would credit the
machine with an effect the weather produces, and that is a false alarm factory.

And on the disproportion between the sources, the practical lesson. **4 rows of failures are worth
as much as 1,516,948 of telemetry**, because they are the only ones saying what actually happened.
The size of a source says nothing about its value.

## Watch out

- **Crossing sources of different rhythms always loses detail.** Bringing telemetry down to hourly
  means throws away the compressor's cycles. It is done knowingly, not carelessly.
- **The time zone is asked for, not assumed.** Everything goes in UTC. A join an hour off works
  perfectly and gives results that look good.
- **An hourly mean built from 12 readings is not worth one built from 360.** That is why the
  `lecturas` column travels with the data, just like module 14's `medido`.
- **Correlation is not cause.** The street and the oil rising together does not prove one moves
  the other, even though the physics backs it here: the compressor breathes street air.
- **A source you do not control can vanish.** The weather JSON is saved in `data/` and read back
  from there. If the API changes tomorrow, the project still reproduces.
- **The reports keep their errata.** What gets added here is types and duration, both derived from
  what is there. Not one capital letter corrected.

## Metallurgical bridge

A plant balance crosses three records that never beat alike. The weighbridge weighs truck by
truck, the laboratory assays one composite per shift, and the maintenance report appears when
something breaks.

Nobody tries to cross them by the second. The shift is chosen as the common grain, its tonnes get
added and the composite's grade gets applied. Inside the shift the grade varied, and that
variation has been lost knowingly.

What separates a serious balance from an improvised one is not avoiding that loss, which is
unavoidable. It is having written down which grain was chosen and why.

## Do it yourself

```reto
pregunta: Split the hours into three bands by street temperature, below 10 degrees, 10 to 20 and above 20, and return `calle`, `horas` and `aceite_medio` with the mean oil temperature in each band. Three rows.
inicio: SELECT count(*) AS horas,
       round(avg(h.aceite), 1) AS aceite_medio
FROM horas h
JOIN clima c ON c.hora = h.hora;
esperado: m15_aceite_por_tramo
pista: The join in the starting point is already right. What is missing is the column that splits, and it is a `CASE` like module 9's, but over `c.temperatura` instead of over the current. Then you group by that new column. Name the bands starting with a letter, `a.`, `b.` and `c.`, so `ORDER BY` brings them out in order.
solucion: SELECT CASE WHEN c.temperatura < 10 THEN 'a. menos de 10'
            WHEN c.temperatura < 20 THEN 'b. de 10 a 20'
            ELSE 'c. mas de 20' END AS calle,
       count(*) AS horas,
       round(avg(h.aceite), 1) AS aceite_medio
FROM horas h
JOIN clima c ON c.hora = h.hora
GROUP BY calle
ORDER BY calle;
```

## Review

### Why bring weather into a project about a compressor

Because the compressor breathes street air, so the temperature and humidity outside are boundary
conditions of its physics. And because it is measured: the street explains oil temperature better
than the compressor's own load, 0.529 against 0.432.

### What has to be decided when crossing two sources of different frequency

Which grain you work at. The fast source has to be summarised down to the slow one's rhythm, and
that throws away detail. Here the compressor's cycles inside each hour are lost. The right
decision is the declared one, because the expensive mistake is crossing them without realising a
choice was made.

### You ask an API that is not yours for data. What precautions do you take

Save the raw response to disk and read it back from there, so you neither depend on the service
being up nor ask it the same thing daily. Always ask for the same time zone, in UTC. And record
the licence and the citation, which here is CC BY 4.0 just like the compressor's.

### Four rows of failures against 1,516,948 of telemetry. Is that table any use

It is the most valuable of the three. Telemetry says what the machine was doing and only the
reports say when it was broken, which is the only thing any detector can be validated against.
The size of a source says nothing about its value.

### What would happen to a twin that ignored the weather

It would be more wrong in summer than in winter. It would predict oil temperature counting only
on the machine's work. The difference between a January street and an August one would be
credited to the compressor, and a detector built on that would fire false alarms in the heat.

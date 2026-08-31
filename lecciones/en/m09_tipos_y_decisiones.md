---
module: 9
---

## In 30 seconds

- Asking for `TP2 = 8.2` finds **107 readings**. The ones you meant were **5,237**.
- It fails not by finding nothing: it fails by finding **2 %** and looking fine.
- The number is not to blame, the **type** is. In DECIMAL it comes out exact, in DOUBLE it does not.
- `CASE` translates a number into a state, turning current into stopped, offloaded or loaded.
- The compressor spends **54.6 % stopped, 30.1 % offloaded and 15.2 % loaded**.

## What this module solves

Until now the columns were numbers and that was that. This module looks at what **type** each one
has, because the type decides how they compare and when they lie.

And then it builds the course's first rule: turning a continuous measurement into a named state.
That is what makes raw data useful.

## Before the theory: a toy example

Six readings from a shift, as the screen shows them:

| time | pressure | current |
|---|---|---|
| 06:00 | 8.20 | 0 |
| 06:10 | 8.20 | 0 |
| 06:20 | 8.15 | 4 |
| 06:30 | 8.20 | 4 |
| 06:40 | 8.31 | 6 |
| 06:50 | 8.15 | 6 |

**First question: how many times was the pressure exactly 8.20?** You count and get **three**.

Now look at what the sensor actually measured, which carries one more decimal:

| time | what the screen shows | what is stored |
|---|---|---|
| 06:00 | 8.20 | 8.202 |
| 06:10 | 8.20 | 8.200 |
| 06:30 | 8.20 | 8.198 |

Asking for the exact value, **the computer finds one, not three**. The other two are not 8.2:
they are 8.202 and 8.198, and the screen was showing them as equal because it only had room for
two decimals.

And there is the dangerous part: no error, and one is a perfectly believable number.

The screen rounds. The comparison does not. That sentence is half the module.

**Second question: what state was the motor in on each row?** With the rule that under 1 A is
stopped, 1 to 5 A is offloaded and over 5 A is loaded, you get **two of each**. A third of the
shift in each state.

That translation, from a number to a word, is what `CASE` does.

## Glossary

- **Type.** What kind of value a column holds, and therefore which operations make sense.
- **DOUBLE.** The type of decimal numbers used by almost every sensor. It stores the number in
  binary and **not every decimal fits exactly**.
- **DECIMAL.** Another type for decimal numbers that does store the decimals exactly. It is used
  for money, where a lost cent is a problem.
- **Floating point.** The way DOUBLE stores numbers. Fast, and approximate.
- **`CASE`.** How you write "if this happens, then that" inside a query.
- **`CAST`.** Converting a value from one type to another, on purpose.
- **Threshold.** The value at which something changes state. Here, the amps separating stopped
  from offloaded and offloaded from loaded.

## Step by step

### Step 1. Look at what type each column is

Before comparing anything it helps to know what you are comparing with. The database says so, and
it does not have to be guessed.

### Step 2. Ask for the datasheet's threshold, and count what comes out

The dataset's datasheet says the compressor starts when the pressure drops below 8.2 bar. It
looks like a direct question: how many readings are at 8.2. You ask it, you count, and then you
ask it properly and count again.

### Step 3. Pick the cuts by looking at the distribution

The datasheet says the motor draws about 0 A stopped, about 4 A offloaded and about 7 A loaded.
Those are three points, not two cuts, and where the boundary goes has to be decided.

It goes where the distribution has its valleys, which is where the fewest readings are and
therefore where the fewest get misclassified.

### Step 4. Check the rule with a signal that was not used to build it

And this step is what separates a rule from an opinion. `DV_eletric` marks load on its own,
without looking at the current. If the cuts are right, nearly every reading above the loaded cut
has to carry that mark.

## The code, in parts

### Step 5. What type each thing is

```sql
SELECT typeof(TP2) AS tipo_de_la_columna,
       typeof(0.1) AS tipo_de_un_literal,
       0.1 + 0.2 = 0.3 AS suman_exacto,
       0.1::DOUBLE + 0.2::DOUBLE = 0.3::DOUBLE AS suman_exacto_en_double
FROM telemetria LIMIT 1;
```

```anota
typeof(x) | says what type a value is, without having to guess it
0.1 | a number written by hand in the query; SQL picks a type for it
::DOUBLE | converts to floating point; the double colon is shorthand for CAST
= | comparing; here the result is true or false, and it comes out as one more column
```

```salida
┌────────────────────┬────────────────────┬──────────────┬────────────────────────┐
│ tipo_de_la_columna │ tipo_de_un_literal │ suman_exacto │ suman_exacto_en_double │
├────────────────────┼────────────────────┼──────────────┼────────────────────────┤
│ DOUBLE             │ DECIMAL(2,1)       │ true         │ false                  │
└────────────────────┴────────────────────┴──────────────┴────────────────────────┘
```

Read that row slowly, because it dismantles what almost everybody believes.

The famous "0.1 plus 0.2 is not 0.3" **is false here**: it comes out `true`. Because a number
written by hand in the query is DECIMAL, and DECIMAL stores decimals exactly.

The failure appears only when the floating point type is asked for, with `::DOUBLE`, and then it
comes out `false`. And look at what type `TP2` is: **DOUBLE**. The sensor's column is stored in
precisely the type that is not exact.

### Step 6. The direct question, and what it leaves out

```sql-vivo
SELECT count(*) AS con_el_igual
FROM telemetria
WHERE TP2 = 8.2;
```

```anota
WHERE TP2 = 8.2 | asks for the rows whose pressure is exactly that value
count(*) AS con_el_igual | counts how many they are and names the result
```

```salida
┌──────────────┐
│ con_el_igual │
│    int64     │
├──────────────┤
│          107 │
└──────────────┘
```

One hundred and seven. Change it to `WHERE round(TP2, 1) = 8.2` and run it again.

### Step 7. The question asked properly

```sql
SELECT count(*) AS redondeando
FROM telemetria
WHERE round(TP2, 1) = 8.2;
```

```anota
round(TP2, 1) | rounds to one decimal before comparing, which is what the eye does reading 8.2
```

```salida
┌─────────────┐
│ redondeando │
│    int64    │
├─────────────┤
│        5237 │
└─────────────┘
```

Five thousand two hundred and thirty seven. The direct question was finding **2 %** of that.

### Step 8. Translating the current into a state

```sql-vivo
SELECT CASE WHEN Motor_current < 1 THEN 'parado'
            WHEN Motor_current < 5 THEN 'en vacio'
            ELSE 'en carga' END AS estado,
       count(*) AS lecturas,
       round(avg(Motor_current), 2) AS corriente_media,
       round(avg(DV_eletric) * 100, 1) AS por_ciento_marcado_en_carga
FROM telemetria
GROUP BY estado
ORDER BY corriente_media;
```

```anota
CASE WHEN ... THEN ... | if the condition holds, the value is that; if not, the next one gets tried
ELSE | what it is worth when no earlier condition held
END | closes the CASE; without it the query is not valid
AS estado | the CASE produces a new column, and here it gets a name
GROUP BY estado | groups by that just invented column, which now exists like any other
avg(DV_eletric) * 100 | the percentage of rows marked as loaded, because the signal is zero or one
```

```salida
┌──────────┬──────────┬─────────────────┬─────────────────────────────┐
│  estado  │ lecturas │ corriente_media │ por_ciento_marcado_en_carga │
├──────────┼──────────┼─────────────────┼─────────────────────────────┤
│ parado   │   829000 │            0.04 │                         0.2 │
│ en vacio │   457356 │            3.79 │                         3.4 │
│ en carga │   230592 │            5.82 │                        98.1 │
└──────────┴──────────┴─────────────────┴─────────────────────────────┘
```

The last column is what validates the rule, and it was not used to build it.

## The result, measured

{{FIG:fig_m09_coma_flotante}}

**What we expected.** Zero rows. It is what every manual on floating point says.

**What came out.** Worse: it returned **107**. On a two decimal screen, no fewer than **498**
readings show as 8.20, and the ones around 8.2 to one decimal are **5,237**. Against those, the
equals found **2.0 %**.

Zero rows would have been lucky, because an empty result makes anyone suspicious. One hundred and
seven readings is a believable number, it fits in a report and nobody looks twice.

The figure shows why. Around 8.2 bar there is no value: there is a cloud of similar values. The
equals falls into one single slit of that cloud.

{{FIG:fig_m09_tres_estados}}

**And the three states rule.** The split of the time comes out at
**54.6 / 30.1 / 15.2 %**: stopped, offloaded and loaded.

The figure shows why the cuts are at 1 and 5 A. They are the two valleys of the distribution, the
zones where there are almost no readings. Putting a boundary where there is little data is
putting it where few readings get misclassified.

**What it means.** The rule stands on its own: **98.1 %** of the readings it calls loaded carry
the `DV_eletric` mark, a signal that was not used to write it. Two independent ways of knowing the
same thing agree.

And there is a disagreement with the datasheet worth saying. The datasheet declares about **7 A**
loaded and in the file the commonest is **6.0 A**. In the figure, the dotted line at 7 A falls in
an almost empty zone. It is not a serious error, and it is the second place in this course where
the paper and the file do not quite agree.

## Watch out

- **Never compare a decimal with equals.** Not in SQL nor anywhere else. You compare with
  `round()`, with `BETWEEN`, or by asking that the difference be small.
- **The failure is not "it finds nothing", it is "it finds something".** A zero draws attention; a
  2 % gets published. That is why this error survives so long inside reports.
- **The type rules over the number.** The same 0.1 is exact as DECIMAL and inexact as DOUBLE.
  Before comparing, look at `typeof`.
- **There are two causes here, and the common one is not the famous one.** The one most people
  know is the binary one, DOUBLE's. What really breaks this query is sillier: **the sensor gives
  three decimals and the screen shows two**. Both lead to the same place, and both are fixed the
  same way.
- **A `CASE` with no `ELSE` leaves gaps.** The rows that meet no condition end up NULL, and module
  8 already showed how silent that is.
- **The order of the `WHEN`s matters.** They get evaluated top to bottom and the first that holds
  wins. Putting `< 5` before `< 1` would classify everything stopped as offloaded.
- **The cuts are a decision, not a datum.** Here they are justified with the distribution and
  checked with a second signal. Without that they would be two numbers picked by eye.

## Metallurgical bridge

A cut-off grade is not chosen with an equals. Nobody says "send me the ore that is exactly 0.5 %
copper", because no sample with exactly that grade exists: 0.4987 and 0.5013 exist.

What gets said is "above 0.5". A threshold, not an equality.

And that cut-off grade is not copied from another mine's report either. It gets calculated with
the metal price, the process cost and the plant's recovery, and revised when they change. That is
exactly what this module's two amp cuts do: they get chosen by looking at your own data, and
checked against something that was not used to choose them.

## Do it yourself

```reto
pregunta: Write the rule that splits the readings into the three states and returns two columns, `estado` and `horas`, with the hours the compressor spent in each. Three rows. Each reading is 10 seconds.
inicio: SELECT CASE WHEN Motor_current < 1 THEN 'parado'
            WHEN Motor_current < 5 THEN 'en vacio'
            ELSE 'en carga' END AS estado,
       count(*) AS lecturas
FROM telemetria
GROUP BY estado
ORDER BY lecturas DESC;
esperado: m09_horas_por_estado
pista: The `CASE` is already written in the starting point and does not need touching. What changes is the second column: instead of counting readings, those readings have to become hours. Each reading is 10 seconds and an hour is 3,600, so you multiply by 10 and divide by 3600.0. Round to one decimal with `round(..., 1)`.
solucion: SELECT CASE WHEN Motor_current < 1 THEN 'parado'
            WHEN Motor_current < 5 THEN 'en vacio'
            ELSE 'en carga' END AS estado,
       round(count(*) * 10 / 3600.0, 1) AS horas
FROM telemetria
GROUP BY estado
ORDER BY horas DESC;
```

## Review

### Why WHERE TP2 = 8.2 does not find what you expected

Because `TP2` is DOUBLE, which stores numbers in binary, and 8.2 has no exact binary
representation. What is stored are values like 8.1999999999999993, which are not equal to 8.2
even though they look identical on screen. The equals compares the bits, not what you see.

### And how do you ask properly

With a margin instead of an equality. `round(TP2, 1) = 8.2` rounds before comparing, which is
what the eye does reading the screen. `TP2 BETWEEN 8.15 AND 8.25` works too. What matters is
deciding the margin on purpose, instead of inheriting it from chance.

### It found 107 rows instead of 5,237. Why is that worse than finding zero

Because zero gets noticed. An empty result makes anyone check the query. One hundred and seven is
a plausible number that enters a report without drawing attention, and the error can live in
there for years. The failures that give a believable result are the expensive ones.

### What is CASE for if you already have the number

For turning a measurement into a decision. Nobody runs a plant wondering how many amps the motor
draws: they ask whether it is stopped, offloaded or loaded. `CASE` is where that translation gets
written, once and in plain sight, instead of scattered across different spreadsheets.

### How do you know the 1 A and 5 A cuts are the right ones

For two reasons, and neither is the datasheet. First, they sit in the valleys of the
distribution, where there are almost no readings and therefore almost nothing gets misclassified.
Second, and more important: 98.1 % of what the rule calls loaded carries the `DV_eletric` mark.
That signal is a different one and was not used to build the rule. When two independent routes
reach the same place, the rule is more than an opinion.

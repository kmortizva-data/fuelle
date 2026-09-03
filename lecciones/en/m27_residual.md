---
module: 27
---

## In 30 seconds

- The residual comes from an identity, not from a fit: `carga × entrega − consumo`, in bar/min.
- And for a leak of size **f**, the residual is **exactly f**. It does not resemble it: it is it.
- The noise floor, over 579 healthy hours, reaches **0.1165**. The ceiling is at **1.1796**.
- Ten times of room, and that is why it works: **0.1165 against 1.1796**.
- Watch two things: the residual **pins** at the top, and daily it loses the overnight failure.

## What this module solves

Module 23 said a twin delivers a difference and nothing else. 24 measured the four numbers, 25 set
them running and 26 checked that they mean something. What is left is the one thing the course has
promised from the start: **turning that difference into a number with units**.

And there is a way of doing it that needs no simulation at all, because it comes from the
conservation of air. Over any long stretch, the compressor puts in as much air as the plant takes
out. And it puts in `entrega` bar/min while loading, for a fraction of the time, so

```
aire que se está gastando = carga × entrega
```

Subtracting the consumption from when the machine was well leaves **what is being spent over the
odds**. That is the residual, and it is the leak.

## Before the theory: a toy example

A water tank with a pump that puts in **10 litres per minute**. Nobody has ever seen inside the tank
nor knows where the leak is. All that is known is how long the pump was on, because there is an hour
counter.

| | Pump on | Litres put in | |
|---|---|---|---|
| A normal week | 60 min a day | 600 l/day | this is how this house lives |
| This week | 180 min a day | 1,800 l/day | |

**1,200 litres a day left over.** And notice what it took to say so: the pump's flow, the hour
counter, and knowing what was normal. Not a drop measured at the leak, nor having found where it is.

That is all. Swap litres for bar, the pump for the compressor and the hour counter for the duty
cycle, and you have this course's residual.

## Glossary

- **Residual.** What the machine spends over the odds compared with when it was healthy, in bar/min.
- **Noise floor.** The highest the residual gets with nothing happening. Every warning has to be
  above it, or it goes off on its own.
- **Ceiling, or censoring.** The residual cannot pass `llena`, because the compressor cannot load
  more than 100 % of the time. On reaching it, it says "at least this much" and cannot say how much.
- **Grain.** The slice of time being averaged over. Here it is the hour, and the choice matters more
  than it looks.
- **Frozen indicator.** The residual against February's healthy machine. It says how far it has
  drifted.
- **Rolling indicator.** The same residual against the previous fourteen days. It says how much it
  has changed. They are two different questions and both are needed.

## Step by step

### Step 1. Write the residual

`carga × entrega − consumo`, hour by hour. Three numbers, two of them measured in module 24 and
frozen ever since, and the duty cycle that comes from counting readings.

### Step 2. Measure the floor before looking at any failure

Over February's 579 hours, which is the healthy window module 26 left clean. **The floor first and
the failures afterwards**, not the other way round: a bar chosen after seeing the signal is a bar
chosen for convenience.

### Step 3. Choose the grain, and check the choice

By hours or by days. It looks like an implementation detail and it decides whether one of the four
failures is visible or not.

### Step 4. Get the same number by another road

The drain slope measures consumption directly: how much the pressure drops divided by the unloaded
minutes. It does not use the delivery, nor the model, nor anything. If both roads agree on a healthy
day, both are right.

## The code, in parts

### Step 5. The residual, in full

```python
avg(DV_eletric) * entrega - consumo AS residual
```

```anota
avg(DV_eletric) | that hour's duty cycle: the fraction of readings with the compressor loaded
× entrega | that turns time into air: bar per minute really being moved
− consumo | and it takes off what the healthy machine spent. What is left is what is over the odds
```

There is no more. Module 25's twin does not appear anywhere, and that is on purpose: **in steady
running the simulation and this sum give the same thing**, so simulating would be a detour.

The simulator is still needed for something else: asking about a leak that has not happened yet. It
is what the knob below does.

### Step 6. The second road, which shares nothing with the first

```python
sum(p_ini - p_fin) / sum(minutos) AS consumo
```

```anota
p_ini − p_fin | how much the pressure drops over an unloaded stretch, in bar
sum / sum | the total over the total, not the mean of the means: a twenty minute stretch weighs twenty times what a one minute one does
AS consumo | and that is it: no delivery, no duty cycle, no model. That is why it counts as a second opinion
```

### Step 7. Turn the knob

```perilla
m27_fuga
```

The knob puts in a leak that never existed, from zero to 0.30 bar/min, and shows what the compressor
would do. Watch the caption as you move it: **the residual keeps reading the same number as the
leak**, and that is not chance nor fitting. It is step 5's identity rearranged.

And it answers the syllabus's question with a number: the leak shows **from 0.12 bar/min upwards**,
which is when the residual clears the noise floor.

With the knob at zero you will see a residual of **−0.003** rather than a clean zero. It is not an
error in the sum: it is the simulation's step, module 25's own. Eight simulated hours do not fit a
whole number of cycles, and the half cycle at the end shows in the third digit.

## The result, measured

{{FIG:fig_m27_residual}}

**What we expected.** That the residual would lift off the floor in the four documented failures.

**What came out.** That, and three more things that were not in the script.

```salida
  el residual es carga x 1.2507 - 0.0711, en bar/min

  el suelo, sobre 579 horas de febrero:
    mediana 0.0053   p95 0.0505   p99 0.0728   máximo 0.1165
  el techo, que es `llena`: 1.1796   o sea 10.1 veces el suelo
  y 156 horas de 3924 llegan a tocarlo

  por día contra por hora, en los cuatro partes:
    #1   2020-04-18   diario  1.1663 (10.01x el suelo)   horario  1.1796 (10.13x)
    #1   2020-05-29   diario  0.1268 ( 1.09x el suelo)   horario  0.8704 ( 7.47x)
    #3   2020-06-05   diario  0.7245 ( 6.22x el suelo)   horario  1.1796 (10.13x)
    #4   2020-07-15   diario  0.5307 ( 4.56x el suelo)   horario  1.1796 (10.13x)

  la segunda ruta, el consumo por pendiente de vaciado:
    2020-02-18     44 tramos,   1368 min   consumo 0.0648   (el residual iba por 0.0505)
    2020-03-06     74 tramos,    894 min   consumo 0.1662   (el residual iba por 1.1796)
    2020-04-18   sin un solo tramo de vacío: la ruta no contesta
    2020-05-30     52 tramos,    947 min   consumo 0.1117   (el residual iba por 1.1796)
    2020-06-05     25 tramos,    508 min   consumo 0.1014   (el residual iba por 1.1796)
    2020-06-06   sin un solo tramo de vacío: la ruta no contesta
    2020-07-15    127 tramos,    726 min   consumo 0.349   (el residual iba por 1.1796)
```

### The room: ten times

The floor reaches **0.1165** and the ceiling sits at **1.1796**. Between one and the other there is a
factor of **10.1**, and that is where everything this twin can say has to fit.

The ceiling is not a chosen limit: it is `llena`, how fast the receiver rises per loaded minute. When
the compressor loads 100 % of the time, the duty cycle is 1 and the residual cannot rise any further
however much the leak keeps growing. **156 hours of the 3,924 measured reach it.**

### The grain: daily, the overnight failure gets lost

#1b starts on 29 May at 23:30, so it dirties half an hour of a twenty four hour day. Hourly the
residual reaches **0.8704**, which is **7.47 times** the floor. Daily it comes out at **0.1268**,
which is **1.09 times**: it clears the bar by nine per cent, and that is not detecting, it is
guessing right.

It is module 15 turned around. There the fast signal came down to the slow one's grain so they could
be joined. Here going down to the slow grain **destroys the signal**: a half hour spike gets spread
across twenty four.

### The two roads, and the one that goes quiet

On a healthy day the two agree: on 18 February the slope gives **0.0648** bar/min of consumption,
very close to the 0.0711 it was calibrated with.

And in failure what happens is what makes both worth having:

| | Duty cycle road | Slope road |
|---|---|---|
| 18 April | pinned at 1.1796 | **does not answer**, not one unloaded stretch |
| 6 June | pinned at 1.1796 | **does not answer** |
| 15 July | pinned at 1.1796 | **0.349 bar/min** |

**The one that always answers cannot say how much, and the one that can say how much sometimes does
not answer.** On 15 July the slope gives a consumption of 0.349, which is **five times** the healthy
one and far above where the residual pins. On 18 April the compressor did not rest for a single
stretch, so there is no slope to measure.

They are not two ways of computing the same thing. They are two instruments with different ranges,
and a twin does well to carry both.

### The drift, and why two readings of one number are needed

The figure's lower panel is the same residual read another way: each day against the median of the
previous fourteen. And it is needed because the upper one shows something uncomfortable.

| Month | Days above the floor | Median residual |
|---|---|---|
| February | 1 of 28 | 0.0053 |
| March | 19 of 31 | 0.0574 |
| April | 14 of 29 | 0.0331 |
| May | 18 of 28 | 0.0644 |
| June | 25 of 28 | 0.0852 |
| July | 26 of 31 | 0.0818 |
| August | 24 of 31 | 0.0713 |

**The machine does not go back to February.** And the twin has not broken: the plant's air really
does rise, from 0.0711 bar/min to more than double. With the floor set in February, almost every day
from June onwards sits above it.

That is not a fault of the frozen indicator, it is its answer: **July's machine is not February's**.
But for setting an alarm it is no good, because it would be sounding all the time.

That is why the same residual is also read against the previous fourteen days. There the reports
stand out again, against a median of **0.0052** on an ordinary day:

| Day | Above the trend |
|---|---|
| 18 April | **+1.0631** |
| 29 May | **+0.5368** |
| 5 June | **+0.8182** |
| 15 July | **+1.0169** |

**And this does not contradict module 23's rule.** The twin stays calibrated on healthy and frozen;
what moves is the reference its residual is read against. They are two different questions about the
same number: how far the machine has drifted from when it was well, and how much it has changed
since last week.

**What it means.** That the residual is now a number with units, with a measured floor and a measured
ceiling, and with two readings that answer two questions. What it does not have yet is a threshold,
and that is module 28 on purpose: if the same script chose the threshold and measured the result, it
would be choosing its own exam.

## Do it yourself

```reto
pregunta: Compute the residual hour by hour with the module's formula (`carga * 1.2507 - 0.0711`) and get, for the four days with a failure report, how many hours clear the noise floor of 0.1165 and what the maximum residual was. Skip incomplete hours, the ones with fewer than 300 readings. Return `dia`, `horas` and `residual_maximo`, ordered by day. Four rows.
inicio: SELECT hora, carga, lecturas,
       carga * 1.2507 - 0.0711 AS residual
FROM horas
WHERE lecturas >= 300;
esperado: m27_horas_sobre_el_suelo
pista: `count(*) FILTER (WHERE ...)` counts only the rows meeting the condition, with no need for a subquery. To group by the day of a timestamp, `hora::DATE` trims it. And the maximum comes from `max` of the same residual.
solucion: SELECT hora::DATE AS dia,
       count(*) FILTER (WHERE carga * 1.2507 - 0.0711 > 0.1165) AS horas,
       round(max(carga * 1.2507 - 0.0711), 4) AS residual_maximo
FROM horas
WHERE lecturas >= 300
  AND hora::DATE IN (DATE '2020-04-18', DATE '2020-05-29',
                     DATE '2020-06-05', DATE '2020-07-15')
GROUP BY 1 ORDER BY 1;
```

On 18 April and 15 July **all twenty four hours** clear the floor. On 5 June, fifteen. And on 29 May,
**four**: it is the overnight failure, and there you see why it thins out at daily grain.

Notice too the maximum column: three of the four days mark exactly **1.1796**. It is not that the
three failures were the same size, it is that all three touched the ceiling.

## Watch out

- **The residual is the leak, in the same units.** It is not an index nor a score. With a leak of
  0.12 bar/min the residual is 0.12, and that can be taken into a meeting.
- **A pinned residual does not say how much.** It says "at least `llena`". Publishing a maximum of
  1.1796 on three different days and presenting them as equally serious would be lying with a true
  number.
- **The grain is not an implementation detail.** The same failure is worth 7.47 or 1.09 times the
  floor depending on whether you look hourly or daily.
- **Measure the floor before looking at the failure.** A bar chosen after seeing the signal always
  ends up just below it.
- **Two independent estimators are worth more than one good one**, above all if they break in
  different places. The day one goes quiet, the other has the floor.
- **A floor set in the past ages.** If the machine really degrades, the frozen indicator ends up
  permanently on, and that is information but it is not an alarm.
- **The threshold is not decided here.** Whoever measures and whoever grades should not be the same
  script.

## Metallurgical bridge

It is exactly a plant's metallurgical balance under another name. Nobody puts a bucket under the
tailings to measure the loss: the feed gets measured, the concentrate gets measured, and **the loss
is the subtraction**. The figure comes out of a balance, not out of an instrument pointed at it.

And this module's two limitations are recognised just as quickly in a plant.

The first is censoring. If a cell overflows, the level gauge marks its top, and from there on every
overflow looks alike even if one is twice the other.

The second is the reference. A balance against the commissioning campaign says how much the circuit
has aged; against last week it says what broke yesterday. Nobody argues about which is the good one,
because you carry both.

## Review

### Where the residual comes from, if nothing is simulated

From the conservation of air. The compressor puts in `entrega` bar/min while loading, so in steady
running the air being spent is `carga × entrega`. Subtracting the healthy machine's consumption
leaves what is spent over the odds, in bar per minute. The simulator gives the same in steady running
and that is why it is not used here.

### Why the residual is measured hourly and not daily

Because a failure starting at 23:30 gets spread across twenty four hours if the whole day is
averaged. #1b goes from being worth 7.47 times the floor hourly to 1.09 daily, that is from a clear
detection to a coin toss.

### What it means that the residual is censored

That it has a physical limit, `llena` = 1.1796, reached when the compressor loads 100 % of the time.
Past that the leak can keep growing and the number does not move. 156 hours of the record are there,
and three of the four reported days mark that same maximum.

### What the second road is for if there is already one

Because they break in different places. The drain slope is not censored, so on 15 July it could say
0.349 bar/min where the first one was pinned. In exchange it needs unloaded stretches to measure, and
on 18 April there were none. An instrument that sometimes goes quiet is not useless: it is an
instrument with a range.

### Why the same residual is read two ways

Because they answer two questions and both are needed. Against February it says how far the machine
has drifted from when it was well, which is what somebody deciding on a replacement wants to know.
Against the previous fourteen days it says what has happened this week, which is what somebody
running a shift wants to know. The twin is not recalibrated in either case.

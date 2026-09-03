---
module: 26
---

## In 30 seconds

- A model's parameters can be **measured** or they can be **searched for**. Module 24 measured them.
- Here they get searched for, and not to improve them: to see whether searching lands in the same
  place.
- Searching on the duty cycle alone **does not give an answer, it gives a valley**: deliveries from
  0.72 to 1.08 all score equally well.
- A second observable is needed. With the starts per hour the two valleys cross at one point.
- There the fit says **1.27 bar/min** and the measurement said **1.1796**: **1.18 against 1.27**.

## What this module solves

Calibrating sounds like improving. In most projects it is: you take a model with knobs, move them
until the curve fits, and publish how well it fits.

This module does the opposite, and it is worth saying why before starting. **The twin's two
parameters are already measured**, one by one, with an air balance that closes. Searching for them
by fitting cannot improve a model that has no loose knobs. What it can do is answer a question worth
more: **do the two roads lead to the same place?**

If they do, the parameters mean something. They are the speed at which this compressor fills its
receiver and the air this train spends, and it does not matter how you get them. If they do not, one
of the two is wrong, and you have to find out which before going on.

They came out **7.8 %** apart. And along the way, the fit uncovered two faults the measurement had
not seen.

## Before the theory: a toy example

A tank with a float. It fills, and on reaching the top a valve lets it out until it drops ten
litres, and round again. Two technicians look at it.

The first says: **10 litres a minute in and 1 out**.
The second says: **20 in and 2 out**.

They disagree by a factor of two. Check how much time each one spends filling:

| | In | Out | Rises 10 l in | Drops 10 l in | Cycle | Fraction filling |
|---|---|---|---|---|---|---|
| The first | 10 l/min | 1 l/min | 1.11 min | 10 min | 11.1 min | **1 in 11** |
| The second | 20 l/min | 2 l/min | 0.56 min | 5 min | 5.6 min | **1 in 11** |

**The same fraction.** With a stopwatch that only looks at how long the pump is on, both technicians
are right and there is no way to decide. And it is not that one of the two is correct: it is that
that measurement **cannot tell them apart**.

Now count the times it starts in an hour. The first, 5 times. The second, nearly 11. **There they do
separate**, because the clock on the wall is not fooled by a ratio.

That is this whole module. One measurement that only sees the ratio, another that sees the scale,
and both are needed.

## Glossary

- **Calibrating.** Setting a model's parameters to their value. Here, searching for them by fitting
  in order to check the ones already measured.
- **Observable.** Something the machine does that can be counted in the record. There are two here:
  the duty cycle and the starts per hour.
- **Error surface.** How badly each combination of parameters does, drawn over every combination
  tried.
- **Valley.** When that surface has no bottom but a groove: many combinations score the same and the
  fit has no way to prefer one.
- **Identifiable.** A parameter is, when the data you have are enough to pin it down. If not, the
  number that comes out comes from the grid or from the starting point, not from the machine.
- **Grid.** Trying every combination on a list, instead of letting an optimiser search. It is slow
  and clumsy, and in exchange it **shows the whole surface**, which is what is needed here.

## Step by step

### Step 1. Decide what is being searched for, and on what grid

Two parameters: the compressor's delivery and the plant's consumption. 33 deliveries by 31
consumptions get tried, **1,023 combinations**, around what module 24 measured and with room to
spare on both sides.

A grid and not an optimiser, on purpose. An optimiser returns a point and says nothing; what has to
be seen here is the shape of the surface.

### Step 2. Decide what it gets compared against

A fit needs something the machine did. The first option is the obvious one: **the duty cycle**, which
is what the twin exists to reproduce.

### Step 3. Discover that this alone is not enough

And here is the module. In steady running, the duty cycle of a receiver with hysteresis is

```
carga = consumo / entrega
```

so it **depends only on the ratio**. Double both and it does not move. So fitting against the duty
cycle cannot return two numbers: it returns a relationship between them.

### Step 4. Add the second observable

The time a whole cycle takes is `banda / llena` to rise plus `banda / consumo` to fall, and that
**does** change when both parameters are scaled together. Counting starts per hour is free, it is in
the same record, and it is what pins the scale.

## The code, in parts

### Step 5. The error at one point of the grid

```python
carga, arranques = resumen(dep)
e_carga = abs(carga - obs["carga"]) / obs["carga"]
e_arr = abs(arranques - obs["arranques_por_hora"]) / obs["arranques_por_hora"]
error = (e_carga if pesa_carga else 0) + (e_arr if pesa_arranques else 0)
```

```anota
resumen(dep) | simulates twelve hours with those parameters and returns the two things that can be compared
/ obs[...] | dividing by what was observed. One is a fraction and the other is events per hour: without dividing, the one with bigger numbers would rule
pesa_carga, pesa_arranques | the two switches that do the module's three fits with a single loop
```

### Step 6. The edge guard, and why it does not apply to all three

```python
if ganador["entrega"] in (ENTREGAS[0], ENTREGAS[-1]) or \
        ganador["consumo"] in (CONSUMOS[0], CONSUMOS[-1]):
    raise SystemExit("El ajuste completo se pega al borde de la rejilla")
```

```anota
ganador | the complete fit is the only one that should have a real minimum, so it is the only one held to this
ENTREGAS[0], ENTREGAS[-1] | the two edges. A valley has no bottom, so it ends up on one of them whatever grid you give it
raise SystemExit | it really did fire: the first grid stopped at 1.200 and the optimum came out exactly there. The number was the grid's, not the machine's
```

### Step 7. Turn the knob

```perilla
m26_valle
```

Move the delivery. The knob keeps the ratio fixed, so it **walks along the valley**. Watch the trace:
it barely moves, because all these pairs give the same duty cycle. Watch the number of starts: it
doubles from end to end.

That is a valley, with your hands on it. And it is why a fit with a single observable has no answer
to give.

## The result, measured

{{FIG:fig_m26_ajuste}}

**What we expected.** That the search would land where the measurement landed, and that a single
observable would be enough to get there.

**What came out.** The first, yes. The second, no.

```salida
  la máquina, del 2020-02-01 al 2020-02-29:
    carga              0.0572
    arranques por hora 2.031

  el gemelo con los parámetros MEDIDOS (entrega 1.2507, consumo 0.0711):
    carga              0.0560   (2.1% de error)
    arranques por hora 1.833   (9.7%)

  y ahora buscándolos, con tres objetivos distintos:
    solo la carga        entrega 0.720  consumo 0.0420  cociente 0.0583  error 0.0004
    solo los arranques   entrega 0.600  consumo 0.0810  cociente 0.1350  error 0.0153
    las dos cosas        entrega 1.350  consumo 0.0780  cociente 0.0578  error 0.0334

  puntos que empatan con el mejor (dentro de 0,002), y qué abarcan:
    solo la carga           4 puntos   entrega de 0.720 a 1.080   cociente de 0.0571 a 0.0588
    solo los arranques     40 puntos   entrega de 0.600 a 1.560   cociente de 0.05 a 0.135
    las dos cosas           1 puntos   entrega de 1.350 a 1.350   cociente de 0.0578 a 0.0578
```

The figure's three panels are that table's three lines.

**Fitting the duty cycle** gives a diagonal: four tied points, with deliveries from **0.72** to
**1.08**, all with the same ratio. The fit has found the right relationship and has nothing to say
about the scale.

**Fitting the starts** gives a vertical, and worse: **forty** tied points, from one end of the grid
to the other. Its best point has a ratio of **0.1350**, which would give a duty cycle more than
double the real one. One observable got right with a preposterous model.

**Fitting both** leaves **one point**, where the two lines cross.

**And there is the module's answer:**

| | Measured, with nothing fitted | Searched for by fitting |
|---|---|---|
| Delivery | 1.2507 bar/min | 1.350 |
| Consumption | 0.0711 bar/min | 0.0780 |
| Rise per loaded minute | **1.1796** | **1.272** |

**7.8 %.** Two roads that do not speak to each other, one of physics and one of brute force, and they
end up less than ten per cent apart.

**And what that is worth, drawn over a healthy week:**

{{FIG:fig_m26_gemelo_vs_real_sano}}

From 16 to 22 February the machine loaded for **497.2** minutes. The twin with the measured
parameters predicted **528.5**, and the twin with the fitted ones, **536.7**.

**The two twins are 8.2 minutes apart over a whole week.** 7.8 % in the parameters turns into 1.6 %
of the machine's work, and in the figure the two curves would be the same line. Notice too which one
lands closer to reality: **the measured one**, by eight minutes. The fit optimised two summaries and
gained nothing where it counts.

### And what the fit found without looking for it

Everything above is this module's second version. The first did not add up, and chasing why uncovered
two things.

**The first: the record has gaps, and they were being counted as compressor time.** Each stretch's
duration came from subtracting two timestamps, the last minus the first. And in the window of the
time there were **35 gaps** longer than an hour, almost all of them at night. A stretch that jumps a
gap takes the gap's hours with it, and that sank both rates at once.

**And the guard that existed could not see it.** It compared the predicted duty cycle against the
observed one, and the duty cycle is a ratio: if both durations are inflated by the same factor, it
does not notice. The starts per hour do, because they are counted against the clock. With the
parameters of the time they were off by **15.4 %** and nobody was looking at them.

This is module 16 again in different clothes: **a check that shares its error with what it compares
always passes.**

**The second is bigger.**

{{FIG:fig_m26_ventana_sucia}}

With the gaps sorted out, the parameters still did not add up. Looking at the calibration window day
by day instead of in one block, this turned up:

| | February, 28 days | 1 to 12 March | 13 to 22 March |
|---|---|---|---|
| Duty cycle | 0.0461 to 0.0781 | 0.0972 to **0.5808** | 0.0676 to 0.1136 |
| Starts per hour | 1.58 to 2.42 | 1.46 to **5.0** | 1.96 to 2.77 |
| Oil | 53.9 to 59.2 °C | **60.7 to 69.2** | 53.5 to 62.0 |
| Motor current | 1.0 to 1.5 A | **1.78 to 3.91** | 1.23 to 1.8 |
| Low pressure alarm | 0.0002 | **0.0208** | 0.0108 |

**From 1 to 12 March 2020 this machine is broken, and there is no report saying so.** The oil and the
current do not even brush against February's: February's maximum sits below March's minimum in both.
On the 11th the low pressure alarm fires for the first time in the whole record. On the 13th
everything goes back to how it was.

Five signals from five different instruments moving together. One alone would be an argument.

**And this course's calibration window ran to 15 March**, so the twin was being calibrated with
**twelve days of failure inside**. The window had been chosen by date, before the first documented
report, precisely so as not to pick the data that confirms the model. That protects against one
thing and does not protect against this.

**What it means.** That the fit did not improve the twin, and was worth it anyway. Searching for the
parameters was the first question the model could answer with a no. It answered no twice, and both
times it was right.

## Do it yourself

```reto
pregunta: Get both of the things the twin is calibrated against, in a single query, for 5 June 2020. Return `carga` (the fraction of readings with the compressor loaded, to four decimals) and `arranques_por_hora` (to two). One row.
inicio: SELECT DV_eletric,
       lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
FROM telemetria WHERE day = DATE '2020-06-05';
esperado: m26_los_dos_observables
pista: The duty cycle is a mean of ones and zeros, so `avg` over a `CASE` gives it directly. For the starts you have to count the readings where `antes` was 0 and `DV_eletric` is 1, and divide by the hours in the day, which are `count(*) * 10 / 3600.0` because each reading is ten seconds.
solucion: SELECT round(avg(CASE WHEN DV_eletric = 1 THEN 1.0 ELSE 0.0 END), 4) AS carga,
       round(sum(CASE WHEN antes = 0 AND DV_eletric = 1 THEN 1 ELSE 0 END)
                 / (count(*) * 10 / 3600.0), 2) AS arranques_por_hora
FROM (SELECT DV_eletric,
             lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
      FROM telemetria WHERE day = DATE '2020-06-05');
```

Duty cycle **0.6363** and **1.28** starts per hour. Compare that with February, which did 0.0572 and
2.031.

The duty cycle is **eleven times higher** and the starts have **gone down**. It is not a
contradiction: 5 June is one of the four days with a failure report, the compressor is loading almost
all the time and so it barely cycles. Keep that oddity, because module 27 trips over it.

## Watch out

- **Fitting is not improving.** If the model has no loose knobs, a fit cannot improve it. It serves
  to check it, which is another thing and sometimes worth more.
- **An observable can pin a relationship and not the numbers.** Before believing a fitted parameter,
  ask whether what you measured could tell it apart from another.
- **An optimum stuck to the edge of the grid is not an optimum**, it is the edge. And if you widen
  the grid and it sticks again, what you have is a valley.
- **A check that shares its error with what it compares always passes.** The duty cycle cannot
  validate two durations because it is a ratio of those durations.
- **Choosing the healthy window by date is not enough.** It protects against picking for convenience
  and does not protect against an undocumented failure. You have to look at it, signal by signal and
  day by day.
- **One odd signal is an argument; five at once is a fact.** None of March's five would have
  convinced on its own.
- **With the fit alongside you can ask what it costs.** Here 7.8 % in the parameters cost 8.2 minutes
  over a week. Without that sum, you cannot tell whether 7.8 % is a lot or a little.

## Metallurgical bridge

A grinding model with two parameters fitted at once, the breakage constant and the selection
function. And a single output size distribution curve to fit them against.

Out comes a beautiful fit and both parameters are invented. The curve cannot tell fast breakage with
little selection from slow breakage with a lot, because it only sees the product.

The way to break the tie is the same as here: **another measurement that depends on another
combination**. A test at a different grinding time, a circulating load, a power draw. Not more data
of the same, but data of something else.

And the other parallel is the window. Anyone who has calibrated a model with plant data knows the
reference period gets chosen by looking, not by date. A campaign with the scavenger cell down inside
it takes the calibration with it. That is exactly what happened here, and it had to be found out
late.

## Review

### What calibrating exactly means here

Searching for the twin's two parameters by trying 1,023 combinations and keeping the one that best
reproduces what the machine did. Not to replace the measured ones, but to check them: two
independent roads ending in the same place are proof that the place means something.

### Why the duty cycle is not enough to calibrate

Because it equals `consumo / entrega`, so it depends only on the ratio. Every pair with the right
ratio scores exactly the same, and the fit has no way to prefer one. On this grid that is deliveries
from 0.72 to 1.08 all tied.

### What the starts per hour add

The scale. The whole cycle takes `banda / llena` plus `banda / consumo`, and that time shortens when
both parameters grow together, even though the ratio does not change. It is the only measurement in
the record that sees what the duty cycle cannot.

### The fit gave 1.272 and the measurement 1.1796. Which is the good one

The measured one, and not out of loyalty. The fit optimises two summaries of the window; the
measurement comes out of an air balance that closes to 0.7 %. And when they are put to compete over
a real week, the measured one lands eight minutes closer. A 7.8 % difference in the parameters is
worth 1.6 % of the machine's work, so the question of which is the good one matters less than it
looked.

### Why the healthy window was moved to February, and what would have happened without looking

Because from 1 to 12 March the machine is broken. The duty cycle reaches 0.5808, the oil rises ten
degrees, the current doubles and the low pressure alarm fires. There is no report covering any of it.
And calibrating with a failure inside teaches the twin that the failure is normal, the one thing it
cannot learn.

Without looking at the window, the twin would have come out with a delivery far below the real one.
And nobody would have found out, because the only check there was is blind to that error. Modules 27
and 28 would have been built on top. That is the argument for calibrating even when calibrating is
not needed.

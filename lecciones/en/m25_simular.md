---
module: 25
---

## In 30 seconds

- Simulating is advancing the model in slices of time. The size of the slice **decides the result**.
- The step gets swept and everything compared against the finest. The one that still works is **5 s**.
- Half of what the record takes between one reading and the next, and there is a reason for it.
- And the criterion cannot be the duty cycle: at a step of 30 s it looks perfect.
- It has already lost **2 cycles out of 15**. Counting cycles cannot go wrong that way.

## What this module solves

Module 24 left four numbers and four lines. With those you already know **how much** the compressor
loads: consumption over delivery, with no simulation at all.

What you do not know is **when**. How many starts, how often, and what happens if consumption
changes mid afternoon. For that the model has to be run through time, and there a decision nobody
announces turns up: **how big a jump to take**.

It looks like an implementation detail. It is not: it is the parameter that can leave the simulation
saying things the machine does not do.

## Before the theory: a toy example

A tank going down 1 litre per minute, with an alarm at 50 litres. It starts at 55.

Look **every minute** and you see them drop one by one: 55, 54, 53 and so on down to 50, where the
alarm goes off. Five minutes in, correct.

Now look **every ten minutes**. You see 55 and then 45. The alarm still goes off, but **five minutes
late**, and if the tank had also been refilled at 52 you would not have noticed a thing.

With a step of an hour it is worse: you can see 55 and then 55 again, because in between it went
down, the alarm sounded, somebody refilled it and it went back up. **A big step does not give an
approximate result: it gives the result of another machine.**

And now this module's trap. If what you measure is the tank's **average level**, all three steps
give you almost the same thing, because the errors cancel. The average level does not notice. What
does notice is **how many times the alarm sounded**.

## Glossary

- **Integrating in time.** Advancing the state in slices: new state equals the old one plus whatever
  changes in that slice.
- **Step.** The size of the slice.
- **Euler's method.** Exactly that, the simplest way to integrate. It is what this twin does.
- **Convergence.** That on refining the step the result stops moving. If it does not stop moving,
  there is no result.
- **Reference run.** The run with the finest step, against which the others are compared.
- **False green.** A check that passes for the wrong reason. It already came up in module 16.

## Step by step

### Step 1. Write the advance

Two branches, one for each thing the compressor can be doing, and a pressure switch check in each.
It is module 24's model, now inside a loop.

### Step 2. Choose what to compare against

There is no absolute truth, so one gets manufactured: the same simulation with a step **two hundred
times finer than the record**, a tenth of a second. That is the reference.

### Step 3. Sweep the step

Ten sizes, from a tenth of a second to two minutes, all over the same eight hour shift.

### Step 4. Choose what to look at, which is the hard part

And here is the module. The first criterion I tried was the duty cycle, the figure that really
matters. **It came out useless**, and not by a little: its error does not grow with the step, it
goes up and down.

What does always grow is something else, and that is the one that ends up being used.

## The code, in parts

### Step 5. The advance, in full

```python
for _ in range(int(minutos / paso)):
    if cargando:
        p += (entrega - consumo) * paso
        if p >= para: cargando = False
    else:
        p -= consumo * paso
        if p <= arranca: cargando = True; arranques += 1
    if cargando: cargados += paso
```

```anota
range(int(minutos / paso)) | how many slices fit. A finer step means more turns and slower going
p += ... * paso | Euler's method: what changes per minute, multiplied by the slice
las comprobaciones | the pressure switch is looked at AFTER moving the pressure, so a big step can overshoot the threshold
arranques | what is going to be counted. It is the measure that does not let itself be fooled
```

Notice where the problem sits: the pressure moves and **then** you look at whether it crossed. With
a two minute step, in a single jump it can rise 1.5 bar and overshoot the whole band.

### Step 6. The test, and its table

```python
patron = avanza(dep, consumo, 8 * 60, 0.1 / 60)
for segundos in (0.1, 0.5, 1, 2, 5, 10, 20, 30, 60, 120):
    r = avanza(dep, consumo, 8 * 60, segundos / 60)
    se_parece = r["arranques"] == patron["arranques"]
```

```anota
0.1 / 60 | the step in minutes, which is the unit the two rates are in
se_parece | the criterion: the same starts as the reference. Not similar, the same
```

```salida
    paso patrón s   carga 0.0543   arranques  15   error de carga 0.00000
    paso    0.1 s   carga 0.0543   arranques  15   error de carga 0.00000
    paso    0.5 s   carga 0.0544   arranques  15   error de carga 0.00010
    paso      1 s   carga 0.0547   arranques  15   error de carga 0.00036
    paso      2 s   carga 0.0552   arranques  15   error de carga 0.00089
    paso      5 s   carga 0.0547   arranques  15   error de carga 0.00036
    paso     10 s   carga 0.0535   arranques  14   error de carga 0.00085   pierde 1 ciclos
    paso     20 s   carga 0.0542   arranques  13   error de carga 0.00016   pierde 2 ciclos
    paso     30 s   carga 0.0542   arranques  13   error de carga 0.00016   pierde 2 ciclos
    paso     60 s   carga 0.0542   arranques  13   error de carga 0.00016   pierde 2 ciclos
    paso    120 s   carga 0.0542   arranques  13   error de carga 0.00016   pierde 2 ciclos
```

Read the duty cycle error column top to bottom and then the starts one. **One goes up and down; the
other only gets worse.**

### Step 7. Turn the knob

```perilla
m25_paso
```

Move the step and watch the trace. At first nothing changes, and past a certain point the steps get
longer and fewer: those are the cycles the simulation is skipping.

## The result, measured

{{FIG:fig_m25_ciclo_carga_vacio}}

That is what the twin does inside: the pressure rises while it loads, crosses **10.10 bar** and the
compressor lets go; it falls slowly to **8.05** and starts again. A sawtooth, and the hysteresis is
what gives it its teeth.

It is the only figure in this course that draws the pressure, and it is allowed because here it
**explains the mechanism**. The double trace rule forbids something else: hunting a leak by looking
at the pressure, which is exactly what does not work.

{{FIG:fig_m25_paso_de_tiempo}}

**What we expected.** An error growing with the step, and a good step equal to the last one below
some threshold.

**What came out.** That the duty cycle's error **does not grow**. At a step of 30 s it is the
smallest in the whole table apart from the reference's, and by then the simulation has already eaten
**2 cycles out of 15**.

It is not chance nor bad luck. A coarse step skips starts, and every skipped start lengthens the
next unload and shortens the next load, **and the two errors cancel in the mean**. The duty cycle
comes out fine for the wrong reason: it is module 16's false green, now in a simulation.

Counting cycles that does not happen:

| Step | Cycles out of 15 | Any good? |
|---|---|---|
| 0.1 to 5 s | 15 | yes |
| 10 s | 14 | no |
| 20 to 120 s | 13 | no |

**The largest step that still works is 5 s**, half of what the record takes between one reading and
the next. And it makes sense that it is finer, because they are two different jobs. The record only
has to **see** the cycles. The simulation has to **close** them.

Each step advances the pressure and then looks at whether it crossed. With ten seconds it overshoots
by up to 0.2 bar, that is a tenth of the band.

What to compare it against so it is not a loose number: the short phase of the cycle, which is the
load, lasts **1.74 minutes**. The good step is a twentieth of that.

**What it means.** That the step is not chosen, it is measured. And **the quantity you measure it
with matters more than the threshold**: with the duty cycle, two minutes would have looked like
enough.

## Watch out

- **The step gets checked, not chosen.** And it is checked against a finer run, because there is no
  other truth to compare with.
- **Do not use the quantity you care about as your convergence criterion.** Here the duty cycle is
  what you want to compute and it is precisely the worst judge, because its errors cancel.
- **Count events.** Starts, crossings, changes of state. An event either happens or it does not:
  there is no way for it to cancel against another.
- **A fine step is not free.** This module's reference takes one turn per tenth of a second of the
  eight hours. For a shift that is fine; for the twin's scenarios it is not.
- **Euler skips thresholds.** It moves the state and then looks. There are methods that detect the
  crossing and step back, and they are not needed here because 5 s already resolves everything.
- **If the machine gets faster, the step has to come down.** This sweep was redone when module 24's
  parameters were corrected, and the good step went from 10 s to 5. It was not corrected by hand: it
  was run again.
- **This holds for this compressor's consumption.** With consumption five times higher the cycles are
  five times shorter and the good step would drop. The test gets repeated if the regime changes.

## Metallurgical bridge

An automatic sampler on a belt takes an increment every so often. And the eternal question is how
often.

Picture ore in truckloads, with grades differing from one to the next. A sampler taking an increment
every two hours will give **a plausible average grade** and will not see a single load. The shift
average comes out spot on and the sampling is useless: it cannot tell you which truck brought the
bad grade.

It is exactly this module's step. The average survives any frequency; **what gets lost are the
events**, and the events are what you are after.

## Do it yourself

```reto
pregunta: Measure how long each load and each unload lasts on 5 June 2020, which is what the simulation has to reproduce. Return `estado`, `tramos` and `minutos` with the median duration in minutes, ordered by `estado`. Two rows.
inicio: SELECT timestamp, DV_eletric,
       sum(CASE WHEN antes IS DISTINCT FROM DV_eletric THEN 1 ELSE 0 END)
           OVER (ORDER BY timestamp) AS tramo
FROM (SELECT timestamp, DV_eletric,
             lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
      FROM telemetria WHERE day = DATE '2020-06-05');
esperado: m25_cuanto_dura
pista: The starting point already numbers the stretches: every time the compressor changes its mind, the running sum goes up by one. What is missing is grouping by `tramo` to get each one's duration with `date_diff` between its first and last mark, and then grouping again by whether it was loading or not.
solucion: SELECT CASE WHEN cargando = 1 THEN 'carga' ELSE 'vacio' END AS estado,
       count(*)                  AS tramos,
       round(median(minutos), 2) AS minutos
FROM (SELECT any_value(DV_eletric) AS cargando,
             date_diff('second', min(timestamp), max(timestamp)) / 60.0 AS minutos
      FROM (SELECT timestamp, DV_eletric,
                   sum(CASE WHEN antes IS DISTINCT FROM DV_eletric THEN 1 ELSE 0 END)
                       OVER (ORDER BY timestamp) AS tramo
            FROM (SELECT timestamp, DV_eletric,
                         lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
                  FROM telemetria WHERE day = DATE '2020-06-05'))
      GROUP BY tramo)
GROUP BY estado
ORDER BY estado;
```

Thirty one cycles in the day, with loads of **2.13** minutes and unloads of **19.98**. Compare those
two figures with what the twin does in the knob above, at its starting position: it is the same
machine.

## Review

### What simulating means here

Advancing the model's state in slices of time, adding in each one whatever changes. The state is a
single variable, the pressure. In each slice the inflow minus the outflow gets added to it, and then
you look at whether the pressure switch changes its mind.

### Why the size of the step changes the result

Because the pressure switch is checked after moving the pressure. With a big step the pressure jumps
over the whole band in a single move, and the start that should have happened in the middle does
not. The simulation does not come out approximate: it comes out of another machine.

### Why the duty cycle is a bad judge of convergence

Because its errors cancel. Every lost start lengthens an unload and shortens a load, and the mean
barely moves. Here, at a step of 30 s the duty cycle's error was among the smallest in the table and
two cycles out of fifteen had already been lost.

### What the criterion is then

Counting events, which here are the starts. A start either happens or it does not, so there is no
way for one error to cover another. With that criterion the degradation is monotone and the boundary
is clear.

### The good step is finer than the record. Why

Because they are two different jobs. The record only has to **see** the cycles, and a load of 1.74
minutes is plainly visible with a reading every ten seconds.

The simulation has to **close** them. It advances the pressure a whole step and only then looks at
whether it crossed the stopping pressure. With ten seconds it overshoots by up to 0.2 bar, and one
cycle out of fifteen escapes it.

An earlier version of this lesson published here that the good step matched the record's, and looked
for a meaning in it. It did match, and the meaning was invented: on correcting module 24's
parameters the coincidence came undone by itself.

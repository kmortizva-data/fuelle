---
module: 23
---

## In 30 seconds

- A digital twin is not a three dimensional drawing nor a pretty dashboard.
- It is **a model running alongside the machine**, and its disagreement means something.
- That disagreement is called the **residual**, and it is the only thing a twin delivers.
- Across healthy days the twin never parts from the machine by more than **14.0 minutes**.
- On 18 April it parts by **1,335.7**, which is **95 times** that worst healthy case.

## What this module solves

"Digital twin" is sold as very different things. A rotating mock up. A dashboard with a photo of the
equipment and some numbers on top. A model trained on six months of data that predicts a failure.

None of the three is what this project is going to build, and it is worth saying so before building
it.

A twin, here, is **a model of the machine's physics that runs at the same time as it does, on the
same inputs**. And what you look at is not what it predicts: it is **how it differs from reality**.

## Before the theory: a toy example

Two identical furnaces, side by side, with the same charge and the same gas.

| Time | Furnace A | Furnace B |
|---|---|---|
| 08:00 | 900 °C | 900 °C |
| 10:00 | 920 °C | 918 °C |
| 12:00 | 915 °C | 870 °C |
| 14:00 | 918 °C | 845 °C |

Nobody needs to know anything about furnaces to see that B has had a problem since midday. **And you
do not need to know what the correct temperature is**: it is enough to have another identical
furnace next to it.

That is a twin, and its value sits exactly there. It does not say "910 degrees is normal", a rule
with an owner and an expiry date. It says **"these two should agree and they do not"**.

The difference between the two columns is the residual. When it is zero there is no news. When it
opens up, there is.

And now the part that makes all of this useful. **In a plant you do not have two furnaces.** You
have one, so the second has to be manufactured, and that is what a model is for: it is furnace B.

## Glossary

- **Digital twin.** A model of a machine that runs on its same inputs, alongside it, so the two can
  be compared.
- **Residual.** The difference between what the machine does and what the model does.
- **Controlled variable.** The one a control loop holds where it wants it. Here, pressure.
- **Manipulated variable.** What the control moves to get there. Here, how hard the compressor works.
- **First principles.** A model made of known physics rather than fitted data. This course's is one.
- **False alarm.** A warning with no failure behind it. It is the currency sensitivity is paid in.

## Step by step

### Step 1. Decide what it has to get right

A twin does not reproduce the whole machine, and wanting that is the fastest way to never finish
one. It reproduces **one thing**, and here it is the **duty cycle**: how much time the compressor
spends loaded.

### Step 2. And decide what it will NOT look at

Pressure, because the control holds it. In a leaking compressor the pressure stays where it should,
and what changes is **how hard you have to work to hold it there**.

This is not a theory of this course, it is measured. On this project's test page, moving a simulated
leak from 5 to 40 litres per minute, **the two pressure curves parted by 32 pixels and then by 31**.
Nothing. The cumulative work ones went from 15 to 51.

### Step 3. Run the model on what it knew before

The twin is calibrated over a healthy period and after that **it is not touched**. It will see
failure days with the parameters from when everything was fine, and that is why it falls short: it
does not know there is a leak.

### Step 4. Look at the gap, not at the prediction

If the twin gets it right there is no news. If it is wrong there is news, and the size of the error
is the news. That is this module's change of mind: **a model whose error is the product**.

## The code, in parts

### Step 5. The whole twin, again

```python
if cargando:
    p += (entrega - consumo) * paso
    if p >= para: cargando = False
else:
    p -= consumo * paso
    if p <= arranca: cargando = True
```

```anota
entrega - consumo | how fast the receiver rises per loaded minute. The four numbers come out of the lake in module 24, none of them invented
p >= para | the pressure switch lets go at the top and asks to load again down at `arranca`. No temperature, no geometry, no fitted data
```

There is no more. That is the whole twin, and modules 24 and 25 are about where its four numbers
come from and how to make it run without breaking it.

### Step 6. And the residual

```python
residual = minutos_que_carga_la_maquina - minutos_que_carga_el_gemelo
```

```anota
residual | that is all. A twin does not deliver a prediction, it delivers a difference
minutos_que_carga_la_maquina | the unit matters: these are compressor minutes, something a maintenance lead understands
```

```salida
  día sano   : la máquina 80.8 min, el gemelo 80.5, hueco 0.3
  los 7 días sanos completos van de 66.5 a 90.0 min, y el hueco mayor entre ellos es 14.0
  18 de abril: la máquina 1416.2 min, el gemelo 80.5, hueco 1335.7
  el hueco de la avería es 95,4 veces el mayor de los días sanos
```

## The result, measured

{{FIG:fig_m23_gemelo_y_residual}}

**What we expected.** That the twin would follow the machine on a healthy day and fall short on a
failure day.

**What came out.** Exactly that, and with a distance between the two cases that leaves no room for
doubt.

On a healthy, complete day, 18 February, the machine loaded for **80.8** minutes and the twin
predicted **80.5**. They are less than twenty seconds apart.

That agreement is too pretty to believe, and it is worth saying why. The twin predicts the same
thing every day, and 18 February is **the day closest to the median** of the healthy days. So the
comparison is habit against the day that looks most like habit. Any other day would come out worse,
and that is exactly the thing to measure.

**So the bar does not come from one day, it comes from all of them.** The healthy window holds
**seven** days with their full 8,640 readings, and the machine loaded between **66.5** and **90.0**
minutes on them. Against the twin's single prediction, the worst of those days is off by **14.0
minutes**.

On 18 April, the first documented failure, the machine loaded for **1,416.2** minutes, that is
almost the whole day. The twin, still knowing nothing, predicted the same **80.5** as always.

| | The seven healthy days | 18 April |
|---|---|---|
| The machine | 66.5 to 90.0 min | **1,416.2 min** |
| The twin | 80.5 min | 80.5 min |
| The gap | up to 14.0 min | **1,335.7 min** |

**95 times the worst healthy day.** That ratio is what makes the idea work. And it is measured
against the worst case, not the best. For setting up a warning that is the only one worth having: an
alarm does not have to clear the quiet day, it has to clear the strangest healthy one.

**What it means.** That there is room. A twin that can be 14 minutes wrong is no good for saying
exactly how many minutes the compressor will load tomorrow, and **it does not need to be**. It is
good for noticing something ninety five times bigger than its worst error.

What is left ahead is engineering, not concept. Checking whether searching for the parameters
instead of measuring them sharpens anything, in module 26. Deciding what size of gap raises a
warning, in 27. And checking against the four failures whether the warning arrives in time and
without waking anybody for nothing, in 28.

## Watch out

- **A twin is not a prediction, it is a comparison.** If somebody sells you one on how well it gets
  things right, they are selling you something else.
- **Do not look at the controlled variable.** The control holds it, so there is no signal there. It
  is measured in this project: 32 pixels against 31 when the leak is quadrupled.
- **The twin is not recalibrated on the failure data.** Let it learn from the bad period and it
  stops being surprised, and the residual disappears. It is calibrated on healthy and frozen.
- **A big residual does not say what is happening.** It says something is. Telling a leak from a
  dirty filter is another job, and this project does not promise it.
- **Four failures are not statistics.** What module 28 will hold is a study of four cases, and it
  says so.
- **A single healthy day is not a noise floor.** Measure the twin's error against one day, and on
  top of that against the one closest to the average, and you get an error of twelve seconds and a
  ratio in the thousands. That is not precision, it is dividing by almost zero. The floor comes from
  the spread.
- **And the healthy window has to be looked at, not just picked by date.** This course's ran to 15
  March, chosen before the first documented failure precisely so as not to pick for convenience. It
  held twelve days of failure inside that nobody had documented. Module 26 tells how it turned up.

## Metallurgical bridge

Any plant carries a theoretical metallurgical balance next to the real one. Not because the
theoretical one is truer, but so the two can be subtracted.

Suppose a measured recovery of 88 % and a model that, at that head grade and that particle size,
expected 91. Those three points of difference **are that week's work for the metallurgist**. It
could be a cell with the froth down, a reagent dosing badly or a biased sample, but nobody would
have looked at any of them without the model alongside.

And notice that nobody cares whether the model nails the 91. What matters is that it be **the same
model every week**, so that a change in the difference means a change in the plant.

## Review

### What exactly a digital twin is, in this project

A model of the compressor's physics, with parameters measured over a healthy period. It runs
alongside the machine and produces one thing: the difference between what was done and what was
expected. That difference is the residual, and it is the product.

### Why the twin looks at the duty cycle and not at the pressure

Because pressure is the controlled variable and the loop holds it whatever happens. A leak does not
drop the pressure, it makes the compressor work harder to keep it. The signal is in the manipulated
variable, and here that is the time spent loaded.

### Why the twin is not recalibrated when new data arrives

Because then it would learn the failure and stop being surprised. The twin has to keep representing
the healthy machine; its disagreement with today's machine is precisely what is being measured.

### The twin can be 14 minutes wrong on a healthy day. That is not too much

It depends what against. For predicting tomorrow's load it is. For detecting something 95 times
bigger than that error, it is not. The useful question is not how wrong a model is, it is how wrong
it is compared with what it has to tell apart.

And notice where that 14 comes from: it is the **worst** of the seven healthy days, not the best nor
the average. A bar set with the best case falls over on the first odd day.

### What this twin will NOT be able to say

Which failure it is. A big residual says the machine is working harder than it should, and that
could be a leak, a dirty filter or more demand from the plant. Separating those causes would need
more signals than there are, and promising it would be selling something else.

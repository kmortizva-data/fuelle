---
module: 28
---

## In 30 seconds

- **4 of 4 against 2 of 4**: the failures the twin catches, and the ones the installed alarm catches.
- And it does it waking somebody **1.5 times a month** against the installed one's 11.4.
- As a **detector** it wins. As a **predictor** it does not: it warns beforehand on one of the four,
  by a day.
- It also finds the twelve days of March nobody documented, and that goes in both counts.
- And an uncomfortable one, checked rather than assumed: **it orders the days just like a threshold
  on the duty cycle**.

## What this module solves

This is where it pays off or it does not. Five modules building a twin, and the question left is
whether it is good for anything that was not already covered.

And there are three ways of answering that question by cheating, so it is worth saying how all three
are avoided before showing any number.

**The first is grading your own exam.** Module 27 measured the residual and **refused to choose a
threshold**. That way, whoever measures and whoever grades are not the same script. Here the
threshold is swept whole, from 0.10 to 1.20, and the numbers are published for the complete sweep.

**The second is calling a standing alarm a warning.** If the alarm fired twelve days before the
report, that is twelve days of warning only if somebody would have done something. If it had been on
for two months, it is worth nothing. That is why every lead time comes with **how long the episode it
belongs to had been sounding**.

**And the third is competing against nobody.** Two rivals: an ordinary threshold on the duty cycle,
and **the low pressure alarm this compressor already has fitted**.

## Before the theory: a toy example

A smoke detector in a kitchen. In a year there are **2 fires** and the detector goes off **50 times**.

| | Goes off | Does not |
|---|---|---|
| There is a fire | 2 | 0 |
| There is no fire | 48 | 313 |

It catches both fires: as a detector it is perfect. And it goes off **48 times for nothing**, nearly
one a week, so by the third somebody takes the battery out and the detector stops existing.

**The two figures always travel together.** A detector that catches everything is easy: set the
threshold at zero and there it is. A detector that never bothers anybody is just as easy. The
question is where the pair lands, and against what pair it is compared.

## Glossary

- **Detector.** Judged on whether it notices the failure while it is happening.
- **Predictor.** Judged on whether it warns **beforehand**. They are two different marks and this
  module gives both.
- **False alarm.** A day it goes off and there was nothing. Here they are counted per month, which is
  the unit whoever is on call suffers them in.
- **Episode.** Alarm days in a row. It is needed so as not to confuse a warning with an alarm that
  had already been on for half a week.
- **Sweep.** Trying every threshold and publishing the whole curve, instead of choosing one and
  showing only what comes out well with it.

## Step by step

### Step 1. Decide what counts as a hit

A failure report covers some days. If the alarm goes off on any of them, that report is detected. The
four reports cover **7 days** between them.

### Step 2. Decide what counts as a warning, which is harder

It is not enough for the alarm to be on before the report. You have to look at **when the episode
that reaches it lit up**. If it lit up the day before, it is a one day warning. If it had been on for
three weeks, it is not a warning: it is background noise that happened to include the date.

### Step 3. Sweep the threshold, do not choose it

Twenty three thresholds, from 0.10 to 1.20 bar/min. The lowest sits just above the noise floor module
27 measured; below it, the alarm would be sounding in February.

### Step 4. Find yourself real rivals

A trivial one, to see whether the twin adds anything. And an installed one, to see whether it adds
anything **beyond what was already there**.

## The code, in parts

### Step 5. The episode, which is what stops the lead time being inflated

```python
for ini, fin in rachas:
    if ini < suceso.date() <= fin + timedelta(days=1):
        antes = (suceso.date() - ini).days
        largo = (fin - ini).days + 1
```

```anota
rachas | the alarm days grouped into consecutive runs, not loose
antes | the days from the episode lighting up to the report. That is the real lead time
largo | and how long the whole episode lasted, which is what the lead time has to be read against
```

### Step 6. The trivial rival gets checked, not asserted

```python
por_residual = sorted(dias, key=lambda f: -f.pico)
por_carga = sorted(dias, key=lambda f: -f.carga)
mismo_orden = por_residual == por_carga
```

```anota
sorted(...) | the same days, ordered by the residual and by the duty cycle
== | if the two lists are identical, any threshold on one has its exact twin on the other
mismo_orden | it is the lesson's most uncomfortable claim, and an uncomfortable claim left unchecked is an excuse
```

### Step 7. Turn the knob

```perilla
m28_umbral
```

The knob starts at the threshold the sweep chose. Lower it and watch the trace pull away from the
dotted line. That line is the days with a real failure, and everything above it is night shifts spent
on nothing.

## The result, measured

{{FIG:fig_m28_cuatro_averias}}

**What we expected.** That the twin would detect all four and warn with some lead time.

**What came out.** The first, yes, and well. The second, no.

```salida
  el suelo de ruido del módulo 27 está en 0.1165, y de ahí para arriba se barre el umbral
  el registro abarca 8 meses, y ese es el divisor de todos
  los cuatro partes cubren 7 días

  congelado, marzo cuenta
    umbral | detecta | avisa antes | antelación | falsas/mes
       0.1 |  5 de 5 |           2 |       10 d |       15.6
       0.3 |  5 de 5 |           1 |        1 d |        3.6
       0.5 |  5 de 5 |           1 |        1 d |        2.9
       0.7 |  5 de 5 |           1 |        1 d |        2.2
       0.9 |  5 de 5 |           1 |        1 d |        1.9
       1.1 |  5 de 5 |           0 |          - |        1.2
```

### As a detector: it wins, and it beats what was already there

The highest threshold that still catches them all is **1.15 bar/min**. There the twin:

| | The twin | The installed alarm |
|---|---|---|
| Failures detected | **4 of 4** | 2 of 4 |
| Days with an alarm | 18 | 94 |
| False alarms per month | **1.5** | 11.4 |

**Twice the failures at a seventh of the false alarms.** In the trade off figure, the orange cross
sits low and far to the right of the curve: worse on both counts at once.

**And now the qualification, which is compulsory.** The LPS is not a leak detector the twin has
beaten on its own ground. It is a low pressure alarm, and it fires above all **when the record comes
back after an outage**, with the receiver empty and the compressor catching up. Of its 136 hours with
the alarm on, 101 fall in incomplete hours of record.

So the honest comparison is not "the twin detects better than the LPS". It is this other one, the one
a plant cares about: **the only thing installed on this machine sounds a third of the days and still
misses half the failures**. A twin made of four measured numbers improves on it in both. That the
rival was answering a different question is part of the problem, not of the excuse.

**A note on method, because it changed the result.** Those 94 days come from counting the LPS over
raw readings. The first version counted it over the same complete hours the twin uses, and got 28
days and 3.1 false alarms a month. The complete hours filter exists because a duty cycle drawn from
thirty readings is not that hour's, but **the LPS averages nothing**: it fires or it does not.
Applying a rule designed for the twin stripped three quarters of its firings and left it looking
better than it is. Winning a comparison on a technicality is the quietest way to cheat.

{{FIG:fig_m28_antelacion_vs_falsas}}

And notice the shape of that curve, because it says something I did not expect: **it is a cliff, not
a slope**. Lowering the threshold below 1.15 does not buy a single failure more and does buy false
alarms, up to 17 a month at the far end. The classic trade off between sensitivity and nuisance does
not exist here, because all four failures take the residual to the ceiling.

### As a predictor: no

Of the four, **only one warns beforehand**: 15 July's, by **one day**, in an episode that lasted two
days in total. The other three raise the alarm **on the day of the report itself**.

In the magnifier's five panels it looks the same: the curve rises right on the shaded band, not
before. This course's syllabus promised "days of warning", and **the data do not give them**. So the
module publishes the two marks separately and does not average one with the other.

There is a physical reason for it, and it is no consolation: an air leak in a pneumatic system does
not grow slowly over days. It opens. The compressor goes from working 6 % of the time to working
100 % within hours, and there is no ramp to see in advance.

### And the detection arrives late

It is worth saying even though it spoils the headline. The threshold that gets the 4 of 4 is
**1.15**, and the residual's ceiling is at **1.1796**. So the alarm fires when the compressor is
practically flat out. That is not subtlety, it is noting a disaster already under way.

With lower thresholds the alarm comes a little earlier and the false ones take off. The reason is
module 27's drift: the machine really does degrade and the twin notices. It is in the table, and
everyone sets the threshold where it hurts them least.

### The twelve days of March, in both counts

Module 26 found that from 1 to 12 March the machine was broken without any report covering it.
Counting it as a hit is believing your own model; not counting it is throwing away the best evidence
there is in the twin's favour. So both counts go in:

| At threshold 1.15 | Detects | False per month |
|---|---|---|
| March counts as a failure | **5 of 5** | **1.2** |
| March counts as a false alarm | **4 of 4** | **1.5** |

**The difference between those two rows is what a missing label costs.** Twelve days of sick machine
left unwritten move this project's result. In any plant it goes the same way: the model gets judged
against a failure log, and that log is also a dataset with its holes.

### The uncomfortable part, said in full

With frozen parameters,

```
residual = carga × entrega − consumo
```

is an increasing function of the duty cycle and nothing else. So **a threshold on the residual and
one on the duty cycle order the days exactly alike**. And this is not a piece of reasoning: the
script checks it over the record's **207** days and it comes out yes.

Put another way: **anything this twin detects is also detected by counting how hard the compressor
works**, which is a three line SQL query and no model.

So what is the twin for? For three things the threshold does not give, and none of them is detecting:

1. **Units.** The twin says "0.35 bar per minute are leaking", not "the index is at 0.73". That gets
   taken into a maintenance meeting and argued about.
2. **It needs no history.** A threshold has to be learned from past failures. The twin's parameters
   are measured over a healthy month, without a single failure inside, as was done in module 24.
3. **It answers questions that have not happened.** How much it would have to leak for the alarm to
   fire, how long the receiver would hold with half the plant stopped. Module 27's knob is exactly
   that.

**What it means.** The twin works, it beats the installed alarm, and it is no good for what it is
most often sold on. A project with only the first half of that sentence would be prettier and less
true.

## Do it yourself

```reto
pregunta: Reproduce the verdict in one query. Get each day's maximum residual (`carga * 1.2507 - 0.0711`, skipping hours with fewer than 300 readings), classify each day as `con parte` or `sin parte` according to whether it is one of the seven days the four reports cover, and count how many days there are of each class and how many clear the threshold of 1.15. Return `clase`, `dias` and `saltan`. Two rows.
inicio: SELECT hora::DATE AS dia,
       max(carga * 1.2507 - 0.0711) AS residual
FROM horas
WHERE lecturas >= 300
GROUP BY 1;
esperado: m28_aciertos_y_falsas
pista: The starting point already gives one day per row. Wrap it in a `WITH` and classify on top with a `CASE WHEN dia IN (...)`. The seven days are 18 April, 29 and 30 May, 5, 6 and 7 June, and 15 July. To count the ones clearing the threshold, `count(*) FILTER (WHERE residual > 1.15)`.
solucion: WITH d AS (
  SELECT hora::DATE AS dia,
         max(carga * 1.2507 - 0.0711) AS residual
  FROM horas WHERE lecturas >= 300 GROUP BY 1
)
SELECT CASE WHEN dia IN (DATE '2020-04-18', DATE '2020-05-29',
                         DATE '2020-05-30', DATE '2020-06-05',
                         DATE '2020-06-06', DATE '2020-06-07',
                         DATE '2020-07-15') THEN 'con parte'
            ELSE 'sin parte' END AS clase,
       count(*)                               AS dias,
       count(*) FILTER (WHERE residual > 1.15) AS saltan
FROM d GROUP BY 1 ORDER BY 1;
```

Of the **7** days with a report **6** go off, and of the **200** without one **12** do.

And there is a lesson hidden there: **6 of 7 days is not the same as 4 of 4 failures**. The missing
day is one of those covered by a long report, and the report is still detected because it went off on
another of its days. Counting days and counting failures give different marks, and you have to say
which one you are counting.

## Watch out

- **Detector and predictor are two marks.** Here one is good and the other is not. Publishing only
  the average would be hiding the bad one behind the good one.
- **A lead time without the episode's length says nothing.** Twelve days of warning from an alarm
  that had been on for forty is zero days of warning.
- **Compare against what is already installed**, not against nothing. A detector that does not beat
  the alarm the machine came with does not get installed.
- **Check the trivial rival.** If an ordinary threshold orders the days just like your model, your
  model does not win on detection and you have to say what it does win on.
- **Four failures are not a sample.** It is a study of four cases and it is presented as one: with
  four events, one hit more or less changes the whole result.
- **The failure log is also data, and it has holes.** Twelve days of sick machine with no report were
  there from the start.
- **A threshold that only fires with the compressor flat out detects disasters, it does not warn of
  them.**

## Metallurgical bridge

Anyone who has set a grade alarm on tailings knows this whole table. Set the threshold tight and the
control room silences it within a week; set it loose and it does not warn about the upset that
mattered. And the conversation always ends the same way: not on which threshold is correct, but on
how many times a shift the operator is willing to get up.

The other parallel is the downtime log. The model gets validated against the maintenance book, and
that book is written by people in a hurry at three in the morning. Short stops do not get written
down, causes get copied from the one before, and a whole shift can end up blank. When the model flags
a day the book does not cover, the first reaction is that the model is wrong. Sometimes it is the
other way round, and here it was, for twelve days of March.

## Review

### What exactly this module answers

Whether the twin detects the four documented failures, with how many false alarms, with how much lead
time, and whether that is better than the alarm the machine already carries. Four questions and four
separate answers, without averaging them into an overall mark.

### Why the twin wins as a detector and loses as a predictor

Because an air leak does not grow slowly. The compressor goes from 6 % to 100 % load within hours, so
when there is something to see it is already enormous and when there is not there is nothing.
Detecting is easy; anticipating would need a signal that moved earlier, and in this record there is
none.

### Why the lead time is measured with the episode and not with the date

Because an alarm on for weeks necessarily includes the day of the report, and presenting that as lead
time would be claiming background noise as a merit. Measuring from when the episode lit up, only one
of the four warns, and it warns by a day.

### If a threshold on the duty cycle does the same, what is the twin for

For what the threshold does not do. It gives the leak in bar per minute rather than as an index with
no units, it is calibrated on a healthy month with no need for a failure history, and it allows
questions about a leak that has not happened yet. On pure detection it does not win, and the module
checks that rather than assuming it.

### What it would take for this twin to predict

Changing signal. The duty cycle fires with the leak already open. Something that moves earlier would
be needed: the oil temperature, the starting current, or the valves' signature within a cycle. This
project does not promise it nor deliver it, and saying so is part of the deliverable.

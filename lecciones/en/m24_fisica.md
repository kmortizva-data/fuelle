---
module: 24
---

## In 30 seconds

- A receiver that fills and empties, and a switch with a memory. There is nothing else.
- The datasheet promises it starts at **8.2 bar** and it starts at 8.05: **8.2 against 8.05**.
- The model's two parameters come out of an **air balance** that closes to **0.7 %**.
- And with them the model predicts a duty cycle of **0.0568** when the machine did **0.0572**.
- Watch the record's gaps: **28 stretches** were swallowing **3,129 minutes** of compressor
  that never existed.

## What this module solves

For a twin to be any good it has to be a model of something, and that something here is simple: **an
air receiver with a pressure switch**. The compressor fills it, the plant empties it, and a pressure
switch decides when to start.

The hard part is not writing those equations. It is **where their numbers come from**, because a
model with invented parameters is a cartoon.

None of them is invented here. All four are measured from the lake and checked against the
manufacturer's datasheet where that is possible. And they are verified with **a law that admits no
argument**: the air that went in equals the air that was spent.

## Before the theory: a toy example

A water tank with a pump and an open tap.

| What | How much |
|---|---|
| The tank, full | 100 litres |
| The pump puts in | 10 litres per minute |
| The tap takes out | 2 litres per minute |
| The pump starts below | 40 litres |
| The pump stops on reaching | 80 litres |

With that you can already tell everything that tank does, with no further physics.

**Filling:** 10 go in and 2 go out, so it rises 8 litres per minute. From 40 to 80 there are 40
litres, so **5 minutes pumping**.

**Emptying:** the pump is stopped and the tap keeps running, so it drops 2 per minute. From 80 to 40
there are 40 litres, so **20 minutes of rest**.

So the cycle lasts 25 minutes and the pump works 5, that is **20 % of the time**. And that 20 % also
comes out of a shorter sum: what is spent divided by what is put in, 2 over 10.

That last one is the result to take away. **The duty cycle is consumption divided by delivery**, and
no simulation is needed to know it. Simulating is for what comes after.

And now the awkward part. In the toy tank I gave you the five numbers. On the real compressor
**nobody gives them to you**: the datasheet gives one, gets it wrong, and the rest have to come out
of the data.

## Glossary

- **Receiver.** The volume of pressurised air that cushions between inlet and outlet. On this train
  it is the APU with its bottles.
- **Pressure switch.** The switch that watches the pressure and decides. `MPG` in this file.
- **Hysteresis.** Starting at one pressure and stopping at a higher one. Without it, the compressor
  would switch on and off endlessly at the threshold.
- **Band.** The distance between those two pressures.
- **Delivery.** What the compressor puts in per minute, measured as a rise in pressure.
- **Consumption.** What the plant spends, measured the same way.
- **Duty cycle.** The fraction of time the compressor spends loaded.

## Step by step

### Step 1. Find the pressure switch's two pressures

You do not ask the datasheet: you look at the moments when `DV_eletric` changes, and note what
pressure there was. The median of those moments is the switching pressure.

### Step 2. Split the record into stretches

Every load and every unload, end to end. A stretch is a piece with the compressor doing the same
thing.

**Without filtering by duration**, and that took a while to understand. The first attempt kept only
stretches of two minutes or more, so the slope would be reliable. Since loads last 1.8 minutes and
unloads 22, that filter threw away almost every load and not one unload.

### Step 3. Close the air

Over a whole month the pressure ends where it started, so **the bar put in have to equal the bar
spent**. It is the check that decides whether the measurement is worth anything.

If they do not close, what is wrong is the measurement, not the machine. And if they do close, the
two parameters come out by themselves: the rise per loaded minute, and the fall per unloaded minute.

### Step 4. Check that they predict the cycle

The toy example's duty cycle, consumption over delivery, has to give what the machine really did.
**Neither parameter was adjusted for that**, so if they match it is because the model describes the
machine.

## The code, in parts

### Step 5. The two pressures, measured

```sql
SELECT CASE WHEN antes = 0 THEN 'arranca' ELSE 'para' END AS momento,
       round(median(TP3), 2) AS presion
FROM (SELECT TP3, DV_eletric,
             lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
      FROM plata WHERE medido AND day BETWEEN DATE '2020-02-01' AND DATE '2020-02-29')
WHERE antes IS NOT NULL AND antes <> DV_eletric
GROUP BY momento
ORDER BY momento;
```

```anota
lag(DV_eletric) | what the compressor was doing on the previous reading. It is module 13's window function
antes <> DV_eletric | keep only the readings where it changed its mind
median(TP3) | the typical pressure at that moment. The median and not the mean, because some transitions fall in a gap in the record
```

```salida
┌─────────┬─────────┐
│ momento │ presion │
│ varchar │ double  │
├─────────┼─────────┤
│ arranca │    8.05 │
│ para    │    10.1 │
└─────────┴─────────┘
```

**The datasheet says 8.2 and the machine starts at 8.05.** It is module 1 again, and the datasheet is
not wrong: a real pressure switch has a tolerance, and what matters is the one fitted to this train.
The stopping pressure the datasheet does not give, and it is **10.10**.

### Step 6. The balance, which is what validates the measurement

```python
metidos  = sum(p_fin - p_ini for tramo in tramos if tramo.cargando)
gastados = sum(p_ini - p_fin for tramo in tramos if not tramo.cargando)
entrega  = metidos / minutos_cargando + consumo
consumo  = gastados / minutos_en_vacio
```

```anota
metidos y gastados | the bar that rise while it loads and the ones that fall while it does not. Over a whole month they have to be equal
partido por minutos | this is where the two parameters come from, per minute and not per reading: what moves the air is the total, not one instant's slope
entrega = subida + consumo | while it loads, air is being spent too, so what the compressor puts in is what you see rise plus what leaves
```

```salida
  el balance de aire, que es lo que decide si la medida vale:
    metidos             2311.7 bar
    gastados            2295.0 bar
    descuadre             0.7%

  sube por minuto cargando   1.1796 bar/min
  mediana instantánea         1.248 bar/min   un 6% de más
  consumo                    0.0711 bar/min
```

It closes to **0.7 %** over a month. I did not impose that: the two numbers are measured separately
and they agree, and that agreement is what says the measurement was done properly.

### Step 7. And the whole model, in four lines

```python
if cargando:
    p += (entrega - consumo) * paso
    if p >= para: cargando = False
else:
    p -= consumo * paso
    if p <= arranca: cargando = True
```

```anota
p | the pressure, which is the twin's entire state. One single variable
paso | the little slice of time advanced each turn. That is what module 25 is about
las dos condiciones | the whole pressure switch. The hysteresis is that the two thresholds differ
```

That is the twin. Four lines and four numbers, and not one of the four is invented.

### Step 8. Turn the knob

```perilla
m24_consumo
```

Raise the consumption and watch the trace: the compressor spends more time loaded, and the steps
bunch up. Lower it and they spread out. **Pressure does not appear anywhere**, and that is on
purpose: it is the variable the control holds, which is why it says nothing.

## The result, measured

{{FIG:fig_m24_balance_del_deposito}}

**What we expected.** That the compressor filled at one rate, a single one, measurable by taking any
of the slopes on the way up.

**What came out.** That there is no one rate, there is a ramp. For the first ten seconds the pressure
rises **0.804 bar/min**, because the motor is starting and that is the 9 A current the datasheet
mentions. Then it peaks at **1.608** and from there it **falls** as the receiver fills and pushes
back.

The **instantaneous median** of those slopes is **1.248 bar/min**, and what the compressor really
achieves per loaded minute is **1.1796**. A **5.8 %** difference, and the median is what comes out if
you measure without thinking.

**It costs less than it looks, and it is worth saying so.** A model built on the median predicts a
duty cycle of **0.0539**, **5.8 %** below what the machine did. The ramp is real and the median is
the wrong measurement, but the price of getting it wrong here is small. With the per minute mean:

| What | Value |
|---|---|
| Duty cycle the model predicts | **0.0568** |
| Duty cycle the machine did | **0.0572** |
| They differ by | 0.7 % |

**What it means.** That the twin now exists, and that its two parameters were not touched to make it
add up. They were measured separately, the air balance was checked, and the prediction came out on
its own.

## Watch out

- **A median of slopes is not a mean rate.** Here they differ by 5.8 %, and the right one for a duty
  cycle is the per minute mean, because what counts is the total air.
- **Filter carefully.** Discarding short stretches looked prudent and threw away almost every load,
  which lasts 1.8 minutes. The balance came out off by a factor of 2.3, and the filter's fault.
- **The manufacturer's datasheet is a hint, not a fact.** It says 8.2 and it is 8.05. A pressure
  switch has a tolerance, and you model the part that is fitted.
- **The instantaneous consumption falls short at ten seconds, and not because of the sensor.** The
  instantaneous median gives 0.0480 bar/min against the mean's 0.0711, 32 % less. TP3's step,
  measured rather than assumed, is 0.001 bar: eight times finer than that median, so it explains
  nothing. What happens is that **air goes in bursts** and half the steps are quieter than average.
- **Close the air before believing anything.** If the bar going in are not the bar going out, there
  is no possible model and the fault is in the measuring.
- **Pressure is not the interesting variable.** The control holds it, so it barely moves. Everything
  this twin will say comes out of the duty cycle.

## Metallurgical bridge

A metallurgical balance is this same thing and has always been done. What enters the plant leaves
through the concentrate plus the tailings. If it does not close, the balance is worthless, and **no
recovery gets discussed until it does**.

And the reason for doing it is the same as here: it is not for the bookkeeping. A balance that
closes to 1 % says the scales, the sampling and the assays are consistent with each other. One that
closes to 30 % says an instrument is lying, and until it is found any conclusion about the process
is air.

This module's air balance closes to 0.7 %. That is why it can go on.

## Do it yourself

```reto
pregunta: Measure the pressure switch's band yourself, with a single day. Return `momento`, `veces` and `presion` with the median pressure at the transitions of 5 June 2020, ordered by `momento`. Two rows.
inicio: SELECT TP3, DV_eletric,
       lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
FROM telemetria
WHERE day = DATE '2020-06-05';
esperado: m24_la_banda
pista: The starting point already brings the column saying what it was doing before. What is missing is wrapping it in an outer `SELECT` that keeps only the rows where `antes <> DV_eletric`, groups by whether it starts or stops, and takes `count(*)` and `round(median(TP3), 2)`.
solucion: SELECT CASE WHEN antes = 0 THEN 'arranca' ELSE 'para' END AS momento,
       count(*)              AS veces,
       round(median(TP3), 2) AS presion
FROM (SELECT TP3, DV_eletric,
             lag(DV_eletric) OVER (ORDER BY timestamp) AS antes
      FROM telemetria WHERE day = DATE '2020-06-05')
WHERE antes IS NOT NULL AND antes <> DV_eletric
GROUP BY momento
ORDER BY momento;
```

A single day gives **8.04** and **10.13**, against the 8.05 and 10.10 of a whole month. With thirty
one transitions the whole band is already visible: the pressure switch is one of the steadiest
things this machine has.

## Review

### What a model of the compressor needs, and what it does not

It needs a receiver, two switching pressures and two rates: what goes in and what comes out. It does
not need geometry, nor temperature, nor a model of the motor. Four numbers reproduce the duty cycle,
which is where everything else is going to come from.

### Why the duty cycle is consumption divided by delivery

Because in steady running the pressure neither rises nor falls in the long run. All the air spent
was put in by the compressor while loading, so if it puts in 10 and 2 are spent, it loads a fifth of
the time. No simulation is needed to know that.

### Why the median of the filling slopes is no good

Because the compressor does not fill at a constant rate. It starts slowly, some 0.8 bar/min for the
first ten seconds, peaks at 1.6 and falls away as the pressure rises. The median takes the good
stretch in the middle and comes out 5.8 % above its per minute mean, which is the figure that moves
the air.

And the other half has to be said: 5.8 % is little. The median is the wrong measurement for a reason
that makes sense, but on this machine it would have cost you cheap. An earlier version of this
lesson published 53 % here, and that number was mostly a measuring fault of my own rather than the
median's. It is told in module 26.

### What check decides whether these parameters are any good

That the air closes. Over the whole of February 2,311.7 bar went in and 2,295.0 came out, a 0.7 %
difference. Without that closure, two numbers measured separately are not a model, they are two
numbers.

And there is a second check this module did not have and now does: **how many times it starts per
hour**. It is needed because the balance cannot see everything. If the two durations were measured
wrongly by the same factor, the duty cycle is a ratio and would not notice; the starts are counted
against the clock and do. It happened, and module 26 tells it.

### The datasheet says 8.2 bar and you publish 8.05. Who is wrong

Neither of the two. The datasheet describes the model of pressure switch and the data describe the
part fitted to this train, with its tolerance and its wear. For a twin of this machine the second one
rules, just as in module 1 the file ruled over the datasheet.

---
module: 30
---

## In 30 seconds

- Whoever is not going to read thirty one modules needs **one page**: a knob that picks the day,
  two curves and one sentence with the verdict.
- The days are worked out beforehand, in Python, and the page only picks which one to show: **214
  days in 26.5 KB**, with no server at all.
- **How the numbers are written weighs more than how many there are**: the same semester weighs
  44.8 KB as a running total and 14.3 KB as the minutes of each slot.
- Rounding each slot on its own pushes the curve as far as **72 minutes** off in one day; rounding
  the running total and subtracting, half a minute at most.
- The browser decides nothing: each day's sentence comes out of Python and **matches the verdict**
  of module 28 day by day.

## What this module solves

Module 28's verdict is a table, and a table is read slowly. Somebody arriving from the portfolio, a
plant manager or whoever is reviewing an application, is not going to read thirty one modules to
get to it.

This module builds the door for that person: a page with the whole semester, day by day. And the
decision holding it up is one of data engineering, not of design. You have to decide what gets
worked out beforehand, what gets worked out on request, and how much each thing weighs in the
reader's browser.

## Before the theory: a toy example

A healthy compressor loads a little and often. Split a shift into five slots, and suppose it loads
**0.4 minutes** in each one: 2 minutes in total.

That curve has to be stored in whole numbers, because whole numbers are short. There are two ways
to round it:

| Slot | 1 | 2 | 3 | 4 | 5 | Sum |
|---|---|---|---|---|---|---|
| Real load, min | 0.4 | 0.4 | 0.4 | 0.4 | 0.4 | 2 |
| Rounded slot by slot | 0 | 0 | 0 | 0 | 0 | **0** |
| Real running total | 0.4 | 0.8 | 1.2 | 1.6 | 2.0 | |
| Rounded running total | 0 | 1 | 1 | 2 | 2 | |
| Each total minus the one before | 0 | 1 | 0 | 1 | 0 | **2** |

**Rounded slot by slot, the curve loses all 2 minutes**: every 0.4 falls to zero, and each slot's
error adds to the next one's. Rounding the running total and subtracting gives the zeros and ones
of the last row, which add up to exactly 2. No point strays more than half a minute, because each
one is rounded against the real curve and not against the one before it.

And there is a second gain that the hand does not see and the panel measures: **the slots repeat**.
Here they are zeros and ones. The running total never repeats, because it always grows, and a file
compressor lives precisely on repetition.

## Glossary

- **Precompute.** Work out beforehand every answer anybody will be able to ask for, and store them.
  Whoever opens the page works nothing out: they choose.
- **Server.** A program switched on day and night to answer whoever calls. It has to be paid for,
  protected and kept up to date.
- **Static page.** A page made only of fixed files. GitHub Pages serves them for free, and they do
  not fall over because there is nothing inside that can fall over.
- **Encoding.** The way some data is written inside a file. The same numbers can take three times
  the room depending on how they are written.
- **Compression.** Rewriting a file so it takes less room without losing anything, making use of
  what repeats. The server compresses and the browser decompresses without anybody noticing.
- **Fingerprint in the URL.** A piece of the file's fingerprint stuck onto its address, `?v=`. If
  the file changes, the address changes, and no cache can serve the old one.
- **Final state without JavaScript.** What you see if the script does not arrive. Here, the
  starting day drawn whole from the server.

## Step by step

### Step 1. Count the questions

The panel answers a single question, what happened on such a day, and there are 214 days. **Two
hundred and fourteen answers can all be worked out beforehand.** A free query, on the other hand,
cannot be precomputed: that is why module 8 sends the whole database engine to the browser, 8.12
MB.

The rule that comes out of here works for any panel. If the questions can be counted, they get
worked out beforehand; if not, a server or an engine in the browser is needed.

### Step 2. Decide what each day carries

Three curves: what the compressor loaded, what the twin would have loaded with a healthy machine,
and the healthy band. Plus the gaps in the record, the marks of the alarm and of the reports, and
the verdict sentence in the language of the page.

**The twin only runs while there is a record.** If it ran through the gaps too, the machine would
stay still in them and the twin would not. The two curves would separate for a reason that has
nothing to do with air.

### Step 3. Weigh before choosing

Three ways of writing the same curves, at six resolutions, compressed the way GitHub Pages
compresses them. They get weighed before deciding because intuition says the resolution rules, and
the measurement says otherwise.

### Step 4. Write the sentence in Python, not in the browser

The page could decide on its own whether the alarm went off on a given day, because it has the
numbers. But then there would be two definitions of an alarm day, module 28's and the page's. **A
single implementation cannot contradict itself.** It is the rule of the knobs, which simulate
nothing in the browser, carried over to the verdict.

### Step 5. Draw the starting day on the server

Without JavaScript the page has to read the same. So 5 June arrives drawn from the server, with its
two curves, its marks and its sentence. The script only adds being able to pick another day.

## The code, in parts

### Step 6. The slots, without dragging the rounding along

```python
def en_tramos(acumulado: list[float]) -> list[int]:
    redondo = [round(v) for v in acumulado]
    return [b - a for a, b in zip([0] + redondo, redondo)]
```

```anota
round(v) for v in acumulado | the running total is rounded and not each slot: that way no point strays more than half a minute from the real curve
zip([0] + redondo, redondo) | pairs each point with the one before. The zero in front stands in as the first one's predecessor
b - a | what the compressor loaded in that slot, in whole minutes. Adding them up brings back the rounded running total, exactly
```

```salida
  el redondeo, en el peor punto de todo el semestre:
    tramo a tramo          72.0 min de error
    acumulado y restar      0.5 min de error
```

It is the toy example to scale. Rounding slot by slot, the worst point of the semester strays **72
minutes** from the real curve; rounding the running total, half a minute at most.

### Step 7. The verdict, with module 28's rules

```python
if pico is None:
    return "sin_juzgar"
if pico > umbral:
    if partes_del_dia:
        return "acierto"
    return "marzo_alarma" if marzo else "falsa"
if partes_del_dia:
    return "escapa"
```

```anota
pico is None | the day does not have a single complete hour, so the twin does not judge it
pico > umbral | the highest residual of the day goes over the verdict's threshold: the alarm goes off
partes_del_dia | the failure reports covering that day. With an alarm it is a hit, and without one, a day that gets away
marzo_alarma | the twelve days of March with no report, which the verdict counts both ways
```

```salida
  los días, por clase:
    acierto               6
    se escapa             1
    falsa alarma         10
    marzo, con alarma     2
    marzo, sin alarma    10
    sobre el ruido       99
    normal               79
    sin juzgar            7
  semestre.es.json       284.4 KB en disco,   26.5 KB por la red
  semestre.en.json       285.3 KB en disco,   26.5 KB por la red

  escrito en results\m30_panel.json
  las cuatro cuentas cuadran con el módulo 28, y el 5 de junio sigue saltando a la hora del parte
```

The six hits are the six days with a report on which the alarm goes off. The one that gets away is
29 May: the leak opens at 23:30 and the alarm goes off the next day. **Before writing anything, the
script compares its counts with module 28's verdict**, and if they do not match it refuses.

### Step 8. Weigh it the way it weighs on the network

```python
def pesa(objeto) -> dict:
    crudo = json.dumps(objeto, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {"kb": round(len(crudo) / 1024, 1),
            "kb_red": round(len(gzip.compress(crudo, compresslevel=NIVEL_DE_PAGES,
                                              mtime=0)) / 1024, 1)}
```

```anota
separators=(",", ":") | without the spaces JSON puts after every comma by default: over 214 days that is thousands of bytes of nothing
compresslevel=NIVEL_DE_PAGES | level 5, the same one GitHub Pages compresses what it serves with. It was checked against their real files
mtime=0 | the time gzip stores in its header. Fixing it leaves the bytes identical on every run
```

```salida
  lo que pesa el semestre entero, tres curvas por día, en KB por la red:
    puntos/día | acumulado | tramos | caracteres
            24 |      12.4 |    6.2 |          -
            48 |      20.8 |    8.4 |        7.0
            96 |      34.5 |   12.0 |        9.8
           144 |      44.8 |   14.3 |       11.7
           288 |      77.6 |   20.1 |       16.0
          1440 |     230.9 |   40.3 |       29.2
```

The characters column does not exist with one point per hour: an hour long slot can carry sixty
minutes of load, and a single character does not reach that far.

### Step 9. The browser only adds up

```js
function camino(tramos, paso, techo) {
  var d = "M0 " + techo, total = 0;
  for (var k = 0; k < tramos.length; k++) {
    total += tramos[k];
    d += " L" + ((k + 1) * paso) + " " + (techo - total);
  }
  return d;
}
```

```anota
total += tramos[k] | the browser's only sum: adding up the minutes of each slot to rebuild the running total
"M0 " + techo | the path starts at the bottom left. In an SVG the height grows downwards, so zero is at the ceiling
" L" + ((k + 1) * paso) | a line to the end of each slot, ten minutes further along than the one before
```

The same sum is written in Python in `render_panel.py`, which draws the starting day without
JavaScript. Drawing is indeed done twice; deciding, only once.

### Step 10. The fingerprint in the URL

```python
def huella(lang: str) -> str:
    return hashlib.sha256((PANEL_DIR / f"semestre.{lang}.json").read_bytes()).hexdigest()[:8]
```

```anota
hashlib.sha256(...) | module 5's fingerprint: it changes completely if a single byte of the file changes
[:8] | eight characters are enough for every version to have an address of its own
```

The page asks for `semestre.en.json?v=` followed by that fingerprint. If tomorrow a day of the
verdict changes, the fingerprint and the address change, so no browser can hold on to the old file.
It really happened in module 24, with a knob drawing against a ceiling that was no longer its own.

### Step 11. Touch the panel

```panel
semestre
```

It starts on 5 June. Drag the cursor over the strip of the semester, or use the buttons to go to
the days that tell the story. The same piece lives on a [page of its own](panel.en.html), which is
the one the portfolio links to.

## The result, measured

{{FIG:fig_m30_peso_del_semestre}}

**What we expected.** That the weight would be decided by the resolution. One point every ten
minutes is six times more numbers than one per hour, and it was reasonable to expect a file six
times bigger.

**What came out.** That the way of writing them rules more. At the panel's resolution, the running
total in hours weighs **44.8 KB** and the minutes of each slot, **14.3 KB**: **3.1 times less**,
with the same data. And the dotted line in the figure shows the strangest part: the slots at one
point per minute, **40.3 KB**, still weigh less than the running total at ten minutes.

The reason is the toy example. The running total always grows, so every number is new and carries
its decimals. The slots are short numbers that repeat, mostly zeros at night and tens with a leak
open, and compression lives on repetition.

The third way of writing, one character per slot, saves **2.6 KB** more. In exchange it asks for a
decoder of its own that would have to be written, tested and maintained, and it is not worth it:
the slots stay in ordinary JSON.

With the curves, the marks and the sentences, one language's file weighs 284.4 KB on disk. Over the
network **26.5 KB** travel, 10.7 times less, and that is the module's figure: **214 days in 26.5
KB**. For comparison, the SQL engine of the live queries weighs 8.12 MB, **314 times more**.

**The figure the syllabus promised was another one.** It asked for a measurement of how many
seconds somebody who does not know the project takes to understand what happened. A script does not
measure that: it needs people and a stopwatch, and there have not been any yet. It was changed for
a figure that measures itself. And it is said here, so as not to give the impression that the
question went away.

**What it means.** A panel that answers instantly, reads without JavaScript and costs 26.5 KB does
not need a server. What is lost is asking something nobody worked out beforehand, and the course's
live queries are already there for that. Each tool where it belongs: precompute what can be
counted, and take the engine to where the questions cannot be counted.

## Watch out

- **Precomputing only works if the questions can be counted.** 214 days are 214 answers. A free
  query cannot be counted, and for that a server or an engine in the browser is needed.
- **Rounding each slot on its own drags the error along.** In this semester it reaches 72 minutes
  in one day. Round the running total and subtract.
- **Weigh it with the real compression.** On disk the file takes 284.4 KB and over the network
  26.5. Deciding by looking at the disk would have led to optimising what does not matter.
- **A data file with no fingerprint in the URL** stays in the reader's cache while the page
  changes. Then the page draws with old data, and gives no warning.
- **Precomputing freezes.** If the data changes, the panel does not find out until somebody runs
  `panel.py` again. That is why the script checks its counts against the verdict every time.
- **If the page decided, there would be two verdicts.** Each day's sentence is written in Python,
  once, and the page only shows it.

## Metallurgical bridge

A belt scale does not note down what happened in each shift: it carries a **totaliser**, a counter
that only goes up. A shift's tonnage is got by subtracting the reading at the end minus the one at
the start. If each shift were estimated and rounded on its own, the month would not match the
counter; by subtracting totaliser readings, it always matches. It is step 6 with conveyor belts.

And the control room whiteboard is this panel. The shift balance is worked out once, noted down,
and anybody reads it at a glance without doing the sums again. When somebody brings a new question,
such as the recovery without counting the three o'clock stoppage, that is no longer on the board:
you go to the laboratory with the data. The whiteboard is what is precomputed; the laboratory, the
live query.

## Review

### Why this panel does not need a server

Because all its questions can be counted: 214 days, one answer per day. They are worked out
beforehand in Python and travel together in a file of 26.5 KB. A server is only needed when the
questions cannot be foreseen, and then it has to be kept switched on, protected and up to date.

### Why the minutes of each slot weigh less than the running total

Because they are short numbers that repeat, and compression lives on repetition. The running total
always grows, so every number is different and carries decimals. At the panel's resolution they are
14.3 KB against 44.8, with the same data.

### What happens if each slot is rounded on its own

Each slot's error adds to the next one's and the curve drifts away, up to 72 minutes on the worst
day of the semester. Rounding the running total and subtracting, no point strays more than half a
minute, because each one is rounded against the real curve.

### Why each day's sentence is written in Python and not in the page

So that a single definition of an alarm day exists. If the page decided, there would be two, and
they could drift apart without anybody seeing it. On top of that the script checks before writing
that its counts match module 28's verdict, day by day.

### What somebody who opens the panel without JavaScript sees

The whole of 5 June, drawn on the server: the two curves, the healthy band, the marks and the
verdict sentence. That day was chosen because it tells the story on its own. At 10:00 the residual
goes over the threshold, the same hour at which the failure report starts.

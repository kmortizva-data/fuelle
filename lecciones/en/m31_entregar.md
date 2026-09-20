---
module: 31
---

## In 30 seconds

- The last deliverable is **one page**: the question, the method in five lines, the verdict table
  and **8 things that would break** in a real plant.
- No figure is typed. The text carries holes, a script fills them from `results/` and **refuses to
  write if any number does not come from a run**.
- It is a page of the course itself printed to PDF, not a LaTeX document: one visual identity, and
  no new tool to install.
- **One page is one page.** The script counts the sides of the PDF and fails on two. It fitted by
  cutting text, not by shrinking the type.
- The course closes the way it has gone all along: by also saying what the twin does not do.

## What this module solves

Work that cannot be handed over is not finished. Whoever decides in a plant is not going to read
thirty one modules, nor move the knob on the panel: they are going to ask for one sheet.

This module writes that sheet with the same discipline as the rest. Every figure comes from a run.
And what the project does not do is written on the same side as what it does. A deliverable that
tells only the good half is not a deliverable, it is advertising.

## The arc of the project

{{FIG:fig_m31_arco_del_proyecto}}

The file from UCI is **208.2 MB** of text. The bronze leaves it at **22.05 MB** without losing a
reading, the silver puts those readings on a grid and goes to **1,841,760** rows, and the gold sums
them up in nine dbt nodes. The same readings served from PostgreSQL take **267.8 MB**, twelve times
more, and in exchange they bring constraints, indexes and a backup that restores.

On the other side is the twin. Four numbers measured in February describe the machine, its
disagreement with her is the residual, and the noise floor of that residual is **0.12 bar/min**.
With the threshold the sweep chose, the verdict is **4 of 4** failures with **1.5** false alarms a
month.

And something the arc does not show: between the silver and the twin, twelve days of March turned
up with the machine broken and no report, found while calibrating. The arc tells what is left
standing; the course tells how we got here.

## Glossary

- **Deliverable.** What is left when the work ends. Another person has to be able to use it without
  asking you anything.
- **One page.** One side of A4. It is not a whim of format: it is what somebody reads standing up,
  in a meeting, before deciding.
- **Template with holes.** A text with marks like `{umbral}` where the figures will go, which a
  script fills from the measured results.
- **Printing without a window.** Asking a browser to turn a page into a PDF without opening itself,
  from the command line.
- **Declared limit.** A limitation written into the deliverable itself, with its measurement beside
  it.
- **Licence.** The permission something is published under. Here, MIT for the code and CC BY 4.0
  for the lessons and the figures, with the citation of the dataset.

## Step by step

### Step 1. Write the page with no figures inside

The text lives in `lecciones/folio.md`, in Spanish and in English, and where a number would go
there is a named hole. That way the page is written as prose and reviewed as prose, and it passes
the same writing gates as a lesson.

### Step 2. Fill the holes from the results

A map says which file in `results/` each hole comes from. The threshold and the counts of the
verdict are read from module 28's sweep, not from a constant: if the sweep ever chose another
threshold, the page would follow on its own.

### Step 3. Read back what was written

The page is not a lesson, so the numbers gate was not looking at it. It gets the same treatment
anyway: the script reads its own text back and looks for figures that do not exist in `results/`.

### Step 4. Print with the browser, not with LaTeX

The plan said Tectonic. That is 47 MB the repository's privacy guard rejects, a second visual
system to maintain, and one more tool for whoever clones this. A page printed by the browser comes
out with the course's own typeface and nothing new.

### Step 5. Count the sides

A page that runs to two sides stops being one page. The script counts the pages of the PDF it has
just written and fails if there is more than one.

## The code, in parts

### Step 6. The hole, and what fills it

```python
def rellena(texto: str, valores: dict[str, str]) -> str:
    def cambia(m: re.Match) -> str:
        clave = m.group(1)
        if clave not in valores:
            raise SystemExit(f"El folio pide «{clave}» y no está entre las cifras medidas.")
        return valores[clave]

    return re.sub(r"\{([a-z_]+)\}", cambia, texto)
```

```anota
re.sub(r"\{([a-z_]+)\}", cambia, texto) | looks for the holes in the text, a lowercase word between braces, and calls `cambia` with each one
clave not in valores | a hole nobody knows how to fill stops the whole page, instead of printing a brace inside the PDF
valores[clave] | the figure, already written in the language of the page: 1,15 in Spanish and 1.15 in English
```

### Step 7. The numbers gate, applied to the page

```python
for m in check_numbers.NUMBER.finditer(texto):
    valor = check_numbers.canonical(m.group(), lang)
    if valor is None or valor in conocidos:
        continue
    fuera.append(m.group())
```

```anota
check_numbers.NUMBER | the same expression that looks for numbers in the lessons. The page does not premiere rules, it inherits the ones already there
canonical(...) | 1.516.948 and 1,516,948 are the same number: this leaves them in a single form before comparing
conocidos | every number any script has written into results/, read just before filling anything in
fuera.append(...) | whatever does not add up gets named and the page is not written
```

```salida
  folio.html       El veredicto, en un folio                       553 palabras
  folio.en.html    The verdict, on one page                        556 palabras
  8 cosas que se romperían, y 24 cifras, todas medidas
  escrito en results\m31_folio.json
```

### Step 8. Count the sides without opening the PDF

```python
def hojas(pdf: Path) -> int:
    crudo = pdf.read_bytes()
    return len(re.findall(rb"/Type\s*/Page[^s]", crudo)) or 1
```

```anota
pdf.read_bytes() | the PDF as it is, without installing any library: inside it is text with marked objects
rb"/Type\s*/Page[^s]" | every page declares itself like this. The `[^s]` is so as not to count `/Pages`, which is the index and would come out as one too many
or 1 | if a PDF declared none, one is counted: the guard is there to catch two sides, not to fall over on its own
```

```salida
  imprime con msedge.exe
  veredicto.pdf      59.4 KB   1 cara
  verdict.pdf        60.1 KB   1 cara
  apuntado en results\m31_folio.json
```

## The result, measured

**What we expected.** That the page would fit on the first try.

**What came out.** Two sides, and the guard said so before anyone else. About three lines were over,
measured in the browser at the width and the type size of the print. It was fixed by cutting text
in both languages and tightening the air between sections in the print stylesheet. The type size
was not touched: on a sheet somebody is going to read standing up, the type is the last thing to
shrink.

The published page is **553** words, **24** figures, all measured, and **8 things that would
break**. The PDF weighs **59.4** KB and takes one side.

**What it means.** The project delivers four things, and each one for a different reader. The
course, for whoever wants to learn this from scratch. The panel, for whoever has two minutes. The
repository, for whoever wants to check it. And the page, for whoever has to decide something with
it in front of them.

The last of the four was the hardest to write, because it forces you to put on one side what works
and what does not. The twin catches the four documented failures with one and a half false alarms a
month, and as a predictor it is no good. The two sentences go together, on the same page, in the
same type size.

## Watch out

- **A page that does not fit is not fixed with the type.** Text gets cut. Shrinking the typeface so
  it goes in is making the deliverable worse to save the format.
- **A figure typed by hand into the deliverable is worth less than having no deliverable.** It is
  the last sheet anybody will read, and the easiest to contaminate by copying numbers.
- **Printing from the wrong place writes nothing.** Launched from Git Bash, this same browser exits
  with code 0 and leaves no PDF. It goes from PowerShell, and the script says so if it fails.
- **The page expires.** If the verdict changes, it has to be generated and printed again. That is
  why its figures come from `results/` and not from anybody's memory.
- **Limitations are written with their measurement beside them.** "The machine degrades" says
  nothing; "healthy consumption doubles between February and August" does.

## Metallurgical bridge

A certificate of analysis carries the result, the method and the detection limit on the same sheet.
A laboratory that gives the grade without saying its limit forces you to trust it; with the limit
written down, anybody knows how far they can use that number.

The page does the same. The verdict goes at the top and, on the same side, what the twin does not
see. A single machine, four failures, no reference leak, and a model that ages if nobody
recalibrates it. And like the shift report, it fits on one side and is read standing up.

## Review

### Why the page is not written by hand

Because it is the sheet that travels furthest and the easiest to contaminate by copying figures.
The text carries holes, a script fills them from the results, and afterwards it reads back what was
written to check that no number without a run behind it has slipped in.

### Why the PDF comes from a page of the course and not from LaTeX

For three measured reasons. The compiler is 47 MB the repository's guard rejects, it would be a
second visual system to maintain, and whoever clones the project would have to install it. The page
already exists, it uses the course's typeface and any browser turns it into a PDF.

### What happens if the page does not fit on one side

The script catches it by counting the pages of the PDF and does not let it go on. The answer is to
cut text or tighten the air between sections, never to shrink the type: an unreadable page meets
the format and fails at the only thing that matters.

### Why the list of what would break goes in the deliverable

Because whoever reads it is going to decide with that in front of them, and each limit changes what
they can do with the result. Hiding them does not remove them: it leaves them for the plant to
discover, which is the worst place and the worst moment.

### What is delivered in the end, and where each thing lives

Four things. The course and the panel live inside the portfolio. The code and the lessons, in the
public repository, under MIT and CC BY 4.0. And the page, in PDF and in both languages, is
generated by `src/entrega/folio.py` and `src/entrega/imprime.py`.

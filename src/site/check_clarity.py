"""Author tool: measure whether a lesson is actually readable, not just short.

Length was never the real problem. A 4.000 word lesson that reads cleanly is fine; a
1.800 word one built from tangled sentences is not, and summarising tangled prose only
makes it worse. So this measures the tangle directly.

What it demands:
  - one idea per sentence, so nothing over 32 words
  - at most three commas in a sentence, because four means two sentences got merged
  - no stacking of subordinate clauses, which in Spanish shows up as three "que" in a row
  - paragraphs of at most six sentences

Code blocks, tables, output and the line-by-line annotations are skipped: those are not
prose and their line lengths mean nothing here.

Usage:
    python src/site/check_clarity.py                 # every lesson, plus curso.md
    python src/site/check_clarity.py 2_Curso/m01_*.md

Exits 1 when a hard limit is broken.
"""

from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent.parent
COURSE_DIR = ROOT / "lecciones"
LESSON_GLOB = "m[0-9][0-9]_*.md"

MAX_WORDS = 32          # one idea per sentence
LONG_ENOUGH = 26        # reported, not fatal: the sentences worth looking at
MAX_COMMAS = 3          # four commas means two sentences got merged
MAX_QUE = 2             # three "que" in one sentence is a stack of subordinates
MAX_SENTENCES = 6       # per paragraph


def prose_paragraphs(text: str) -> list[tuple[int, str]]:
    """The prose of a lesson as (line number, paragraph), with everything else dropped."""
    if text.startswith("---"):
        _, _, text = text.split("---", 2)

    paragraphs: list[tuple[int, str]] = []
    current: list[str] = []
    start = 0
    in_code = False

    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        # Headings, tables, quotes and list markers are not running prose.
        skip = (in_code or stripped.startswith("#") or stripped.startswith("|")
                or stripped.startswith(">"))
        if not stripped or skip:
            if current:
                paragraphs.append((start, " ".join(current)))
                current = []
            continue
        # A bullet is one idea on its own, so it counts as its own paragraph.
        bullet = re.match(r"^\s*([-*]|\d+\.)\s+(.*)$", line)
        if bullet:
            if current:
                paragraphs.append((start, " ".join(current)))
                current = []
            paragraphs.append((number, bullet.group(2)))
            continue
        if not current:
            start = number
        current.append(stripped)

    if current:
        paragraphs.append((start, " ".join(current)))
    return paragraphs


def sentences(paragraph: str) -> list[str]:
    """Split into sentences without tripping over Spanish thousands separators.

    "737.453 filas" is one number, not the end of a sentence, so the periods that sit
    between two digits are hidden before the split and put back afterwards.
    """
    guarded = re.sub(r"(?<=\d)\.(?=\d)", "\x00", paragraph)
    parts = re.split(r"(?<=[.!?…])\s+", guarded)
    return [p.replace("\x00", ".").strip() for p in parts if p.strip()]


def strip_markup(sentence: str) -> str:
    """Drop inline code and the figure directives before counting words."""
    sentence = re.sub(r"`[^`]*`", "", sentence)
    sentence = re.sub(r"\{\{FIG:[^}]*\}\}", "", sentence)
    return re.sub(r"[*_]", "", sentence)


def check(path: Path) -> tuple[list[str], dict]:
    problems: list[str] = []
    lengths: list[int] = []
    watch: list[tuple[int, int, str]] = []

    for line_number, paragraph in prose_paragraphs(path.read_text(encoding="utf-8")):
        found = sentences(strip_markup(paragraph))
        if len(found) > MAX_SENTENCES:
            problems.append(f"línea {line_number}: párrafo de {len(found)} frases, "
                            f"el máximo es {MAX_SENTENCES}")

        for clean in found:
            words = len(clean.split())
            if words < 3:
                continue
            lengths.append(words)
            commas = len(re.findall(r"(?<!\d),|,(?!\d)", clean))
            ques = len(re.findall(r"\bque\b", clean, re.I))

            if words > MAX_WORDS:
                problems.append(f"línea {line_number}: frase de {words} palabras · "
                                f"{clean[:78]}...")
            elif words >= LONG_ENOUGH:
                watch.append((line_number, words, clean))
            if commas > MAX_COMMAS:
                problems.append(f"línea {line_number}: {commas} comas en una frase · "
                                f"{clean[:78]}...")
            if ques > MAX_QUE:
                problems.append(f"línea {line_number}: {ques} veces «que» en una frase · "
                                f"{clean[:78]}...")

    stats = {
        "frases": len(lengths),
        "mediana": statistics.median(lengths) if lengths else 0,
        "media": statistics.mean(lengths) if lengths else 0,
        "maxima": max(lengths) if lengths else 0,
        "vigiladas": len(watch),
    }
    return problems, stats


PANEL_DIR = ROOT / "assets" / "panel"


def check_panel() -> tuple[list[str], int]:
    """Las frases del panel del módulo 30, con los mismos límites que la prosa.

    Son una o dos frases por día y por idioma, escritas por src/twin/panel.py a
    partir de plantillas. Una plantilla que se enreda se enreda 214 veces, así
    que se miran todas y no una muestra.
    """
    problems: list[str] = []
    contadas = 0
    for fuente in sorted(PANEL_DIR.glob("semestre.*.json")):
        datos = json.loads(fuente.read_text(encoding="utf-8"))
        for dia in datos["dias"]:
            for clean in sentences(dia["frase"]):
                words = len(clean.split())
                if words < 3:
                    continue
                contadas += 1
                commas = len(re.findall(r"(?<!\d),|,(?!\d)", clean))
                ques = len(re.findall(r"\bque\b", clean, re.I))
                donde = f"{fuente.name} {dia['dia']}"
                if words > MAX_WORDS:
                    problems.append(f"{donde}: frase de {words} palabras · {clean[:78]}...")
                if commas > MAX_COMMAS:
                    problems.append(f"{donde}: {commas} comas en una frase · {clean[:78]}...")
                if ques > MAX_QUE:
                    problems.append(f"{donde}: {ques} veces «que» · {clean[:78]}...")
    return problems, contadas


def main() -> None:
    paths = [Path(a) for a in sys.argv[1:]]
    del_panel = not paths
    if not paths:
        paths = sorted(COURSE_DIR.glob(LESSON_GLOB))
        paths += [p for p in (COURSE_DIR / "curso.md", COURSE_DIR / "panel.md",
                              COURSE_DIR / "en" / "panel.md") if p.exists()]
    if not paths:
        print("Todavía no hay nada que revisar.")
        return

    total = 0
    for path in paths:
        problems, stats = check(path)
        total += len(problems)
        print(f"\n{path.name}")
        print(f"  {stats['frases']} frases · mediana {stats['mediana']:.0f} palabras · "
              f"media {stats['media']:.1f} · la más larga {stats['maxima']} · "
              f"{stats['vigiladas']} entre {LONG_ENOUGH} y {MAX_WORDS}")
        for problem in problems:
            print(f"    {problem}")

    if del_panel:
        problems, contadas = check_panel()
        total += len(problems)
        print(f"\nlas frases del panel")
        print(f"  {contadas} frases, en los dos idiomas")
        for problem in problems:
            print(f"    {problem}")

    print(f"\n{'-' * 66}")
    if total:
        print(f"{total} frases que arreglar. Se parten en dos, no se acortan a la fuerza.")
        raise SystemExit(1)
    print(f"Los {len(paths)} archivos se leen sin nudos.")


if __name__ == "__main__":
    main()

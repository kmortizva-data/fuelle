"""Author tool: check that a lesson follows the anatomy described in 2_Curso/MANUAL.md.

A manual nobody checks is a wish list. This turns the structural half of it into something
that fails on its own, before a commit rather than three rewrites later.

What it demands of every lesson:
  - the nine sections, with their exact names and in order
  - a worked numeric example, which has to come before the method
  - every python block followed by its line-by-line annotation, and a real output somewhere
  - a measured result, which is the section that keeps this from turning back into a diary
  - five review questions
  - no em dashes (the rest of the prose rules live in check_prose.py)

Usage:
    python src/site/check_lesson.py                 # every lesson written
    python src/site/check_lesson.py 2_Curso/m01_*.md

Exits 1 when something is missing, so it can gate a commit.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent.parent
COURSE_DIR = ROOT / "2_Curso"

# A lesson file is m<NN>_<slug>.md. The pattern is this strict because Windows
# matches globs case-insensitively, so a loose "m*.md" also picked up MANUAL.md and
# reported the manual for quoting the very phrases it bans.
LESSON_GLOB = "m[0-9][0-9]_*.md"


REQUIRED = [
    "En 30 segundos",
    "Qué resuelve este módulo",
    "Antes de la teoría: un ejemplo de juguete",
    "Glosario",
    "Paso a paso",
    "El código, por partes",
    "El resultado, medido",
    "Ojo",
    "Puente metalúrgico",
    "Repaso",
]

# The closing module delivers the project instead of teaching a new idea, so it swaps the
# toy example for the arc of the whole thing.
BRIEF = "En 30 segundos"
MAX_BRIEF_BULLETS = 5
CLOSING = "El arco del proyecto"
TOY_EXAMPLE = "Antes de la teoría: un ejemplo de juguete"


def promised_figure(path: str, body: str) -> list[str]:
    """The number temario.json promised for this module has to appear in the lesson.

    This is the guard against the way the old notes drifted: note 20 closed saying R2
    0,64 was the best result of the project, note 23 measured the real baseline, and the
    correction ended up as a footnote in the index instead of in the note that was wrong.
    A module cannot quietly report a different number from the one the plan promised.
    """
    syllabus = json.loads((COURSE_DIR / "temario.json").read_text(encoding="utf-8"))
    match = re.search(r"^module:\s*(\d+)", body, re.M)
    if not match:
        return ["falta 'module: N' en el front matter"]
    module = next((m for m in syllabus["modules"]
                   if m["number"] == int(match.group(1))), None)
    if module is None:
        return [f"el módulo {match.group(1)} no está en temario.json"]

    wanted = module["cifra"]["value"]
    if wanted == "por medir":
        return []  # part 2 declares the question, and fills the answer once measured
    # Compare with whitespace flattened, so "737 453" matches however it got typed.
    flat = " ".join(body.split())
    if " ".join(wanted.split()) not in flat:
        return [f"el temario promete la cifra «{wanted}» y no aparece en la lección"]
    return []


def sections(body: str) -> list[str]:
    return [line[3:].strip() for line in body.splitlines() if line.startswith("## ")]


def code_blocks(body: str) -> list[tuple[int, str]]:
    """Opening fences as (line number, language), so a problem can be pointed at."""
    found = []
    for number, line in enumerate(body.splitlines(), 1):
        match = re.match(r"^```(\w*)\s*$", line)
        if match:
            found.append((number, match.group(1)))
    return [(n, lang) for n, lang in found if lang]


def check(path: Path) -> list[str]:
    body = path.read_text(encoding="utf-8")
    problems: list[str] = []

    present = sections(body)
    closing = CLOSING if CLOSING in present else None
    for wanted in REQUIRED:
        if wanted in present:
            continue
        if wanted == TOY_EXAMPLE and closing:
            continue  # the delivery module closes the project instead of teaching
        problems.append(f"falta la sección «{wanted}»")

    def position(name: str | None) -> int:
        return present.index(name) if name and name in present else -1

    # The worked example goes before the method: that is what gives the theory something
    # to hold on to.
    example = max(position(TOY_EXAMPLE), position(closing))
    method = position("Paso a paso")
    if example > -1 and method > -1 and example > method:
        problems.append("el ejemplo va después del método, y tiene que ir antes")

    # The result goes after the code, because it reports what the code produced.
    result, code = position("El resultado, medido"), position("El código, por partes")
    if result > -1 and code > -1 and result < code:
        problems.append("«El resultado, medido» va antes del código, y tiene que ir después")

    blocks = code_blocks(body)
    python = [n for n, lang in blocks if lang == "python"]
    outputs = [n for n, lang in blocks if lang == "salida"]

    for line in python:
        following = [lang for n, lang in blocks if n > line][:2]
        if "anota" not in following:
            problems.append(f"línea {line}: bloque de código sin su «anota» detrás")

    if python and not outputs:
        problems.append("hay código pero ningún bloque «salida» con el resultado real")

    questions = (len(re.findall(r"^### ", body.split("## Repaso")[-1], re.M))
                 if "## Repaso" in body else 0)
    if questions != 5:
        problems.append(f"el repaso tiene {questions} preguntas y deben ser 5")

    for number, line in enumerate(body.splitlines(), 1):
        if "—" in line or "–" in line:
            problems.append(f"línea {number}: raya o guion medio")

    problems += promised_figure(path.name, body)

    # The brief is the way in, so it goes first and stays short.
    if present and present[0] != "En 30 segundos":
        problems.append("«En 30 segundos» tiene que ser la primera sección")
    brief = ""
    if BRIEF in present:
        after = body.split("## " + BRIEF)[-1]
        brief = after.split(chr(10) + "## ")[0]
    bullets = len(re.findall(r"^\s*[-*]\s+", brief, re.M))
    if brief and not 1 <= bullets <= MAX_BRIEF_BULLETS:
        problems.append(f"«En 30 segundos» tiene {bullets} viñetas y el máximo es "
                        f"{MAX_BRIEF_BULLETS}")

    return problems


def main() -> None:
    paths = [Path(a) for a in sys.argv[1:]] or sorted(COURSE_DIR.glob(LESSON_GLOB))
    if not paths:
        print("Todavía no hay lecciones escritas.")
        return

    failures = 0
    for path in paths:
        problems = check(path)
        print(f"{path.name[:46]:<48} {'OK' if not problems else f'{len(problems)} problemas'}")
        for problem in problems:
            print(f"     {problem}")
        failures += len(problems)

    print(f"\n{'-' * 60}")
    if failures:
        print(f"{failures} problemas en {len(paths)} lecciones. Ver 2_Curso/MANUAL.md.")
        raise SystemExit(1)
    plural = "lecciones cumplen" if len(paths) > 1 else "lección cumple"
    print(f"{len(paths)} {plural} la anatomía del manual.")


if __name__ == "__main__":
    main()

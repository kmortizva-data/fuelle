"""The English twins keep step with the Spanish lessons, or the build is red.

A twin (2_Curso/en/mNN_slug.md) is free in its prose and bound in everything else: the
same ten sections in the same order, the same figures, the same code blocks, and the
same numbers. The number check is the one that matters most: every digit run outside
code is collected from both editions and the two multisets must match, so a translated
lesson cannot round, drop or invent a figure. Thousands and decimal separators differ
between the languages (737.453 / 737,453; 0,80 / 0.80) and split into the same runs.

It also applies the anatomy rules of check_lesson.py to the English text (section names
in English), the dash ban, and the figure that temario.json promised.

Usage:
    python src/site/check_english.py            # every twin written so far
    python src/site/check_english.py 2_Curso/en/m01_*.md
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent.parent
COURSE_DIR = ROOT / "2_Curso"
EN_DIR = COURSE_DIR / "en"
LESSON_GLOB = "m[0-9][0-9]_*.md"

REQUIRED = [
    "In 30 seconds",
    "What this module solves",
    "Before the theory: a toy example",
    "Glossary",
    "Step by step",
    "The code, in parts",
    "The result, measured",
    "Watch out",
    "Metallurgical bridge",
    "Review",
]
BRIEF = "In 30 seconds"
MAX_BRIEF_BULLETS = 5
CLOSING = "The arc of the project"
TOY_EXAMPLE = "Before the theory: a toy example"

FRONT_PAGE_SECTIONS = [
    "What this project is about",
    "The verdict, up front",
    "The path, module by module",
    "What you can do by the end",
    "How to read this course",
    "Where all this comes from",
]


def sections(body: str) -> list[str]:
    return [line[3:].strip() for line in body.splitlines() if line.startswith("## ")]


def code_blocks(body: str) -> list[tuple[int, str]]:
    found = []
    for number, line in enumerate(body.splitlines(), 1):
        match = re.match(r"^```(\w*)\s*$", line)
        if match:
            found.append((number, match.group(1)))
    return [(n, lang) for n, lang in found if lang]


def prose_only(body: str) -> str:
    """The text outside fenced code and outside the front matter."""
    if body.startswith("---"):
        body = body.split("---", 2)[2]
    kept, in_code = [], False
    for line in body.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            kept.append(line)
    return "\n".join(kept)


def numbers(body: str) -> Counter:
    return Counter(re.findall(r"\d+", prose_only(body)))


def figures(body: str) -> list[str]:
    return [name.strip() for name in re.findall(r"\{\{FIG:([^|}]+)", body)]


def block_shape(body: str) -> Counter:
    return Counter(lang for _, lang in code_blocks(body))


def promised_figure(body: str, syllabus: dict) -> list[str]:
    match = re.search(r"^module:\s*(\d+)", body, re.M)
    if not match:
        return ["falta 'module: N' en el front matter"]
    module = next((m for m in syllabus["modules"]
                   if m["number"] == int(match.group(1))), None)
    if module is None:
        return [f"el módulo {match.group(1)} no está en temario.json"]
    wanted = module["cifra"].get("value_en") or module["cifra"]["value"]
    if wanted == "por medir":
        return []
    flat = " ".join(body.split())
    if " ".join(wanted.split()) not in flat:
        return [f"el temario promete la cifra «{wanted}» y no aparece en la lección inglesa"]
    return []


def check(path: Path, syllabus: dict) -> list[str]:
    body = path.read_text(encoding="utf-8")
    problems: list[str] = []
    twin = COURSE_DIR / path.name
    if not twin.exists():
        return [f"no existe la lección española {twin.name} de la que esta es gemela"]
    spanish = twin.read_text(encoding="utf-8")

    # --- anatomy, in English ---
    present = sections(body)
    closing = CLOSING if CLOSING in present else None
    for wanted in REQUIRED:
        if wanted in present:
            continue
        if wanted == TOY_EXAMPLE and closing:
            continue
        problems.append(f"falta la sección «{wanted}»")

    def position(name: str | None) -> int:
        return present.index(name) if name and name in present else -1

    example = max(position(TOY_EXAMPLE), position(closing))
    method = position("Step by step")
    if example > -1 and method > -1 and example > method:
        problems.append("el ejemplo va después del método, y tiene que ir antes")
    result, code = position("The result, measured"), position("The code, in parts")
    if result > -1 and code > -1 and result < code:
        problems.append("«The result, measured» va antes del código, y tiene que ir después")

    blocks = code_blocks(body)
    python = [n for n, lang in blocks if lang == "python"]
    outputs = [n for n, lang in blocks if lang == "salida"]
    for line in python:
        following = [lang for n, lang in blocks if n > line][:2]
        if "anota" not in following:
            problems.append(f"línea {line}: bloque de código sin su «anota» detrás")
    if python and not outputs:
        problems.append("hay código pero ningún bloque «salida» con el resultado real")

    questions = (len(re.findall(r"^### ", body.split("## Review")[-1], re.M))
                 if "## Review" in body else 0)
    if questions != 5:
        problems.append(f"el repaso tiene {questions} preguntas y deben ser 5")

    for number, line in enumerate(body.splitlines(), 1):
        if "—" in line or "–" in line:
            problems.append(f"línea {number}: raya o guion medio")

    if present and present[0] != BRIEF:
        problems.append(f"«{BRIEF}» tiene que ser la primera sección")
    brief = ""
    if BRIEF in present:
        brief = body.split("## " + BRIEF)[-1].split(chr(10) + "## ")[0]
    bullets = len(re.findall(r"^\s*[-*]\s+", brief, re.M))
    if brief and not 1 <= bullets <= MAX_BRIEF_BULLETS:
        problems.append(f"«{BRIEF}» tiene {bullets} viñetas y el máximo es {MAX_BRIEF_BULLETS}")

    problems += promised_figure(body, syllabus)

    # --- parity with the Spanish lesson ---
    if len(present) != len(sections(spanish)):
        problems.append(f"{len(present)} secciones frente a {len(sections(spanish))} en español")
    if figures(body) != figures(spanish):
        problems.append(f"figuras distintas: {figures(body)} frente a {figures(spanish)}")
    if block_shape(body) != block_shape(spanish):
        problems.append(f"bloques de código distintos: {dict(block_shape(body))} frente a "
                        f"{dict(block_shape(spanish))}")
    mine, theirs = numbers(body), numbers(spanish)
    if mine != theirs:
        extra = sorted((mine - theirs).elements())
        missing = sorted((theirs - mine).elements())
        problems.append(f"números que no cuadran con el español: sobran {extra[:12]} · "
                        f"faltan {missing[:12]}")
    return problems


def check_front_page() -> list[str]:
    page = EN_DIR / "curso.md"
    if not page.exists():
        return []
    present = sections(page.read_text(encoding="utf-8"))
    problems = [f"portada inglesa: falta la sección «{s}»" for s in FRONT_PAGE_SECTIONS
                if s not in present]
    spanish = COURSE_DIR / "curso.md"
    mine, theirs = numbers(page.read_text(encoding="utf-8")), numbers(spanish.read_text(encoding="utf-8"))
    if mine != theirs:
        problems.append(f"portada inglesa: números que no cuadran: sobran "
                        f"{sorted((mine - theirs).elements())[:12]} · faltan "
                        f"{sorted((theirs - mine).elements())[:12]}")
    return problems


def main() -> None:
    syllabus = json.loads((COURSE_DIR / "temario.json").read_text(encoding="utf-8"))
    paths = [Path(a) for a in sys.argv[1:]] or sorted(EN_DIR.glob(LESSON_GLOB))
    failures = 0
    for path in paths:
        problems = check(path, syllabus)
        print(f"en/{path.name[:43]:<45} {'OK' if not problems else f'{len(problems)} problemas'}")
        for problem in problems:
            print(f"     {problem}")
        failures += len(problems)
    front = check_front_page()
    for problem in front:
        print(f"     {problem}")
    failures += len(front)

    print(f"\n{'-' * 60}")
    if failures:
        print(f"{failures} problemas en la edición inglesa. No commitear.")
        raise SystemExit(1)
    print(f"{len(paths)} gemelas inglesas en paz con sus lecciones españolas"
          + (" y la portada." if (EN_DIR / 'curso.md').exists() else "."))


if __name__ == "__main__":
    main()

"""Author tool: flag the writing tics that make a page read as machine-written.

The em dash is the loudest one. Spanish uses the raya legitimately, but a document
sprinkled with it every few lines reads as generated, and this material has to hold up in
a portfolio. The fix is never a search-and-replace to a hyphen: it is rewriting the
sentence with a comma, a colon, parentheses, or a full stop.

There is a second list here that the Concentra original did not need: the diary phrases.
The 31 original notes were written as the project advanced, so they narrate discovery
("esto es una sorpresa", "esto cambia el plan"). Copying one of those into a lesson would
undo the whole reason this course exists, so they fail the check.

Code blocks are skipped, and so is anything inside a `salida` block, because that is real
program output and must not be edited.

Usage:
    python src/site/check_prose.py                 # every lesson, plus curso.md
    python src/site/check_prose.py 2_Curso/m01_*.md

Exits 1 when it finds something, so it works as a guard before committing.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent.parent
COURSE_DIR = ROOT / "lecciones"

# A lesson file is m<NN>_<slug>.md. The pattern is this strict because Windows
# matches globs case-insensitively, so a loose "m*.md" also picked up MANUAL.md and
# reported the manual for quoting the very phrases it bans.
LESSON_GLOB = "m[0-9][0-9]_*.md"


DASHES = {"—": "raya (—)", "–": "guion medio (–)"}

# Stock phrases that show up in generated Spanish prose and say nothing.
FILLER = [
    "en el mundo de", "es importante destacar", "es importante mencionar",
    "cabe destacar", "cabe mencionar", "en resumen,", "en conclusión,",
    "sumérgete", "desbloquea", "potencia tu", "lleva tu", "no solo eso",
    "vale la pena señalar", "en el vertiginoso", "en la era digital",
]

# The voice of the old notes: written while the project was still happening. A lesson
# knows the ending before it starts, so none of these can be true in one.
DIARY = [
    "esto es una sorpresa", "no resulta como", "no resultó como",
    "esto cambia el plan", "como habíamos previsto", "como teníamos previsto",
    "no esperábamos esto", "veremos qué pasa", "a ver qué sale",
    "en el próximo apunte", "en el siguiente apunte", "spoiler",
]

FILLER_RE = re.compile("|".join(re.escape(f) for f in FILLER), re.I)
DIARY_RE = re.compile("|".join(re.escape(d) for d in DIARY), re.I)


def scan(path: Path) -> list[tuple[int, str, str]]:
    """Return (line number, what, the offending line) for each hit outside code."""
    findings: list[tuple[int, str, str]] = []
    in_code = False

    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue

        for mark, name in DASHES.items():
            if mark in line:
                findings.append((number, name, line.strip()))
        filler = FILLER_RE.search(line)
        if filler:
            findings.append((number, f"muletilla «{filler.group(0)}»", line.strip()))
        diary = DIARY_RE.search(line)
        if diary:
            findings.append((number, f"voz de diario «{diary.group(0)}»", line.strip()))

    return findings


PANEL_DIR = ROOT / "assets" / "panel"


def scan_panel() -> list[tuple[str, str, str]]:
    """Las frases del panel del módulo 30, que no viven en ningún Markdown.

    Las escribe src/twin/panel.py, una por día y por idioma, y la página las
    publica tal cual. Sin esto serían el único texto del curso que no pasa por
    esta puerta.
    """
    findings: list[tuple[str, str, str]] = []
    for fuente in sorted(PANEL_DIR.glob("semestre.*.json")):
        datos = json.loads(fuente.read_text(encoding="utf-8"))
        textos = [(a["t"], "atajo") for a in datos["atajos"]]
        for dia in datos["dias"]:
            textos += [(dia["frase"], dia["dia"]), (dia["etiqueta"], dia["dia"])]
            textos += [(m["t"], dia["dia"]) for m in dia["marcas"]]
        for texto, donde in textos:
            for mark, name in DASHES.items():
                if mark in texto:
                    findings.append((f"{fuente.name} {donde}", name, texto))
            for regla, nombre in ((FILLER_RE, "muletilla"), (DIARY_RE, "voz de diario")):
                hallado = regla.search(texto)
                if hallado:
                    findings.append((f"{fuente.name} {donde}",
                                     f"{nombre} «{hallado.group(0)}»", texto))
    return findings


def main() -> None:
    paths = [Path(a) for a in sys.argv[1:]]
    del_panel = not paths
    if not paths:
        paths = sorted(COURSE_DIR.glob(LESSON_GLOB))
        # La portada, y el texto de la página propia del panel en los dos idiomas.
        paths += [p for p in (COURSE_DIR / "curso.md", COURSE_DIR / "panel.md",
                              COURSE_DIR / "en" / "panel.md")
                  if p.exists()]
    if not paths:
        print("Todavía no hay nada que revisar.")
        return

    total = 0
    for path in paths:
        findings = scan(path)
        total += len(findings)
        print(f"{path.name[:46]:<48} {'OK' if not findings else f'{len(findings)} avisos'}")
        for number, what, line in findings:
            print(f"     línea {number}: {what}")
            print(f"       {line[:100]}")

    if del_panel:
        findings_panel = scan_panel()
        total += len(findings_panel)
        estado = "OK" if not findings_panel else f"{len(findings_panel)} avisos"
        print(f"{'las frases del panel':<48} {estado}")
        for donde, what, texto in findings_panel:
            print(f"     {donde}: {what}")
            print(f"       {texto[:100]}")

    print(f"\n{'-' * 60}")
    if total:
        print(f"{total} avisos en {len(paths)} archivos. No se sustituye la raya por un "
              f"guion: se reescribe la frase.")
        raise SystemExit(1)
    print(f"Los {len(paths)} archivos pasan las reglas de escritura.")


if __name__ == "__main__":
    main()

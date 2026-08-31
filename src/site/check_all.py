"""Run every checker and fail if any of them fails.

This exists because of a real mistake: the checkers were being run from a shell loop that
always exited zero, so a module got committed with check_clarity red and nobody noticed
until the next run. A gate that does not gate is worse than no gate, because it is
believed.

Usage:
    python src/site/check_all.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CHECKERS = [
    "check_lesson",    # la anatomía: las diez secciones, y Hazlo tú cuando hay reto
    "check_prose",     # cero rayas, cero emoji, cero muletillas
    "check_clarity",   # frases que no se enreden
    "check_numbers",   # ningún número sin una corrida detrás
    "check_sql",       # cada consulta publicada corre y su salida dice la verdad
    "check_muestras",  # y corre contra la muestra que el lector se baja, no solo contra el lago
    "check_palette",   # los acentos calculados, y AA en los dos temas
    "check_layout",    # la maqueta no vuelve a ser la de Sílice
    "check_english",   # las dos ediciones dicen los mismos números
]


def main() -> None:
    failed = []
    for name in CHECKERS:
        finished = subprocess.run([sys.executable, str(HERE / f"{name}.py")],
                                  cwd=ROOT, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace")
        state = "verde" if finished.returncode == 0 else "ROJO"
        print(f"  {name:<16} {state}")
        if finished.returncode:
            failed.append((name, finished.stdout))

    print(f"\n{'-' * 60}")
    if failed:
        for name, output in failed:
            print(f"\n=== {name} ===")
            print("\n".join(line for line in output.splitlines()
                            if line.strip().startswith(("línea", "módulo", "falta", "el ",
                                                        "«", "hay "))) or output[-900:])
        raise SystemExit(f"{len(failed)} verificadores en rojo. No commitear.")
    print(f"Los {len(CHECKERS)} verificadores en verde.")


if __name__ == "__main__":
    main()

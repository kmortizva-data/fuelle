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
CHECKERS = ["check_numbers", "check_layout", "check_english"]
# Pendientes de adaptar desde Sílice: check_lesson (la anatomía, con la sección
# Hazlo tú), check_prose (rayas y emoji), check_clarity (frases enredadas),
# check_palette (contraste en los dos temas) y check_sql (que cada consulta
# publicada se ejecute y coincida con su salida).


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

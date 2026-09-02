"""Draws every figure again, in English, and reports what it could not translate.

Runs each `figures_moduleN.py` **in its own process** with `FIG_LANG=en`. One
process each, and not one interpreter for all of them, because matplotlib keeps
state between figures and a shared run makes a drawing depend on what ran before
it. The Silice course learned that one the expensive way.

Nothing here knows how to draw. `figures_i18n` patches the three points every
visible string and every saved file passes through, so the 16 drawing scripts are
untouched and their geometry stays exactly as it was validated.

The report is the point. A figure that quietly keeps a Spanish axis in the English
edition is the failure this exists to prevent, so any visible string with no
translation is printed by name and the script exits with that count.

Correr:  .venv\\Scripts\\python.exe src\\figures_build_en.py
         .venv\\Scripts\\python.exe src\\figures_build_en.py module17 module18
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# La consola de esta máquina es cp1252, y el mensaje de SystemExit sale por
# stderr: sin reconfigurar los dos, «español» se imprime roto justo en la
# línea que dice qué falta traducir.
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SRC = Path(__file__).resolve().parent
PROJECT = SRC.parents[0]
PYTHON = PROJECT / ".venv" / "Scripts" / "python.exe"


def scripts(filtros: list[str]) -> list[Path]:
    """Los scripts de figuras, en orden de módulo y no alfabético."""
    todos = sorted(SRC.glob("figures_module*.py"),
                   key=lambda p: int(p.stem.removeprefix("figures_module")))
    if not filtros:
        return todos
    return [p for p in todos if any(f in p.stem for f in filtros)]


def corre(script: Path) -> tuple[int, list[str], list[str], str]:
    """Corre un script en inglés y devuelve qué escribió y qué no supo traducir."""
    with tempfile.TemporaryDirectory() as tmp:
        informe = Path(tmp) / "i18n.json"
        entorno = {**os.environ, "FIG_LANG": "en", "FIG_I18N_REPORT": str(informe),
                   "PYTHONIOENCODING": "utf-8"}
        proceso = subprocess.run([str(PYTHON), str(script)], cwd=str(PROJECT),
                                 capture_output=True, text=True, encoding="utf-8",
                                 errors="replace", env=entorno)
        datos = {}
        if informe.exists():
            datos = json.loads(informe.read_text(encoding="utf-8"))
    return (proceso.returncode, datos.get("escritas", []), datos.get("sin_traducir", []),
            (proceso.stdout + proceso.stderr))


def main() -> None:
    filtros = sys.argv[1:]
    objetivo = scripts(filtros)
    if not objetivo:
        raise SystemExit(f"Ningún script de figuras casa con {filtros}")

    escritas, sin_traducir, fallados = [], set(), []
    for script in objetivo:
        codigo, hechas, faltan, salida = corre(script)
        escritas += hechas
        sin_traducir |= set(faltan)
        estado = f"{len(hechas)} figuras" if codigo == 0 else "FALLA"
        print(f"  {script.stem:<24} {estado}")
        if codigo != 0:
            fallados.append(script.stem)
            for linea in salida.strip().splitlines()[-6:]:
                print(f"      {linea}")

    print()
    print(f"  {len(escritas)} ficheros en inglés escritos")

    if fallados:
        raise SystemExit(f"{len(fallados)} scripts fallaron: {', '.join(fallados)}")

    if sin_traducir:
        print(f"  {len(sin_traducir)} cadenas visibles SIN traducir:")
        for texto in sorted(sin_traducir):
            print(f"    {texto!r}")
        print()
        print("  Se añaden a TRADUCCIONES en src/figures_i18n.py, o a NEUTRAL si")
        print("  no son prosa (nombres de señal, unidades, identificadores del lago).")
        raise SystemExit(f"{len(sin_traducir)} cadenas siguen en español")

    print("  Ninguna cadena visible se queda en español.")


if __name__ == "__main__":
    main()

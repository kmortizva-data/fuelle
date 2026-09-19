"""Open Dagster's web interface on this project: the graph, the runs, the checks.

It exists for one line, the one that sets DAGSTER_HOME. Started by hand, Dagster
does not know about dagster_home/, and without that folder's dagster.yaml it
sends usage statistics to its authors. Going through here, it never does.

The interface is only for looking. The rebuild that module 29 measures runs
without it, through Dagster's Python API, in reconstruye.py; the runs it makes
show up here all the same, because both use the same DAGSTER_HOME.

Run:  .venv\\Scripts\\python.exe src\\orchestration\\abre.py
Then: http://localhost:3029  (Ctrl+C here to stop it)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
PUERTO = 3029  # por el módulo 29, y lejos de los puertos de los otros proyectos

sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    entorno = {**os.environ, "DAGSTER_HOME": str(PROJECT / "dagster_home")}
    dagster = PROJECT / ".venv" / "Scripts" / "dagster.exe"
    print(f"  Dagster en http://localhost:{PUERTO}  (Ctrl+C para pararlo)")
    subprocess.run([str(dagster), "dev", "-f",
                    str(PROJECT / "src" / "orchestration" / "definitions.py"),
                    "-p", str(PUERTO)], cwd=PROJECT, env=entorno)


if __name__ == "__main__":
    main()

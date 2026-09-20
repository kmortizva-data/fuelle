"""The folio, printed to PDF. Module 31.

No LaTeX. The page written by `folio.py` is printed by a headless browser, which
is what turns the course's own fonts, colours and print rules into a PDF that
looks like the rest of the project instead of like a different document.

Two things this refuses to do quietly:

  - print without a browser: it says which ones it looked for;
  - hand over a folio that is not one page. If the text grows past a side of A4,
    the answer is to cut text, not to shrink the type, so this counts the pages
    in the PDF it just made and fails on two.

**Run it from PowerShell, never from the Bash tool**: launched from Git Bash,
this same Edge exits with code 0 and writes no file, silently. That cost an
afternoon in another project and is written down in the machine's memory.

Correr:  .venv\\Scripts\\python.exe src\\entrega\\imprime.py
"""

from __future__ import annotations

import io
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

sys.stdout.reconfigure(encoding="utf-8")

PROJECT = Path(__file__).resolve().parents[2]
OUT = PROJECT / "out"
RESULTS = PROJECT / "results" / "m31_folio.json"

PAGINAS = {"folio.html": "veredicto.pdf", "folio.en.html": "verdict.pdf"}

NAVEGADORES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
]


def navegador() -> Path:
    for ruta in NAVEGADORES:
        if ruta.exists():
            return ruta
    raise SystemExit("No hay navegador para imprimir. Se buscó en:\n  "
                     + "\n  ".join(str(r) for r in NAVEGADORES))


def hojas(pdf: Path) -> int:
    """Cuántas páginas trae el PDF, contadas en su propio índice de objetos."""
    crudo = pdf.read_bytes()
    return len(re.findall(rb"/Type\s*/Page[^s]", crudo)) or 1


def imprime(exe: Path, pagina: Path, destino: Path) -> None:
    # La ruta del proyecto lleva espacios, así que la URL va con %20. El perfil
    # aparte evita que una sesión abierta del navegador se quede con la orden.
    #
    # Y va en el temporal del sistema, NO en out/: la primera versión lo dejaba
    # dentro, el espejado del portafolio se llevó las 337 carpetas del perfil de
    # Chromium al sitio, y acabaron en un commit. Lo que se publica es out/, así
    # que ahí no puede quedar nada que no sea la página.
    url = "file:///" + quote(str(pagina).replace("\\", "/"))
    perfil = Path(tempfile.gettempdir()) / "fuelle_impresion"
    orden = [str(exe), "--headless=new", "--disable-gpu",
             f"--user-data-dir={perfil}", "--no-pdf-header-footer",
             "--virtual-time-budget=10000", f"--print-to-pdf={destino}", url]
    destino.unlink(missing_ok=True)
    r = subprocess.run(orden, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=180)
    if not destino.exists():
        raise SystemExit(f"El navegador salió con {r.returncode} y no escribió "
                         f"{destino.name}. Si se lanzó desde Bash, ese es el motivo: "
                         "este paso va desde PowerShell.")


def main() -> None:
    exe = navegador()
    print(f"  imprime con {exe.name}")
    medido = {}
    for nombre, salida in PAGINAS.items():
        pagina = OUT / nombre
        if not pagina.exists():
            raise SystemExit(f"Falta {pagina.relative_to(PROJECT)}. "
                             "Corre src/entrega/folio.py primero.")
        destino = OUT / salida
        imprime(exe, pagina, destino)
        caras = hojas(destino)
        kb = round(destino.stat().st_size / 1024, 1)
        medido[salida] = {"kb": kb, "caras": caras}
        print(f"  {salida:<16} {kb:>6.1f} KB   {caras} cara{'s' if caras != 1 else ''}")
        if caras != 1:
            raise SystemExit(f"{salida} ocupa {caras} caras y un folio es un folio. "
                             "Se quita texto, no se encoge la letra.")

    # Lo impreso se apunta donde el módulo 31 lee sus cifras, para que la lección
    # no tenga que creerse el peso de un fichero que no ha visto.
    if RESULTS.exists():
        datos = json.loads(io.open(RESULTS, encoding="utf-8").read())
        datos["impreso"] = medido
        with io.open(RESULTS, "w", encoding="utf-8") as fh:
            json.dump(datos, fh, ensure_ascii=False, indent=2)
        print(f"  apuntado en {RESULTS.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
